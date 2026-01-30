"""
Tests for distributed training orchestrator.
"""

import pytest
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset
from hyrax import DistributedTrainer


class DummyModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.linear = nn.Linear(10, 1)
    
    def forward(self, x):
        return self.linear(x)


def create_dataset(size=100):
    x = torch.randn(size, 10)
    y = torch.randn(size, 1)
    return TensorDataset(x, y)


def test_trainer_init():
    datasets = [create_dataset() for _ in range(2)]
    trainer = DistributedTrainer(
        model=DummyModel,
        datasets=datasets
    )
    assert trainer.model_class == DummyModel
    assert len(trainer.datasets) == 2


def test_single_dataset_training():
    datasets = [create_dataset()]
    trainer = DistributedTrainer(
        model=DummyModel,
        datasets=datasets
    )
    results = trainer.train(epochs=5)
    assert len(results) == 1
    assert 'worker_id' in results[0]
    assert 'final_loss' in results[0]


def test_multi_dataset_training():
    datasets = [create_dataset() for _ in range(3)]
    trainer = DistributedTrainer(
        model=DummyModel,
        datasets=datasets
    )
    results = trainer.train(epochs=5)
    assert len(results) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])