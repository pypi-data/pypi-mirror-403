# tests/test_converter.py
import pytest
from markdown2feishu.converter import MarkdownConverter
from markdown2feishu.blocks import BlockType


class TestHeadings:
    """Test heading conversion."""

    def test_heading1(self):
        converter = MarkdownConverter()
        blocks = converter.convert("# Hello World")

        assert len(blocks) == 1
        assert blocks[0]["block_type"] == BlockType.HEADING1
        assert blocks[0]["heading1"]["elements"][0]["text_run"]["content"] == "Hello World"

    def test_heading2(self):
        converter = MarkdownConverter()
        blocks = converter.convert("## Section Title")

        assert blocks[0]["block_type"] == BlockType.HEADING2

    def test_heading_with_bold(self):
        converter = MarkdownConverter()
        blocks = converter.convert("# Hello **World**")

        elements = blocks[0]["heading1"]["elements"]
        assert elements[0]["text_run"]["content"] == "Hello "
        assert elements[1]["text_run"]["content"] == "World"
        assert elements[1]["text_run"]["text_element_style"]["bold"] is True


class TestInlineFormatting:
    """Test inline formatting conversion."""

    def test_bold(self):
        converter = MarkdownConverter()
        blocks = converter.convert("This is **bold** text")

        elements = blocks[0]["text"]["elements"]
        assert elements[1]["text_run"]["text_element_style"]["bold"] is True

    def test_italic(self):
        converter = MarkdownConverter()
        blocks = converter.convert("This is *italic* text")

        elements = blocks[0]["text"]["elements"]
        assert elements[1]["text_run"]["text_element_style"]["italic"] is True

    def test_link(self):
        converter = MarkdownConverter()
        blocks = converter.convert("Click [here](https://example.com)")

        elements = blocks[0]["text"]["elements"]
        link_element = next(e for e in elements if e["text_run"]["content"] == "here")
        assert link_element["text_run"]["text_element_style"]["link"]["url"] == "https://example.com"

    def test_inline_code(self):
        converter = MarkdownConverter()
        blocks = converter.convert("Use `print()` function")

        elements = blocks[0]["text"]["elements"]
        code_element = next(e for e in elements if e["text_run"]["content"] == "print()")
        assert code_element["text_run"]["text_element_style"]["inline_code"] is True


class TestLists:
    """Test list conversion."""

    def test_bullet_list(self):
        converter = MarkdownConverter()
        blocks = converter.convert("- Item 1\n- Item 2")

        assert len(blocks) == 2
        assert blocks[0]["block_type"] == BlockType.BULLET
        assert blocks[1]["block_type"] == BlockType.BULLET

    def test_ordered_list(self):
        converter = MarkdownConverter()
        blocks = converter.convert("1. First\n2. Second")

        assert blocks[0]["block_type"] == BlockType.ORDERED


class TestDivider:
    """Test divider conversion."""

    def test_horizontal_rule(self):
        converter = MarkdownConverter()
        blocks = converter.convert("Above\n\n---\n\nBelow")

        divider = next(b for b in blocks if b["block_type"] == BlockType.DIVIDER)
        assert divider is not None


class TestTable:
    """Test table conversion."""

    def test_simple_table(self):
        converter = MarkdownConverter()
        md = """| Name | Age |
| --- | --- |
| Alice | 30 |
| Bob | 25 |"""

        blocks = converter.convert(md)
        table = next(b for b in blocks if b["block_type"] == BlockType.TABLE)

        assert table["table"]["property"]["row_size"] == 3  # header + 2 data rows
        assert table["table"]["property"]["column_size"] == 2
