#!/usr/bin/env python3
"""
Three-Computer FLOPS Calculator
Calculates TFLOPS and PFLOPS for:
1. Puget Workstation E211-XL (AMD EPYC + RTX 6000 Blackwell)
2. NVIDIA DGX Station (Windows)
3. NVIDIA DGX Spark
"""

import json
from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum


class PrecisionType(Enum):
    FP32 = "FP32 (Single Precision)"
    FP64 = "FP64 (Double Precision)"
    FP16 = "FP16 (Half Precision)"
    BF16 = "BF16 (BFloat16)"
    INT8 = "INT8"
    FP8 = "FP8"


@dataclass
class CPU:
    """CPU specification for FLOPS calculation."""
    name: str
    cores: int
    threads_per_core: int
    clock_speed_ghz: float
    flops_per_cycle: float
    quantity: int = 1
    
    def calculate_flops(self) -> float:
        """Calculate FLOPS for this CPU configuration."""
        total_cores = self.cores * self.threads_per_core * self.quantity
        flops = total_cores * self.clock_speed_ghz * 1e9 * self.flops_per_cycle
        return flops


@dataclass
class GPU:
    """GPU specification for FLOPS calculation."""
    name: str
    cuda_cores: int
    clock_speed_ghz: float
    flops_per_cycle_fp32: float
    flops_per_cycle_fp64: float = 1.0
    tensor_cores: int = 0
    tensor_flops_per_cycle_fp16: float = 0.0
    tensor_flops_per_cycle_fp8: float = 0.0
    memory_gb: int = 0
    quantity: int = 1
    
    def calculate_flops(self, precision: PrecisionType = PrecisionType.FP32) -> float:
        """Calculate FLOPS for this GPU at specified precision."""
        if precision == PrecisionType.FP64:
            flops = (self.cuda_cores * self.quantity * 
                    self.clock_speed_ghz * 1e9 * self.flops_per_cycle_fp64)
        elif precision == PrecisionType.FP16 or precision == PrecisionType.BF16:
            if self.tensor_cores > 0:
                flops = (self.tensor_cores * self.quantity * 
                        self.clock_speed_ghz * 1e9 * self.tensor_flops_per_cycle_fp16)
            else:
                # FP16 without tensor cores is typically 2x FP32
                flops = (self.cuda_cores * self.quantity * 
                        self.clock_speed_ghz * 1e9 * self.flops_per_cycle_fp32 * 2)
        elif precision == PrecisionType.FP8:
            if self.tensor_cores > 0:
                flops = (self.tensor_cores * self.quantity * 
                        self.clock_speed_ghz * 1e9 * self.tensor_flops_per_cycle_fp8)
            else:
                flops = 0
        else:  # FP32 default
            flops = (self.cuda_cores * self.quantity * 
                    self.clock_speed_ghz * 1e9 * self.flops_per_cycle_fp32)
        return flops


@dataclass
class System:
    """Complete computer system specification."""
    name: str
    description: str
    cpus: List[CPU]
    gpus: List[GPU]
    ram_tb: float = 0.0
    storage_tb: float = 0.0
    os: str = ""
    
    def calculate_total_flops(self, precision: PrecisionType = PrecisionType.FP32) -> Dict:
        """Calculate total FLOPS for this system."""
        cpu_flops = sum(cpu.calculate_flops() for cpu in self.cpus)
        gpu_flops = sum(gpu.calculate_flops(precision) for gpu in self.gpus)
        
        return {
            'cpu_flops': cpu_flops,
            'gpu_flops': gpu_flops,
            'total_flops': cpu_flops + gpu_flops
        }


def format_flops(flops: float) -> Dict[str, float]:
    """Format FLOPS value into different units."""
    return {
        'FLOPS': flops,
        'KFLOPS': flops / 1e3,
        'MFLOPS': flops / 1e6,
        'GFLOPS': flops / 1e9,
        'TFLOPS': flops / 1e12,
        'PFLOPS': flops / 1e15,
        'EFLOPS': flops / 1e18
    }


