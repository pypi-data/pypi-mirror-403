"""Local storage implementation for OwLab."""

import csv
from datetime import datetime
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from owlab.core.logger import get_logger

logger = get_logger("owlab.storage.local_storage")


class LocalStorage:
    """Local storage manager for experiments.

    Output layout (aligned with Feishu folder structure):
        <base_path>/<type>/<experiment_name>_<timestamp>/
            results.csv   -- final experiment results (same as Feishu)
            results.json  -- same data as JSON
            owlab.log     -- log file (handler added by experiment)
            model/        -- directory for model files
    """

    def __init__(self, base_path: str = "./output"):
        """Initialize local storage.

        Args:
            base_path: Root path for experiment output (e.g. ./output).
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._current_experiment_dir: Optional[Path] = None
        logger.debug(f"Local storage root: {self.base_path}")

    def set_experiment(
        self, experiment_type: str, experiment_name: str
    ) -> Path:
        """Create and set current experiment directory.

        Creates: <base_path>/<type>/<experiment_name>_<timestamp>/ and model/.

        Args:
            experiment_type: Experiment type (e.g. default, baseline).
            experiment_name: Experiment name.

        Returns:
            Path to the experiment directory.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dir_name = f"{experiment_name}_{timestamp}"
        type_dir = self.base_path / experiment_type
        type_dir.mkdir(parents=True, exist_ok=True)
        experiment_dir = type_dir / dir_name
        experiment_dir.mkdir(parents=True, exist_ok=True)
        (experiment_dir / "model").mkdir(exist_ok=True)
        self._current_experiment_dir = experiment_dir
        logger.debug(f"Experiment output dir: {experiment_dir}")
        return experiment_dir

    def get_experiment_dir(self) -> Optional[Path]:
        """Return current experiment directory or None."""
        return self._current_experiment_dir

    def get_model_dir(self) -> Optional[Path]:
        """Return current experiment's model directory or None."""
        if self._current_experiment_dir is None:
            return None
        d = self._current_experiment_dir / "model"
        return d if d.exists() else None

    def save_results(self, results: List[Dict[str, Any]]) -> None:
        """Save final experiment results (same as Feishu).

        Writes results.json and results.csv under current experiment dir.
        Does nothing if no experiment dir is set.

        Args:
            results: List of result dicts (method + per-dataset metrics).
        """
        if self._current_experiment_dir is None:
            logger.warning("No experiment dir set; skipping save_results")
            return
        if not results:
            logger.debug("No results to save")
            return

        # Save JSON (same structure as Feishu)
        results_path = self._current_experiment_dir / "results.json"
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.debug(f"Saved results to {results_path}")

        # Save CSV: flatten to one row per method
        csv_path = self._current_experiment_dir / "results.csv"
        self._write_results_csv(csv_path, results)
        logger.debug(f"Saved results to {csv_path}")

    def _write_results_csv(self, csv_path: Path, results: List[Dict[str, Any]]) -> None:
        """Write results to CSV with one row per method."""
        if not results or not isinstance(results[0], dict):
            return
        # Build columns: method, then for each dataset: measure, metric1, metric2, ...
        dataset_keys = sorted(
            k for k in results[0].keys() if k != "method"
        )
        fieldnames = ["method"]
        for key in dataset_keys:
            val = results[0].get(key)
            if isinstance(val, dict):
                for m in sorted(val.keys()):
                    fieldnames.append(f"{key}_{m}")
            else:
                fieldnames.append(key)

        rows = []
        for item in results:
            if not isinstance(item, dict):
                continue
            row = {"method": item.get("method", "")}
            for key in dataset_keys:
                val = item.get(key)
                if isinstance(val, dict):
                    for m, v in val.items():
                        row[f"{key}_{m}"] = v
                else:
                    row[key] = val
            rows.append(row)

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)

    def clear_experiment(self) -> None:
        """Clear current experiment dir (call on finish)."""
        self._current_experiment_dir = None
