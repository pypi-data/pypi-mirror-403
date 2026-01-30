"""
Tests for resource detection and management.
"""

import pytest
from hyrax.resource_manager import ResourceManager, GPUInfo


def test_resource_manager_init():
    rm = ResourceManager()
    assert rm.cpu_count > 0
    assert rm.total_ram > 0


def test_get_device_type():
    rm = ResourceManager()
    device_type = rm.get_device_type()
    assert device_type in ['cpu', 'cuda', 'mps']


def test_get_device_capacities():
    rm = ResourceManager()
    capacities = rm.get_device_capacities()
    assert len(capacities) > 0
    for device_id, capacity in capacities.items():
        assert capacity > 0


def test_print_resources():
    rm = ResourceManager()
    # should not raise
    rm.print_resources()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])