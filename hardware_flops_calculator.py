#!/usr/bin/env python3
"""
Hardware FLOPS Calculator
Calculates TFLOPS and PFLOPS for CPUs, GPUs, and other hardware components.
"""

import json
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class CPU:
    """CPU specification for FLOPS calculation."""
    name: str
    cores: int
    threads_per_core: int
    clock_speed_ghz: float
    flops_per_cycle: float  # Depends on architecture (e.g., AVX2, AVX-512)
    
    def calculate_flops(self) -> float:
        """Calculate FLOPS for this CPU."""
        total_cores = self.cores * self.threads_per_core
        # FLOPS = cores * threads * clock_speed * flops_per_cycle
        flops = total_cores * self.clock_speed_ghz * 1e9 * self.flops_per_cycle
        return flops


@dataclass
class GPU:
    """GPU specification for FLOPS calculation."""
    name: str
    cuda_cores: int  # or stream processors for AMD
    clock_speed_ghz: float
    flops_per_cycle: float  # Usually 2 for FP32, 1 for FP64
    tensor_cores: int = 0
    tensor_flops_per_cycle: float = 0.0
    
    def calculate_flops(self, use_tensor: bool = False) -> float:
        """Calculate FLOPS for this GPU."""
        if use_tensor and self.tensor_cores > 0:
            # Tensor core performance
            flops = self.tensor_cores * self.clock_speed_ghz * 1e9 * self.tensor_flops_per_cycle
        else:
            # Standard CUDA/stream processor performance
            flops = self.cuda_cores * self.clock_speed_ghz * 1e9 * self.flops_per_cycle
        return flops


@dataclass
class TPU:
    """TPU specification for FLOPS calculation."""
    name: str
    matrix_units: int
    clock_speed_ghz: float
    operations_per_cycle: float
    
    def calculate_flops(self) -> float:
        """Calculate FLOPS for this TPU."""
        flops = self.matrix_units * self.clock_speed_ghz * 1e9 * self.operations_per_cycle
        return flops


@dataclass
class FPGA:
    """FPGA specification for FLOPS calculation."""
    name: str
    dsp_blocks: int
    clock_speed_mhz: float
    operations_per_block: float
    
    def calculate_flops(self) -> float:
        """Calculate FLOPS for this FPGA."""
        flops = self.dsp_blocks * self.clock_speed_mhz * 1e6 * self.operations_per_block
        return flops


