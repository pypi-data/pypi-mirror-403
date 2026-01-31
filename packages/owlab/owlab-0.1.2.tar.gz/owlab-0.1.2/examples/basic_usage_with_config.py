"""Basic usage example for OwLab with configuration."""

from owlab import OwLab
from owlab.core.config import Config

# Create configuration with Lark and SwanLab
# config = Config(
#     lark={
#         "webhook": {
#             "webhook_url": "https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_WEBHOOK_URL",
#             "signature": "YOUR_SIGNATURE",
#         },
#         "api": {
#             "app_id": "YOUR_APP_ID",
#             "app_secret": "YOUR_APP_SECRET",
#             "root_folder_token": "YOUR_ROOT_FOLDER_TOKEN",
#         },
#     },
#     swanlab={"api_key": "YOUR_SWANLAB_API_KEY"},  # Optional, can be None
#     storage={"local_path": "./experiments"},
# )

# Initialize OwLab with configuration
owlab = OwLab()

# Start experiment
owlab.init(
    project="my_project",  # Project name (required)
    experiment_name="my_experiment",  # Experiment name (optional)
    description="This is a test experiment",
    type="baseline",  # Experiment type for folder organization
    version="1.0",  # Experiment version
    tags=["baseline"],  # Tags: ["baseline"], ["debug"], ["ablation"], etc.
    config={
        # Note: experiment_name and version should not be in config
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
        ],
        "experiment_params": {
            "learning_rate": 0.01,
            "batch_size": 32,
            "epochs": 100,
        },
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
]

owlab.finish(results=results)
