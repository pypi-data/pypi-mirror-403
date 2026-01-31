"""Tests for configuration management."""

import json
import os
import tempfile

from owlab.core.config import Config
from owlab.core.config import LarkAPIConfig
from owlab.core.config import LarkConfig
from owlab.core.config import LarkWebhookConfig


class TestConfig:
    """Tests for Config class."""

    def test_default_config(self):
        """Test default configuration."""
        config = Config()
        assert config.storage.local_path == "./output"
        assert config.logging.level == "INFO"

    def test_load_from_dict(self):
        """Test loading configuration from dictionary."""
        config_dict = {
            "storage": {"local_path": "/tmp/test"},
            "logging": {"level": "DEBUG"},
        }
        config = Config(**config_dict)
        assert config.storage.local_path == "/tmp/test"
        assert config.logging.level == "DEBUG"

    def test_load_from_file(self):
        """Test loading configuration from file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_dict = {
                "storage": {"local_path": "/tmp/test"},
                "logging": {"level": "DEBUG"},
            }
            json.dump(config_dict, f)
            temp_path = f.name

        try:
            config = Config.load(config_path=temp_path)
            assert config.storage.local_path == "/tmp/test"
            assert config.logging.level == "DEBUG"
        finally:
            os.unlink(temp_path)

    def test_load_from_env(self, monkeypatch):
        """Test loading configuration from environment variables."""
        monkeypatch.setenv("OWLAB_STORAGE__LOCAL_PATH", "/tmp/env_test")
        monkeypatch.setenv("OWLAB_LOGGING__LEVEL", "WARNING")

        config = Config.load()
        assert config.storage.local_path == "/tmp/env_test"
        assert config.logging.level == "WARNING"

    def test_save_config(self):
        """Test saving configuration to file."""
        config = Config(storage={"local_path": "/tmp/save_test"})

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            config.save(temp_path)
            assert os.path.exists(temp_path)

            # Verify saved content
            with open(temp_path, "r") as f:
                saved_config = json.load(f)
            assert saved_config["storage"]["local_path"] == "/tmp/save_test"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_lark_webhook_config(self):
        """Test Lark Webhook configuration."""
        webhook_config = LarkWebhookConfig(
            webhook_url="https://test.com/webhook", signature="test_signature"
        )
        assert webhook_config.webhook_url == "https://test.com/webhook"
        assert webhook_config.signature == "test_signature"

    def test_lark_api_config(self):
        """Test Lark API configuration."""
        api_config = LarkAPIConfig(
            app_id="test_app_id",
            app_secret="test_secret",
            root_folder_token="test_token",
        )
        assert api_config.app_id == "test_app_id"
        assert api_config.app_secret == "test_secret"
        assert api_config.root_folder_token == "test_token"

    def test_lark_config(self):
        """Test Lark configuration."""
        lark_config = LarkConfig(
            webhook=LarkWebhookConfig(
                webhook_url="https://test.com/webhook", signature="test_signature"
            ),
            api=LarkAPIConfig(
                app_id="test_app_id",
                app_secret="test_secret",
                root_folder_token="test_token",
            ),
        )
        assert lark_config.webhook is not None
        assert lark_config.api is not None
