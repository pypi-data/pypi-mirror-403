"""Tests for data formatter."""

import pytest

from owlab.utils.formatter import ExperimentDataFormatter


class TestExperimentDataFormatter:
    """Tests for ExperimentDataFormatter."""

    @pytest.fixture
    def sample_config(self):
        """Sample experiment configuration."""
        return {
            "experiment_name": "test",
            "methods": [
                {"name": "method1", "display_name": "Method 1"},
                {"name": "method2", "display_name": "Method 2"},
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
                    "order": 1,
                },
                {
                    "name": "loss",
                    "display_name": "Loss (↓)",
                    "direction": "min",
                    "order": 2,
                },
            ],
            "measures": [
                {"name": "MCM", "display_name": "MCM", "order": 1},
            ],
        }

    @pytest.fixture
    def sample_data(self):
        """Sample experiment data."""
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

    def test_formatter_init(self, sample_config):
        """Test formatter initialization."""
        formatter = ExperimentDataFormatter(sample_config)
        assert len(formatter.datasets) == 2
        assert len(formatter.metrics) == 2
        assert len(formatter.measures) == 1

    def test_format_experiment_data(self, sample_config, sample_data):
        """Test formatting experiment data."""
        formatter = ExperimentDataFormatter(sample_config)
        result = formatter.format_experiment_data(sample_data)
        assert "MCM" in result
        assert len(result["MCM"]) > 0

    def test_format_to_sheet_rows(self, sample_config, sample_data):
        """Test formatting to sheet rows."""
        formatter = ExperimentDataFormatter(sample_config)
        rows = formatter.format_to_sheet_rows(sample_data, include_average=True)
        assert len(rows) > 0
        # Check first row structure: [method, measure, metrics...]
        assert len(rows[0]) >= 2  # At least method and measure

    def test_get_header_rows(self, sample_config):
        """Test getting header rows."""
        formatter = ExperimentDataFormatter(sample_config)
        headers = formatter.get_header_rows(include_average=True)
        assert len(headers) == 2
        assert headers[0][0] == ""  # First header row starts with empty
        assert headers[1][0] == "Method"  # Second header row starts with Method

    def test_get_merge_ranges(self, sample_config):
        """Test getting merge ranges."""
        formatter = ExperimentDataFormatter(sample_config)
        ranges = formatter.get_merge_ranges("Sheet1", 1, include_average=True)
        assert len(ranges) > 0
        assert all("Sheet1!" in r for r in ranges)

    def test_get_best_value_ranges(self, sample_config, sample_data):
        """Test getting best value ranges."""
        formatter = ExperimentDataFormatter(sample_config)
        rows = formatter.format_to_sheet_rows(sample_data, include_average=True)
        ranges = formatter.get_best_value_ranges("Sheet1", rows, 1, include_average=True)
        assert isinstance(ranges, list)
        # Best values should be found for accuracy (max) and loss (min)
        assert len(ranges) > 0

    def test_col_letter(self):
        """Test column letter conversion."""
        assert ExperimentDataFormatter._col_letter(1) == "A"
        assert ExperimentDataFormatter._col_letter(26) == "Z"
        assert ExperimentDataFormatter._col_letter(27) == "AA"
