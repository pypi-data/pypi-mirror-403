"""GitHub CLI wrapper for PR comment operations.

Provides functions to interact with GitHub via the gh CLI tool.
"""

import json
import subprocess
from typing import Any


class GitHubCLIError(Exception):
    """Exception raised when gh CLI command fails."""

    def __init__(self, message: str, returncode: int = 1):
        super().__init__(message)
        self.returncode = returncode


def run_gh_command(args: list[str], timeout: int = 30) -> str:
    """Run a gh CLI command and return output.

    Args:
        args: Command arguments (excluding 'gh')
        timeout: Command timeout in seconds

    Returns:
        Command stdout

    Raises:
        GitHubCLIError: If command fails or gh is not available
    """
    try:
        result = subprocess.run(
            ["gh"] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip() or "Unknown error"
            raise GitHubCLIError(f"gh command failed: {error_msg}", result.returncode)
        return result.stdout.strip()
    except FileNotFoundError:
        raise GitHubCLIError(
            "GitHub CLI (gh) not found. Please install: https://cli.github.com/"
        )
    except subprocess.TimeoutExpired:
        raise GitHubCLIError(f"gh command timed out after {timeout} seconds")


def get_pr_info(pr_number: int, repo: str | None = None) -> dict[str, Any]:
    """Get PR details using gh pr view.

    Args:
        pr_number: PR number to look up
        repo: Optional repository (owner/repo format)

    Returns:
        Dictionary with PR info (number, url, headRefName, baseRefName)

    Raises:
        GitHubCLIError: If command fails
    """
    args = ["pr", "view", str(pr_number), "--json", "number,url,headRefName,baseRefName"]
    if repo:
        args.extend(["--repo", repo])

    output = run_gh_command(args)
    return json.loads(output)


def get_repo_info(repo: str | None = None) -> dict[str, Any]:
    """Get repository information.

    Args:
        repo: Optional repository (owner/repo format)

    Returns:
        Dictionary with repo info (nameWithOwner, defaultBranchRef)

    Raises:
        GitHubCLIError: If command fails
    """
    args = ["repo", "view", "--json", "nameWithOwner,defaultBranchRef"]
    if repo:
        args.extend(["--repo", repo])

    output = run_gh_command(args)
    return json.loads(output)


def post_pr_comment(pr_number: int, body: str, repo: str | None = None) -> str:
    """Post a comment on a PR using gh pr comment.

    Args:
        pr_number: PR number to comment on
        body: Comment body (markdown)
        repo: Optional repository (owner/repo format)

    Returns:
        URL of the created comment

    Raises:
        GitHubCLIError: If command fails
    """
    args = ["pr", "comment", str(pr_number), "--body", body]
    if repo:
        args.extend(["--repo", repo])

    run_gh_command(args, timeout=60)

    pr_info = get_pr_info(pr_number, repo)
    pr_url = pr_info.get("url", "")

    return f"{pr_url}#issuecomment"


def build_file_link(repo: str, branch: str, file_path: str, line: int | None = None) -> str:
    """Create a GitHub permalink to a file.

    Args:
        repo: Repository in owner/repo format
        branch: Branch name or commit SHA
        file_path: Path to file within repo
        line: Optional line number

    Returns:
        GitHub permalink URL
    """
    base_url = f"https://github.com/{repo}/blob/{branch}/{file_path}"
    if line:
        return f"{base_url}#L{line}"
    return base_url


def check_gh_auth() -> bool:
    """Check if gh CLI is authenticated.

    Returns:
        True if authenticated, False otherwise
    """
    try:
        run_gh_command(["auth", "status"])
        return True
    except GitHubCLIError:
        return False


def list_recent_prs(limit: int = 5, repo: str | None = None) -> list[dict[str, Any]]:
    """List recent open PRs.

    Args:
        limit: Max number of PRs to return (default 5)
        repo: Optional repository (owner/repo format)

    Returns:
        List of PR info dicts with number, title, headRefName, author, url

    Raises:
        GitHubCLIError: If command fails
    """
    args = [
        "pr", "list",
        "--state", "open",
        "--limit", str(limit),
        "--json", "number,title,headRefName,author,url"
    ]
    if repo:
        args.extend(["--repo", repo])

    output = run_gh_command(args)
    return json.loads(output)


class FileLinkBuilder:
    """Builder for GitHub file permalinks with cached repo/branch info."""

    def __init__(self, repo: str, branch: str):
        """Initialize with repo and branch.

        Args:
            repo: Repository in owner/repo format
            branch: Branch name
        """
        self.repo = repo
        self.branch = branch

    def __call__(self, file_path: str, line: int | None = None) -> str:
        """Build file link.

        Args:
            file_path: Path to file
            line: Optional line number

        Returns:
            GitHub permalink URL
        """
        return build_file_link(self.repo, self.branch, file_path, line)

    @classmethod
    def from_pr(cls, pr_number: int, repo: str | None = None) -> "FileLinkBuilder":
        """Create builder from PR info.

        Args:
            pr_number: PR number
            repo: Optional repository

        Returns:
            FileLinkBuilder instance
        """
        pr_info = get_pr_info(pr_number, repo)
        branch = pr_info.get("headRefName", "main")

        if repo:
            repo_name = repo
        else:
            repo_info = get_repo_info()
            repo_name = repo_info.get("nameWithOwner", "")

        return cls(repo_name, branch)
