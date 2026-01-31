"""Tests for local storage."""

import csv
import json
from pathlib import Path
import tempfile

from owlab.storage.local_storage import LocalStorage


class TestLocalStorage:
    """Tests for LocalStorage class."""

    def test_init(self):
        """Test LocalStorage initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorage(base_path=tmpdir)
            assert storage.base_path == Path(tmpdir)
            assert storage.base_path.exists()
            assert storage.get_experiment_dir() is None

    def test_set_experiment(self):
        """Test setting experiment directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorage(base_path=tmpdir)
            path = storage.set_experiment(
                experiment_type="default",
                experiment_name="test_exp",
            )
            assert path is not None
            assert path.parent.name == "default"
            assert path.name.startswith("test_exp_")
            assert (path / "model").exists()
            assert storage.get_experiment_dir() == path
            assert storage.get_model_dir() == path / "model"

    def test_save_results(self):
        """Test saving final experiment results (list, same as Feishu)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorage(base_path=tmpdir)
            storage.set_experiment(experiment_type="default", experiment_name="test_exp")
            results = [
                {
                    "method": "m1",
                    "dataset1": {"measure": "MCM", "accuracy": 0.95, "loss": 0.05},
                    "Average": {"measure": "MCM", "accuracy": 0.93, "loss": 0.07},
                },
                {
                    "method": "m2",
                    "dataset1": {"measure": "MCM", "accuracy": 0.97, "loss": 0.03},
                    "Average": {"measure": "MCM", "accuracy": 0.96, "loss": 0.04},
                },
            ]
            storage.save_results(results)

            exp_dir = storage.get_experiment_dir()
            results_json = exp_dir / "results.json"
            results_csv = exp_dir / "results.csv"
            assert results_json.exists()
            assert results_csv.exists()

            with open(results_json, "r", encoding="utf-8") as f:
                saved = json.load(f)
            assert saved == results

            with open(results_csv, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 2
                assert rows[0]["method"] == "m1"
                assert "dataset1_accuracy" in rows[0] or "Average_accuracy" in rows[0]

    def test_save_results_no_experiment_dir(self):
        """Test save_results when no experiment dir is set."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorage(base_path=tmpdir)
            storage.save_results([{"method": "m1"}])
            # Should not raise; just skips
            assert storage.get_experiment_dir() is None

    def test_clear_experiment(self):
        """Test clearing current experiment."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorage(base_path=tmpdir)
            storage.set_experiment(experiment_type="default", experiment_name="test_exp")
            assert storage.get_experiment_dir() is not None
            storage.clear_experiment()
            assert storage.get_experiment_dir() is None
            assert storage.get_model_dir() is None
