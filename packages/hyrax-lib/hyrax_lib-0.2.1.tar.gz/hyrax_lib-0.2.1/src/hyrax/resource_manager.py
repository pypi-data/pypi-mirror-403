import torch
import psutil
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class GPUInfo:
    id: int
    name: str
    total_memory: int 
    available_memory: int 
    device_type: str 
    
    def __repr__(self):
        return f"GPU {self.id}: {self.name} ({self.available_memory / 1e9:.1f}GB free) [{self.device_type}]"

class ResourceManager:
    def __init__(self):
        self.gpus = self._detect_gpus()
        self.cpu_count = psutil.cpu_count()
        self.total_ram = psutil.virtual_memory().total
        
    def _detect_gpus(self) -> List[GPUInfo]:
        gpus = []
        if torch.cuda.is_available():
            for i in range(torch.cuda.device_count()):
                props = torch.cuda.get_device_properties(i)
                torch.cuda.set_device(i)
                free_mem, total_mem = torch.cuda.mem_get_info(i)
                
                gpu = GPUInfo(
                    id=i,
                    name=props.name,
                    total_memory=total_mem,
                    available_memory=free_mem,
                    device_type='cuda'
                )
                gpus.append(gpu)
                
        elif torch.backends.mps.is_available():
            vm = psutil.virtual_memory()
            gpu = GPUInfo(
                id=0,
                name="Apple Silicon GPU",
                total_memory=vm.total,
                available_memory=vm.available,
                device_type='mps'
            )
            gpus.append(gpu)
            
        return gpus

    def print_resources(self):
        print("\ndetected hardware:")
        print(f"   cpus: {self.cpu_count}")
        print(f"   ram: {self.total_ram / 1e9:.1f}gb")
        
        if self.gpus:
            print(f"   gpus: {len(self.gpus)}")
            for gpu in self.gpus:
                print(f"      {gpu}")
        else:
            print("   gpus: none (cpu mode)")
        print()

    def get_device_capacities(self) -> Dict[int, int]:
        safety_factor = 0.85
        capacities = {}
        
        if not self.gpus:
            return {-1: int(psutil.virtual_memory().available * safety_factor)}
            
        for gpu in self.gpus:
            if gpu.device_type == 'mps':
                 capacities[gpu.id] = int(psutil.virtual_memory().available * safety_factor)
            else:
                 capacities[gpu.id] = int(gpu.available_memory * safety_factor)
                 
        return capacities

    def get_device_type(self) -> str:
        if not self.gpus: return 'cpu'
        return self.gpus[0].device_type