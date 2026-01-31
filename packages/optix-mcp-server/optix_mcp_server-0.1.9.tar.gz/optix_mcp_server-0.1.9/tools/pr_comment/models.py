"""Data models for the pr_comment tool.

Provides type-safe entities for PR comment generation including:
- PRCommentResponse for successful comment posting
- PRCommentError for failure responses
- FormattedFinding for individual finding representation
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class FormattedFinding:
    """Represents a single formatted finding for PR comment display."""

    file_path: str
    line_number: int | None
    description: str
    severity: str
    file_link: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "description": self.description,
            "severity": self.severity,
        }
        if self.file_link:
            result["file_link"] = self.file_link
        return result


@dataclass
class PRCommentResponse:
    """Response from successful PR comment posting."""

    success: bool
    pr_number: int
    comment_url: str
    findings_count: int
    message: str

    def to_dict(self) -> dict[str, Any]:
        """Convert response to dictionary for MCP JSON response."""
        return {
            "success": self.success,
            "pr_number": self.pr_number,
            "comment_url": self.comment_url,
            "findings_count": self.findings_count,
            "message": self.message,
        }


@dataclass
class PRCommentError:
    """Response from failed PR comment posting."""

    success: bool = False
    error: str = ""
    error_type: str = "GeneralError"

    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary for MCP JSON response."""
        return {
            "success": self.success,
            "error": self.error,
            "error_type": self.error_type,
        }


@dataclass
class PRInfo:
    """Info about a single PR for selection."""

    number: int
    title: str
    branch: str
    author: str
    url: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "number": self.number,
            "title": self.title,
            "branch": self.branch,
            "author": self.author,
            "url": self.url,
        }

    @classmethod
    def from_gh_response(cls, data: dict[str, Any]) -> "PRInfo":
        """Create from gh pr list response."""
        author = data.get("author", {})
        author_login = author.get("login", "") if isinstance(author, dict) else str(author)
        return cls(
            number=data.get("number", 0),
            title=data.get("title", ""),
            branch=data.get("headRefName", ""),
            author=author_login,
            url=data.get("url", ""),
        )


@dataclass
class PRListResponse:
    """Response with list of PRs for selection."""

    success: bool
    prs: list[PRInfo]
    findings_count: int
    message: str

    def to_dict(self) -> dict[str, Any]:
        """Convert response to dictionary for MCP JSON response."""
        return {
            "success": self.success,
            "prs": [pr.to_dict() for pr in self.prs],
            "findings_count": self.findings_count,
            "message": self.message,
            "action_required": "select_pr",
        }
