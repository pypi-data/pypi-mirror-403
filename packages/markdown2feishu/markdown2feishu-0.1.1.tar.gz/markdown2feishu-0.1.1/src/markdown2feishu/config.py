"""Configuration loading for markdown2feishu."""

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


@dataclass
class FeishuConfig:
    """Feishu API configuration."""

    app_id: str
    app_secret: str
    webhook_url: Optional[str] = None
    folder_token: Optional[str] = None


def _load_toml_config() -> dict:
    """Load config from TOML file.

    Searches in order:
    1. .feishu.toml in current directory
    2. ~/.feishu.toml
    """
    search_paths = [
        Path.cwd() / ".feishu.toml",
        Path.home() / ".feishu.toml",
    ]

    for path in search_paths:
        if path.exists():
            with open(path, "rb") as f:
                data = tomllib.load(f)
                return data.get("feishu", {})

    return {}


def load_config(
    app_id: Optional[str] = None,
    app_secret: Optional[str] = None,
    webhook_url: Optional[str] = None,
    folder_token: Optional[str] = None,
) -> FeishuConfig:
    """Load configuration with priority: code params > env vars > config file.

    Args:
        app_id: Feishu app ID (optional, can come from env/config)
        app_secret: Feishu app secret (optional, can come from env/config)
        webhook_url: Webhook URL for sending messages (optional)
        folder_token: Default folder token for documents (optional)

    Returns:
        FeishuConfig with resolved values

    Raises:
        ValueError: If required config (app_id, app_secret) is missing
    """
    # Load from TOML file (lowest priority)
    file_config = _load_toml_config()

    # Resolve each field with priority: code > env > file
    resolved_app_id = (
        app_id
        or os.environ.get("FEISHU_APP_ID")
        or file_config.get("app_id")
    )

    resolved_app_secret = (
        app_secret
        or os.environ.get("FEISHU_APP_SECRET")
        or file_config.get("app_secret")
    )

    resolved_webhook_url = (
        webhook_url
        or os.environ.get("FEISHU_WEBHOOK_URL")
        or file_config.get("webhook_url")
    )

    resolved_folder_token = (
        folder_token
        or os.environ.get("FEISHU_FOLDER_TOKEN")
        or file_config.get("folder_token")
    )

    # Validate required fields
    if not resolved_app_id:
        raise ValueError(
            "Missing FEISHU_APP_ID. Set via environment variable, config file, or code parameter."
        )

    if not resolved_app_secret:
        raise ValueError(
            "Missing FEISHU_APP_SECRET. Set via environment variable, config file, or code parameter."
        )

    return FeishuConfig(
        app_id=resolved_app_id,
        app_secret=resolved_app_secret,
        webhook_url=resolved_webhook_url,
        folder_token=resolved_folder_token,
    )
