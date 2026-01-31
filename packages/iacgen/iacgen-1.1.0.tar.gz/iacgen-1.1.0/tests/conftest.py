"""
Pytest configuration and shared fixtures for iacgen tests.
"""

import pytest
from pathlib import Path


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """
    Provide a temporary directory for test file operations.
    
    Args:
        tmp_path: pytest's built-in temporary directory fixture
        
    Returns:
        Path object pointing to a temporary directory
    """
    return tmp_path


@pytest.fixture
def sample_config():
    """
    Provide a sample configuration for testing.
    
    Returns:
        Dictionary containing sample blueprint configuration
    """
    # Placeholder - will be replaced with actual config structure
    return {
        "modules": {
            "vpc": True,
            "eks": True,
            "alb": False,
        },
        "services": ["api", "worker"],
        "output_dir": "./infra",
    }
