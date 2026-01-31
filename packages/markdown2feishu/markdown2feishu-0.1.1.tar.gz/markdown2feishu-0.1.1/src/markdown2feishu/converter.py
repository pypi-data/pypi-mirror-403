# src/markdown2feishu/converter.py
"""Markdown to Feishu blocks converter using mistune."""

import re
from typing import Any, Dict, List, Optional

import mistune

from .blocks import (
    BlockType,
    create_bullet,
    create_code,
    create_divider,
    create_equation,
    create_heading,
    create_ordered,
    create_quote,
    create_table,
    create_text,
    create_text_run,
)


# Custom math plugin for mistune v3
INLINE_MATH_PATTERN = r'\$[^\$\n]+?\$'
BLOCK_MATH_PATTERN = r'\$\$\n[\s\S]+?\n\$\$'


def parse_inline_math(inline, m, state):
    """Parse inline math $...$."""
    # Extract content between $ delimiters
    text = m.group(0)[1:-1]
    state.append_token({"type": "inline_math", "raw": text})
    return m.end()


def parse_block_math(block, m, state):
    """Parse block math $$...$$."""
    # Extract content between $$ delimiters
    text = m.group(0)[3:-3].strip()
    state.append_token({"type": "block_math", "raw": text})
    return m.end()


def math_plugin(md):
    """Plugin to add math support to mistune v3."""
    # Register inline math before emphasis to avoid conflicts with $
    md.inline.register(
        "inline_math",
        INLINE_MATH_PATTERN,
        parse_inline_math,
        before="emphasis",
    )

    # Register block math before paragraph
    md.block.register(
        "block_math",
        BLOCK_MATH_PATTERN,
        parse_block_math,
        before="list",
    )


