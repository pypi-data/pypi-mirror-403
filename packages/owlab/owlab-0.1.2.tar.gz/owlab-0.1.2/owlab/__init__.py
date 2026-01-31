"""OwLab: A Python toolkit for ML experiment management.

OwLab provides a unified interface for managing machine learning experiments
using SwanLab for tracking and Lark (Feishu) for notifications and data management.
"""

__version__ = "0.1.0"

from owlab.core.experiment import OwLab

__all__ = ["OwLab"]
