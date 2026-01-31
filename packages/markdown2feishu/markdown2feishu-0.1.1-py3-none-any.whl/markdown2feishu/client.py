# src/markdown2feishu/client.py
"""Feishu API client for creating and managing documents."""

import asyncio
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from .config import FeishuConfig, load_config
from .converter import MarkdownConverter

# API endpoints
AUTH_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
CREATE_DOC_URL = "https://open.feishu.cn/open-apis/docx/v1/documents"

# Block batching limit
BLOCKS_PER_BATCH = 50

# Token cache duration (1.5 hours in seconds)
TOKEN_CACHE_DURATION = 5400


@dataclass
class Document:
    """Represents a Feishu document."""

    document_id: str
    url: str
    title: str


class FeishuClient:
    """Async client for Feishu API operations.

    Supports creating documents, writing blocks, and sending webhooks.
    """

    def __init__(
        self,
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None,
        webhook_url: Optional[str] = None,
        folder_token: Optional[str] = None,
    ) -> None:
        """Initialize the Feishu client.

        Args:
            app_id: Feishu app ID (optional, uses load_config if not provided).
            app_secret: Feishu app secret (optional, uses load_config if not provided).
            webhook_url: Webhook URL for sending messages (optional).
            folder_token: Default folder token for documents (optional).

        Raises:
            ValueError: If required credentials are missing.
        """
        self._config: FeishuConfig = load_config(
            app_id=app_id,
            app_secret=app_secret,
            webhook_url=webhook_url,
            folder_token=folder_token,
        )
        self._http_client: Optional[httpx.AsyncClient] = None
        self._converter = MarkdownConverter()

        # Token cache
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client

    async def close(self) -> None:
        """Close the HTTP client and release resources."""
        if self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None

    async def __aenter__(self) -> "FeishuClient":
        """Enter async context manager."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context manager."""
        await self.close()

    async def _get_access_token(self) -> str:
        """Get tenant access token with caching.

        The token is cached for 1.5 hours (5400 seconds).

        Returns:
            Valid access token string.

        Raises:
            httpx.HTTPStatusError: If token request fails.
        """
        current_time = time.time()

        # Return cached token if still valid
        if self._access_token and current_time < self._token_expires_at:
            return self._access_token

        # Request new token
        client = await self._get_client()
        response = await client.post(
            AUTH_URL,
            json={
                "app_id": self._config.app_id,
                "app_secret": self._config.app_secret,
            },
        )
        response.raise_for_status()

        data = response.json()
        self._access_token = data["tenant_access_token"]
        # Cache for slightly less than actual expiry (1.5 hours)
        self._token_expires_at = current_time + TOKEN_CACHE_DURATION

        return self._access_token

    async def _create_document(
        self,
        title: str,
        folder_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new Feishu document.

        Args:
            title: Document title.
            folder_token: Folder to create document in (uses default if not provided).

        Returns:
            API response data containing document info.

        Raises:
            httpx.HTTPStatusError: If document creation fails.
        """
        token = await self._get_access_token()
        client = await self._get_client()

        headers = {"Authorization": f"Bearer {token}"}

        payload: Dict[str, Any] = {"title": title}
        effective_folder = folder_token or self._config.folder_token
        if effective_folder:
            payload["folder_token"] = effective_folder

        response = await client.post(
            CREATE_DOC_URL,
            headers=headers,
            json=payload,
        )
        response.raise_for_status()

        return response.json()

    async def _write_blocks(
        self,
        document_id: str,
        blocks: List[Dict[str, Any]],
    ) -> None:
        """Write blocks to a document with batching.

        Args:
            document_id: Target document ID.
            blocks: List of Feishu block dictionaries.

        Raises:
            httpx.HTTPStatusError: If block writing fails.
        """
        if not blocks:
            return

        # Split blocks into batches
        for i in range(0, len(blocks), BLOCKS_PER_BATCH):
            batch = blocks[i : i + BLOCKS_PER_BATCH]
            await self._write_block_batch(document_id, batch)

    async def _write_block_batch(
        self,
        document_id: str,
        blocks: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Write a batch of blocks to a document.

        Args:
            document_id: Target document ID.
            blocks: List of blocks (max 50).

        Returns:
            API response data.

        Raises:
            httpx.HTTPStatusError: If request fails.
        """
        token = await self._get_access_token()
        client = await self._get_client()

        headers = {"Authorization": f"Bearer {token}"}
        url = f"{CREATE_DOC_URL}/{document_id}/blocks/{document_id}/children"

        # Separate table blocks for special handling
        regular_blocks = []
        for block in blocks:
            if block.get("block_type") == 31:  # TABLE
                # Write any accumulated regular blocks first
                if regular_blocks:
                    await self._write_regular_blocks(
                        client, url, headers, regular_blocks
                    )
                    regular_blocks = []
                # Write table with special handling
                await self._write_table(document_id, block)
            else:
                regular_blocks.append(block)

        # Write remaining regular blocks
        if regular_blocks:
            return await self._write_regular_blocks(
                client, url, headers, regular_blocks
            )

        return {"code": 0}

    async def _write_regular_blocks(
        self,
        client: httpx.AsyncClient,
        url: str,
        headers: Dict[str, str],
        blocks: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Write non-table blocks to document.

        Args:
            client: HTTP client.
            url: API endpoint URL.
            headers: Request headers.
            blocks: List of blocks to write.

        Returns:
            API response data.
        """
        response = await client.post(
            url,
            headers=headers,
            json={"children": blocks},
        )
        response.raise_for_status()
        return response.json()

    async def _write_table(
        self,
        document_id: str,
        table_block: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Write a table block using the table-specific API.

        Tables require special handling:
        1. Create table structure
        2. Fill cells with content

        Args:
            document_id: Target document ID.
            table_block: Table block dictionary.

        Returns:
            API response data.
        """
        token = await self._get_access_token()
        client = await self._get_client()

        headers = {"Authorization": f"Bearer {token}"}
        url = f"{CREATE_DOC_URL}/{document_id}/blocks/{document_id}/children"

        table_data = table_block.get("table", {})
        prop = table_data.get("property", {})
        row_size = prop.get("row_size", 1)
        column_size = prop.get("column_size", 1)

        # Step 1: Create empty table
        create_payload = {
            "children": [
                {
                    "block_type": 31,
                    "table": {
                        "property": {
                            "row_size": row_size,
                            "column_size": column_size,
                        }
                    },
                }
            ]
        }

        response = await client.post(
            url,
            headers=headers,
            json=create_payload,
        )
        response.raise_for_status()
        result = response.json()

        # Get table block ID from response
        data = result.get("data", {})
        children = data.get("children", [])
        if not children:
            return result

        table_block_id = children[0].get("block_id")
        if not table_block_id:
            return result

        # Get cell block IDs
        table_children = children[0].get("children", [])
        if not table_children:
            return result

        # Step 2: Fill cells with content
        # Small delay to ensure table is fully created
        await asyncio.sleep(0.1)
        cells = table_data.get("cells", [])
        cell_index = 0

        for row_idx, row in enumerate(cells):
            for col_idx, cell_content in enumerate(row):
                if cell_index >= len(table_children):
                    break

                cell_block_id = table_children[cell_index]
                cell_index += 1

                if cell_content:
                    # Add text block to cell
                    cell_url = f"{CREATE_DOC_URL}/{document_id}/blocks/{cell_block_id}/children"
                    cell_payload = {
                        "children": [
                            {
                                "block_type": 2,  # TEXT
                                "text": {
                                    "elements": [
                                        {
                                            "text_run": {
                                                "content": cell_content,
                                                "text_element_style": {
                                                    "bold": False,
                                                    "italic": False,
                                                    "strikethrough": False,
                                                    "underline": False,
                                                    "inline_code": False,
                                                },
                                            }
                                        }
                                    ],
                                    "style": {},
                                },
                            }
                        ]
                    }

                    cell_response = await client.post(
                        cell_url,
                        headers=headers,
                        json=cell_payload,
                    )
                    cell_response.raise_for_status()
                    # Small delay to avoid rate limiting
                    await asyncio.sleep(0.05)

        return result

    async def push_markdown(
        self,
        content: str,
        title: str,
        folder_token: Optional[str] = None,
    ) -> Document:
        """Convert Markdown and push to Feishu as a document.

        Args:
            content: Markdown content string.
            title: Document title.
            folder_token: Target folder (uses default if not provided).

        Returns:
            Document object with document_id and url.

        Raises:
            httpx.HTTPStatusError: If API requests fail.
        """
        # Create document
        doc_response = await self._create_document(title, folder_token)
        doc_data = doc_response.get("data", {}).get("document", {})
        document_id = doc_data.get("document_id", "")
        url = doc_data.get("url", f"https://feishu.cn/docx/{document_id}")

        # Convert markdown to blocks
        blocks = self._converter.convert(content)

        # Write blocks to document
        await self._write_blocks(document_id, blocks)

        return Document(
            document_id=document_id,
            url=url,
            title=title,
        )

    async def push_file(
        self,
        file_path: str,
        title: Optional[str] = None,
        folder_token: Optional[str] = None,
    ) -> Document:
        """Read Markdown from file and push to Feishu.

        Args:
            file_path: Path to Markdown file.
            title: Document title (uses filename if not provided).
            folder_token: Target folder (uses default if not provided).

        Returns:
            Document object with document_id and url.

        Raises:
            FileNotFoundError: If file doesn't exist.
            httpx.HTTPStatusError: If API requests fail.
        """
        path = Path(file_path)
        content = path.read_text(encoding="utf-8")

        # Use filename as title if not provided
        effective_title = title or path.stem

        return await self.push_markdown(content, effective_title, folder_token)

    async def send_webhook(
        self,
        content: str,
        title: Optional[str] = None,
    ) -> bool:
        """Send content to Feishu webhook.

        Args:
            content: Message content (Markdown supported).
            title: Optional message title.

        Returns:
            True if message sent successfully.

        Raises:
            ValueError: If webhook_url is not configured.
            httpx.HTTPStatusError: If request fails.
        """
        if not self._config.webhook_url:
            raise ValueError(
                "webhook_url not configured. Set FEISHU_WEBHOOK_URL or provide webhook_url parameter."
            )

        client = await self._get_client()

        # Build webhook message
        message: Dict[str, Any] = {
            "msg_type": "interactive",
            "card": {
                "elements": [
                    {
                        "tag": "markdown",
                        "content": content,
                    }
                ],
            },
        }

        if title:
            message["card"]["header"] = {
                "title": {
                    "tag": "plain_text",
                    "content": title,
                },
            }

        response = await client.post(
            self._config.webhook_url,
            json=message,
        )
        response.raise_for_status()

        result = response.json()
        return result.get("StatusCode") == 0 or result.get("code") == 0
