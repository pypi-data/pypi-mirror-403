"""Security module for PairCoder.

This module provides security controls for autonomous execution:
- Command allowlist management
- Pre-execution security review
- Secret detection
- Dependency vulnerability scanning
- Docker sandbox isolation
- Git checkpoint/rollback
- Containment mode for filesystem locking
"""

from .allowlist import (
    AllowlistManager,
    CommandDecision,
    CheckResult,
)
from .containment import (
    ContainmentManager,
    ContainmentViolationError,
)
from .network import (
    NetworkGuard,
    NetworkRestrictionError,
)
from .review import (
    ReviewResult,
    SecurityReviewHook,
    CodeChangeReviewer,
    AgentEnhancedReviewHook,
)
from .sandbox import (
    SandboxConfig,
    SandboxRunner,
    SandboxResult,
    FileChange,
    MountConfig,
)
from .checkpoint import (
    GitCheckpoint,
    CheckpointError,
    NotAGitRepoError,
    CheckpointNotFoundError,
    NoCheckpointsError,
    format_checkpoint_list,
    format_rollback_preview,
)
from .secrets import (
    SecretScanner,
    SecretMatch,
    SecretType,
    AllowlistConfig,
    format_scan_results,
)
from .dependencies import (
    DependencyScanner,
    Vulnerability,
    ScanReport,
    Severity,
    format_scan_report,
)

__all__ = [
    # Allowlist
    "AllowlistManager",
    "CommandDecision",
    "CheckResult",
    # Containment
    "ContainmentManager",
    "ContainmentViolationError",
    # Network
    "NetworkGuard",
    "NetworkRestrictionError",
    # Review
    "ReviewResult",
    "SecurityReviewHook",
    "CodeChangeReviewer",
    "AgentEnhancedReviewHook",
    # Sandbox
    "SandboxConfig",
    "SandboxRunner",
    "SandboxResult",
    "FileChange",
    "MountConfig",
    # Checkpoint
    "GitCheckpoint",
    "CheckpointError",
    "NotAGitRepoError",
    "CheckpointNotFoundError",
    "NoCheckpointsError",
    "format_checkpoint_list",
    "format_rollback_preview",
    # Secrets
    "SecretScanner",
    "SecretMatch",
    "SecretType",
    "AllowlistConfig",
    "format_scan_results",
    # Dependencies
    "DependencyScanner",
    "Vulnerability",
    "ScanReport",
    "Severity",
    "format_scan_report",
]
