# src/markdown2feishu/blocks.py
"""Feishu document block types and factory functions."""

from enum import IntEnum
from typing import Any, Dict, List, Optional


class BlockType(IntEnum):
    """Feishu block type constants."""

    TEXT = 2
    HEADING1 = 3
    HEADING2 = 4
    HEADING3 = 5
    HEADING4 = 6
    HEADING5 = 7
    HEADING6 = 8
    HEADING7 = 9
    HEADING8 = 10
    HEADING9 = 11
    BULLET = 12
    ORDERED = 13
    CODE = 14
    QUOTE = 15
    DIVIDER = 22
    TABLE = 31


# Language name to Feishu code mapping
LANGUAGE_CODES: dict[str, int] = {
    "": 1,  # PlainText
    "plaintext": 1,
    "text": 1,
    "abap": 2,
    "ada": 3,
    "apache": 4,
    "apex": 5,
    "assembly": 6,
    "asm": 6,
    "bash": 7,
    "sh": 7,
    "shell": 7,
    "csharp": 8,
    "cs": 8,
    "c#": 8,
    "cpp": 9,
    "c++": 9,
    "c": 10,
    "cobol": 11,
    "css": 12,
    "coffeescript": 13,
    "coffee": 13,
    "d": 14,
    "dart": 15,
    "delphi": 16,
    "pascal": 16,
    "django": 17,
    "dockerfile": 18,
    "docker": 18,
    "erlang": 19,
    "fortran": 20,
    "foxpro": 21,
    "go": 22,
    "golang": 22,
    "groovy": 23,
    "html": 24,
    "handlebars": 25,
    "hbs": 25,
    "http": 26,
    "haskell": 27,
    "hs": 27,
    "json": 28,
    "java": 29,
    "javascript": 30,
    "js": 30,
    "julia": 31,
    "kotlin": 32,
    "kt": 32,
    "latex": 33,
    "tex": 33,
    "lisp": 34,
    "logo": 35,
    "lua": 36,
    "matlab": 37,
    "makefile": 38,
    "make": 38,
    "markdown": 39,
    "md": 39,
    "nginx": 40,
    "objectivec": 41,
    "objc": 41,
    "objective-c": 41,
    "openedgeabl": 42,
    "php": 43,
    "perl": 44,
    "pl": 44,
    "postscript": 45,
    "ps": 45,
    "powershell": 46,
    "ps1": 46,
    "prolog": 47,
    "protobuf": 48,
    "proto": 48,
    "python": 49,
    "py": 49,
    "r": 50,
    "rpg": 51,
    "ruby": 52,
    "rb": 52,
    "rust": 53,
    "rs": 53,
    "sas": 54,
    "scss": 55,
    "sass": 55,
    "sql": 56,
    "scala": 57,
    "scheme": 58,
    "scratch": 59,
    "shellscript": 60,
    "swift": 61,
    "thrift": 62,
    "typescript": 63,
    "ts": 63,
    "vbscript": 64,
    "vb": 65,
    "visualbasic": 65,
    "xml": 66,
    "yaml": 67,
    "yml": 67,
    "cmake": 68,
    "diff": 69,
    "patch": 69,
    "gherkin": 70,
    "cucumber": 70,
    "graphql": 71,
    "gql": 71,
    "glsl": 72,
    "properties": 73,
    "ini": 73,
    "solidity": 74,
    "sol": 74,
    "toml": 75,
}


def create_text_run(
    content: str,
    bold: bool = False,
    italic: bool = False,
    strikethrough: bool = False,
    underline: bool = False,
    inline_code: bool = False,
    link: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a text run element."""
    style: Dict[str, Any] = {
        "bold": bold,
        "italic": italic,
        "strikethrough": strikethrough,
        "underline": underline,
        "inline_code": inline_code,
    }

    if link:
        style["link"] = {"url": link}

    return {
        "text_run": {
            "content": content,
            "text_element_style": style,
        }
    }


def create_equation(content: str) -> Dict[str, Any]:
    """Create an equation (math formula) element."""
    return {
        "equation": {
            "content": content + "\n",
            "text_element_style": {
                "bold": False,
                "italic": False,
                "strikethrough": False,
                "underline": False,
                "inline_code": False,
            }
        }
    }


def create_text(elements: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create a text block."""
    return {
        "block_type": BlockType.TEXT,
        "text": {
            "elements": elements,
            "style": {},
        }
    }


def create_heading1(content: str) -> Dict[str, Any]:
    """Create a heading1 block."""
    return {
        "block_type": BlockType.HEADING1,
        "heading1": {
            "elements": [create_text_run(content)],
            "style": {},
        }
    }


def create_heading2(content: str) -> Dict[str, Any]:
    """Create a heading2 block."""
    return {
        "block_type": BlockType.HEADING2,
        "heading2": {
            "elements": [create_text_run(content)],
            "style": {},
        }
    }


def create_heading(level: int, elements: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create a heading block of specified level."""
    level = max(1, min(9, level))
    block_type = BlockType.HEADING1 + level - 1
    key = f"heading{level}"

    return {
        "block_type": block_type,
        key: {
            "elements": elements,
            "style": {},
        }
    }


def create_bullet(elements: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create a bullet list item block."""
    return {
        "block_type": BlockType.BULLET,
        "bullet": {
            "elements": elements,
            "style": {},
        }
    }


def create_ordered(elements: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create an ordered list item block."""
    return {
        "block_type": BlockType.ORDERED,
        "ordered": {
            "elements": elements,
            "style": {},
        }
    }


def create_quote(elements: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create a quote block."""
    return {
        "block_type": BlockType.QUOTE,
        "quote": {
            "elements": elements,
            "style": {},
        }
    }


def create_code(content: str, language: str = "") -> Dict[str, Any]:
    """Create a code block."""
    # Convert language name to Feishu code
    lang_code = LANGUAGE_CODES.get(language.lower(), 1)  # Default to PlainText
    return {
        "block_type": BlockType.CODE,
        "code": {
            "elements": [create_text_run(content)],
            "style": {
                "language": lang_code,
            }
        }
    }


def create_divider() -> Dict[str, Any]:
    """Create a divider (horizontal rule) block."""
    return {
        "block_type": BlockType.DIVIDER,
        "divider": {},
    }


def create_table(row_size: int, column_size: int, cells: List[List[str]]) -> Dict[str, Any]:
    """Create a table block structure."""
    return {
        "block_type": BlockType.TABLE,
        "table": {
            "property": {
                "row_size": row_size,
                "column_size": column_size,
            },
            "cells": cells,
        }
    }
