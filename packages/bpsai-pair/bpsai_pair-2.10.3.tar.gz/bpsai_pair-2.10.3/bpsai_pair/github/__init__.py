"""GitHub integration for PairCoder."""
from .client import GitHubClient, GitHubService
from .pr import PRManager, PRInfo

__all__ = ["GitHubClient", "GitHubService", "PRManager", "PRInfo"]
