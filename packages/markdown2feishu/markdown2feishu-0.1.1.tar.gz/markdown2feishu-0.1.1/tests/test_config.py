# tests/test_config.py
import pytest
from markdown2feishu.config import load_config


def test_load_config_from_env(monkeypatch):
    """Config loads from environment variables."""
    monkeypatch.setenv("FEISHU_APP_ID", "env_app_id")
    monkeypatch.setenv("FEISHU_APP_SECRET", "env_secret")
    monkeypatch.setenv("FEISHU_WEBHOOK_URL", "https://webhook.example.com")

    config = load_config()

    assert config.app_id == "env_app_id"
    assert config.app_secret == "env_secret"
    assert config.webhook_url == "https://webhook.example.com"


def test_load_config_code_params_override_env(monkeypatch):
    """Code parameters override environment variables."""
    monkeypatch.setenv("FEISHU_APP_ID", "env_app_id")
    monkeypatch.setenv("FEISHU_APP_SECRET", "env_secret")

    config = load_config(app_id="code_app_id")

    assert config.app_id == "code_app_id"
    assert config.app_secret == "env_secret"


def test_load_config_missing_required_raises(monkeypatch):
    """Missing required config raises clear error."""
    # Clear environment variables
    monkeypatch.delenv("FEISHU_APP_ID", raising=False)
    monkeypatch.delenv("FEISHU_APP_SECRET", raising=False)
    # Mock config file loading to return empty
    monkeypatch.setattr("markdown2feishu.config._load_toml_config", lambda: {})

    with pytest.raises(ValueError, match="Missing FEISHU_APP_ID"):
        load_config()