def create_puget_workstation() -> System:
    """
    Computer 1: Puget Workstation E211-XL
    Based on user specifications
    """
    # AMD EPYC 9965 "Turin" - 192 cores, 2.25 GHz base
    # Zen 5 architecture with AVX-512 support (32 FLOPS/cycle for FP32)
    cpu = CPU(
        name="AMD EPYC 9965",
        cores=192,
        threads_per_core=2,  # SMT enabled
        clock_speed_ghz=2.25,
        flops_per_cycle=32.0,  # AVX-512 FP32
        quantity=2  # Dual CPU configuration
    )
    
    # NVIDIA RTX 6000 Blackwell Max-Q Workstation Edition
    # Based on GB202 Blackwell architecture
    # Estimated specs based on Blackwell architecture
    gpu = GPU(
        name="NVIDIA RTX 6000 Blackwell Max-Q",
        cuda_cores=18176,  # Based on GB202 full config
        clock_speed_ghz=1.5,  # Max-Q variant (lower power)
        flops_per_cycle_fp32=2.0,
        flops_per_cycle_fp64=1.0,
        tensor_cores=568,  # 4th gen Tensor Cores
        tensor_flops_per_cycle_fp16=256.0,  # FP16/BF16 with sparsity
        tensor_flops_per_cycle_fp8=512.0,  # FP8 with sparsity
        memory_gb=96,
        quantity=1
    )
    
    return System(
        name="Puget Workstation E211-XL",
        description="""
        High-end workstation with dual AMD EPYC 9965 CPUs and 
        NVIDIA RTX 6000 Blackwell Max-Q workstation GPU.
        Optimized for professional workloads with ECC memory.
        """,
        cpus=[cpu],
        gpus=[gpu],
        ram_tb=2.25,
        storage_tb=30.72 + 30.72 + 24 + 24,  # Total storage
        os="Linux Ubuntu 24.04 LTS"
    )


def create_dgx_station() -> System:
    """
    Computer 2: NVIDIA DGX Station
    Based on published specifications for DGX Station A100/H100
    Using latest available DGX Station H100 specs
    """
    # AMD EPYC 7003 series (typical for DGX Station)
    cpu = CPU(
        name="AMD EPYC 7763 (DGX Station Host)",
        cores=64,
        threads_per_core=2,
        clock_speed_ghz=2.45,
        flops_per_cycle=32.0,  # AVX-512
        quantity=1
    )
    
    # 4x NVIDIA H100 GPUs (DGX Station H100 configuration)
    # H100 SXM5 specs
    gpu = GPU(
        name="NVIDIA H100 SXM5",
        cuda_cores=14592,
        clock_speed_ghz=1.98,  # H100 boost clock
        flops_per_cycle_fp32=2.0,
        flops_per_cycle_fp64=1.0,
        tensor_cores=456,  # 4th gen Tensor Cores
        tensor_flops_per_cycle_fp16=992.0,  # FP16 with sparsity (H100 feature)
        tensor_flops_per_cycle_fp8=1984.0,  # FP8 with sparsity
        memory_gb=80,
        quantity=4  # DGX Station has 4 GPUs
    )
    
    return System(
        name="NVIDIA DGX Station H100",
        description="""
        AI supercomputer for Windows/Linux desktop environments.
        Features 4x H100 GPUs with NVLink interconnect.
        Designed for enterprise AI development and training.
        """,
        cpus=[cpu],
        gpus=[gpu],
        ram_tb=2.0,  # Typical DGX Station configuration
        storage_tb=30.0,  # Typical NVMe storage
        os="Windows 11 Pro / Ubuntu 22.04 LTS"
    )


def create_dgx_spark() -> System:
    """
    Computer 3: NVIDIA DGX Spark
    Based on announced specifications for personal AI supercomputer
    Note: DGX Spark is a newer product with Grace CPU + Blackwell GPU
    """
    # NVIDIA Grace CPU (ARM-based)
    # Grace CPU Superchip specifications
    cpu = CPU(
        name="NVIDIA Grace CPU Superchip",
        cores=72,
        threads_per_core=1,  # ARM cores, no SMT
        clock_speed_ghz=3.4,
        flops_per_cycle=16.0,  # NEON/Scalable Vector Extension
        quantity=1
    )
    
    # Blackwell B200 GPU (DGX Spark configuration)
    # Based on announced B200 specifications
    gpu = GPU(
        name="NVIDIA Blackwell B200",
        cuda_cores=20736,
        clock_speed_ghz=1.6,
        flops_per_cycle_fp32=2.0,
        flops_per_cycle_fp64=1.0,
        tensor_cores=648,  # 5th gen Tensor Cores
        tensor_flops_per_cycle_fp16=1280.0,  # FP16/BF16 with sparsity
        tensor_flops_per_cycle_fp8=2560.0,  # FP8 with sparsity
        memory_gb=188,  # HBM3e
        quantity=1
    )
    
    return System(
        name="NVIDIA DGX Spark",
        description="""
        Personal AI supercomputer with Grace CPU and Blackwell GPU.
        Compact form factor designed for individual developers.
        Optimized for LLM development and AI inference.
        """,
        cpus=[cpu],
        gpus=[gpu],
        ram_tb=0.512,  # Unified memory architecture
        storage_tb=8.0,
        os="Ubuntu 24.04 LTS with DGX OS"
    )


