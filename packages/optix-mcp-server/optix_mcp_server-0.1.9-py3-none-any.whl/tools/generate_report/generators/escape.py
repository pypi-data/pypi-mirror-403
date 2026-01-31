"""Markdown escape utilities for report generation.

Handles safe content formatting to prevent HTML injection and
table rendering issues in markdown reports.
"""

import re


def escape_markdown_content(text: str) -> str:
    """Escape content for safe markdown rendering.

    If text contains HTML tags, wrap them in inline code backticks.

    Args:
        text: Raw text that may contain HTML

    Returns:
        Text with HTML tags wrapped in backticks for code display
    """
    if not text:
        return text

    html_pattern = r'</?[a-zA-Z][^>]*/?>'

    if re.search(html_pattern, text):
        text = re.sub(html_pattern, lambda m: f'`{m.group(0)}`', text)

    return text


def escape_for_table_cell(text: str) -> str:
    """Escape content for use in markdown table cells.

    Escapes pipe characters that would break table structure.

    Args:
        text: Raw text for table cell

    Returns:
        Text safe for markdown table cells
    """
    if not text:
        return text

    text = text.replace('|', '\\|')

    return text
