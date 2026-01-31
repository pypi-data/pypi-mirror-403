"""
Skill Installer - Install skills from URLs or local paths.

Supports:
- Local paths: ~/skills/my-skill, ./path/to/skill
- GitHub URLs: https://github.com/user/repo/tree/main/.claude/skills/skill
"""

import shutil
import tempfile
import logging
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import yaml

from .validator import SkillValidator

logger = logging.getLogger(__name__)


class SkillSource(Enum):
    """Type of skill source."""

    PATH = "path"
    URL = "url"
    REGISTRY = "registry"  # Future: @org/skill-name


class SkillInstallerError(Exception):
    """Error during skill installation."""

    pass


def find_project_root() -> Path:
    """Find project root by looking for .paircoder directory."""
    from ..core.ops import find_project_root as _find_project_root

    return _find_project_root()


def parse_source(source: str) -> tuple:
    """Parse source and determine its type.

    Args:
        source: Source string (URL, path, or registry reference)

    Returns:
        Tuple of (SkillSource, parsed_source)

    Raises:
        SkillInstallerError: If source is invalid
    """
    # Check if it's a URL
    if source.startswith("http://") or source.startswith("https://"):
        if "github.com" in source:
            return SkillSource.URL, source
        raise SkillInstallerError(f"Unsupported URL: {source}. Only GitHub URLs are supported.")

    # Check if it's a registry reference (future)
    if source.startswith("@"):
        raise SkillInstallerError("Registry installation not yet supported. Use URL or path.")

    # Assume it's a local path
    path = Path(source).expanduser().resolve()
    if not path.exists():
        raise SkillInstallerError(f"Path does not exist: {source}")
    if not (path / "SKILL.md").exists():
        raise SkillInstallerError(f"No SKILL.md found in: {source}")

    return SkillSource.PATH, str(path)


def parse_github_url(url: str) -> Dict[str, str]:
    """Parse GitHub URL to extract owner, repo, branch, and path.

    Args:
        url: GitHub URL (tree or blob format)

    Returns:
        Dict with owner, repo, branch, path keys
    """
    parsed = urlparse(url)
    path_parts = parsed.path.strip("/").split("/")

    if len(path_parts) < 4:
        raise SkillInstallerError(f"Invalid GitHub URL format: {url}")

    owner = path_parts[0]
    repo = path_parts[1]
    url_type = path_parts[2]  # 'tree' or 'blob'

    # Find where branch ends and path begins
    # Branch can contain slashes (e.g., feature/branch)
    remaining = path_parts[3:]

    # Look for .claude in the path to determine where branch ends
    branch_parts = []
    skill_path_parts = []
    found_claude = False

    for part in remaining:
        if part == ".claude" or found_claude:
            found_claude = True
            skill_path_parts.append(part)
        else:
            branch_parts.append(part)

    branch = "/".join(branch_parts) if branch_parts else "main"
    skill_path = "/".join(skill_path_parts)

    # If it's a blob URL pointing to SKILL.md, get the parent directory
    if url_type == "blob" and skill_path.endswith("SKILL.md"):
        skill_path = "/".join(skill_path_parts[:-1])

    return {
        "owner": owner,
        "repo": repo,
        "branch": branch,
        "path": skill_path,
    }


def extract_skill_name(source: str) -> str:
    """Extract skill name from source path or URL.

    Args:
        source: Source path or URL

    Returns:
        Skill name
    """
    # Handle URLs
    if source.startswith("http://") or source.startswith("https://"):
        parsed = parse_github_url(source)
        return parsed["path"].rstrip("/").split("/")[-1]

    # Handle local paths
    path = Path(source)
    return path.name


def check_conflicts(skill_name: str, target_dir: Path) -> bool:
    """Check if a skill with the same name already exists.

    Args:
        skill_name: Name of skill to check
        target_dir: Target skills directory

    Returns:
        True if conflict exists
    """
    existing = target_dir / skill_name
    return existing.exists() and (existing / "SKILL.md").exists()