def display_system_results(system: System, precision: PrecisionType = PrecisionType.FP32):
    """Display detailed FLOPS results for a system."""
    print("\n" + "="*80)
    print(f"🖥️  {system.name}")
    print("="*80)
    print(f"\nDescription:{system.description}")
    print(f"OS: {system.os}")
    print(f"RAM: {system.ram_tb:.2f} TB")
    print(f"Storage: {system.storage_tb:.2f} TB")
    
    # Display hardware configuration
    print("\n📋 HARDWARE CONFIGURATION:")
    print("-"*80)
    
    for i, cpu in enumerate(system.cpus, 1):
        print(f"\n  CPU #{i}: {cpu.name}")
        print(f"    • Cores: {cpu.cores} x {cpu.quantity} = {cpu.cores * cpu.quantity} total")
        print(f"    • Threads per Core: {cpu.threads_per_core}")
        print(f"    • Clock Speed: {cpu.clock_speed_ghz} GHz")
        print(f"    • FLOPS/Cycle: {cpu.flops_per_cycle} ({'AVX-512' if cpu.flops_per_cycle >= 32 else 'AVX2' if cpu.flops_per_cycle >= 16 else 'SSE'})")
    
    for i, gpu in enumerate(system.gpus, 1):
        print(f"\n  GPU #{i}: {gpu.name} (x{gpu.quantity})")
        print(f"    • CUDA Cores: {gpu.cuda_cores} each")
        print(f"    • Clock Speed: {gpu.clock_speed_ghz} GHz")
        print(f"    • Memory: {gpu.memory_gb} GB")
        if gpu.tensor_cores > 0:
            print(f"    • Tensor Cores: {gpu.tensor_cores} (5th Gen)")
    
    # Calculate and display FLOPS
    results = system.calculate_total_flops(precision)
    
    print("\n📊 PERFORMANCE METRICS:")
    print("-"*80)
    print(f"\nPrecision: {precision.value}")
    
    # CPU Performance
    cpu_formatted = format_flops(results['cpu_flops'])
    print(f"\n  👤 CPU Performance:")
    print(f"    • GFLOPS: {cpu_formatted['GFLOPS']:,.2f}")
    print(f"    • TFLOPS: {cpu_formatted['TFLOPS']:,.4f}")
    if cpu_formatted['PFLOPS'] >= 0.001:
        print(f"    • PFLOPS: {cpu_formatted['PFLOPS']:,.6f}")
    
    # GPU Performance
    gpu_formatted = format_flops(results['gpu_flops'])
    print(f"\n  🎮 GPU Performance:")
    print(f"    • GFLOPS: {gpu_formatted['GFLOPS']:,.2f}")
    print(f"    • TFLOPS: {gpu_formatted['TFLOPS']:,.4f}")
    if gpu_formatted['PFLOPS'] >= 0.001:
        print(f"    • PFLOPS: {gpu_formatted['PFLOPS']:,.6f}")
    
    # Total Performance
    total_formatted = format_flops(results['total_flops'])
    print("\n" + "="*80)
    print(f"  🚀 TOTAL SYSTEM PERFORMANCE ({precision.value}):")
    print("="*80)
    print(f"\n    • FLOPS:  {total_formatted['FLOPS']:,.2f}")
    print(f"    • GFLOPS: {total_formatted['GFLOPS']:,.2f}")
    print(f"    • TFLOPS: {total_formatted['TFLOPS']:,.4f}")
    print(f"    • PFLOPS: {total_formatted['PFLOPS']:,.6f}")
    
    # Achievement badges
    if total_formatted['PFLOPS'] >= 1:
        print(f"\n    🏆 PLATINUM: Your system achieves {total_formatted['PFLOPS']:.2f} PetaFLOPS!")
    elif total_formatted['TFLOPS'] >= 100:
        print(f"\n    🥇 GOLD: Your system achieves {total_formatted['TFLOPS']:.2f} TeraFLOPS!")
    elif total_formatted['TFLOPS'] >= 10:
        print(f"\n    🥈 SILVER: Your system achieves {total_formatted['TFLOPS']:.2f} TeraFLOPS!")
    elif total_formatted['TFLOPS'] >= 1:
        print(f"\n    🥉 BRONZE: Your system achieves {total_formatted['TFLOPS']:.2f} TeraFLOPS!")
    
    print("="*80)
    
    return total_formatted


