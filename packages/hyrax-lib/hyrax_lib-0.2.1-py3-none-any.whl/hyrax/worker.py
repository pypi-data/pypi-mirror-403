"""
Training worker that runs on a single GPU/CPU with one dataset.
"""

import torch
import torch.multiprocessing as mp
from torch.utils.data import DataLoader, Dataset
from typing import Any, Callable, Optional, Dict
from dataclasses import dataclass

@dataclass
class WorkerConfig:
    worker_id: int
    dataset: Any
    model_class: type
    device_id: Optional[int]
    device_type: str
    epochs: int
    dataset_loader: Optional[Callable] = None 
    
class TrainingWorker:
    def __init__(self, config: WorkerConfig):
        self.config = config
        self.device = self._setup_device()
        
    def _setup_device(self) -> torch.device:
        if self.config.device_type == 'cpu':
            return torch.device('cpu')
        elif self.config.device_type == 'mps':
            return torch.device('mps')
        elif self.config.device_type == 'cuda':
            return torch.device(f'cuda:{self.config.device_id}')
        
    def train(self, progress_queue: Optional[mp.Queue] = None) -> Dict:
        model = self.config.model_class()
        model = model.to(self.device)
        model.train()
        
        optimizer = torch.optim.SGD(model.parameters(), lr=0.01)
        criterion = torch.nn.MSELoss() # default fallback

        train_loader = None
        
        # logic: load real data
        if self.config.dataset_loader and isinstance(self.config.dataset, str):
            real_data = self.config.dataset_loader(self.config.dataset)
            train_loader = DataLoader(real_data, batch_size=32, shuffle=True)
        elif isinstance(self.config.dataset, Dataset):
            train_loader = DataLoader(self.config.dataset, batch_size=32, shuffle=True)
        elif isinstance(self.config.dataset, DataLoader):
            train_loader = self.config.dataset
            
        if not train_loader:
            raise ValueError(f"worker {self.config.worker_id}: no valid dataset or loader provided")

        results = {
            'worker_id': self.config.worker_id,
            'device': str(self.device),
            'epochs_completed': 0,
            'final_loss': 0.0
        }
        
        print(f"worker {self.config.worker_id} starting training on {self.device}")

        for epoch in range(self.config.epochs):
            epoch_loss = 0.0
            batch_count = 0
            
            for batch_idx, (data, target) in enumerate(train_loader):
                data, target = data.to(self.device), target.to(self.device)
                optimizer.zero_grad()
                output = model(data)
                loss = criterion(output, target)
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item()
                batch_count += 1
                
            avg_loss = epoch_loss / max(1, batch_count)
            results['epochs_completed'] = epoch + 1
            results['final_loss'] = avg_loss
            
            if progress_queue:
                progress_queue.put({
                    'worker_id': self.config.worker_id,
                    'epoch': epoch + 1,
                    'loss': avg_loss
                })
        
        return results

def worker_process(config: WorkerConfig, result_queue: mp.Queue, progress_queue: mp.Queue):
    worker = TrainingWorker(config)
    try:
        results = worker.train(progress_queue)
        result_queue.put(results)
    except Exception as e:
        result_queue.put({'worker_id': config.worker_id, 'error': str(e)})