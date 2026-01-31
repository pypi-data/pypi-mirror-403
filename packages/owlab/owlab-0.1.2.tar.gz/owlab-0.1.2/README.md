<p align="center">
  <img src="./assets/logo.png" width="512" height="256" alt="OwLab logo"/>
</p>

<h1 align="center">OwLab</h1>

<p align="center">
  <strong>ML experiments, tracked & notified.</strong>
</p>

<p align="center">
  A Python toolkit for the full lifecycle of machine learning experiments — experiment tracking with <a href="https://swanlab.cn/">SwanLab</a>, notifications & data management with <a href="https://open.feishu.cn/">Lark (Feishu)</a>, and local storage.
</p>

<p align="center">
  <a href="https://pypi.org/project/owlab/"><img src="https://img.shields.io/pypi/v/owlab?color=blue" alt="PyPI"/></a>
  <a href="https://swanlab.cn"><img src="https://raw.githubusercontent.com/SwanHubX/assets/main/badge2.svg" alt="swanlab"/></a>
  <a href="https://www.feishu.cn/"><img alt="Static Badge" src="https://img.shields.io/badge/notification_by-Lark-blue?link=%23000000"></a>
  <a href="https://github.com/Lounwb/OwLab/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License"/></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.9+-green.svg" alt="Python 3.9+"/></a>
</p>

---

## ✨ Features

📈 **Metrics and Tracking**: Embed minimal code into your ML pipeline to track and record key training metrics based on [SwanLab](https://swanlab.cn/).\
📊 **Data Management**: Automatically organize your experiment directory structure based on experiment type and tags, enabling better management of experimental data.\
📢 **Message Notifications**: Automatic push notifications are sent when the experiment starts, ends, or is interrupted, keeping you informed of the latest progress.\
💾 **Backup**: Back up your data in the cloud and locally to prevent data loss.

---

## 🚀 Quick Start

### 📦 Installation
```bash
pip install owlab
# or: uv pip install owlab
# or: use source code
# git clone https://github.com/Lounwb/OwLab.git && cd OwLab && pip install -e .

```

### ⚙️ Configuration

To enable **Lark** and **Swanlab**, you need to configure the relevant tokens and secrets.
Owlab supports both configuration files and environment variables, providing you with flexible options：

- **Configuration file:** `~/.owlab/config.json` or `./.owlab/config.json`, here is an example:
```json
// configure your lark and swanlab in .owlab/config.json
{
    "lark": {
      "webhook": {
        "webhook_url": "<your webhook url>",
        "signature": "<your webhook signature>"
      },
      "api": {
        "app_id": "<your app id>",
        "app_secret": "<your app secret>",
        "root_folder_token": "<your root folder token>"
      }
    },
    "swanlab": {
      "api_key": "<your swanlab api key>"
    },
    "storage": {
      "local_path": "./output",
      "csv_path": "./output/csv",
      "model_path": "./output/models"
    },
    "logging": {
      "level": "INFO",
      "format": null,
      "file": "./logs/owlab.log"
    }
  }
  
```
- **Environment:** `OWLAB_LARK__WEBHOOK__WEBHOOK_URL`, `OWLAB_LARK__API__APP_ID`, etc.


### 📖 Usage

#### 1. Initialize

```python
from owlab import OwLab

owlab = OwLab()
owlab.init(
    project="my_project",           # Required
    experiment_name="exp_001",      # Optional; defaults to project
    description="Short description",
    type="baseline",                # e.g. baseline / debug / ablation — used for folder naming
    version="1.0",                 # Experiment version
    tags=["baseline"],             # Optional tags
    config={
        "methods": [...],          # Method definitions for result tables
        "datasets": [...],
        "metrics": [...],
        "measures": [...],
        "experiment_params": {"learning_rate": 0.01, "batch_size": 32},
        "seed": 42,
    },
)
```

#### 2. Log metrics during training

```python
for epoch in range(100):
    owlab.log({"loss": loss, "accuracy": acc}, step=epoch)
```

#### 3. Finish and save results

Call `finish(results=...)` with a list of result rows. Each row can include method, dataset, measure, and metric values. These are written to local files and, when configured, to Feishu spreadsheets.

```python
owlab.finish(results=[
    {
        "method": "method1",
        "dataset1": {"measure": "MCM", "accuracy": 0.95, "loss": 0.05},
        "dataset2": {"measure": "MCM", "accuracy": 0.92, "loss": 0.08},
        "Average": {"measure": "MCM", "accuracy": 0.935, "loss": 0.065},
    },
    # ...
])
```

#### 4. Sync PyTorch TensorBoard to SwanLab

Like SwanLab’s `swanlab.sync_tensorboard_torch()`: call **after** `init()` and **before** creating `SummaryWriter`. Then `writer.add_scalar()` / `add_scalars()` also log to the current SwanLab run.

```python
owlab.init(project="my_project", experiment_name="exp_1", ...)
owlab.sync_tensorboard_torch()

from torch.utils.tensorboard import SummaryWriter
writer = SummaryWriter(log_dir="./runs")
writer.add_scalar("loss", loss, step)   # also sent to SwanLab
writer.add_scalar("acc", acc, step)
```

#### 5. Output layout

- **Local:** `./output/<type>/<experiment_name>_<timestamp>/`
  - `results.csv`, `results.json`, `owlab.log`, `model/`
- **Lark:** Notifications via webhook; result tables written to Feishu via API (when configured).
- **SwanLab:** Metrics and runs visible in your SwanLab project (when `api_key` is set).

---


## 📄 License & Links

- **PyPI:** [pypi.org/project/owlab](https://pypi.org/project/owlab/)
- **License:** [MIT](LICENSE)
- **Repository:** [github.com/Lounwb/OwLab](https://github.com/Lounwb/OwLab)
- **Issues:** [github.com/Lounwb/OwLab/issues](https://github.com/Lounwb/OwLab/issues)

---

## 🙏 Acknowledgments

- [SwanLab](https://swanlab.cn/) — experiment tracking
- [Lark / Feishu](https://open.feishu.cn/) — notifications and spreadsheets

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Lounwb/OwLab&type=date&legend=top-left)](https://www.star-history.com/#Lounwb/OwLab&type=date&legend=top-left)