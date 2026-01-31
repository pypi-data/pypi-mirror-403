"""Lark Webhook Bot for sending notifications."""

import base64
import hashlib
import hmac
import time
from typing import Any, Dict, List, Optional

import requests

from owlab.core.logger import get_logger
from owlab.utils.retry import retry_on_http_error

logger = get_logger("owlab.lark.webhook_bot")


class LarkWebhookBot:
    """Lark Webhook Bot for sending experiment notifications."""

    def __init__(self, webhook_url: str, signature: str):
        """Initialize Lark Webhook Bot.

        Args:
            webhook_url: Lark webhook URL
            signature: Webhook signature for authentication
        """
        self.webhook_url = webhook_url
        self.signature = signature
        logger.info("Lark Webhook Bot initialized")

    def _sign(self, timestamp: str) -> str:
        """Generate signature for webhook request.

        According to Lark API docs:
        - key = timestamp + "\n" + secret
        - sign = Base64(HMAC-SHA256(key, ""))

        Args:
            timestamp: Timestamp string (seconds)

        Returns:
            Base64 encoded signature string
        """
        # Build signing key: timestamp + "\n" + secret
        key = f"{timestamp}\n{self.signature}"
        key_enc = key.encode("utf-8")

        # Message is empty string for webhook
        msg_enc = "".encode("utf-8")

        # Calculate HMAC-SHA256
        hmac_code = hmac.new(key_enc, msg_enc, digestmod=hashlib.sha256).digest()

        # Base64 encode
        sign = base64.b64encode(hmac_code).decode("utf-8")
        return sign

    @retry_on_http_error(max_attempts=3, delay=1.0)
    def _send_message(self, content: Dict) -> bool:
        """Send message to Lark webhook.

        Args:
            content: Message content dictionary

        Returns:
            True if successful, False otherwise
        """
        # Generate timestamp (seconds, not milliseconds)
        timestamp = str(int(time.time()))
        sign = self._sign(timestamp)

        # Webhook payload format (no nonce needed for Lark webhook)
        payload = {
            "timestamp": timestamp,
            "sign": sign,
            "msg_type": "interactive",
            "card": content,
        }

        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()

            # Check response code
            if result.get("code") == 0:
                logger.info("Message sent successfully")
                return True
            else:
                error_msg = result.get("msg", "Unknown error")
                error_code = result.get("code", "Unknown")
                logger.error(f"Failed to send message (code: {error_code}): {error_msg}")
                logger.debug(f"Payload timestamp: {timestamp}, sign: {sign[:20]}...")
                logger.debug(f"Response: {result}")
                return False
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error sending message: {e}")
            if hasattr(e.response, 'text'):
                logger.debug(f"Response text: {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"Exception sending message: {e}")
            return False

    def _format_experiment_params(self, config: Dict) -> str:
        """Format experiment parameters as readable text.

        Args:
            config: Experiment configuration dictionary

        Returns:
            Formatted parameter text
        """
        lines = []
        params = config.get("experiment_params", {})
        if params:
            for key, value in params.items():
                lines.append(f"  • {key}: {value}")
        return "\n".join(lines) if lines else "  (none)"

    def send_start_notification(
        self,
        experiment_name: str,
        description: str,
        config: Dict,
        type: str = "default",
        tags: Optional[List[str]] = None,
        swanlab_url: str = "",
        folder_url: str = "",
    ) -> bool:
        """Send experiment start notification.

        Args:
            experiment_name: Name of the experiment
            description: Experiment description
            config: Experiment configuration
            type: Experiment type
            tags: Experiment tags
            swanlab_url: SwanLab experiment URL
            folder_url: Lark folder URL

        Returns:
            True if successful, False otherwise
        """
        # Extract seed (check both top-level and experiment_params)
        seed = config.get("seed")
        if seed is None:
            params = config.get("experiment_params", {})
            seed = params.get("seed")

        # Format experiment parameters
        params_text = self._format_experiment_params(config)

        # Build content text
        content_parts = []
        content_parts.append(f"**Experiment:** {experiment_name}")
        content_parts.append(f"**Type:** {type or config.get('type', 'default')}")
        if tags:
            content_parts.append(f"**Tags:** {', '.join(tags)}")
        if description:
            content_parts.append(f"**Description:** {description}")
        if seed is not None:
            content_parts.append(f"**Seed:** {seed}")
        if params_text != "  (none)":
            content_parts.append(f"**Parameters:**\n{params_text}")

        content: Dict[str, Any] = {
            "config": {
                "wide_screen_mode": True,
            },
            "header": {
                "title": {"tag": "plain_text", "content": f"🚀 Experiment Started: {experiment_name}"},
                "template": "blue",
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {"tag": "lark_md", "content": "\n".join(content_parts)},
                },
            ],
        }

        if swanlab_url:
            content["elements"].append(
                {
                    "tag": "div",
                    "text": {"tag": "lark_md", "content": f"**SwanLab:** {swanlab_url}"},
                }
            )

        if folder_url:
            content["elements"].append(
                {
                    "tag": "div",
                    "text": {"tag": "lark_md", "content": f"**Experiment Data:** {folder_url}"},
                }
            )

        return self._send_message(content)  # type: ignore[no-any-return]

    def _format_results_table(self, results: list, max_rows: int = 10) -> str:
        """Format experiment results as markdown table.

        Args:
            results: List of experiment result dictionaries
            max_rows: Maximum number of rows to display

        Returns:
            Formatted table text
        """
        if not results or not isinstance(results, list):
            return "No results"

        # Limit results to max_rows
        display_results = results[:max_rows]

        # Build table header
        # Extract all unique keys from results (excluding 'method')
        all_keys = set()
        for result in display_results:
            if isinstance(result, dict):
                for key in result.keys():
                    if key != "method":
                        all_keys.add(key)

        # Sort keys: datasets first, then Average
        sorted_keys = sorted([k for k in all_keys if k != "Average"])
        if "Average" in all_keys:
            sorted_keys.append("Average")

        if not sorted_keys:
            return "No results"

        # Build table rows
        table_rows = []

        # Header row
        header = ["Method"] + sorted_keys
        table_rows.append("| " + " | ".join(header) + " |")
        table_rows.append("| " + " | ".join(["---"] * len(header)) + " |")

        # Data rows
        for result in display_results:
            if not isinstance(result, dict) or "method" not in result:
                continue

            method = result.get("method", "")
            row = [method]

            for key in sorted_keys:
                value = result.get(key, "")
                if isinstance(value, dict):
                    # Extract metrics from dataset result
                    metrics = []
                    for metric_key, metric_value in value.items():
                        if metric_key != "measure":
                            if isinstance(metric_value, float):
                                metrics.append(f"{metric_key}: {metric_value:.3f}")
                            else:
                                metrics.append(f"{metric_key}: {metric_value}")
                    # Use comma separator for better display in table cells
                    row.append(", ".join(metrics) if metrics else "")
                else:
                    row.append(str(value))

            table_rows.append("| " + " | ".join(row) + " |")

        table_text = "\n".join(table_rows)

        # Add note if results were truncated
        if len(results) > max_rows:
            table_text += f"\n\n*Showing first {max_rows} of {len(results)} results*"

        return table_text

    def send_finish_notification(
        self,
        experiment_name: str,
        results: Dict,
        description: str = "",
        config: Optional[Dict] = None,
        type: str = "default",
        tags: Optional[List[str]] = None,
        swanlab_url: str = "",
        folder_url: str = "",
    ) -> bool:
        """Send experiment finish notification.

        Args:
            experiment_name: Name of the experiment
            results: Experiment results (list or dict) - not displayed in notification
            description: Experiment description
            config: Experiment configuration dictionary
            type: Experiment type
            tags: Experiment tags
            swanlab_url: SwanLab experiment URL
            folder_url: Lark folder URL

        Returns:
            True if successful, False otherwise
        """
        config = config or {}

        # Extract seed (check both top-level and experiment_params)
        seed = config.get("seed")
        if seed is None:
            params = config.get("experiment_params", {})
            seed = params.get("seed")

        # Format experiment parameters
        params_text = self._format_experiment_params(config)

        # Build content text (without results table)
        content_parts = []
        content_parts.append(f"**Experiment:** {experiment_name}")
        content_parts.append(f"**Type:** {type or config.get('type', 'default')}")
        if tags:
            content_parts.append(f"**Tags:** {', '.join(tags)}")
        if description:
            content_parts.append(f"**Description:** {description}")
        if seed is not None:
            content_parts.append(f"**Seed:** {seed}")
        if params_text != "  (none)":
            content_parts.append(f"**Parameters:**\n{params_text}")

        content: Dict[str, Any] = {
            "config": {
                "wide_screen_mode": True,
            },
            "header": {
                "title": {"tag": "plain_text", "content": f"✅ Experiment Finished: {experiment_name}"},
                "template": "green",
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {"tag": "lark_md", "content": "\n".join(content_parts)},
                },
            ],
        }

        if swanlab_url:
            content["elements"].append(
                {
                    "tag": "div",
                    "text": {"tag": "lark_md", "content": f"**SwanLab:** {swanlab_url}"},
                }
            )

        if folder_url:
            content["elements"].append(
                {
                    "tag": "div",
                    "text": {"tag": "lark_md", "content": f"**Experiment Data:** {folder_url}"},
                }
            )

        return self._send_message(content)  # type: ignore[no-any-return]
