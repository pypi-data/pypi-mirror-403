"""SwanLab tracker wrapper."""

from typing import Any, Dict, List, Optional

from owlab.core.logger import get_logger

logger = get_logger("owlab.swanlab.tracker")


class SwanLabTracker:
    """SwanLab tracker wrapper for experiment tracking."""

    def __init__(self, api_key: Optional[str] = None, **kwargs: Any):
        """Initialize SwanLab tracker.

        Args:
            api_key: SwanLab API key (optional, uses system default if not provided)
            **kwargs: Additional SwanLab init parameters
        """
        self.api_key = api_key
        self.kwargs = kwargs
        self._run = None
        self._initialized = False

        try:
            import swanlab

            self.swanlab = swanlab
            self.url = ""  # Will be set after initialization
            logger.info("SwanLab module imported successfully")
        except ImportError:
            logger.error("SwanLab not installed. Install with: pip install swanlab")
            raise

    def init(
        self,
        project: str,
        experiment_name: Optional[str] = None,
        description: str = "",
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> None:
        """Initialize SwanLab run.

        Args:
            project: Project name (required, used for grouping experiments)
            experiment_name: Name of the experiment/run (optional, defaults to project)
            description: Experiment description
            config: Experiment configuration dictionary
            tags: List of tags for categorization (e.g., ["baseline", "debug", "ablation"])
        """
        # Use project as experiment_name if not provided
        if experiment_name is None:
            experiment_name = project

        init_params = {
            "project": project,
            "experiment_name": experiment_name,  # SwanLab uses run_name for individual experiment name
            "description": description,
            "config": config or {},
            **self.kwargs,
        }

        # Add tags if provided
        if tags:
            init_params["tags"] = tags

        if self.api_key:
            init_params["api_key"] = self.api_key

        try:
            self._run = self.swanlab.init(**init_params)
            self._initialized = True
            logger.info(f"SwanLab run initialized: {experiment_name}")

            # Try to get URL immediately after initialization
            # Some SwanLab versions may generate URL immediately, others may need time
            try:
                url = self.get_url()
                if url:
                    logger.debug(f"SwanLab URL obtained: {url}")
            except Exception:
                # URL may not be available immediately, will be retrieved later
                logger.debug("SwanLab URL not available immediately, will be retrieved later")
        except Exception as e:
            logger.error(f"Failed to initialize SwanLab run: {e}")
            raise

    def log(self, metrics: Dict[str, Any], step: Optional[int] = None) -> None:
        """Log metrics to SwanLab.

        Args:
            metrics: Dictionary of metrics to log
            step: Step number (optional)
        """
        if not self._initialized:
            raise RuntimeError("SwanLab tracker not initialized. Call init() first.")

        try:
            if step is not None:
                self.swanlab.log(metrics, step=step)
            else:
                self.swanlab.log(metrics)
            logger.debug(f"Logged metrics to SwanLab: {metrics}")
        except Exception as e:
            logger.error(f"Failed to log metrics to SwanLab: {e}")
            raise

    def finish(self) -> str:
        """Finish SwanLab run and return URL.

        Returns:
            SwanLab experiment URL
        """
        if not self._initialized:
            raise RuntimeError("SwanLab tracker not initialized. Call init() first.")

        try:
            # SwanLab automatically finishes when the process ends
            # We can get the URL from the run object if available
            if hasattr(self._run, "url"):
                url = self._run.url  # type: ignore[attr-defined]
            else:
                # Try to get URL from swanlab settings
                url = getattr(self.swanlab, "settings", {}).get("url", "")
            logger.info(f"SwanLab run finished. URL: {url}")
            return url  # type: ignore[no-any-return]
        except Exception as e:
            logger.error(f"Failed to finish SwanLab run: {e}")
            return ""

    def get_url(self) -> str:
        """Get current SwanLab experiment URL.

        Returns:
            SwanLab experiment URL
        """
        if not self._initialized:
            return ""

        # Try multiple ways to get URL
        try:
            # Method 1: From run object
            if hasattr(self._run, "url") and self._run.url:  # type: ignore[attr-defined]
                self.url = self._run.url  # type: ignore[attr-defined]
                return self.url

            # Method 2: From swanlab.get_url()
            url = self.swanlab.get_url()
            if url:
                self.url = url
                return url  # type: ignore[no-any-return]

            # Method 3: From swanlab settings
            settings = getattr(self.swanlab, "settings", {})
            if isinstance(settings, dict):
                url = settings.get("url", "")
                if url:
                    self.url = url
                    return url  # type: ignore[no-any-return]
        except Exception as e:
            logger.debug(f"Failed to get SwanLab URL: {e}")

        return self.url if self.url else ""