class HardwareFLOPSCalculator:
    """Main calculator class for computing system FLOPS."""
    
    def __init__(self):
        self.cpus: List[CPU] = []
        self.gpus: List[GPU] = []
        self.tpus: List[TPU] = []
        self.fpgas: List[FPGA] = []
    
    def add_cpu(self, cpu: CPU):
        """Add a CPU to the system."""
        self.cpus.append(cpu)
        print(f"✓ Added CPU: {cpu.name}")
    
    def add_gpu(self, gpu: GPU):
        """Add a GPU to the system."""
        self.gpus.append(gpu)
        print(f"✓ Added GPU: {gpu.name}")
    
    def add_tpu(self, tpu: TPU):
        """Add a TPU to the system."""
        self.tpus.append(tpu)
        print(f"✓ Added TPU: {tpu.name}")
    
    def add_fpga(self, fpga: FPGA):
        """Add an FPGA to the system."""
        self.fpgas.append(fpga)
        print(f"✓ Added FPGA: {fpga.name}")
    
    def calculate_total_flops(self) -> dict:
        """Calculate total FLOPS from all hardware components."""
        total_flops = 0.0
        breakdown = {}
        
        # CPU FLOPS
        cpu_flops = sum(cpu.calculate_flops() for cpu in self.cpus)
        if cpu_flops > 0:
            breakdown['CPU'] = cpu_flops
            total_flops += cpu_flops
        
        # GPU FLOPS (standard)
        gpu_flops = sum(gpu.calculate_flops(use_tensor=False) for gpu in self.gpus)
        if gpu_flops > 0:
            breakdown['GPU'] = gpu_flops
            total_flops += gpu_flops
        
        # GPU Tensor Core FLOPS (separate metric)
        tensor_flops = sum(gpu.calculate_flops(use_tensor=True) for gpu in self.gpus 
                          if gpu.tensor_cores > 0)
        if tensor_flops > 0:
            breakdown['GPU_Tensor'] = tensor_flops
        
        # TPU FLOPS
        tpu_flops = sum(tpu.calculate_flops() for tpu in self.tpus)
        if tpu_flops > 0:
            breakdown['TPU'] = tpu_flops
            total_flops += tpu_flops
        
        # FPGA FLOPS
        fpga_flops = sum(fpga.calculate_flops() for fpga in self.fpgas)
        if fpga_flops > 0:
            breakdown['FPGA'] = fpga_flops
            total_flops += fpga_flops
        
        breakdown['TOTAL'] = total_flops
        
        return breakdown
    
    def format_flops(self, flops: float) -> dict:
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
    
    def display_results(self):
        """Display formatted FLOPS results."""
        print("\n" + "="*70)
        print("HARDWARE FLOPS CALCULATION RESULTS")
        print("="*70)
        
        breakdown = self.calculate_total_flops()
        
        if not breakdown:
            print("\nNo hardware components added yet!")
            return
        
        # Display individual components
        print("\n📊 COMPONENT BREAKDOWN:")
        print("-"*70)
        
        for component, flops in breakdown.items():
            if component == 'TOTAL':
                continue
            
            formatted = self.format_flops(flops)
            print(f"\n{component}:")
            print(f"  • GFLOPS: {formatted['GFLOPS']:,.2f}")
            print(f"  • TFLOPS: {formatted['TFLOPS']:,.4f}")
            if formatted['PFLOPS'] >= 0.001:
                print(f"  • PFLOPS: {formatted['PFLOPS']:,.6f}")
        
        # Display totals
        print("\n" + "="*70)
        print("🎯 TOTAL SYSTEM PERFORMANCE:")
        print("="*70)
        
        total_flops = breakdown.get('TOTAL', 0)
        formatted_total = self.format_flops(total_flops)
        
        print(f"\n  FLOPS:  {formatted_total['FLOPS']:,.2f}")
        print(f"  GFLOPS: {formatted_total['GFLOPS']:,.2f}")
        print(f"  TFLOPS: {formatted_total['TFLOPS']:,.4f}")
        print(f"  PFLOPS: {formatted_total['PFLOPS']:,.6f}")
        
        if formatted_total['PFLOPS'] >= 1:
            print(f"\n  🚀 Your system achieves {formatted_total['PFLOPS']:.2f} PetaFLOPS!")
        elif formatted_total['TFLOPS'] >= 1:
            print(f"\n  ⚡ Your system achieves {formatted_total['TFLOPS']:.2f} TeraFLOPS!")
        
        print("="*70)
    
    def export_json(self, filename: str = "flops_results.json"):
        """Export results to JSON file."""
        breakdown = self.calculate_total_flops()
        results = {
            'components': {},
            'totals': {}
        }
        
        for component, flops in breakdown.items():
            formatted = self.format_flops(flops)
            results['components' if component != 'TOTAL' else 'totals'][component] = formatted
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n✓ Results exported to {filename}")


