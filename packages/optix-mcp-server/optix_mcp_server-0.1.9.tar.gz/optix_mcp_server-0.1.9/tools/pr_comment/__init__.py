"""PR Comment tool for posting audit findings to GitHub PRs.

This module provides the PRCommentTool class for posting audit findings
as formatted comments on GitHub Pull Requests.
"""

from tools.pr_comment.formatter import (
    format_comment,
    format_finding,
    format_severity_section,
    parse_issue_to_finding,
    truncate_description,
)
from tools.pr_comment.github import (
    FileLinkBuilder,
    GitHubCLIError,
    build_file_link,
    check_gh_auth,
    get_pr_info,
    get_repo_info,
    list_recent_prs,
    post_pr_comment,
)
from tools.pr_comment.models import (
    FormattedFinding,
    PRCommentError,
    PRCommentResponse,
    PRInfo,
    PRListResponse,
)
from tools.pr_comment.tool import PRCommentTool

__all__ = [
    "PRCommentTool",
    "PRCommentResponse",
    "PRCommentError",
    "PRListResponse",
    "PRInfo",
    "FormattedFinding",
    "format_comment",
    "format_finding",
    "format_severity_section",
    "parse_issue_to_finding",
    "truncate_description",
    "FileLinkBuilder",
    "GitHubCLIError",
    "build_file_link",
    "check_gh_auth",
    "get_pr_info",
    "get_repo_info",
    "list_recent_prs",
    "post_pr_comment",
]
