"""
GitHub client for PairCoder.

Provides GitHub API integration using PyGithub when available,
with fallback to direct API calls for basic operations.
"""
from __future__ import annotations

import logging
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class RepoInfo:
    """GitHub repository information."""

    owner: str
    name: str
    full_name: str
    default_branch: str = "main"
    url: str = ""

    @classmethod
    def from_remote_url(cls, url: str) -> Optional["RepoInfo"]:
        """Parse repository info from git remote URL.

        Args:
            url: Git remote URL (SSH or HTTPS)

        Returns:
            RepoInfo if parseable, None otherwise
        """
        # Handle SSH format: git@github.com:owner/repo.git
        if url.startswith("git@github.com:"):
            path = url.replace("git@github.com:", "").replace(".git", "")
            parts = path.split("/")
            if len(parts) == 2:
                return cls(
                    owner=parts[0],
                    name=parts[1],
                    full_name=f"{parts[0]}/{parts[1]}",
                    url=f"https://github.com/{parts[0]}/{parts[1]}",
                )

        # Handle HTTPS format: https://github.com/owner/repo.git
        if "github.com" in url:
            # Remove .git suffix and https:// prefix
            path = url.replace("https://github.com/", "").replace(".git", "")
            parts = path.split("/")
            if len(parts) >= 2:
                return cls(
                    owner=parts[0],
                    name=parts[1],
                    full_name=f"{parts[0]}/{parts[1]}",
                    url=f"https://github.com/{parts[0]}/{parts[1]}",
                )

        return None


