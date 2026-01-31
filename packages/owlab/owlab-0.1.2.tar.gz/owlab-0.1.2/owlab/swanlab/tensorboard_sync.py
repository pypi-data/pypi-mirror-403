"""Sync PyTorch TensorBoard SummaryWriter to SwanLab (like swanlab.sync_tensorboard_torch())."""

from typing import Any, Callable, Optional

from owlab.core.logger import get_logger

logger = get_logger("owlab.swanlab.tensorboard_sync")

# Callback (tracker.log) to receive synced metrics; set by patch_torch_tensorboard().
_sync_log_callback: Optional[Callable[[dict, Optional[int]], None]] = None
_patched = False


def _make_scalar_value(value: Any) -> float:
    """Convert tensor/scalar to float for logging."""
    if hasattr(value, "item"):
        return float(value.item())
    return float(value)


def _patched_add_scalar(original_add_scalar: Any) -> Any:
    """Return wrapped add_scalar that also logs to SwanLab."""

    def wrapper(
        self: Any,
        tag: str,
        scalar_value: Any,
        global_step: Optional[int] = None,
        walltime: Optional[float] = None,
        **kwargs: Any,
    ) -> None:
        original_add_scalar(self, tag, scalar_value, global_step, walltime, **kwargs)
        if _sync_log_callback is not None:
            try:
                val = _make_scalar_value(scalar_value)
                _sync_log_callback({tag: val}, global_step)
            except Exception as e:
                logger.debug(f"TensorBoard sync log failed: {e}")

    return wrapper


def _patched_add_scalars(original_add_scalars: Any) -> Any:
    """Return wrapped add_scalars that also logs to SwanLab."""

    def wrapper(
        self: Any,
        main_tag: str,
        tag_scalar_dict: Any,
        global_step: Optional[int] = None,
        walltime: Optional[float] = None,
        **kwargs: Any,
    ) -> None:
        original_add_scalars(
            self, main_tag, tag_scalar_dict, global_step, walltime, **kwargs
        )
        if _sync_log_callback is not None and isinstance(tag_scalar_dict, dict):
            try:
                metrics = {
                    k: _make_scalar_value(v) for k, v in tag_scalar_dict.items()
                }
                if metrics:
                    _sync_log_callback(metrics, global_step)
            except Exception as e:
                logger.debug(f"TensorBoard sync log failed: {e}")

    return wrapper


def patch_torch_tensorboard(tracker: Any) -> None:
    """Patch PyTorch SummaryWriter so add_scalar/add_scalars also log to the given tracker.

    Call this after owlab.init(...) and before creating SummaryWriter.
    Usage:
        owlab = OwLab()
        owlab.init(project="my_project", ...)
        owlab.sync_tensorboard_torch()
        writer = torch.utils.tensorboard.SummaryWriter(log_dir="./runs")
        writer.add_scalar("loss", loss, step)  # also sent to SwanLab
    """
    global _sync_log_callback, _patched

    try:
        from torch.utils.tensorboard import writer as tb_writer
    except ImportError:
        logger.error(
            "PyTorch TensorBoard not found. Install with: pip install torch tensorboard"
        )
        raise

    SummaryWriter = getattr(tb_writer, "SummaryWriter", None)
    if SummaryWriter is None:
        logger.error("torch.utils.tensorboard.writer.SummaryWriter not found")
        raise AttributeError("SummaryWriter not found in torch.utils.tensorboard")

    def log_callback(metrics: dict, step: Optional[int] = None) -> None:
        tracker.log(metrics=metrics, step=step)

    _sync_log_callback = log_callback  # noqa: PLW0603

    if not _patched:
        _patched = True
        orig_add_scalar = SummaryWriter.add_scalar
        orig_add_scalars = SummaryWriter.add_scalars
        SummaryWriter.add_scalar = _patched_add_scalar(orig_add_scalar)
        SummaryWriter.add_scalars = _patched_add_scalars(orig_add_scalars)
        logger.info("PyTorch TensorBoard synced to SwanLab (add_scalar/add_scalars)")
    else:
        logger.debug("TensorBoard sync callback updated (already patched)")