def get_target_dir(project: bool = False, personal: bool = False) -> Path:
    """Get the target directory for skill installation.

    Args:
        project: Install to project .claude/skills/
        personal: Install to ~/.claude/skills/

    Returns:
        Path to target directory
    """
    if personal:
        return Path.home() / ".claude" / "skills"

    if project:
        try:
            project_root = find_project_root()
            return project_root / ".claude" / "skills"
        except Exception:
            raise SkillInstallerError("Could not find project root. Use --personal for user-wide installation.")

    # Default to project if available
    try:
        project_root = find_project_root()
        return project_root / ".claude" / "skills"
    except Exception:
        return Path.home() / ".claude" / "skills"


def _download_github_skill(url: str) -> Dict[str, str]:
    """Download skill files from GitHub.

    Args:
        url: GitHub tree URL

    Returns:
        Dict mapping filename to content

    Raises:
        SkillInstallerError: If download fails
    """
    try:
        import urllib.request

        parsed = parse_github_url(url)
        owner = parsed["owner"]
        repo = parsed["repo"]
        branch = parsed["branch"]
        skill_path = parsed["path"]

        # Use GitHub API to get directory contents
        api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{skill_path}?ref={branch}"

        req = urllib.request.Request(api_url)
        req.add_header("Accept", "application/vnd.github.v3+json")
        req.add_header("User-Agent", "bpsai-pair-skill-installer")

        with urllib.request.urlopen(req, timeout=30) as response:
            import json

            contents = json.loads(response.read().decode())

        files = {}

        # Handle single file response (when URL points to a file)
        if isinstance(contents, dict):
            contents = [contents]

        for item in contents:
            if item["type"] == "file":
                # Download file content
                file_url = item["download_url"]
                with urllib.request.urlopen(file_url, timeout=30) as file_response:
                    files[item["name"]] = file_response.read().decode()
            elif item["type"] == "dir":
                # Recursively download directory
                subdir_url = f"https://github.com/{owner}/{repo}/tree/{branch}/{skill_path}/{item['name']}"
                subfiles = _download_github_skill(subdir_url)
                for subname, subcontent in subfiles.items():
                    files[f"{item['name']}/{subname}"] = subcontent

        return files

    except urllib.error.HTTPError as e:
        raise SkillInstallerError(f"GitHub API error: {e.code} - {e.reason}")
    except urllib.error.URLError as e:
        raise SkillInstallerError(f"Network error: {e.reason}")
    except Exception as e:
        raise SkillInstallerError(f"Download failed: {e}")


def _validate_skill_content(skill_dir: Path) -> None:
    """Validate skill files before installation.

    Args:
        skill_dir: Path to skill directory

    Raises:
        SkillInstallerError: If validation fails
    """
    validator = SkillValidator(skill_dir.parent)
    result = validator.validate_skill(skill_dir)

    if not result["valid"]:
        errors = "\n  - ".join(result["errors"])
        raise SkillInstallerError(f"Skill validation failed:\n  - {errors}")


def _update_skill_name(skill_file: Path, new_name: str) -> None:
    """Update skill name in SKILL.md frontmatter.

    Args:
        skill_file: Path to SKILL.md
        new_name: New skill name
    """
    content = skill_file.read_text(encoding="utf-8")

    # Parse and update frontmatter
    if content.startswith("---"):
        lines = content.split("\n")
        end_idx = None
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == "---":
                end_idx = i
                break

        if end_idx:
            yaml_content = "\n".join(lines[1:end_idx])
            try:
                frontmatter = yaml.safe_load(yaml_content) or {}
                frontmatter["name"] = new_name
                new_yaml = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)
                body = "\n".join(lines[end_idx + 1 :])
                new_content = f"---\n{new_yaml}---\n{body}"
                skill_file.write_text(new_content, encoding="utf-8")
            except yaml.YAMLError:
                pass  # Skip if YAML is invalid


