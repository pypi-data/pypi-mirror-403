"""Adapters for converting other experiment tracking formats to SwanLab."""

from pathlib import Path
from typing import Any, Dict

from owlab.core.logger import get_logger

logger = get_logger("owlab.swanlab.adapter")


class TensorBoardAdapter:
    """Adapter for converting TensorBoard logs to SwanLab format."""

    def __init__(self, log_dir: str):
        """Initialize TensorBoard adapter.

        Args:
            log_dir: Directory containing TensorBoard event files
        """
        self.log_dir = Path(log_dir)
        if not self.log_dir.exists():
            raise ValueError(f"Log directory does not exist: {log_dir}")

        logger.info(f"TensorBoard adapter initialized for: {log_dir}")

    def convert_to_swanlab(
        self, swanlab_tracker: Any, step_offset: int = 0
    ) -> None:
        """Convert TensorBoard logs to SwanLab.

        Args:
            swanlab_tracker: SwanLab tracker instance
            step_offset: Offset to add to step numbers
        """
        try:
            from tensorboard.backend.event_processing.event_accumulator import (  # noqa: F401
                EventAccumulator,
            )
        except ImportError:
            logger.error(
                "TensorBoard not installed. Install with: pip install tensorboard"
            )
            raise

        # Find event files
        event_files = list(self.log_dir.rglob("events.out.tfevents.*"))
        if not event_files:
            logger.warning(f"No TensorBoard event files found in {self.log_dir}")
            return

        logger.info(f"Found {len(event_files)} event file(s)")

        # Process each event file
        for event_file in event_files:
            try:
                self._process_event_file(
                    event_file, swanlab_tracker, step_offset
                )
            except Exception as e:
                logger.error(f"Error processing {event_file}: {e}")

    def _process_event_file(
        self, event_file: Path, swanlab_tracker: Any, step_offset: int
    ) -> None:
        """Process a single TensorBoard event file.

        Args:
            event_file: Path to event file
            swanlab_tracker: SwanLab tracker instance
            step_offset: Offset to add to step numbers
        """
        try:
            from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
        except ImportError:
            return

        # Create event accumulator
        ea = EventAccumulator(str(event_file.parent))
        ea.Reload()

        # Get scalar tags
        scalar_tags = ea.Tags().get("scalars", [])

        if not scalar_tags:
            logger.debug(f"No scalar tags found in {event_file}")
            return

        logger.info(f"Processing {len(scalar_tags)} scalar tags from {event_file}")

        # Process each scalar tag
        for tag in scalar_tags:
            try:
                scalar_events = ea.Scalars(tag)

                for event in scalar_events:
                    step = int(event.step) + step_offset
                    value = float(event.value)

                    # Log to SwanLab
                    swanlab_tracker.log({tag: value}, step=step)

                logger.debug(f"Processed {len(scalar_events)} events for tag '{tag}'")
            except Exception as e:
                logger.error(f"Error processing tag '{tag}': {e}")

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of TensorBoard logs.

        Returns:
            Dictionary containing summary information
        """
        try:
            from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
        except ImportError:
            logger.error(
                "TensorBoard not installed. Install with: pip install tensorboard"
            )
            return {}

        summary = {
            "log_dir": str(self.log_dir),
            "event_files": [],
            "scalar_tags": [],
            "total_events": 0,
        }

        # Find event files
        event_files = list(self.log_dir.rglob("events.out.tfevents.*"))
        summary["event_files"] = [str(f) for f in event_files]

        if not event_files:
            return summary

        # Process first event file for summary
        try:
            ea = EventAccumulator(str(event_files[0].parent))
            ea.Reload()
            scalar_tags = ea.Tags().get("scalars", [])
            summary["scalar_tags"] = scalar_tags

            # Count total events
            total = 0
            for tag in scalar_tags:
                try:
                    events = ea.Scalars(tag)
                    total += len(events)
                except Exception:
                    pass
            summary["total_events"] = total
        except Exception as e:
            logger.error(f"Error getting summary: {e}")

        return summary


def convert_tensorboard_to_swanlab(
    tensorboard_log_dir: str,
    swanlab_tracker: Any,
    step_offset: int = 0,
) -> None:
    """Convenience function to convert TensorBoard logs to SwanLab.

    Args:
        tensorboard_log_dir: Directory containing TensorBoard event files
        swanlab_tracker: SwanLab tracker instance
        step_offset: Offset to add to step numbers
    """
    adapter = TensorBoardAdapter(tensorboard_log_dir)
    adapter.convert_to_swanlab(swanlab_tracker, step_offset=step_offset)