class GitHubClient:
    """Low-level GitHub API client.

    Uses gh CLI for operations when available, falls back to PyGithub.
    """

    def __init__(self, token: Optional[str] = None):
        """Initialize GitHub client.

        Args:
            token: GitHub personal access token (optional, uses gh auth if not provided)
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        self._gh_cli_available: Optional[bool] = None
        self._github = None

    @property
    def gh_cli_available(self) -> bool:
        """Check if gh CLI is available and authenticated."""
        if self._gh_cli_available is None:
            try:
                result = subprocess.run(
                    ["gh", "auth", "status"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                self._gh_cli_available = result.returncode == 0
            except (FileNotFoundError, subprocess.TimeoutExpired):
                self._gh_cli_available = False
        return self._gh_cli_available

    def _run_gh(self, *args: str, **kwargs) -> subprocess.CompletedProcess:
        """Run a gh CLI command.

        Args:
            *args: Command arguments

        Returns:
            Completed process

        Raises:
            RuntimeError: If gh CLI is not available
        """
        if not self.gh_cli_available:
            raise RuntimeError("gh CLI is not available or not authenticated")

        return subprocess.run(
            ["gh", *args],
            capture_output=True,
            text=True,
            timeout=kwargs.get("timeout", 30),
        )

    def get_repo_info(self, cwd: Optional[Path] = None) -> Optional[RepoInfo]:
        """Get repository information for current directory.

        Args:
            cwd: Working directory (uses current if not provided)

        Returns:
            RepoInfo if in a git repo with GitHub remote
        """
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=5,
            )
            if result.returncode == 0:
                return RepoInfo.from_remote_url(result.stdout.strip())
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        return None

    def get_current_branch(self, cwd: Optional[Path] = None) -> Optional[str]:
        """Get current git branch name.

        Args:
            cwd: Working directory

        Returns:
            Branch name or None
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        return None

    def get_default_branch(self, cwd: Optional[Path] = None) -> str:
        """Get the default branch name.

        Args:
            cwd: Working directory

        Returns:
            Default branch name (main or master)
        """
        # Try to get from remote
        try:
            result = subprocess.run(
                ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=5,
            )
            if result.returncode == 0:
                # refs/remotes/origin/main -> main
                return result.stdout.strip().split("/")[-1]
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # Default to main
        return "main"

    def create_pr(
        self,
        title: str,
        body: str,
        base: Optional[str] = None,
        head: Optional[str] = None,
        draft: bool = False,
        cwd: Optional[Path] = None,
    ) -> Optional[Dict[str, Any]]:
        """Create a pull request.

        Args:
            title: PR title
            body: PR body/description
            base: Base branch (default: repo default)
            head: Head branch (default: current branch)
            draft: Create as draft PR
            cwd: Working directory

        Returns:
            PR info dict with 'number', 'url', 'html_url' keys
        """
        if not self.gh_cli_available:
            logger.warning("gh CLI not available, cannot create PR")
            return None

        args = ["pr", "create", "--title", title, "--body", body]

        if base:
            args.extend(["--base", base])
        if head:
            args.extend(["--head", head])
        if draft:
            args.append("--draft")

        try:
            result = subprocess.run(
                ["gh", *args],
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=30,
            )

            if result.returncode == 0:
                # gh pr create outputs the PR URL
                pr_url = result.stdout.strip()
                # Parse PR number from URL
                pr_number = int(pr_url.split("/")[-1])
                return {
                    "number": pr_number,
                    "url": pr_url,
                    "html_url": pr_url,
                }
            else:
                logger.error(f"Failed to create PR: {result.stderr}")
                return None
        except (subprocess.TimeoutExpired, ValueError) as e:
            logger.error(f"Error creating PR: {e}")
            return None

    def get_pr_status(
        self,
        pr_number: Optional[int] = None,
        cwd: Optional[Path] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get PR status for current branch or specific PR.

        Args:
            pr_number: PR number (uses current branch if not provided)
            cwd: Working directory

        Returns:
            PR status dict with 'state', 'mergeable', 'reviews' etc.
        """
        if not self.gh_cli_available:
            return None

        args = ["pr", "view"]
        if pr_number:
            args.append(str(pr_number))
        args.extend(["--json", "number,state,title,url,mergeable,reviewDecision,statusCheckRollup"])

        try:
            import json
            result = subprocess.run(
                ["gh", *args],
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=30,
            )

            if result.returncode == 0:
                return json.loads(result.stdout)
            return None
        except (subprocess.TimeoutExpired, json.JSONDecodeError):
            return None

    def list_prs(
        self,
        state: str = "open",
        author: Optional[str] = None,
        base: Optional[str] = None,
        limit: int = 30,
        cwd: Optional[Path] = None,
    ) -> List[Dict[str, Any]]:
        """List pull requests.

        Args:
            state: PR state (open, closed, merged, all)
            author: Filter by author
            base: Filter by base branch
            limit: Maximum number of PRs to return
            cwd: Working directory

        Returns:
            List of PR info dicts
        """
        if not self.gh_cli_available:
            return []

        args = ["pr", "list", "--state", state, "--limit", str(limit)]
        args.extend(["--json", "number,title,state,url,author,createdAt,updatedAt"])

        if author:
            args.extend(["--author", author])
        if base:
            args.extend(["--base", base])

        try:
            import json
            result = subprocess.run(
                ["gh", *args],
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=30,
            )

            if result.returncode == 0:
                return json.loads(result.stdout)
            return []
        except (subprocess.TimeoutExpired, json.JSONDecodeError):
            return []

    def merge_pr(
        self,
        pr_number: int,
        method: str = "squash",
        delete_branch: bool = True,
        cwd: Optional[Path] = None,
    ) -> bool:
        """Merge a pull request.

        Args:
            pr_number: PR number to merge
            method: Merge method (merge, squash, rebase)
            delete_branch: Delete branch after merge
            cwd: Working directory

        Returns:
            True if merged successfully
        """
        if not self.gh_cli_available:
            return False

        args = ["pr", "merge", str(pr_number), f"--{method}"]
        if delete_branch:
            args.append("--delete-branch")

        try:
            result = subprocess.run(
                ["gh", *args],
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=60,
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            return False


class GitHubService:
    """High-level GitHub service for PairCoder integration."""

    def __init__(
        self,
        client: Optional[GitHubClient] = None,
        project_root: Optional[Path] = None,
    ):
        """Initialize GitHub service.

        Args:
            client: GitHub client (creates default if not provided)
            project_root: Project root directory
        """
        self.client = client or GitHubClient()
        self.project_root = project_root or Path.cwd()
        self._repo_info: Optional[RepoInfo] = None

    @property
    def repo_info(self) -> Optional[RepoInfo]:
        """Get cached repository info."""
        if self._repo_info is None:
            self._repo_info = self.client.get_repo_info(self.project_root)
        return self._repo_info

    def is_github_repo(self) -> bool:
        """Check if current directory is a GitHub repository."""
        return self.repo_info is not None

    def get_current_branch(self) -> Optional[str]:
        """Get current branch name."""
        return self.client.get_current_branch(self.project_root)

    def healthcheck(self) -> Dict[str, Any]:
        """Check GitHub integration health.

        Returns:
            Dict with 'ok', 'gh_cli', 'repo', 'authenticated' keys
        """
        return {
            "ok": self.client.gh_cli_available and self.is_github_repo(),
            "gh_cli": self.client.gh_cli_available,
            "repo": self.repo_info.full_name if self.repo_info else None,
            "authenticated": self.client.gh_cli_available,
        }