def compare_all_systems():
    """Compare all three systems side by side."""
    systems = [
        create_puget_workstation(),
        create_dgx_station(),
        create_dgx_spark()
    ]
    
    precisions = [
        PrecisionType.FP32,
        PrecisionType.FP16,
        PrecisionType.FP8
    ]
    
    print("\n" + "🔬"*40)
    print("           THREE-COMPUTER COMPARISON ANALYSIS")
    print("🔬"*40)
    
    for precision in precisions:
        print(f"\n\n{'='*90}")
        print(f"COMPARISON AT {precision.value}")
        print(f"{'='*90}")
        print(f"\n{'System':<35} {'CPU TFLOPS':>15} {'GPU TFLOPS':>15} {'TOTAL TFLOPS':>15}")
        print("-"*90)
        
        best_total = 0
        best_system = ""
        
        for system in systems:
            results = system.calculate_total_flops(precision)
            formatted = format_flops(results['total_flops'])
            
            cpu_tflops = format_flops(results['cpu_flops'])['TFLOPS']
            gpu_tflops = format_flops(results['gpu_flops'])['TFLOPS']
            total_tflops = formatted['TFLOPS']
            
            marker = " ⭐" if total_tflops > best_total else ""
            if total_tflops > best_total:
                best_total = total_tflops
                best_system = system.name
            
            print(f"{system.name:<35} {cpu_tflops:>14.4f} {gpu_tflops:>14.4f} {total_tflops:>14.4f}{marker}")
        
        print("-"*90)
        print(f"🏆 Best performer in {precision.value}: {best_system}")
        print(f"   Peak Performance: {format_flops(best_total)['TFLOPS']:,.4f} TFLOPS")
    
    return systems


