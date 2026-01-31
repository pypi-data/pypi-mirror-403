from __future__ import annotations
import os
import sys
import stat
import shutil
import platform
from contextlib import ExitStack
from pathlib import Path
try:
    from importlib.resources import files as res_files, as_file
except ImportError:
    from importlib_resources import files as res_files, as_file  # py<=3.8 fallback

APP_NAME = "bpsai-pair-init"

# Enable debug mode via environment variable
DEBUG = os.environ.get("BPSAI_INIT_DEBUG", "").lower() in ("1", "true", "yes")

# Files that need special handling during bundled copy.
# Note: config.yaml was removed from the template as of v2.10.0.
# Config is now generated dynamically by presets/wizard/Config.save()
# to ensure it always matches the current schema version.
SKIP_FILES: set[str] = set()


def _debug(msg: str) -> None:
    """Print debug message if DEBUG mode is enabled."""
    if DEBUG:
        print(f"[{APP_NAME}] DEBUG: {msg}")


def copytree_non_destructive(src: Path, dst: Path) -> int:
    """Copy files/dirs only if missing; never overwrite existing files.

    Returns:
        Number of files copied.
    """
    files_copied = 0
    dirs_created = 0

    for root, dirs, files in os.walk(src):
        rel = Path(root).relative_to(src)
        out_dir = dst / rel
        if not out_dir.exists():
            out_dir.mkdir(parents=True, exist_ok=True)
            dirs_created += 1

        for name in files:
            # Skip files that contain unrendered cookiecutter templates
            if name in SKIP_FILES:
                continue
            s = Path(root) / name
            d = out_dir / name
            if not d.exists():
                d.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(s, d)
                files_copied += 1

    _debug(f"Copied {files_copied} files, created {dirs_created} directories")

    # make scripts executable (skip on Windows where chmod is no-op)
    if platform.system() != "Windows":
        scripts_dir = dst / "scripts"
        if scripts_dir.exists():
            for p in scripts_dir.glob("*.sh"):
                mode = p.stat().st_mode
                p.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    return files_copied

def _log_debug_info_for_extraction(template_root: Path) -> None:
    """Log debug info about template extraction."""
    _debug(f"template_root after as_file(): {template_root}")
    _debug(f"template_root type: {type(template_root).__name__}")
    _debug(f"template_root exists: {template_root.exists()}")
    if template_root.exists():
        contents = list(template_root.iterdir())
        _debug(f"template_root contents: {len(contents)} items")
        for item in contents[:5]:  # Show first 5
            _debug(f"  - {item.name}")


def _find_template_traversable():
    """Find the packaged template directory.

    Returns:
        Traversable pointing to template, or None on error.
    """
    pkg_root = res_files("bpsai_pair") / "data" / "cookiecutter-paircoder"
    _debug(f"pkg_root type: {type(pkg_root).__name__}")
    _debug(f"pkg_root: {pkg_root}")

    try:
        candidates = [p for p in pkg_root.iterdir() if p.is_dir()]
    except Exception as e:
        print(f"[{APP_NAME}] ERROR: Failed to iterate pkg_root: {e}", file=sys.stderr)
        if DEBUG:
            import traceback
            traceback.print_exc()
        return None

    _debug(f"Found {len(candidates)} candidate directories")
    for i, c in enumerate(candidates):
        _debug(f"  [{i}] {c} (type: {type(c).__name__})")

    if not candidates:
        print(f"[{APP_NAME}] ERROR: packaged template not found", file=sys.stderr)
        return None

    return candidates[0]  # '{{cookiecutter.project_slug}}'


def _warn_no_files_copied() -> None:
    """Print warning when no files were copied."""
    print(f"[{APP_NAME}] WARNING: No files were copied. This may indicate:", file=sys.stderr)
    print(f"[{APP_NAME}]   - All scaffolding files already exist (non-destructive)", file=sys.stderr)
    print(f"[{APP_NAME}]   - Template extraction failed silently", file=sys.stderr)
    print(f"[{APP_NAME}]   - Set BPSAI_INIT_DEBUG=1 for debug output", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]

    _debug(f"Platform: {platform.system()} {platform.release()}")
    _debug(f"Python: {sys.version}")

    template_traversable = _find_template_traversable()
    if template_traversable is None:
        return 1

    dst = Path(".").resolve()
    _debug(f"template_traversable: {template_traversable}")
    _debug(f"destination: {dst}")

    # Use as_file() to properly extract from wheel if needed.
    try:
        with ExitStack() as stack:
            template_root = stack.enter_context(as_file(template_traversable))
            _log_debug_info_for_extraction(template_root)
            files_copied = copytree_non_destructive(template_root, dst)
    except Exception as e:
        print(f"[{APP_NAME}] ERROR: Failed during file extraction/copy: {e}", file=sys.stderr)
        if DEBUG:
            import traceback
            traceback.print_exc()
        return 1

    if files_copied == 0:
        _warn_no_files_copied()

    print(f"[{APP_NAME}] Initialized repo with bundled scaffolding (non-destructive). Review diffs and commit.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