def interactive_mode():
    """Run the calculator in interactive mode."""
    print("\n" + "="*70)
    print("🖥️  HARDWARE FLOPS CALCULATOR")
    print("="*70)
    print("\nThis tool calculates TFLOPS and PFLOPS for your hardware setup.")
    print("Supports: CPUs, GPUs, TPUs, and FPGAs\n")
    
    calculator = HardwareFLOPSCalculator()
    
    while True:
        print("\n" + "-"*70)
        print("OPTIONS:")
        print("  1. Add CPU")
        print("  2. Add GPU")
        print("  3. Add TPU")
        print("  4. Add FPGA")
        print("  5. Calculate & Display Results")
        print("  6. Export Results to JSON")
        print("  7. Exit")
        print("-"*70)
        
        choice = input("\nEnter your choice (1-7): ").strip()
        
        if choice == '1':
            print("\n--- Add CPU ---")
            name = input("CPU Name (e.g., Intel i9-13900K): ").strip()
            cores = int(input("Number of Cores: ").strip())
            threads = int(input("Threads per Core (usually 1 or 2): ").strip())
            clock = float(input("Clock Speed (GHz): ").strip())
            print("\nFLOPS per cycle depends on instruction set:")
            print("  - Standard (SSE): 4")
            print("  - AVX2: 16")
            print("  - AVX-512: 32")
            flops_cycle = float(input("FLOPS per Cycle: ").strip())
            
            cpu = CPU(name, cores, threads, clock, flops_cycle)
            calculator.add_cpu(cpu)
        
        elif choice == '2':
            print("\n--- Add GPU ---")
            name = input("GPU Name (e.g., NVIDIA RTX 4090): ").strip()
            cuda_cores = int(input("CUDA Cores / Stream Processors: ").strip())
            clock = float(input("Boost Clock Speed (GHz): ").strip())
            print("\nFLOPS per cycle:")
            print("  - FP32 (single precision): 2")
            print("  - FP64 (double precision): 1")
            flops_cycle = float(input("FLOPS per Cycle: ").strip())
            
            has_tensor = input("Has Tensor Cores? (y/n): ").strip().lower()
            tensor_cores = 0
            tensor_flops = 0.0
            
            if has_tensor == 'y':
                tensor_cores = int(input("Number of Tensor Cores: ").strip())
                print("\nTensor Core FLOPS per cycle (FP16/BF16): typically 64-256")
                tensor_flops = float(input("Tensor FLOPS per Cycle: ").strip())
            
            gpu = GPU(name, cuda_cores, clock, flops_cycle, tensor_cores, tensor_flops)
            calculator.add_gpu(gpu)
        
        elif choice == '3':
            print("\n--- Add TPU ---")
            name = input("TPU Name (e.g., Google TPU v4): ").strip()
            matrix_units = int(input("Matrix Multiply Units: ").strip())
            clock = float(input("Clock Speed (GHz): ").strip())
            ops_cycle = float(input("Operations per Cycle: ").strip())
            
            tpu = TPU(name, matrix_units, clock, ops_cycle)
            calculator.add_tpu(tpu)
        
        elif choice == '4':
            print("\n--- Add FPGA ---")
            name = input("FPGA Name (e.g., Xilinx Alveo U250): ").strip()
            dsp_blocks = int(input("DSP Blocks: ").strip())
            clock = float(input("Clock Speed (MHz): ").strip())
            ops_block = float(input("Operations per DSP Block: ").strip())
            
            fpga = FPGA(name, dsp_blocks, clock, ops_block)
            calculator.add_fpga(fpga)
        
        elif choice == '5':
            calculator.display_results()
        
        elif choice == '6':
            filename = input("Enter filename (default: flops_results.json): ").strip()
            if not filename:
                filename = "flops_results.json"
            calculator.export_json(filename)
        
        elif choice == '7':
            print("\nThank you for using Hardware FLOPS Calculator! Goodbye.\n")
            break
        
        else:
            print("\n❌ Invalid choice. Please enter 1-7.")


def demo_mode():
    """Run a demonstration with pre-configured hardware."""
    print("\nRunning demonstration with sample hardware...\n")
    
    calculator = HardwareFLOPSCalculator()
    
    # Add a high-end CPU
    calculator.add_cpu(CPU(
        name="Intel Core i9-13900K",
        cores=24,
        threads_per_core=2,
        clock_speed_ghz=5.8,
        flops_per_cycle=16.0  # AVX2
    ))
    
    # Add multiple high-end GPUs
    calculator.add_gpu(GPU(
        name="NVIDIA RTX 4090",
        cuda_cores=16384,
        clock_speed_ghz=2.52,
        flops_per_cycle=2.0,  # FP32
        tensor_cores=512,
        tensor_flops_per_cycle=128.0
    ))
    
    calculator.add_gpu(GPU(
        name="NVIDIA RTX 4090",
        cuda_cores=16384,
        clock_speed_ghz=2.52,
        flops_per_cycle=2.0,
        tensor_cores=512,
        tensor_flops_per_cycle=128.0
    ))
    
    calculator.add_gpu(GPU(
        name="NVIDIA RTX 4090",
        cuda_cores=16384,
        clock_speed_ghz=2.52,
        flops_per_cycle=2.0,
        tensor_cores=512,
        tensor_flops_per_cycle=128.0
    ))
    
    calculator.add_gpu(GPU(
        name="NVIDIA RTX 4090",
        cuda_cores=16384,
        clock_speed_ghz=2.52,
        flops_per_cycle=2.0,
        tensor_cores=512,
        tensor_flops_per_cycle=128.0
    ))
    
    # Display results
    calculator.display_results()
    calculator.export_json("demo_results.json")
    
    return calculator


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        demo_mode()
    else:
        interactive_mode()
