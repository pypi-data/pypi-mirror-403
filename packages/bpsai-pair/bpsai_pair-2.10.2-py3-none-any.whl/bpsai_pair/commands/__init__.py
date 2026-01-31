"""CLI command modules.

This package contains CLI command implementations extracted from the
monolithic cli.py file for better organization and maintainability.

Sprint 22 extractions:
- preset: Preset management commands
- config: Configuration commands
- orchestrate: Multi-agent orchestration commands
- metrics: Token tracking and cost estimation
- timer: Time tracking integration
- benchmark: AI agent benchmarking framework
- cache: Context caching commands
- mcp: MCP server commands
- flow: Flow management commands
- security: Security scanning commands
- core: Core commands (init, feature, pack, etc.)
- session: Session and compaction management
"""

from .preset import app as preset_app
from .config import app as config_app
from .orchestrate import app as orchestrate_app
from .metrics import app as metrics_app
from .timer import app as timer_app
from .benchmark import app as benchmark_app
from .cache import app as cache_app
from .mcp import app as mcp_app
from .security import app as security_app
from .security import scan_secrets, scan_deps  # For shortcut commands
from .core import register_core_commands
from .session import session_app, compaction_app, containment_app, contained_auto, claude666
from .upgrade import upgrade_app
from .budget import app as budget_app
from .audit import app as audit_app
from .state import app as state_app
from .enforce import app as enforce_app
from .arch import app as arch_app
from .license import app as license_app
from .wizard import wizard_app

__all__ = [
    "preset_app",
    "config_app",
    "orchestrate_app",
    "metrics_app",
    "timer_app",
    "benchmark_app",
    "cache_app",
    "mcp_app",
    "security_app",
    "scan_secrets",
    "scan_deps",
    "register_core_commands",
    "session_app",
    "compaction_app",
    "containment_app",
    "contained_auto",
    "claude666",
    "upgrade_app",
    "budget_app",
    "audit_app",
    "state_app",
    "enforce_app",
    "arch_app",
    "license_app",
    "wizard_app",
]
