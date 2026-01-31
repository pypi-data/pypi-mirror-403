"""Schema validation utilities."""

from typing import Any, Dict, Optional

from owlab.core.logger import get_logger

logger = get_logger("owlab.utils.schema_validator")


class SchemaValidator:
    """Schema validator for experiment data and configuration."""

    @staticmethod
    def validate_experiment_data(
        data: Any, config: Optional[Dict[str, Any]] = None
    ) -> tuple[bool, Optional[str]]:
        """Validate experiment data against schema.

        Args:
            data: Experiment data to validate (list of dictionaries)
            config: Optional experiment configuration for cross-validation

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if data is a list
        if not isinstance(data, list):
            return False, "Experiment data must be a list"

        if len(data) == 0:
            return False, "Experiment data cannot be empty"

        # Validate each item
        for idx, item in enumerate(data):
            if not isinstance(item, dict):
                return False, f"Item {idx} must be a dictionary"

            # Check required 'method' field
            if "method" not in item:
                return False, f"Item {idx} missing required field 'method'"

            method_name = item["method"]
            if not isinstance(method_name, str) or not method_name.strip():
                return False, f"Item {idx} 'method' must be a non-empty string"

            # Validate dataset results
            dataset_keys = [k for k in item.keys() if k not in ["method", "Average"]]
            if not dataset_keys:
                return False, f"Item {idx} must have at least one dataset result"

            for dataset_key in dataset_keys:
                dataset_result = item[dataset_key]
                if not isinstance(dataset_result, dict):
                    return False, f"Item {idx} dataset '{dataset_key}' must be a dictionary"

                # Check required 'measure' field
                if "measure" not in dataset_result:
                    return False, (
                        f"Item {idx} dataset '{dataset_key}' missing required field 'measure'"
                    )

                measure = dataset_result["measure"]
                if not isinstance(measure, str) or not measure.strip():
                    return False, (
                        f"Item {idx} dataset '{dataset_key}' 'measure' must be a non-empty string"
                    )

                # Check if there are metrics
                metric_keys = [
                    k for k in dataset_result.keys() if k != "measure"
                ]
                if not metric_keys:
                    return False, (
                        f"Item {idx} dataset '{dataset_key}' must have at least one metric"
                    )

                # Validate metric values are numbers
                for metric_key in metric_keys:
                    metric_value = dataset_result[metric_key]
                    if not isinstance(metric_value, (int, float)):
                        return False, (
                            f"Item {idx} dataset '{dataset_key}' metric '{metric_key}' "
                            "must be a number"
                        )

            # Validate Average if present
            if "Average" in item:
                avg_result = item["Average"]
                if not isinstance(avg_result, dict):
                    return False, f"Item {idx} 'Average' must be a dictionary"

                if "measure" not in avg_result:
                    return False, f"Item {idx} 'Average' missing required field 'measure'"

                # Validate average metric values
                avg_metric_keys = [k for k in avg_result.keys() if k != "measure"]
                for metric_key in avg_metric_keys:
                    metric_value = avg_result[metric_key]
                    if not isinstance(metric_value, (int, float)):
                        return False, (
                            f"Item {idx} 'Average' metric '{metric_key}' must be a number"
                        )

            # Cross-validate with config if provided
            if config:
                method_names = [m["name"] for m in config.get("methods", [])]
                if method_name not in method_names:
                    logger.warning(
                        f"Method '{method_name}' not found in config methods list"
                    )

        return True, None

    @staticmethod
    def validate_experiment_config(config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate experiment configuration against schema.

        Args:
            config: Experiment configuration to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required fields
        if "experiment_name" not in config:
            return False, "Missing required field 'experiment_name'"

        experiment_name = config["experiment_name"]
        if not isinstance(experiment_name, str) or not experiment_name.strip():
            return False, "'experiment_name' must be a non-empty string"

        # Validate methods
        if "methods" not in config:
            return False, "Missing required field 'methods'"

        methods = config["methods"]
        if not isinstance(methods, list):
            return False, "'methods' must be a list"

        if len(methods) == 0:
            return False, "'methods' cannot be empty"

        method_names = set()
        for idx, method in enumerate(methods):
            if not isinstance(method, dict):
                return False, f"Method {idx} must be a dictionary"

            if "name" not in method:
                return False, f"Method {idx} missing required field 'name'"

            method_name = method["name"]
            if not isinstance(method_name, str) or not method_name.strip():
                return False, f"Method {idx} 'name' must be a non-empty string"

            if method_name in method_names:
                return False, f"Duplicate method name: '{method_name}'"

            method_names.add(method_name)

        # Validate datasets
        if "datasets" not in config:
            return False, "Missing required field 'datasets'"

        datasets = config["datasets"]
        if not isinstance(datasets, list):
            return False, "'datasets' must be a list"

        if len(datasets) == 0:
            return False, "'datasets' cannot be empty"

        dataset_names = set()
        for idx, dataset in enumerate(datasets):
            if not isinstance(dataset, dict):
                return False, f"Dataset {idx} must be a dictionary"

            if "name" not in dataset:
                return False, f"Dataset {idx} missing required field 'name'"

            dataset_name = dataset["name"]
            if not isinstance(dataset_name, str) or not dataset_name.strip():
                return False, f"Dataset {idx} 'name' must be a non-empty string"

            if dataset_name in dataset_names:
                return False, f"Duplicate dataset name: '{dataset_name}'"

            dataset_names.add(dataset_name)

        # Validate metrics
        if "metrics" not in config:
            return False, "Missing required field 'metrics'"

        metrics = config["metrics"]
        if not isinstance(metrics, list):
            return False, "'metrics' must be a list"

        if len(metrics) == 0:
            return False, "'metrics' cannot be empty"

        metric_names = set()
        for idx, metric in enumerate(metrics):
            if not isinstance(metric, dict):
                return False, f"Metric {idx} must be a dictionary"

            if "name" not in metric:
                return False, f"Metric {idx} missing required field 'name'"

            metric_name = metric["name"]
            if not isinstance(metric_name, str) or not metric_name.strip():
                return False, f"Metric {idx} 'name' must be a non-empty string"

            if metric_name in metric_names:
                return False, f"Duplicate metric name: '{metric_name}'"

            metric_names.add(metric_name)

            # Validate direction
            if "direction" not in metric:
                return False, f"Metric {idx} missing required field 'direction'"

            direction = metric["direction"]
            if direction not in ["min", "max"]:
                return False, f"Metric {idx} 'direction' must be 'min' or 'max'"

        # Validate measures
        if "measures" not in config:
            return False, "Missing required field 'measures'"

        measures = config["measures"]
        if not isinstance(measures, list):
            return False, "'measures' must be a list"

        if len(measures) == 0:
            return False, "'measures' cannot be empty"

        measure_names = set()
        for idx, measure in enumerate(measures):
            if not isinstance(measure, dict):
                return False, f"Measure {idx} must be a dictionary"

            if "name" not in measure:
                return False, f"Measure {idx} missing required field 'name'"

            measure_name = measure["name"]
            if not isinstance(measure_name, str) or not measure_name.strip():
                return False, f"Measure {idx} 'name' must be a non-empty string"

            if measure_name in measure_names:
                return False, f"Duplicate measure name: '{measure_name}'"

            measure_names.add(measure_name)

        # Validate experiment_params if present
        if "experiment_params" in config:
            params = config["experiment_params"]
            if not isinstance(params, dict):
                return False, "'experiment_params' must be a dictionary"

        # Validate visualization if present
        if "visualization" in config:
            viz = config["visualization"]
            if not isinstance(viz, dict):
                return False, "'visualization' must be a dictionary"

        return True, None
