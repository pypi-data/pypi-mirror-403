"""MCP tool implementation for pr_comment.

Posts audit findings as GitHub PR comments with a concise format.
"""

from typing import Optional

from logging_utils import get_tool_logger
from tools.generate_report.models import AuditLens
from tools.pr_comment.formatter import (
    format_comment,
    parse_issue_to_finding,
)
from tools.pr_comment.github import (
    FileLinkBuilder,
    GitHubCLIError,
    check_gh_auth,
    get_pr_info,
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
from tools.workflow.state import WorkflowStateManager


class PRCommentTool:
    """MCP tool for posting audit findings as PR comments."""

    def __init__(self) -> None:
        """Initialize the PR comment tool."""
        self._state_manager = WorkflowStateManager()
        self._logger = None

    def _get_logger(self):
        if self._logger is None:
            self._logger = get_tool_logger("pr_comment")
        return self._logger

    @property
    def name(self) -> str:
        """Unique identifier for the tool."""
        return "pr_comment"

    @property
    def description(self) -> str:
        """Human-readable description."""
        return (
            "Post audit findings as a GitHub PR comment. "
            "If no PR number provided, lists recent PRs for selection."
        )

    def execute(
        self,
        pr_number: Optional[int] = None,
        continuation_id: Optional[str] = None,
        include_file_links: bool = False,
        repo: Optional[str] = None,
    ) -> PRCommentResponse | PRListResponse | PRCommentError:
        """Execute the PR comment tool.

        Args:
            pr_number: GitHub PR number to comment on. If omitted, returns
                list of recent PRs for selection.
            continuation_id: Optional UUID of specific workflow to use.
                If omitted, uses most recent workflow from WorkflowStateManager.
            include_file_links: Add GitHub permalinks to file references
            repo: Repository (owner/repo), auto-detected if omitted

        Returns:
            PRListResponse if no pr_number (for selection),
            PRCommentResponse on success,
            PRCommentError on failure
        """
        logger = self._get_logger()

        try:
            if not check_gh_auth():
                logger.warn("GitHub CLI not authenticated")
                return PRCommentError(
                    error="GitHub CLI is not authenticated. Run 'gh auth login' first.",
                    error_type="AuthenticationError",
                )

            findings, lens = self._get_findings(continuation_id)
            logger.debug(f"Retrieved {len(findings)} findings from {lens.value} audit")

            if not findings:
                logger.info("No findings to post")
                return PRCommentError(
                    error="No findings found in the audit workflow.",
                    error_type="NoFindingsError",
                )

            if pr_number is None:
                return self._list_prs_for_selection(findings, repo)

            return self._post_comment(
                pr_number=pr_number,
                findings=findings,
                lens=lens,
                include_file_links=include_file_links,
                repo=repo,
            )

        except GitHubCLIError as e:
            logger.warn(f"GitHub CLI error: {e}")
            return PRCommentError(
                error=str(e),
                error_type="GitHubCLIError",
            )

        except ValueError as e:
            error_msg = str(e)
            logger.warn(f"Value error: {error_msg}")
            if "No completed audit" in error_msg or "No audit workflow" in error_msg:
                return PRCommentError(
                    error=error_msg,
                    error_type="NoAuditFound",
                )
            return PRCommentError(
                error=error_msg,
                error_type="GeneralError",
            )

        except Exception as e:
            logger.warn(f"Unexpected error: {e}")
            return PRCommentError(
                error=f"Unexpected error: {e}",
                error_type="GeneralError",
            )

    def _list_prs_for_selection(
        self,
        findings: list[dict],
        repo: Optional[str] = None,
    ) -> PRListResponse | PRCommentError:
        """List recent PRs for user selection.

        Args:
            findings: List of findings from audit
            repo: Optional repository

        Returns:
            PRListResponse with available PRs
        """
        logger = self._get_logger()
        logger.info("No PR number provided, listing recent PRs for selection")

        try:
            raw_prs = list_recent_prs(limit=5, repo=repo)

            if not raw_prs:
                return PRCommentError(
                    error="No open PRs found in this repository.",
                    error_type="NoPRsFound",
                )

            prs = [PRInfo.from_gh_response(pr) for pr in raw_prs]
            logger.info(f"Found {len(prs)} open PRs")

            return PRListResponse(
                success=True,
                prs=prs,
                findings_count=len(findings),
                message=(
                    f"Found {len(findings)} audit findings. "
                    f"Select a PR from the list below to post the comment:\n\n"
                    + "\n".join(
                        f"  [{pr.number}] {pr.title} ({pr.branch}) by @{pr.author}"
                        for pr in prs
                    )
                    + "\n\nCall pr_comment again with pr_number to post."
                ),
            )

        except GitHubCLIError as e:
            logger.warn(f"Failed to list PRs: {e}")
            return PRCommentError(
                error=f"Failed to list PRs: {e}",
                error_type="GitHubCLIError",
            )

    def _post_comment(
        self,
        pr_number: int,
        findings: list[dict],
        lens: AuditLens,
        include_file_links: bool,
        repo: Optional[str],
    ) -> PRCommentResponse | PRCommentError:
        """Post comment to the specified PR.

        Args:
            pr_number: PR number to comment on
            findings: List of findings from audit
            lens: The audit lens type
            include_file_links: Whether to include file links
            repo: Optional repository

        Returns:
            PRCommentResponse on success, PRCommentError on failure
        """
        logger = self._get_logger()
        logger.info(f"Starting PR comment for PR #{pr_number}")

        file_link_builder = None
        if include_file_links:
            try:
                file_link_builder = FileLinkBuilder.from_pr(pr_number, repo)
                logger.debug(f"File link builder created for {file_link_builder.repo}")
            except GitHubCLIError as e:
                logger.warn(f"Could not create file links: {e}")

        formatted = self._format_findings(findings, file_link_builder)
        logger.debug(f"Formatted {len(formatted)} findings")

        comment_body = format_comment(formatted, lens.value)

        get_pr_info(pr_number, repo)
        logger.info(f"Posting comment to PR #{pr_number}")

        comment_url = post_pr_comment(pr_number, comment_body, repo)

        logger.info(f"PR comment posted successfully: {comment_url}")

        return PRCommentResponse(
            success=True,
            pr_number=pr_number,
            comment_url=comment_url,
            findings_count=len(formatted),
            message=f"Posted {len(formatted)} findings to PR #{pr_number}",
        )

    def _get_findings(
        self, continuation_id: Optional[str]
    ) -> tuple[list[dict], AuditLens]:
        """Retrieve findings from WorkflowStateManager.

        Args:
            continuation_id: Optional specific workflow ID to use

        Returns:
            Tuple of (issues list, AuditLens)

        Raises:
            ValueError: If no audit found or invalid tool name
        """
        if continuation_id:
            state = self._state_manager.get(continuation_id)
            if state is None:
                raise ValueError(
                    f"No audit workflow found with continuation_id: {continuation_id}. "
                    "Please ensure you completed an audit workflow first."
                )
        else:
            workflows = self._state_manager._workflows
            if not workflows:
                raise ValueError(
                    "No completed audit found. Please run an audit "
                    "(security_audit, a11y_audit, principal_audit, or devops_audit) "
                    "before posting a PR comment."
                )
            state = max(
                workflows.values(),
                key=lambda w: (w.updated_at, -w.created_at.timestamp()),
            )

        tool_name = state.tool_name
        lens = AuditLens.from_tool_name(tool_name)

        issues = []
        if state.consolidated:
            issues = state.consolidated.issues_found

        return issues, lens

    def _format_findings(
        self,
        issues: list[dict],
        file_link_builder: Optional[FileLinkBuilder],
    ) -> list[FormattedFinding]:
        """Format issues into FormattedFinding objects.

        Args:
            issues: List of issue dictionaries from workflow
            file_link_builder: Optional builder for file links

        Returns:
            List of FormattedFinding objects
        """
        formatted = []
        for issue in issues:
            finding = parse_issue_to_finding(issue, file_link_builder)
            formatted.append(finding)
        return formatted
