"""Unit tests for markdown escape utilities."""

import pytest

from tools.generate_report.generators.escape import (
    escape_markdown_content,
    escape_for_table_cell,
)


class TestEscapeMarkdownContent:
    """Tests for escape_markdown_content function."""

    def test_returns_empty_for_empty_string(self):
        assert escape_markdown_content("") == ""

    def test_returns_none_for_none(self):
        assert escape_markdown_content(None) is None

    def test_leaves_plain_text_unchanged(self):
        text = "This is plain text without any HTML"
        assert escape_markdown_content(text) == text

    def test_wraps_simple_html_tag_in_backticks(self):
        text = "Use <button> element"
        result = escape_markdown_content(text)
        assert result == "Use `<button>` element"

    def test_wraps_html_tag_with_attributes(self):
        text = 'Add <button aria-label="Close">X</button>'
        result = escape_markdown_content(text)
        assert result == 'Add `<button aria-label="Close">`X`</button>`'

    def test_wraps_self_closing_tag(self):
        text = "Use <input/> for form"
        result = escape_markdown_content(text)
        assert result == "Use `<input/>` for form"

    def test_wraps_multiple_html_tags(self):
        text = "Wrap <div> with <span> elements"
        result = escape_markdown_content(text)
        assert result == "Wrap `<div>` with `<span>` elements"

    def test_handles_typical_remediation_text(self):
        text = 'Add aria-label: <button aria-label="Close dialog">X</button>'
        result = escape_markdown_content(text)
        assert '`<button aria-label="Close dialog">`' in result

    def test_does_not_escape_angle_brackets_without_tag(self):
        text = "Use x < 5 and y > 3"
        result = escape_markdown_content(text)
        assert result == text

    def test_handles_nested_quotes_in_attributes(self):
        text = """Use <div class="container" data-test='value'>"""
        result = escape_markdown_content(text)
        assert "`<div class=\"container\" data-test='value'>`" in result


class TestEscapeForTableCell:
    """Tests for escape_for_table_cell function."""

    def test_returns_empty_for_empty_string(self):
        assert escape_for_table_cell("") == ""

    def test_returns_none_for_none(self):
        assert escape_for_table_cell(None) is None

    def test_leaves_plain_text_unchanged(self):
        text = "This is plain text"
        assert escape_for_table_cell(text) == text

    def test_escapes_pipe_character(self):
        text = "Choice A | Choice B"
        result = escape_for_table_cell(text)
        assert result == "Choice A \\| Choice B"

    def test_escapes_multiple_pipes(self):
        text = "A | B | C"
        result = escape_for_table_cell(text)
        assert result == "A \\| B \\| C"

    def test_handles_pipe_at_start(self):
        text = "| leading pipe"
        result = escape_for_table_cell(text)
        assert result == "\\| leading pipe"

    def test_handles_pipe_at_end(self):
        text = "trailing pipe |"
        result = escape_for_table_cell(text)
        assert result == "trailing pipe \\|"
