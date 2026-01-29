"""bpsai_pair package"""
try:
    from importlib.metadata import version, PackageNotFoundError
    __version__ = version("bpsai-pair")
except PackageNotFoundError:
    __version__ = "dev"

# Core modules
from . import cli
from .core import config  # Moved to core/ in T24.2
from .core import utils  # Merged utils/pyutils/jsonio to core/ in T24.7

# Feature modules (public API)
from . import planning
from . import tasks
from . import trello
from . import github
from . import metrics
from . import orchestration
from . import mcp
from . import context
from .core import presets  # Moved to core/ in T24.6

__all__ = [
    "__version__",
    # Core
    "cli",
    "config",
    "utils",
    # Features
    "planning",
    "tasks",
    "trello",
    "github",
    "metrics",
    "orchestration",
    "mcp",
    "context",
    "presets",
]
