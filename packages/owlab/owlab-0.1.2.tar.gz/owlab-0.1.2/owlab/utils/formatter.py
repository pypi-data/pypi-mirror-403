"""Data formatting utilities for experiment results."""

from typing import Any, Dict, List, Optional

from owlab.core.logger import get_logger

logger = get_logger("owlab.utils.formatter")


class ExperimentDataFormatter:
    """Formatter for experiment data to Lark sheet format."""

    def __init__(self, experiment_config: Dict[str, Any]):
        """Initialize formatter with experiment configuration.

        Args:
            experiment_config: Experiment configuration dictionary
        """
        self.config = experiment_config
        self.datasets = self._get_sorted_datasets()
        self.metrics = self._get_sorted_metrics()
        self.measures = self._get_sorted_measures()

    def _get_sorted_datasets(self) -> List[Dict[str, Any]]:
        """Get datasets sorted by order.

        Returns:
            List of dataset dictionaries
        """
        datasets = self.config.get("datasets", [])
        return sorted(datasets, key=lambda x: x.get("order", 999))

    def _get_sorted_metrics(self) -> List[Dict[str, Any]]:
        """Get metrics sorted by order.

        Returns:
            List of metric dictionaries
        """
        metrics = self.config.get("metrics", [])
        return sorted(metrics, key=lambda x: x.get("order", 999))

    def _get_sorted_measures(self) -> List[Dict[str, Any]]:
        """Get measures sorted by order.

        Returns:
            List of measure dictionaries
        """
        measures = self.config.get("measures", [])
        return sorted(measures, key=lambda x: x.get("order", 999))

    def format_experiment_data(
        self, experiment_data: List[Dict[str, Any]]
    ) -> Dict[str, List[List[Any]]]:
        """Format experiment data into sheet format grouped by measure.

        Args:
            experiment_data: List of experiment data dictionaries

        Returns:
            Dictionary mapping measure names to data rows
        """
        result = {}

        # Group data by measure
        for measure in self.measures:
            measure_name = measure["name"]
            measure_data = []

            # Filter methods for this measure
            for method_data in experiment_data:
                method_name = method_data.get("method", "")

                # Find datasets with this measure
                for dataset in self.datasets:
                    dataset_name = dataset["name"]
                    if dataset_name in method_data:
                        dataset_result = method_data[dataset_name]
                        if dataset_result.get("measure") == measure_name:
                            # Extract metric values
                            row = [method_name, measure_name]
                            for metric in self.metrics:
                                metric_name = metric["name"]
                                value = dataset_result.get(metric_name, "")
                                row.append(value)
                            measure_data.append(row)

            if measure_data:
                result[measure_name] = measure_data

        return result

    def format_to_sheet_rows(
        self,
        experiment_data: List[Dict[str, Any]],
        include_average: bool = True,
        target_measure: Optional[str] = None,
    ) -> List[List[Any]]:
        """Format experiment data to sheet rows with proper structure.

        Args:
            experiment_data: List of experiment data dictionaries
            include_average: Whether to include average row
            target_measure: Optional measure name to filter by (if None, uses first measure found)

        Returns:
            List of rows, each row is [method, measure, dataset1_metrics..., dataset2_metrics..., ...]
        """
        rows = []
        grouped_by_method: dict[str, Any] = {}

        # Group data by method for the target measure
        for method_data in experiment_data:
            method_name = method_data.get("method", "")

            if method_name not in grouped_by_method:
                grouped_by_method[method_name] = {}

            # Process each dataset
            for dataset in self.datasets:
                dataset_name = dataset["name"]
                if dataset_name in method_data:
                    dataset_result = method_data[dataset_name]
                    measure_name = dataset_result.get("measure", "")

                    # Filter by target measure if specified
                    if target_measure and measure_name != target_measure:
                        continue

                    if dataset_name not in grouped_by_method[method_name]:
                        grouped_by_method[method_name][dataset_name] = {}

                    # Extract metric values
                    metric_values = []
                    for metric in self.metrics:
                        metric_name = metric["name"]
                        value = dataset_result.get(metric_name, "")
                        metric_values.append(value)

                    grouped_by_method[method_name][dataset_name] = {
                        "measure": measure_name,
                        "metrics": metric_values,
                    }

        # Determine the measure name to use
        measure_name = target_measure
        if not measure_name:
            # Find the first measure from the data
            for method_data in experiment_data:
                for dataset in self.datasets:
                    dataset_name = dataset["name"]
                    if dataset_name in method_data:
                        measure_name = method_data[dataset_name].get("measure")
                        if measure_name:
                            break
                if measure_name:
                    break

        if not measure_name:
            measure_name = self.measures[0]["name"] if self.measures else ""

        # Convert to rows: [method, measure, dataset1_metrics..., dataset2_metrics..., ...]
        for method_name in sorted(grouped_by_method.keys()):
            method_data = grouped_by_method[method_name]
            row = [method_name, measure_name]

            # Add metrics for each dataset
            for dataset in self.datasets:
                dataset_name = dataset["name"]
                if dataset_name in method_data:
                    dataset_info = method_data[dataset_name]
                    # Only include if measure matches
                    if dataset_info.get("measure") == measure_name:
                        row.extend(dataset_info["metrics"])
                    else:
                        row.extend([""] * len(self.metrics))
                else:
                    # Fill with empty values
                    row.extend([""] * len(self.metrics))

            # Add average if available
            if include_average:
                avg_data: dict[str, Any] = next(
                    (
                        d.get("Average", {})
                        for d in experiment_data
                        if d.get("method") == method_name
                    ),
                    {},
                )
                if avg_data.get("measure") == measure_name:
                    for metric in self.metrics:
                        metric_name = metric["name"]
                        value = avg_data.get(metric_name, "")
                        row.append(value)
                else:
                    row.extend([""] * len(self.metrics))

            rows.append(row)

        return rows

    def get_header_rows(self, include_average: bool = True) -> List[List[str]]:
        """Get header rows for the sheet.

        Args:
            include_average: Whether to include average column

        Returns:
            List of header rows
        """
        # First header row: Method, Measure, Dataset1 (merged), Dataset2 (merged), ...
        header_row1 = ["", ""]  # Method, Measure columns
        for dataset in self.datasets:
            dataset_display = dataset.get("display_name", dataset["name"])
            # Add dataset name and empty cells for metrics
            header_row1.append(dataset_display)
            header_row1.extend([""] * (len(self.metrics) - 1))

        if include_average:
            header_row1.append("Average(*)")
            header_row1.extend([""] * (len(self.metrics) - 1))

        # Second header row: Method, Measure, Metric1, Metric2, ... (repeated for each dataset)
        header_row2 = ["Method", "Measure"]
        metric_display_names = [
            metric.get("display_name", metric["name"]) for metric in self.metrics
        ]

        # Repeat metrics for each dataset
        for _ in self.datasets:
            header_row2.extend(metric_display_names)

        if include_average:
            header_row2.extend(metric_display_names)

        return [header_row1, header_row2]

    def get_merge_ranges(
        self, sheet_id: str, start_row: int, include_average: bool = True
    ) -> List[str]:
        """Get cell ranges to merge for headers.

        Args:
            sheet_id: Sheet ID
            start_row: Starting row number (1-based)
            include_average: Whether average column is included

        Returns:
            List of range strings to merge
        """
        merge_ranges = []
        col_start = 3  # Start from column C (after Method and Measure)

        for dataset_idx in range(len(self.datasets)):
            col_end = col_start + len(self.metrics) - 1
            range_str = f"{sheet_id}!{self._col_letter(col_start)}{start_row}:{self._col_letter(col_end)}{start_row}"
            merge_ranges.append(range_str)
            col_start = col_end + 1

        if include_average:
            col_end = col_start + len(self.metrics) - 1
            range_str = f"{sheet_id}!{self._col_letter(col_start)}{start_row}:{self._col_letter(col_end)}{start_row}"
            merge_ranges.append(range_str)

        return merge_ranges

    def get_best_value_ranges(
        self,
        sheet_id: str,
        data_rows: List[List[Any]],
        start_row: int,
        include_average: bool = True,
    ) -> List[str]:
        """Get cell ranges for best values to bold.

        For each metric column (across all datasets + average):
        - If direction=max: bold the maximum value(s)
        - If direction=min: bold the minimum value(s)
        - If multiple rows have the same best value, bold all of them

        Args:
            sheet_id: Sheet ID
            data_rows: Data rows
            start_row: Starting row number for data (1-based)
            include_average: Whether average column is included

        Returns:
            List of cell ranges to bold
        """
        if not data_rows:
            return []

        bold_ranges = []
        num_datasets = len(self.datasets)
        num_metrics = len(self.metrics)

        # Process each metric across all datasets and average
        for metric_idx in range(num_metrics):
            metric = self.metrics[metric_idx]
            direction = metric.get("direction", "max")
            is_min = direction == "min"

            # Process each dataset column for this metric
            for dataset_idx in range(num_datasets + (1 if include_average else 0)):
                # Column index: 2 (start after Method=0, Measure=1) + dataset_idx * num_metrics + metric_idx
                # Row structure: [method, measure, dataset1_metrics..., dataset2_metrics..., average_metrics...]
                col_idx = 2 + dataset_idx * num_metrics + metric_idx

                # Extract values for this column
                col_values = []
                for row_idx, row in enumerate(data_rows):
                    if col_idx < len(row):
                        val = row[col_idx]
                        if isinstance(val, (int, float)):
                            col_values.append((row_idx, val))

                if not col_values:
                    continue

                # Find best value based on direction
                if is_min:
                    # For min direction: smaller is better
                    best_val = min(v for _, v in col_values)
                else:
                    # For max direction: larger is better
                    best_val = max(v for _, v in col_values)

                # Find all rows with best value (using epsilon for float comparison)
                epsilon = 1e-9
                best_rows = [
                    row_idx
                    for row_idx, v in col_values
                    if abs(v - best_val) < epsilon
                ]

                # Add ranges for all best rows
                for row_idx in best_rows:
                    cell_row = start_row + row_idx
                    # col_idx is 0-based (0=method, 1=measure, 2+=metrics), convert to 1-based for column letter
                    col_letter = self._col_letter(col_idx + 1)
                    range_str = f"{sheet_id}!{col_letter}{cell_row}:{col_letter}{cell_row}"
                    bold_ranges.append(range_str)

        return bold_ranges

    @staticmethod
    def _col_letter(col_idx: int) -> str:
        """Convert 1-based column index to letter.

        Args:
            col_idx: 1-based column index

        Returns:
            Column letter(s)
        """
        string = ""
        while col_idx > 0:
            col_idx, remainder = divmod(col_idx - 1, 26)
            string = chr(65 + remainder) + string
        return string
