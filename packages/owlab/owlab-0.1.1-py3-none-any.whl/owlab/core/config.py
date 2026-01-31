"""Configuration management for OwLab."""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel
from pydantic import Field

logger = logging.getLogger("owlab.core.config")


class LarkWebhookConfig(BaseModel):
    """Configuration for Lark Webhook Bot."""

    webhook_url: str = Field(..., description="Lark webhook URL")
    signature: str = Field(..., description="Lark webhook signature")


class LarkAPIConfig(BaseModel):
    """Configuration for Lark API Bot."""

    app_id: str = Field(..., description="Lark app ID")
    app_secret: str = Field(..., description="Lark app secret")
    root_folder_token: str = Field(..., description="Root folder token in Lark")


class LarkConfig(BaseModel):
    """Configuration for Lark integration."""

    webhook: Optional[LarkWebhookConfig] = Field(None, description="Webhook bot config")
    api: Optional[LarkAPIConfig] = Field(None, description="API bot config")


class SwanLabConfig(BaseModel):
    """Configuration for SwanLab integration."""

    api_key: Optional[str] = Field(None, description="SwanLab API key (optional)")


class StorageConfig(BaseModel):
    """Configuration for storage."""

    local_path: str = Field("./output", description="Local output root (e.g. ./output)")
    csv_path: Optional[str] = Field(None, description="CSV storage path")
    model_path: Optional[str] = Field(None, description="Model storage path")


class LoggingConfig(BaseModel):
    """Configuration for logging."""

    level: str = Field("INFO", description="Logging level")
    format: Optional[str] = Field(None, description="Log format")
    file: Optional[str] = Field(None, description="Log file path")


class ExperimentConfig(BaseModel):
    """Configuration for experiment parameters."""

    seed: Optional[int] = Field(None, description="Random seed for reproducibility")


class Config(BaseModel):
    """Main configuration class for OwLab."""

    lark: Optional[LarkConfig] = Field(None, description="Lark configuration")
    swanlab: Optional[SwanLabConfig] = Field(None, description="SwanLab configuration")
    storage: StorageConfig = Field(default_factory=StorageConfig, description="Storage config")  # type: ignore[arg-type]
    logging: LoggingConfig = Field(default_factory=LoggingConfig, description="Logging config")  # type: ignore[arg-type]
    experiment: Optional[ExperimentConfig] = Field(None, description="Experiment configuration")

    @classmethod
    def load(
        cls,
        config_path: Optional[str] = None,
        env_prefix: str = "OWLAB_",
        **kwargs: Any,
    ) -> "Config":
        """Load configuration from file, environment variables, or kwargs.

        Priority: kwargs > environment variables > config file > defaults

        Args:
            config_path: Path to config file (JSON)
            env_prefix: Prefix for environment variables
            **kwargs: Configuration overrides

        Returns:
            Config instance
        """
        config_dict: Dict[str, Any] = {}

        # Load from config file
        if config_path and os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config_dict = json.load(f)
        elif not config_path:
            # Try default locations
            default_paths = [
                Path.home() / ".owlab" / "config.json",
                Path.cwd() / ".owlab" / "config.json",  # Project directory
                Path.cwd() / "owlab_config.json",
            ]
            loaded_path = None
            for path in default_paths:
                if path.exists():
                    with open(path, "r", encoding="utf-8") as f:
                        config_dict = json.load(f)
                    loaded_path = path
                    logger.info(f"Loaded config from: {loaded_path}")
                    break

            # Log if no config file was found
            if not loaded_path and not config_dict:
                logger.debug("No config file found in default locations")

        # Override with environment variables
        env_config = cls._load_from_env(env_prefix)
        config_dict = cls._merge_dicts(config_dict, env_config)

        # Override with kwargs
        if kwargs:
            config_dict = cls._merge_dicts(config_dict, kwargs)

        return cls(**config_dict)

    @staticmethod
    def _load_from_env(prefix: str) -> Dict[str, Any]:
        """Load configuration from environment variables.

        Args:
            prefix: Prefix for environment variables

        Returns:
            Dictionary of configuration values
        """
        config: dict[str, Any] = {}
        prefix_len = len(prefix)

        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Remove prefix and convert to nested dict
                key_path = key[prefix_len:].lower().split("__")
                d = config
                for k in key_path[:-1]:
                    d = d.setdefault(k, {})
                d[key_path[-1]] = value

        return config

    @staticmethod
    def _merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge two dictionaries.

        Args:
            base: Base dictionary
            override: Override dictionary

        Returns:
            Merged dictionary
        """
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = Config._merge_dicts(result[key], value)
            else:
                result[key] = value
        return result

    def save(self, config_path: str) -> None:
        """Save configuration to file.

        Args:
            config_path: Path to save config file
        """
        config_dir = os.path.dirname(config_path)
        if config_dir:
            os.makedirs(config_dir, exist_ok=True)

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(self.model_dump(exclude_none=True), f, indent=2, ensure_ascii=False)
