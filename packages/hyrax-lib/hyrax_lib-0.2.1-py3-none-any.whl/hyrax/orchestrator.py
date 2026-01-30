"""
Main distributed training orchestrator.
"""

import torch.multiprocessing as mp
import time
import queue
from typing import List, Any, Callable, Optional, Dict

from .resource_manager import ResourceManager
from .load_balancer import LoadBalancer
from .worker import WorkerConfig, worker_process
from .monitor import TrainingMonitor

class DistributedTrainer:
    def __init__(
        self,
        model: type,
        datasets: List[Any],
        dataset_loader: Optional[Callable] = None,
        job_size_estimates: Optional[List[int]] = None
    ):
        self.model_class = model
        self.datasets = datasets
        self.dataset_loader = dataset_loader
        
        # default to 1gb per job if no estimates provided
        if job_size_estimates:
            self.job_sizes = job_size_estimates
        else:
            self.job_sizes = [1024**3] * len(datasets)
        
        self.resource_manager = ResourceManager()
        self.load_balancer = LoadBalancer(self.resource_manager)
        self.device_type = self.resource_manager.get_device_type()
        self.monitor = TrainingMonitor()
        
    def train(self, epochs: int = 100) -> List[Dict]:
        print(f"\nstarting distributed training:")
        print(f"  datasets: {len(self.datasets)}")
        print(f"  device: {self.device_type}")
        
        self.resource_manager.print_resources()
        
        # step 1: schedule
        schedule = self.load_balancer.create_schedule(self.job_sizes)
        
        # step 2: setup mp
        try:
            mp.set_start_method('spawn', force=True)
        except RuntimeError:
            pass

        result_queue = mp.Queue()
        progress_queue = mp.Queue()
        final_results = []
        
        # step 3: execute batches
        for batch_idx, batch_assignment in enumerate(schedule):
            print(f"\n--- executing batch {batch_idx + 1}/{len(schedule)} ---")
            
            processes = []
            active_workers = 0
            
            for gpu_id, job_indices in batch_assignment.items():
                target_gpu = gpu_id if gpu_id != -1 else None
                
                for job_idx in job_indices:
                    config = WorkerConfig(
                        worker_id=job_idx,
                        dataset=self.datasets[job_idx],
                        model_class=self.model_class,
                        device_id=target_gpu,
                        device_type=self.device_type,
                        epochs=epochs,
                        dataset_loader=self.dataset_loader
                    )
                    
                    p = mp.Process(
                        target=worker_process,
                        args=(config, result_queue, progress_queue)
                    )
                    p.start()
                    processes.append(p)
                    active_workers += 1
                    print(f"launched job {job_idx} on {'cpu' if target_gpu is None else f'gpu {target_gpu}'}")
            
            # monitor this batch
            while any(p.is_alive() for p in processes):
                try:
                    msg = progress_queue.get_nowait()
                    self.monitor.update(msg)
                except queue.Empty:
                    time.sleep(0.1)
            
            # flush queue
            while not progress_queue.empty():
                try:
                    msg = progress_queue.get_nowait()
                    self.monitor.update(msg)
                except queue.Empty:
                    break

            for p in processes:
                p.join()
                
        self.monitor.close()
        
        while not result_queue.empty():
            final_results.append(result_queue.get())
        
        print("\nall workers finished")
        return final_results