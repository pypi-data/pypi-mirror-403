"""Tests for schema validator."""

from owlab.utils.schema_validator import SchemaValidator


class TestSchemaValidator:
    """Tests for SchemaValidator."""

    def test_validate_experiment_data_valid(self):
        """Test validating valid experiment data."""
        data = [
            {
                "method": "method1",
                "dataset1": {
                    "measure": "MCM",
                    "accuracy": 0.95,
                    "loss": 0.05,
                },
                "Average": {
                    "measure": "MCM",
                    "accuracy": 0.95,
                    "loss": 0.05,
                },
            }
        ]
        is_valid, error_msg = SchemaValidator.validate_experiment_data(data)
        assert is_valid is True
        assert error_msg is None

    def test_validate_experiment_data_invalid_not_list(self):
        """Test validating invalid experiment data (not a list)."""
        data = {"method": "method1"}
        is_valid, error_msg = SchemaValidator.validate_experiment_data(data)
        assert is_valid is False
        assert "must be a list" in error_msg

    def test_validate_experiment_data_invalid_missing_method(self):
        """Test validating invalid experiment data (missing method)."""
        data = [{"dataset1": {"measure": "MCM", "accuracy": 0.95}}]
        is_valid, error_msg = SchemaValidator.validate_experiment_data(data)
        assert is_valid is False
        assert "missing required field 'method'" in error_msg

    def test_validate_experiment_data_invalid_missing_measure(self):
        """Test validating invalid experiment data (missing measure)."""
        data = [
            {
                "method": "method1",
                "dataset1": {"accuracy": 0.95},
            }
        ]
        is_valid, error_msg = SchemaValidator.validate_experiment_data(data)
        assert is_valid is False
        assert "missing required field 'measure'" in error_msg

    def test_validate_experiment_config_valid(self):
        """Test validating valid experiment configuration."""
        config = {
            "experiment_name": "test_experiment",
            "methods": [{"name": "method1"}],
            "datasets": [{"name": "dataset1"}],
            "metrics": [
                {"name": "accuracy", "direction": "max"},
            ],
            "measures": [{"name": "MCM"}],
        }
        is_valid, error_msg = SchemaValidator.validate_experiment_config(config)
        assert is_valid is True
        assert error_msg is None

    def test_validate_experiment_config_invalid_missing_name(self):
        """Test validating invalid config (missing experiment_name)."""
        config = {
            "methods": [{"name": "method1"}],
            "datasets": [{"name": "dataset1"}],
        }
        is_valid, error_msg = SchemaValidator.validate_experiment_config(config)
        assert is_valid is False
        assert "Missing required field 'experiment_name'" in error_msg

    def test_validate_experiment_config_invalid_missing_methods(self):
        """Test validating invalid config (missing methods)."""
        config = {
            "experiment_name": "test",
            "datasets": [{"name": "dataset1"}],
        }
        is_valid, error_msg = SchemaValidator.validate_experiment_config(config)
        assert is_valid is False
        assert "Missing required field 'methods'" in error_msg

    def test_validate_experiment_config_invalid_duplicate_method(self):
        """Test validating invalid config (duplicate method name)."""
        config = {
            "experiment_name": "test",
            "methods": [{"name": "method1"}, {"name": "method1"}],
            "datasets": [{"name": "dataset1"}],
            "metrics": [{"name": "accuracy", "direction": "max"}],
            "measures": [{"name": "MCM"}],
        }
        is_valid, error_msg = SchemaValidator.validate_experiment_config(config)
        assert is_valid is False
        assert "Duplicate method name" in error_msg

    def test_validate_experiment_config_invalid_metric_direction(self):
        """Test validating invalid config (invalid metric direction)."""
        config = {
            "experiment_name": "test",
            "methods": [{"name": "method1"}],
            "datasets": [{"name": "dataset1"}],
            "metrics": [{"name": "accuracy", "direction": "invalid"}],
            "measures": [{"name": "MCM"}],
        }
        is_valid, error_msg = SchemaValidator.validate_experiment_config(config)
        assert is_valid is False
        assert "must be 'min' or 'max'" in error_msg
