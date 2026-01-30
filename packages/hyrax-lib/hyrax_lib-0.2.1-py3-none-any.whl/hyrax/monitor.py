import os
from datetime import datetime
from typing import Dict
from torch.utils.tensorboard import SummaryWriter

class TrainingMonitor:
    def __init__(self, log_dir: str = "runs"):
        run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.log_path = os.path.join(log_dir, f"hyrax_run_{run_id}")
        self.writer = SummaryWriter(log_dir=self.log_path)
        
        # tensorboard --logdir=runs
        print(f"monitor initialized: {self.log_path}")

    def update(self, msg: Dict):
        worker_id = msg['worker_id']
        epoch = msg['epoch']
        loss = msg['loss']
        
        self.writer.add_scalar(f'Loss/worker_{worker_id}', loss, epoch)
        
        # if epoch % 10 == 0:
        #     print(f"[worker {worker_id}] epoch {epoch}: loss = {loss:.4f}")

    def close(self):
        self.writer.close()