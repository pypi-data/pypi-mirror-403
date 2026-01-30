"""
Load balancing and job scheduling across GPUs.
Uses bin-packing to optimally distribute jobs.
"""

from typing import List, Dict

try:
    from .resource_manager import ResourceManager
except ImportError:
    from resource_manager import ResourceManager


class LoadBalancer:
    def __init__(self, resource_manager: ResourceManager):
        self.rm = resource_manager

    def create_schedule(self, job_sizes: List[int]) -> List[Dict[int, List[int]]]:
        device_caps = self.rm.get_device_capacities()
        device_ids = list(device_caps.keys())
        
        indexed_jobs = []
        for i, size in enumerate(job_sizes):
            max_capacity = max(device_caps.values())
            if size > max_capacity:
                print(f"warning: job {i} ({size/1e9:.1f}gb) exceeds max gpu capacity ({max_capacity/1e9:.1f}gb)")
            indexed_jobs.append((size, i))
        
        # sort jobs by size (largest first) for better bin packing
        indexed_jobs.sort(key=lambda x: x[0], reverse=True)
        
        batches = []
        
        while indexed_jobs:
            current_batch_usage = {d_id: 0 for d_id in device_ids}
            current_batch_assignment = {d_id: [] for d_id in device_ids}
            
            jobs_to_remove = []
            
            for size, job_idx in indexed_jobs:
                best_device = None
                min_remaining_space = float('inf')
                
                for d_id in device_ids:
                    capacity = device_caps[d_id]
                    current_usage = current_batch_usage[d_id]
                    
                    if current_usage + size <= capacity:
                        remaining = capacity - (current_usage + size)
                        if remaining < min_remaining_space:
                            min_remaining_space = remaining
                            best_device = d_id
                
                if best_device is not None:
                    current_batch_assignment[best_device].append(job_idx)
                    current_batch_usage[best_device] += size
                    jobs_to_remove.append((size, job_idx))
            
            for job in jobs_to_remove:
                indexed_jobs.remove(job)
                
            batches.append(current_batch_assignment)
            
            if not jobs_to_remove and indexed_jobs:
                print("critical: remaining jobs cannot fit on any device")
                break

        return batches