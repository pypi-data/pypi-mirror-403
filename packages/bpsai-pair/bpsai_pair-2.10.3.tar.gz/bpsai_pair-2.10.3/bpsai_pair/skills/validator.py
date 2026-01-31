"""
Skill Validator - Validates Claude Code skills against Anthropic specs.

Validation rules:
1. Frontmatter: Only `name` and `description` fields allowed
2. Description: Under 1024 characters, 3rd-person voice preferred
3. File size: SKILL.md under 500 lines
4. Naming: lowercase-hyphenated, gerund form preferred
5. Name must match directory name
"""

import re
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)

# Allowed frontmatter fields per Anthropic spec
ALLOWED_FIELDS = {"name", "description"}

# Max description length
MAX_DESCRIPTION_LENGTH = 1024

# Max file lines
MAX_FILE_LINES = 500

# Patterns for 2nd person detection
SECOND_PERSON_PATTERNS = [
    r"\byou\b",
    r"\byour\b",
    r"\byou're\b",
    r"\byourself\b",
]

# Common non-gerund to gerund mappings
GERUND_SUGGESTIONS = {
    "code-review": "reviewing-code",
    "code-analyze": "analyzing-code",
    "test-run": "running-tests",
    "bug-fix": "fixing-bugs",
    "plan": "planning",
    "review": "reviewing",
    "analyze": "analyzing",
    "implement": "implementing",
    "design": "designing",
    "finish": "finishing",
}


def find_skills_dir(start_path: Optional[Path] = None) -> Path:
    """Find the .claude/skills directory.

    Args:
        start_path: Starting path to search from

    Returns:
        Path to skills directory

    Raises:
        FileNotFoundError: If skills directory not found
    """
    if start_path is None:
        start_path = Path.cwd()

    # Search up to 10 levels
    current = start_path
    for _ in range(10):
        skills_dir = current / ".claude" / "skills"
        if skills_dir.exists():
            return skills_dir
        if current.parent == current:
            break
        current = current.parent

    raise FileNotFoundError("Could not find .claude/skills directory")