class MarkdownConverter:
    """Convert Markdown text to Feishu document blocks."""

    def __init__(self) -> None:
        """Initialize the converter with mistune parser."""
        self._markdown = mistune.create_markdown(
            renderer="ast",
            plugins=["strikethrough", "table", math_plugin],
        )

    def convert(self, text: str) -> List[Dict[str, Any]]:
        """Convert Markdown text to a list of Feishu blocks.

        Args:
            text: Markdown formatted text.

        Returns:
            List of Feishu block dictionaries.
        """
        tokens = self._markdown(text)
        return self._process_tokens(tokens)

    def _process_tokens(self, tokens: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process a list of AST tokens into Feishu blocks."""
        blocks: List[Dict[str, Any]] = []

        for token in tokens:
            token_type = token.get("type")

            if token_type == "paragraph":
                elements = self._process_inline(token.get("children", []))
                blocks.append(create_text(elements))

            elif token_type == "heading":
                level = token.get("attrs", {}).get("level", 1)
                elements = self._process_inline(token.get("children", []))
                blocks.append(create_heading(level, elements))

            elif token_type == "list":
                list_blocks = self._process_list(token)
                blocks.extend(list_blocks)

            elif token_type == "thematic_break":
                blocks.append(create_divider())

            elif token_type == "block_code":
                raw = token.get("raw", "")
                info = token.get("attrs", {}).get("info", "")
                blocks.append(create_code(raw, info))

            elif token_type == "block_quote":
                elements = self._flatten_quote_children(token.get("children", []))
                blocks.append(create_quote(elements))

            elif token_type == "table":
                table_block = self._process_table(token)
                blocks.append(table_block)

            elif token_type == "block_math":
                # Block math formula $$...$$
                raw = token.get("raw", "")
                elements = [create_equation(raw)]
                blocks.append(create_text(elements))

            elif token_type == "blank_line":
                # Skip blank lines - they don't produce blocks
                pass

        return blocks

    def _process_inline(
        self,
        children: List[Dict[str, Any]],
        bold: bool = False,
        italic: bool = False,
        strikethrough: bool = False,
        link: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Process inline elements recursively.

        Args:
            children: List of inline tokens.
            bold: Whether text is bold (inherited from parent).
            italic: Whether text is italic (inherited from parent).
            strikethrough: Whether text has strikethrough (inherited from parent).
            link: URL if text is a link (inherited from parent).

        Returns:
            List of text_run elements.
        """
        elements: List[Dict[str, Any]] = []

        for child in children:
            child_type = child.get("type")

            if child_type == "text":
                content = child.get("raw", "")
                elements.append(
                    create_text_run(
                        content,
                        bold=bold,
                        italic=italic,
                        strikethrough=strikethrough,
                        link=link,
                    )
                )

            elif child_type == "strong":
                # Bold: recurse with bold=True
                nested = self._process_inline(
                    child.get("children", []),
                    bold=True,
                    italic=italic,
                    strikethrough=strikethrough,
                    link=link,
                )
                elements.extend(nested)

            elif child_type == "emphasis":
                # Italic: recurse with italic=True
                nested = self._process_inline(
                    child.get("children", []),
                    bold=bold,
                    italic=True,
                    strikethrough=strikethrough,
                    link=link,
                )
                elements.extend(nested)

            elif child_type == "strikethrough":
                # Strikethrough: recurse with strikethrough=True
                nested = self._process_inline(
                    child.get("children", []),
                    bold=bold,
                    italic=italic,
                    strikethrough=True,
                    link=link,
                )
                elements.extend(nested)

            elif child_type == "link":
                # Link: recurse with URL
                url = child.get("attrs", {}).get("url", "")
                nested = self._process_inline(
                    child.get("children", []),
                    bold=bold,
                    italic=italic,
                    strikethrough=strikethrough,
                    link=url,
                )
                elements.extend(nested)

            elif child_type == "codespan":
                # Inline code
                content = child.get("raw", "")
                elements.append(create_text_run(content, inline_code=True))

            elif child_type == "softbreak":
                # Soft line break (single newline in source)
                elements.append(create_text_run("\n"))

            elif child_type == "linebreak":
                # Hard line break
                elements.append(create_text_run("\n"))

            elif child_type == "image":
                # Images - for now, just show alt text
                alt = child.get("alt", "")
                elements.append(create_text_run(f"[Image: {alt}]"))

            elif child_type == "inline_math":
                # Inline math formula $...$
                content = child.get("raw", "")
                elements.append(create_equation(content))

        return elements

    def _process_list(self, token: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process a list token into multiple Feishu blocks.

        Args:
            token: List token from mistune AST.

        Returns:
            List of bullet or ordered list item blocks.
        """
        blocks: List[Dict[str, Any]] = []
        ordered = token.get("attrs", {}).get("ordered", False)
        children = token.get("children", [])

        for item in children:
            if item.get("type") == "list_item":
                elements = self._process_list_item(item)
                if ordered:
                    blocks.append(create_ordered(elements))
                else:
                    blocks.append(create_bullet(elements))

        return blocks

    def _process_list_item(self, item: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process a list item's content into text elements.

        Args:
            item: List item token.

        Returns:
            List of text_run elements.
        """
        elements: List[Dict[str, Any]] = []
        children = item.get("children", [])

        for child in children:
            child_type = child.get("type")

            if child_type == "block_text":
                # Simple text in list item
                nested = self._process_inline(child.get("children", []))
                elements.extend(nested)

            elif child_type == "paragraph":
                # Paragraph in list item (loose list)
                nested = self._process_inline(child.get("children", []))
                elements.extend(nested)

        return elements

    def _flatten_quote_children(
        self, children: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Flatten blockquote children into text elements.

        Args:
            children: Children of blockquote token.

        Returns:
            List of text_run elements.
        """
        elements: List[Dict[str, Any]] = []

        for child in children:
            child_type = child.get("type")

            if child_type == "paragraph":
                nested = self._process_inline(child.get("children", []))
                elements.extend(nested)
                # Add newline between paragraphs
                elements.append(create_text_run("\n"))

        # Remove trailing newline if present
        if elements and elements[-1]["text_run"]["content"] == "\n":
            elements.pop()

        return elements

    def _process_table(self, token: Dict[str, Any]) -> Dict[str, Any]:
        """Process a table token into a Feishu table block.

        Args:
            token: Table token from mistune AST.

        Returns:
            Feishu table block.
        """
        rows: List[List[str]] = []
        children = token.get("children", [])

        for child in children:
            child_type = child.get("type")

            if child_type == "table_head":
                # Process header row
                row = self._process_table_row(child.get("children", []))
                rows.append(row)

            elif child_type == "table_body":
                # Process body rows
                for row_child in child.get("children", []):
                    if row_child.get("type") == "table_row":
                        row = self._process_table_row(row_child.get("children", []))
                        rows.append(row)

        row_size = len(rows)
        column_size = len(rows[0]) if rows else 0

        return create_table(row_size, column_size, rows)

    def _process_table_row(self, cells: List[Dict[str, Any]]) -> List[str]:
        """Process a table row into cell strings.

        Args:
            cells: List of table_cell tokens.

        Returns:
            List of cell content strings.
        """
        row: List[str] = []

        for cell in cells:
            if cell.get("type") == "table_cell":
                content = self._extract_text_content(cell.get("children", []))
                row.append(content)

        return row

    def _extract_text_content(self, children: List[Dict[str, Any]]) -> str:
        """Extract plain text content from inline tokens.

        Args:
            children: List of inline tokens.

        Returns:
            Plain text content.
        """
        parts: List[str] = []

        for child in children:
            child_type = child.get("type")

            if child_type == "text":
                parts.append(child.get("raw", ""))
            elif child_type in ("strong", "emphasis", "strikethrough", "link"):
                # Recurse into nested inline elements
                nested_text = self._extract_text_content(child.get("children", []))
                parts.append(nested_text)
            elif child_type == "codespan":
                parts.append(child.get("raw", ""))

        return "".join(parts)
