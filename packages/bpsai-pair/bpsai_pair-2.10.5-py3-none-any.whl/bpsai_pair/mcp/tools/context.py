"""
MCP Context Tools

Implements context tools:
- paircoder_context_read: Read project context files
"""

from pathlib import Path
from typing import Any


def find_paircoder_dir() -> Path:
    """Find the .paircoder directory."""
    from ...core.ops import find_paircoder_dir as _find_paircoder_dir, ProjectRootNotFoundError
    try:
        paircoder_dir = _find_paircoder_dir()
    except ProjectRootNotFoundError:
        raise FileNotFoundError("No .paircoder directory found")
    if not paircoder_dir.exists():
        raise FileNotFoundError("No .paircoder directory found")
    return paircoder_dir


def register_context_tools(server: Any) -> None:
    """Register context tools with the MCP server."""

    @server.tool()
    async def paircoder_context_read(
        file: str = "state",
    ) -> dict:
        """
        Read project context files.

        Args:
            file: Context file to read (state, project, workflow, config, capabilities)

        Returns:
            File content and metadata
        """
        try:
            paircoder_dir = find_paircoder_dir()

            # Map file names to paths
            file_map = {
                "state": paircoder_dir / "context" / "state.md",
                "project": paircoder_dir / "context" / "project.md",
                "workflow": paircoder_dir / "context" / "workflow.md",
                "config": paircoder_dir / "config.yaml",
                "capabilities": paircoder_dir / "capabilities.yaml",
            }

            if file not in file_map:
                return {
                    "error": {
                        "code": "INVALID_FILE",
                        "message": f"Unknown file: {file}. Valid options: {', '.join(file_map.keys())}",
                    }
                }

            file_path = file_map[file]

            if not file_path.exists():
                return {
                    "error": {
                        "code": "FILE_NOT_FOUND",
                        "message": f"Context file not found: {file_path}",
                    }
                }

            content = file_path.read_text(encoding="utf-8")

            return {
                "file": file,
                "path": str(file_path),
                "content": content,
                "size": len(content),
            }
        except FileNotFoundError:
            return {"error": {"code": "NOT_FOUND", "message": "No .paircoder directory found"}}
        except Exception as e:
            return {"error": {"code": "ERROR", "message": str(e)}}
