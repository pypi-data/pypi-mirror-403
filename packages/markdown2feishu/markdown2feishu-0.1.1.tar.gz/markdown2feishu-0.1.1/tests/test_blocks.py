# tests/test_blocks.py
from markdown2feishu.blocks import (
    create_heading1,
    create_text,
    create_text_run,
    BlockType,
)


def test_create_heading1():
    """Creates heading1 block with correct structure."""
    block = create_heading1("Hello World")

    assert block["block_type"] == BlockType.HEADING1
    assert block["heading1"]["elements"][0]["text_run"]["content"] == "Hello World"


def test_create_text_with_bold():
    """Creates text block with bold formatting."""
    elements = [
        create_text_run("normal "),
        create_text_run("bold", bold=True),
        create_text_run(" text"),
    ]
    block = create_text(elements)

    assert block["block_type"] == BlockType.TEXT
    assert block["text"]["elements"][1]["text_run"]["text_element_style"]["bold"] is True


def test_create_text_run_with_link():
    """Creates text run with link."""
    element = create_text_run("click here", link="https://example.com")

    assert element["text_run"]["content"] == "click here"
    assert element["text_run"]["text_element_style"]["link"]["url"] == "https://example.com"
