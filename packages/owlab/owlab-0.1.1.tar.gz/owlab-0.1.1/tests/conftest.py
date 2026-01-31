"""Pytest configuration and fixtures."""

import os
from pathlib import Path
import tempfile

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_experiment_config():
    """Sample experiment configuration for testing."""
    return {
        "version": "1.0",
        "experiment_name": "test_experiment",
        "description": "Test experiment description",
        "methods": [
            {
                "name": "method1",
                "display_name": "Method 1",
                "category": "baseline",
            },
            {
                "name": "method2",
                "display_name": "Method 2",
                "category": "proposed",
            },
        ],
        "datasets": [
            {
                "name": "dataset1",
                "display_name": "Dataset 1",
                "order": 1,
            },
            {
                "name": "dataset2",
                "display_name": "Dataset 2",
                "order": 2,
            },
        ],
        "metrics": [
            {
                "name": "accuracy",
                "display_name": "Accuracy (↑)",
                "direction": "max",
                "format": "float",
                "decimal_places": 3,
                "order": 1,
            },
            {
                "name": "loss",
                "display_name": "Loss (↓)",
                "direction": "min",
                "format": "float",
                "decimal_places": 3,
                "order": 2,
            },
        ],
        "measures": [
            {
                "name": "MCM",
                "display_name": "MCM",
                "order": 1,
            },
        ],
        "experiment_params": {
            "learning_rate": 0.01,
            "batch_size": 32,
            "epochs": 100,
        },
    }


@pytest.fixture
def sample_experiment_data():
    """Sample experiment data for testing."""
    return [
        {
            "method": "method1",
            "dataset1": {
                "measure": "MCM",
                "accuracy": 0.95,
                "loss": 0.05,
            },
            "dataset2": {
                "measure": "MCM",
                "accuracy": 0.92,
                "loss": 0.08,
            },
            "Average": {
                "measure": "MCM",
                "accuracy": 0.935,
                "loss": 0.065,
            },
        },
        {
            "method": "method2",
            "dataset1": {
                "measure": "MCM",
                "accuracy": 0.97,
                "loss": 0.03,
            },
            "dataset2": {
                "measure": "MCM",
                "accuracy": 0.94,
                "loss": 0.06,
            },
            "Average": {
                "measure": "MCM",
                "accuracy": 0.955,
                "loss": 0.045,
            },
        },
    ]


@pytest.fixture(autouse=True)
def reset_env_vars(monkeypatch):
    """Reset environment variables before each test."""
    # Remove OWLAB_ prefixed env vars
    env_vars_to_remove = [
        key for key in os.environ.keys() if key.startswith("OWLAB_")
    ]
    for key in env_vars_to_remove:
        monkeypatch.delenv(key, raising=False)