def install_from_path(
    source_dir: Path,
    target_dir: Path,
    name: Optional[str] = None,
    force: bool = False,
) -> Dict[str, Any]:
    """Install skill from local path.

    Args:
        source_dir: Source skill directory
        target_dir: Target skills directory
        name: Optional name override
        force: Overwrite existing skill

    Returns:
        Dict with success status and details

    Raises:
        SkillInstallerError: If installation fails
    """
    source_path = Path(source_dir)
    target_path = Path(target_dir)

    # Determine skill name
    skill_name = name or source_path.name

    # Validate source skill
    _validate_skill_content(source_path)

    # Check for conflicts
    if check_conflicts(skill_name, target_path) and not force:
        raise SkillInstallerError(
            f"Skill '{skill_name}' already exists in {target_path}. Use --force to overwrite."
        )

    # Create target directory if needed
    target_path.mkdir(parents=True, exist_ok=True)

    # Install skill
    dest_dir = target_path / skill_name

    if dest_dir.exists() and force:
        shutil.rmtree(dest_dir)

    shutil.copytree(source_path, dest_dir)

    # Update name in frontmatter if renamed
    if name and name != source_path.name:
        _update_skill_name(dest_dir / "SKILL.md", name)

    return {
        "success": True,
        "skill_name": skill_name,
        "installed_to": str(dest_dir),
    }


def install_from_url(
    url: str,
    target_dir: Path,
    name: Optional[str] = None,
    force: bool = False,
) -> Dict[str, Any]:
    """Install skill from GitHub URL.

    Args:
        url: GitHub URL
        target_dir: Target skills directory
        name: Optional name override
        force: Overwrite existing skill

    Returns:
        Dict with success status and details

    Raises:
        SkillInstallerError: If installation fails
    """
    try:
        # Download skill files
        files = _download_github_skill(url)

        if not files:
            raise SkillInstallerError("No files found at URL")

        if "SKILL.md" not in files:
            raise SkillInstallerError("No SKILL.md found in downloaded files")

        # Determine skill name
        skill_name = name or extract_skill_name(url)

        # Check for conflicts
        if check_conflicts(skill_name, target_dir) and not force:
            raise SkillInstallerError(
                f"Skill '{skill_name}' already exists in {target_dir}. Use --force to overwrite."
            )

        # Create temporary directory for validation
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_skill_dir = Path(tmpdir) / skill_name
            temp_skill_dir.mkdir()

            # Write files
            for filename, content in files.items():
                file_path = temp_skill_dir / filename
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content, encoding="utf-8")

            # Update name if needed
            if name:
                _update_skill_name(temp_skill_dir / "SKILL.md", name)

            # Validate
            _validate_skill_content(temp_skill_dir)

            # Install
            target_dir.mkdir(parents=True, exist_ok=True)
            dest_dir = target_dir / skill_name

            if dest_dir.exists() and force:
                shutil.rmtree(dest_dir)

            shutil.copytree(temp_skill_dir, dest_dir)

        return {
            "success": True,
            "skill_name": skill_name,
            "installed_to": str(dest_dir),
        }

    except SkillInstallerError:
        raise
    except Exception as e:
        raise SkillInstallerError(f"Failed to download skill: {e}")


def install_skill(
    source: str,
    project: bool = False,
    personal: bool = False,
    name: Optional[str] = None,
    force: bool = False,
) -> Dict[str, Any]:
    """Install a skill from source.

    Args:
        source: Source URL, path, or registry reference
        project: Install to project directory
        personal: Install to personal directory
        name: Optional name override
        force: Overwrite existing skill

    Returns:
        Dict with success status and details
    """
    # Parse source
    source_type, parsed = parse_source(source)

    # Get target directory
    target_dir = get_target_dir(project=project, personal=personal)

    # Install based on source type
    if source_type == SkillSource.PATH:
        return install_from_path(Path(parsed), target_dir, name=name, force=force)
    elif source_type == SkillSource.URL:
        return install_from_url(parsed, target_dir, name=name, force=force)
    else:
        raise SkillInstallerError(f"Unsupported source type: {source_type}")
