"""Main experiment management class for OwLab."""

from typing import Any, Dict, List, Optional

from owlab.core.config import Config
from owlab.core.logger import get_logger
from owlab.utils.schema_validator import SchemaValidator

logger = get_logger("owlab.core.experiment")


class OwLab:
    """Main entry point for OwLab experiment management.

    This class provides a unified interface for managing machine learning
    experiments using SwanLab for tracking and Lark for notifications.
    """

    def __init__(self, config: Optional[Config] = None):
        """Initialize OwLab with configuration.

        Args:
            config: Configuration instance. If None, will load from default locations.
        """
        self.config = config or Config.load()
        self._project: Optional[str] = None
        self._experiment_name: Optional[str] = None
        self._description: Optional[str] = None
        self._experiment_config: Optional[Dict[str, Any]] = None
        self._tags: List[str] = []
        self._swanlab_tracker: Any = None
        self._lark_webhook_bot: Any = None
        self._lark_api_bot: Any = None
        self._local_storage: Any = None
        self._experiment_folder_token: Optional[str] = None  # Cache folder token
        self._swanlab_url: str = ""  # Cache SwanLab URL
        self._version: str = "1.0"  # Experiment version
        self._type: str = "default"  # Experiment type
        self._initialized = False
        self._log_file_handler_id: Optional[int] = None  # Loguru handler for owlab.log

        # Debug: Log configuration status
        logger.debug(f"Config loaded - Lark: {self.config.lark is not None}, SwanLab: {self.config.swanlab is not None}")
        logger.info("OwLab initialized")

    def init(
        self,
        project: str,
        experiment_name: Optional[str] = None,
        description: str = "",
        type: str = "default",
        version: str = "1.0",
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize a new experiment.

        Args:
            project: Project name (required, used for SwanLab project grouping)
            experiment_name: Name of the experiment (optional, defaults to project name)
            description: Description of the experiment
            type: Experiment type for folder organization (e.g., "baseline", "debug", "ablation")
            version: Experiment version (default: "1.0")
            config: Experiment configuration dictionary (should not contain experiment_name)
            tags: List of tags for experiment categorization (e.g., ["baseline", "debug"])
            **kwargs: Additional configuration parameters
        """
        # Use project as experiment_name if not provided
        if experiment_name is None:
            experiment_name = project

        self._experiment_name = experiment_name
        self._project = project
        self._description = description
        self._version = version
        # Remove experiment_name from config if present (use top-level experiment_name instead)
        self._experiment_config = config or {}
        if "experiment_name" in self._experiment_config:
            logger.warning("experiment_name in config will be ignored, using top-level experiment_name")
            del self._experiment_config["experiment_name"]

        # Merge seed from Config.experiment.seed if present and not already in config
        if self.config.experiment and self.config.experiment.seed is not None:
            if "seed" not in self._experiment_config:
                self._experiment_config["seed"] = self.config.experiment.seed

        self._tags = tags or []
        self._type = type or "default"

        # Create experiment output dir and add owlab.log handler as early as possible
        # so that all subsequent logs (including "Initializing experiment...") go to both console and file
        if self._local_storage is None:
            try:
                from owlab.storage.local_storage import LocalStorage

                base_path = self.config.storage.local_path
                if base_path in ("./experiments", "experiments"):
                    base_path = "./output"
                self._local_storage = LocalStorage(base_path=base_path)
            except Exception as e:
                logger.warning(f"Failed to initialize local storage: {e}")
        if self._local_storage:
            try:
                experiment_dir = self._local_storage.set_experiment(
                    experiment_type=self._type,
                    experiment_name=experiment_name,
                )
                from loguru import logger as _loguru_logger

                from owlab.core.logger import get_logger_level
                from owlab.core.logger import LOG_FORMAT_PLAIN
                log_path = experiment_dir / "owlab.log"
                self._log_file_handler_id = _loguru_logger.add(
                    str(log_path),
                    format=LOG_FORMAT_PLAIN,
                    level=get_logger_level(),
                    colorize=False,
                    rotation="10 MB",
                    retention="7 days",
                    encoding="utf-8",
                )
            except Exception as e:
                logger.warning(f"Failed to set experiment output dir: {e}")

        # Validate experiment configuration
        config_to_validate = {
            "experiment_name": experiment_name,
            "description": description,
            **self._experiment_config,
        }
        is_valid, error_msg = SchemaValidator.validate_experiment_config(
            config_to_validate
        )
        if not is_valid:
            logger.warning(f"Experiment config validation warning: {error_msg}")

        logger.info(f"Initializing experiment: {experiment_name} (project: {project})")
        if self._tags:
            logger.info(f"Experiment tags: {', '.join(self._tags)}")
        if self._local_storage:
            logger.info(f"Experiment output dir: {self._local_storage.get_experiment_dir()}")

        # Initialize SwanLab tracker
        if self.config.swanlab:
            try:
                from owlab.swanlab.tracker import SwanLabTracker

                self._swanlab_tracker = SwanLabTracker(
                    api_key=self.config.swanlab.api_key, **kwargs
                )
                self._swanlab_tracker.init(
                    project=project,
                    experiment_name=experiment_name,
                    description=description,
                    config=self._experiment_config,
                    tags=self._tags,
                )
                logger.info("SwanLab tracker initialized")

                # Get SwanLab URL immediately after initialization
                self._swanlab_url = self._swanlab_tracker.get_url()
                if self._swanlab_url:
                    logger.info(f"SwanLab URL: {self._swanlab_url}")
                else:
                    logger.warning("SwanLab URL not available yet, may be generated later")

                # Convert TensorBoard logs if specified
                tensorboard_dir = kwargs.get("tensorboard_dir")
                if tensorboard_dir:
                    try:
                        from owlab.swanlab.adapter import convert_tensorboard_to_swanlab

                        logger.info(f"Converting TensorBoard logs from {tensorboard_dir}")
                        convert_tensorboard_to_swanlab(
                            tensorboard_dir, self._swanlab_tracker
                        )
                    except Exception as e:
                        logger.warning(f"Failed to convert TensorBoard logs: {e}")
            except Exception as e:
                logger.warning(f"Failed to initialize SwanLab tracker: {e}")
        else:
            logger.info("SwanLab not configured (no swanlab config found)")

        # Initialize Lark Webhook Bot
        if self.config.lark and self.config.lark.webhook:
            try:
                from owlab.lark.webhook_bot import LarkWebhookBot

                self._lark_webhook_bot = LarkWebhookBot(
                    webhook_url=self.config.lark.webhook.webhook_url,
                    signature=self.config.lark.webhook.signature,
                )
                logger.info("Lark Webhook Bot initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Lark Webhook Bot: {e}")
        else:
            if not self.config.lark:
                logger.info("Lark not configured (no lark config found)")
            elif not self.config.lark.webhook:
                logger.info("Lark Webhook Bot not configured (no webhook config found)")

        # Initialize Lark API Bot
        if self.config.lark and self.config.lark.api:
            try:
                from owlab.lark.api_bot import LarkAPIBot

                self._lark_api_bot = LarkAPIBot(
                    app_id=self.config.lark.api.app_id,
                    app_secret=self.config.lark.api.app_secret,
                    root_folder_token=self.config.lark.api.root_folder_token,
                )
                logger.info("Lark API Bot initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Lark API Bot: {e}")
        else:
            if not self.config.lark:
                logger.info("Lark not configured (no lark config found)")
            elif not self.config.lark.api:
                logger.info("Lark API Bot not configured (no api config found)")

        # Send start notification
        if self._lark_webhook_bot:
            try:
                # Use cached SwanLab URL (obtained during initialization)
                swanlab_url = self._swanlab_url

                folder_url = ""
                if self._lark_api_bot:
                    # Create folder once at initialization
                    if not self._experiment_folder_token:
                        self._experiment_folder_token = self._lark_api_bot.create_experiment_folder(
                            experiment_name=experiment_name,
                            description=description,
                            experiment_type=self._type,
                        )
                        if not self._experiment_folder_token:
                            # Use root folder if creation fails
                            if self.config.lark and self.config.lark.api:
                                self._experiment_folder_token = self.config.lark.api.root_folder_token
                            logger.warning("Failed to create experiment folder, using root folder")

                    if self._experiment_folder_token:
                        folder_url = f"https://bytedance.feishu.cn/drive/folder/{self._experiment_folder_token}"

                self._lark_webhook_bot.send_start_notification(
                    experiment_name=experiment_name,
                    description=description,
                    config=self._experiment_config,
                    type=self._type,
                    tags=self._tags if self._tags else None,
                    swanlab_url=swanlab_url,
                    folder_url=folder_url,
                )
            except Exception as e:
                logger.warning(f"Failed to send start notification: {e}")

        self._initialized = True
        logger.info(f"Experiment '{experiment_name}' initialized successfully")

    def sync_tensorboard_torch(self) -> None:
        """Sync PyTorch TensorBoard to SwanLab (like swanlab.sync_tensorboard_torch()).

        Call after init() and before creating torch.utils.tensorboard.SummaryWriter.
        Then writer.add_scalar() / add_scalars() will also log to the current SwanLab run.
        """
        if not self._initialized:
            raise RuntimeError("Experiment not initialized. Call init() first.")
        if not self._swanlab_tracker:
            logger.warning(
                "SwanLab not configured; sync_tensorboard_torch() has no effect."
            )
            return
        try:
            from owlab.swanlab.tensorboard_sync import patch_torch_tensorboard

            patch_torch_tensorboard(self._swanlab_tracker)
        except Exception as e:
            logger.warning(f"Failed to sync TensorBoard to SwanLab: {e}")

    def log(self, metrics: Dict[str, Any], step: Optional[int] = None) -> None:
        """Log metrics to SwanLab and local storage.

        Args:
            metrics: Dictionary of metrics to log
            step: Step number (optional)
        """
        if not self._initialized:
            raise RuntimeError("Experiment not initialized. Call init() first.")

        # Log to SwanLab
        if self._swanlab_tracker:
            try:
                self._swanlab_tracker.log(metrics=metrics, step=step)
            except Exception as e:
                logger.warning(f"Failed to log to SwanLab: {e}")

        # Intermediate metrics (e.g. loss) are not saved locally; only final results in finish()
        logger.debug(f"Logged metrics at step {step}: {metrics}")

    def finish(self, results: Optional[Dict[str, Any]] = None) -> None:
        """Finish experiment and generate reports.

        Args:
            results: Final experiment results (optional)
        """
        if not self._initialized:
            raise RuntimeError("Experiment not initialized. Call init() first.")

        logger.info(f"Finishing experiment: {self._experiment_name}")

        # Use cached SwanLab URL (obtained during initialization)
        swanlab_url = self._swanlab_url
        if not swanlab_url and self._swanlab_tracker:
            # Try to get URL if not cached (fallback)
            try:
                swanlab_url = self._swanlab_tracker.get_url()
                if swanlab_url:
                    self._swanlab_url = swanlab_url
                    logger.info(f"SwanLab URL: {swanlab_url}")
            except Exception as e:
                logger.warning(f"Failed to get SwanLab URL: {e}")

        # Note: SwanLab automatically finishes when the process ends
        # We don't need to explicitly call finish() here

        # Save final results locally (same as Feishu): results.csv, results.json under ./output/<type>/<name>_<ts>/
        if self._local_storage and results:
            try:
                result_list = results if isinstance(results, list) else [results]
                self._local_storage.save_results(result_list)
            except Exception as e:
                logger.warning(f"Failed to save results to local storage: {e}")

        # Write results to Lark sheet
        folder_url = ""
        if self._lark_api_bot and results:
            try:
                # Validate results data
                if isinstance(results, list):
                    is_valid, error_msg = SchemaValidator.validate_experiment_data(
                        results, self._experiment_config
                    )
                    if not is_valid:
                        logger.warning(f"Results validation warning: {error_msg}")

                # Use the folder token created during initialization
                folder_token = self._experiment_folder_token
                if not folder_token:
                    # Fallback to root folder if no folder was created
                    if self.config.lark and self.config.lark.api:
                        folder_token = self.config.lark.api.root_folder_token
                    logger.warning("No experiment folder token, using root folder")

                if folder_token:
                    # Prepare experiment config for sheet writing
                    sheet_config = {
                        "project": self._project or "unknown",
                        "experiment_name": self._experiment_name or "unknown",
                        "description": self._description or "",
                        "version": self._version,
                        **(self._experiment_config or {}),
                    }
                    self._lark_api_bot.write_results_to_sheet(
                        folder_token=folder_token,
                        experiment_config=sheet_config,
                        experiment_data=results if isinstance(results, list) else [],
                        swanlab_url=swanlab_url,
                    )
                    folder_url = f"https://bytedance.feishu.cn/drive/folder/{folder_token}"
                    logger.info(f"Experiment folder URL: {folder_url}")
            except Exception as e:
                logger.warning(f"Failed to write results to Lark: {e}")

        # Send finish notification
        if self._lark_webhook_bot:
            try:
                # Prepare config for notification
                notification_config = {
                    "project": self._project or "unknown",
                    "experiment_name": self._experiment_name or "unknown",
                    "description": self._description or "",
                    "version": self._version,
                    **(self._experiment_config or {}),
                }
                self._lark_webhook_bot.send_finish_notification(
                    experiment_name=self._experiment_name or "unknown",
                    results=results or {},
                    description=self._description or "",
                    config=notification_config,
                    type=self._type,
                    tags=self._tags if self._tags else None,
                    swanlab_url=swanlab_url,
                    folder_url=folder_url,
                )
            except Exception as e:
                logger.warning(f"Failed to send finish notification: {e}")

        logger.info(f"Experiment '{self._experiment_name}' finished successfully")

        # Remove owlab.log file handler and clear experiment dir only after all logging is done
        if self._log_file_handler_id is not None:
            try:
                from loguru import logger as _loguru_logger
                _loguru_logger.remove(self._log_file_handler_id)
            except Exception:
                pass
            self._log_file_handler_id = None
        if self._local_storage:
            self._local_storage.clear_experiment()

        # Reset state for next experiment
        self._initialized = False
        self._project = None
        self._experiment_name = None
        self._experiment_folder_token = None
        self._swanlab_url = ""
        self._tags = []
        self._version = "1.0"
        self._type = "default"