class SkillValidator:
    """Validates skill files against Anthropic specs."""

    def __init__(self, skills_dir: Path):
        """Initialize validator.

        Args:
            skills_dir: Path to skills directory
        """
        self.skills_dir = Path(skills_dir)

    def validate_skill(self, skill_dir: Path) -> Dict[str, Any]:
        """Validate a single skill.

        Args:
            skill_dir: Path to skill directory

        Returns:
            Dict with:
            - valid: bool
            - errors: List[str]
            - warnings: List[str]
            - name: str (skill name)
        """
        errors = []
        warnings = []
        skill_name = skill_dir.name

        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            return {
                "valid": False,
                "errors": [f"SKILL.md not found in {skill_dir}"],
                "warnings": [],
                "name": skill_name,
            }

        content = skill_file.read_text(encoding="utf-8")
        lines = content.split("\n")

        # Check file length
        if len(lines) > MAX_FILE_LINES:
            errors.append(f"File exceeds {MAX_FILE_LINES} lines ({len(lines)} lines)")

        # Parse frontmatter
        frontmatter, frontmatter_errors = self._parse_frontmatter(content)
        errors.extend(frontmatter_errors)

        if frontmatter:
            # Check required fields
            if "name" not in frontmatter:
                errors.append("Missing required 'name' field in frontmatter")
            if "description" not in frontmatter:
                errors.append("Missing required 'description' field in frontmatter")

            # Check for extra fields
            extra_fields = set(frontmatter.keys()) - ALLOWED_FIELDS
            if extra_fields:
                errors.append(f"Extra frontmatter fields not allowed: {', '.join(extra_fields)}")

            # Validate name matches directory
            if "name" in frontmatter and frontmatter["name"] != skill_name:
                errors.append(
                    f"Name '{frontmatter['name']}' does not match directory '{skill_name}'"
                )

            # Validate description
            if "description" in frontmatter:
                desc = frontmatter["description"]
                if len(desc) > MAX_DESCRIPTION_LENGTH:
                    errors.append(
                        f"Description too long ({len(desc)} chars, max {MAX_DESCRIPTION_LENGTH})"
                    )

                # Check for 2nd person voice
                if self._uses_second_person(desc):
                    warnings.append(
                        "Description uses 2nd person voice (e.g., 'you'). "
                        "3rd person preferred (e.g., 'Manages...', 'Reviews...')"
                    )

            # Check naming convention
            if "name" in frontmatter:
                name_warnings = self._check_naming(frontmatter["name"])
                warnings.extend(name_warnings)

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "name": skill_name,
        }

    def _parse_frontmatter(self, content: str) -> tuple:
        """Parse YAML frontmatter from content.

        Args:
            content: File content

        Returns:
            Tuple of (frontmatter dict, errors list)
        """
        errors = []
        frontmatter = {}

        if not content.startswith("---"):
            errors.append("Missing YAML frontmatter (should start with ---)")
            return frontmatter, errors

        # Find the closing ---
        lines = content.split("\n")
        end_index = None
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == "---":
                end_index = i
                break

        if end_index is None:
            errors.append("Unclosed YAML frontmatter (missing closing ---)")
            return frontmatter, errors

        # Parse YAML
        yaml_content = "\n".join(lines[1:end_index])
        try:
            frontmatter = yaml.safe_load(yaml_content) or {}
        except yaml.YAMLError as e:
            errors.append(f"Invalid YAML frontmatter: {e}")

        return frontmatter, errors

    def _uses_second_person(self, text: str) -> bool:
        """Check if text uses 2nd person voice.

        Args:
            text: Text to check

        Returns:
            True if 2nd person detected
        """
        text_lower = text.lower()
        for pattern in SECOND_PERSON_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        return False

    def _check_naming(self, name: str) -> List[str]:
        """Check naming conventions.

        Args:
            name: Skill name

        Returns:
            List of warning messages
        """
        warnings = []

        # Check if name is lowercase with hyphens
        if name != name.lower():
            warnings.append(f"Name should be lowercase: '{name.lower()}'")

        if "_" in name:
            warnings.append(f"Name should use hyphens, not underscores: '{name.replace('_', '-')}'")

        # Check for gerund form
        if name in GERUND_SUGGESTIONS:
            warnings.append(
                f"Name should use gerund form: '{GERUND_SUGGESTIONS[name]}'"
            )

        return warnings

    def validate_all(self) -> Dict[str, Dict[str, Any]]:
        """Validate all skills in the directory.

        Returns:
            Dict mapping skill name to validation result
        """
        results = {}

        if not self.skills_dir.exists():
            return results

        for skill_dir in self.skills_dir.iterdir():
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                results[skill_dir.name] = self.validate_skill(skill_dir)

        return results

    def get_summary(self, results: Dict[str, Dict[str, Any]]) -> Dict[str, int]:
        """Get summary of validation results.

        Args:
            results: Validation results from validate_all()

        Returns:
            Dict with total, passed, failed, warnings counts
        """
        total = len(results)
        passed = sum(1 for r in results.values() if r["valid"])
        failed = total - passed
        with_warnings = sum(1 for r in results.values() if r["warnings"])

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "with_warnings": with_warnings,
        }

    def fix_skill(self, skill_dir: Path) -> bool:
        """Attempt to auto-fix skill issues.

        Args:
            skill_dir: Path to skill directory

        Returns:
            True if fixes were applied
        """
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            return False

        content = skill_file.read_text(encoding="utf-8")
        original_content = content

        # Parse frontmatter
        frontmatter, errors = self._parse_frontmatter(content)
        if errors:
            return False

        fixed = False

        # Remove extra fields
        extra_fields = set(frontmatter.keys()) - ALLOWED_FIELDS
        if extra_fields:
            for field in extra_fields:
                del frontmatter[field]
            fixed = True

        # Fix name mismatch
        skill_name = skill_dir.name
        if "name" in frontmatter and frontmatter["name"] != skill_name:
            frontmatter["name"] = skill_name
            fixed = True

        # Try to fix 2nd person voice (simple replacement)
        if "description" in frontmatter:
            desc = frontmatter["description"]
            # Simple fix: replace "Use when you" with "Triggers when"
            if "use when you" in desc.lower():
                desc = re.sub(
                    r"Use when you", "Triggers when user", desc, flags=re.IGNORECASE
                )
                frontmatter["description"] = desc
                fixed = True
            # Replace "you need" with "user needs"
            if " you " in desc.lower():
                desc = re.sub(r"\byou\b", "user", desc, flags=re.IGNORECASE)
                frontmatter["description"] = desc
                fixed = True

        if fixed:
            # Rebuild content
            lines = content.split("\n")

            # Find frontmatter end
            end_index = None
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == "---":
                    end_index = i
                    break

            if end_index:
                # Rebuild with fixed frontmatter
                new_yaml = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)
                body = "\n".join(lines[end_index + 1:])
                new_content = f"---\n{new_yaml}---\n{body}"
                skill_file.write_text(new_content, encoding="utf-8")

        return fixed