def export_comparison_json(filename: str = "three_computer_comparison.json"):
    """Export all system comparisons to JSON."""
    systems = [
        create_puget_workstation(),
        create_dgx_station(),
        create_dgx_spark()
    ]
    
    precisions = [
        PrecisionType.FP32,
        PrecisionType.FP16,
        PrecisionType.FP64,
        PrecisionType.FP8
    ]
    
    export_data = {
        'systems': [],
        'comparison': {}
    }
    
    for system in systems:
        system_data = {
            'name': system.name,
            'description': system.description.strip(),
            'os': system.os,
            'ram_tb': system.ram_tb,
            'storage_tb': system.storage_tb,
            'cpus': [],
            'gpus': [],
            'performance': {}
        }
        
        for cpu in system.cpus:
            system_data['cpus'].append({
                'name': cpu.name,
                'cores': cpu.cores,
                'threads_per_core': cpu.threads_per_core,
                'clock_ghz': cpu.clock_speed_ghz,
                'quantity': cpu.quantity
            })
        
        for gpu in system.gpus:
            system_data['gpus'].append({
                'name': gpu.name,
                'cuda_cores': gpu.cuda_cores,
                'clock_ghz': gpu.clock_speed_ghz,
                'memory_gb': gpu.memory_gb,
                'tensor_cores': gpu.tensor_cores,
                'quantity': gpu.quantity
            })
        
        for precision in precisions:
            results = system.calculate_total_flops(precision)
            formatted = format_flops(results['total_flops'])
            system_data['performance'][precision.name] = {
                'cpu_flops': results['cpu_flops'],
                'gpu_flops': results['gpu_flops'],
                'total_flops': results['total_flops'],
                'tflops': formatted['TFLOPS'],
                'pflops': formatted['PFLOPS']
            }
        
        export_data['systems'].append(system_data)
    
    # Add comparison summary
    for precision in precisions:
        comparison = {}
        best_tflops = 0
        best_system = ""
        
        for system in systems:
            results = system.calculate_total_flops(precision)
            tflops = format_flops(results['total_flops'])['TFLOPS']
            comparison[system.name] = tflops
            
            if tflops > best_tflops:
                best_tflops = tflops
                best_system = system.name
        
        export_data['comparison'][precision.name] = {
            'all_systems': comparison,
            'best_system': best_system,
            'best_tflops': best_tflops
        }
    
    with open(filename, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print(f"\n✓ Comparison data exported to {filename}")
    return export_data


def main():
    """Main function to run the three-computer FLOPS calculator."""
    print("\n" + "🚀"*40)
    print("       THREE-COMPUTER FLOPS CALCULATOR")
    print("   Professional Workstation vs DGX Systems")
    print("🚀"*40)
    
    print("\nThis calculator analyzes three high-performance systems:")
    print("\n  1. Puget Workstation E211-XL")
    print("     • Dual AMD EPYC 9965 (192-core each)")
    print("     • NVIDIA RTX 6000 Blackwell Max-Q")
    print("     • 2.25TB RAM, 109TB Storage")
    print("\n  2. NVIDIA DGX Station H100")
    print("     • AMD EPYC 7763 Host CPU")
    print("     • 4x NVIDIA H100 SXM5 GPUs")
    print("     • Enterprise AI Development Platform")
    print("\n  3. NVIDIA DGX Spark")
    print("     • NVIDIA Grace CPU Superchip")
    print("     • NVIDIA Blackwell B200 GPU")
    print("     • Personal AI Supercomputer")
    
    while True:
        print("\n" + "-"*80)
        print("\nOPTIONS:")
        print("  1. Analyze Puget Workstation E211-XL")
        print("  2. Analyze NVIDIA DGX Station H100")
        print("  3. Analyze NVIDIA DGX Spark")
        print("  4. Compare All Three Systems")
        print("  5. Export Results to JSON")
        print("  6. Exit")
        print("-"*80)
        
        choice = input("\nEnter your choice (1-6): ").strip()
        
        if choice == '1':
            system = create_puget_workstation()
            print("\nSelect precision:")
            print("  1. FP32 (Single Precision) - Standard for most workloads")
            print("  2. FP16/BF16 (Half Precision) - AI/ML training")
            print("  3. FP8 - Next-gen AI inference")
            prec_choice = input("\nChoice (1-3): ").strip()
            
            if prec_choice == '1':
                display_system_results(system, PrecisionType.FP32)
            elif prec_choice == '2':
                display_system_results(system, PrecisionType.FP16)
            elif prec_choice == '3':
                display_system_results(system, PrecisionType.FP8)
            else:
                display_system_results(system, PrecisionType.FP32)
        
        elif choice == '2':
            system = create_dgx_station()
            print("\nSelect precision:")
            print("  1. FP32 (Single Precision)")
            print("  2. FP16/BF16 (Half Precision) - Optimal for H100")
            print("  3. FP8 - Maximum AI throughput")
            prec_choice = input("\nChoice (1-3): ").strip()
            
            if prec_choice == '1':
                display_system_results(system, PrecisionType.FP32)
            elif prec_choice == '2':
                display_system_results(system, PrecisionType.FP16)
            elif prec_choice == '3':
                display_system_results(system, PrecisionType.FP8)
            else:
                display_system_results(system, PrecisionType.FP32)
        
        elif choice == '3':
            system = create_dgx_spark()
            print("\nSelect precision:")
            print("  1. FP32 (Single Precision)")
            print("  2. FP16/BF16 (Half Precision) - Optimal for Blackwell")
            print("  3. FP8 - Maximum AI throughput")
            prec_choice = input("\nChoice (1-3): ").strip()
            
            if prec_choice == '1':
                display_system_results(system, PrecisionType.FP32)
            elif prec_choice == '2':
                display_system_results(system, PrecisionType.FP16)
            elif prec_choice == '3':
                display_system_results(system, PrecisionType.FP8)
            else:
                display_system_results(system, PrecisionType.FP32)
        
        elif choice == '4':
            compare_all_systems()
        
        elif choice == '5':
            filename = input("Enter filename (default: three_computer_comparison.json): ").strip()
            if not filename:
                filename = "three_computer_comparison.json"
            export_comparison_json(filename)
        
        elif choice == '6':
            print("\n👋 Thank you for using the Three-Computer FLOPS Calculator!")
            print("   Goodbye!\n")
            break
        
        else:
            print("\n❌ Invalid choice. Please enter 1-6.")


if __name__ == "__main__":
    main()
