# tests/test_client.py
"""Tests for FeishuClient."""

import pytest
from dataclasses import dataclass
from markdown2feishu.client import FeishuClient, Document


@dataclass
class MockResponse:
    status_code: int
    _json: dict

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


class TestFeishuClientInit:
    """Test client initialization."""

    def test_init_with_params(self):
        client = FeishuClient(
            app_id="test_id",
            app_secret="test_secret",
        )
        assert client._config.app_id == "test_id"

    def test_init_missing_credentials_raises(self, monkeypatch):
        # Clear environment variables
        monkeypatch.delenv("FEISHU_APP_ID", raising=False)
        monkeypatch.delenv("FEISHU_APP_SECRET", raising=False)
        # Mock config file loading to return empty
        monkeypatch.setattr("markdown2feishu.config._load_toml_config", lambda: {})

        with pytest.raises(ValueError, match="Missing FEISHU_APP_ID"):
            FeishuClient()


class TestDocument:
    """Test Document dataclass."""

    def test_document_attributes(self):
        doc = Document(
            document_id="doc123",
            url="https://feishu.cn/docx/doc123",
            title="Test Doc",
        )
        assert doc.document_id == "doc123"
        assert doc.url == "https://feishu.cn/docx/doc123"
        assert doc.title == "Test Doc"
