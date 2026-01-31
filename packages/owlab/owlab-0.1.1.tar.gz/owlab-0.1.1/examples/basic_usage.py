"""Basic usage example for OwLab.

Note: This example runs without Lark and SwanLab configuration.
To enable Lark notifications and SwanLab tracking, see basic_usage_with_config.py
or configure via:
1. Config file: ~/.owlab/config.json or ./owlab_config.json
2. Environment variables: OWLAB_LARK__WEBHOOK__WEBHOOK_URL, etc.
"""

from owlab import OwLab

# Initialize OwLab (will load config from default locations or environment variables)
# If no config is found, it will run with default settings (local storage only)
owlab = OwLab()

# Start experiment
owlab.init(
    project="my_project",  # Project name (required)
    experiment_name="my_experiment",  # Experiment name (optional, defaults to project)
    description="This is a test experiment",
    type="baseline",  # Experiment type for folder organization (e.g., "baseline", "debug", "ablation")
    version="1.0",  # Experiment version
    tags=["baseline"],  # Tags for categorization (optional)
    config={
        # Note: experiment_name and version should not be in config
        # They are provided as top-level parameters
        "methods": [
            {"name": "method1", "display_name": "Method 1", "category": "baseline"},
            {"name": "method2", "display_name": "Method 2", "category": "proposed"},
        ],
        "datasets": [
            {"name": "dataset1", "display_name": "Dataset 1", "order": 1},
            {"name": "dataset2", "display_name": "Dataset 2", "order": 2},
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
            {"name": "MCM", "display_name": "MCM", "order": 1},
            {"name": "GL-MCM", "display_name": "GL-MCM", "order": 2},
        ],
        "experiment_params": {
            "learning_rate": 0.01,
            "batch_size": 32,
            "epochs": 100,
        },
        "seed": 42,
    },
)

# Log metrics during training
for epoch in range(100):
    metrics = {
        "accuracy": 0.5 + epoch * 0.005,
        "loss": 1.0 - epoch * 0.01,
    }
    owlab.log(metrics, step=epoch)

# Finish experiment with results
results = [
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
    {
        "method": "method1",
        "dataset1": {
            "measure": "GL-MCM",
            "accuracy": 0.96,
            "loss": 0.04,
        },
        "dataset2": {
            "measure": "GL-MCM",
            "accuracy": 0.93,
            "loss": 0.07,
        },
        "Average": {
            "measure": "GL-MCM",
            "accuracy": 0.945,
            "loss": 0.055,
        },
    },
    {
        "method": "method2",
        "dataset1": {
            "measure": "GL-MCM",
            "accuracy": 0.98,
            "loss": 0.02,
        },
        "dataset2": {
            "measure": "GL-MCM",
            "accuracy": 0.95,
            "loss": 0.05,
        },
        "Average": {
            "measure": "GL-MCM",
            "accuracy": 0.965,
            "loss": 0.035,
        },
    },
]

owlab.finish(results=results)
