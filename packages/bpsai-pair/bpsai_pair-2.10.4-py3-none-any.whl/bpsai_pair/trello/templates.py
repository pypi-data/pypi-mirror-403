"""
Card description templates for Trello sync.

Provides BPS-formatted card descriptions with configurable templates.
"""
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import re


# Default BPS card description template
DEFAULT_BPS_TEMPLATE = """## Objective
{objective}

## Implementation Plan
{implementation_plan}

## Acceptance Criteria
{acceptance_criteria}

## Links
{links}

---
{metadata}
Created by: PairCoder"""


@dataclass
class CardDescriptionData:
    """Data for rendering a card description."""
    task_id: str
    title: str
    objective: str = ""
    implementation_plan: str = ""
    acceptance_criteria: List[str] = None
    complexity: int = 50
    priority: str = "P1"
    plan_title: str = ""
    task_link: str = ""
    pr_link: str = ""
    tags: List[str] = None

    def __post_init__(self):
        if self.acceptance_criteria is None:
            self.acceptance_criteria = []
        if self.tags is None:
            self.tags = []


class CardDescriptionTemplate:
    """Template renderer for Trello card descriptions."""

    # Section markers to look for in task body
    SECTION_MARKERS = {
        'objective': ['# Objective', '## Objective', '### Objective'],
        'implementation_plan': [
            '# Implementation Plan', '## Implementation Plan', '### Implementation Plan',
            '# Implementation', '## Implementation', '### Implementation',
            '# Plan', '## Plan',
        ],
        'acceptance_criteria': [
            '# Acceptance Criteria', '## Acceptance Criteria', '### Acceptance Criteria',
            '# Criteria', '## Criteria',
        ],
        'links': ['# Links', '## Links', '### Links'],
    }

    def __init__(self, template: Optional[str] = None):
        """Initialize with optional custom template.

        Args:
            template: Custom template string. Uses DEFAULT_BPS_TEMPLATE if not provided.
        """
        self.template = template or DEFAULT_BPS_TEMPLATE

    def extract_sections(self, body: str) -> Dict[str, str]:
        """Extract sections from task body.

        Args:
            body: Task body text

        Returns:
            Dict mapping section names to their content
        """
        if not body:
            return {}

        sections = {}
        lines = body.split('\n')
        current_section = None
        current_content = []

        for line in lines:
            # Check if this line is a section header
            found_section = None
            for section_name, markers in self.SECTION_MARKERS.items():
                for marker in markers:
                    if line.strip().lower() == marker.lower():
                        found_section = section_name
                        break
                if found_section:
                    break

            if found_section:
                # Save previous section
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = found_section
                current_content = []
            elif current_section:
                current_content.append(line)

        # Save last section
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()

        return sections

    def extract_objective(self, body: str, sections: Dict[str, str]) -> str:
        """Extract objective from body or sections.

        Args:
            body: Full task body
            sections: Pre-extracted sections

        Returns:
            Objective text
        """
        # First, check if there's an explicit Objective section
        if 'objective' in sections:
            return sections['objective']

        # Otherwise, use first non-header paragraph
        if not body:
            return ""

        paragraphs = body.split('\n\n')
        for para in paragraphs:
            para = para.strip()
            # Skip headers and empty paragraphs
            if para and not para.startswith('#'):
                # Skip if it's a list item
                if not para.startswith('-') and not para.startswith('*'):
                    return para

        return ""

    def extract_implementation_plan(self, body: str, sections: Dict[str, str]) -> str:
        """Extract implementation plan from body or sections.

        Args:
            body: Full task body
            sections: Pre-extracted sections

        Returns:
            Implementation plan text or placeholder
        """
        if 'implementation_plan' in sections:
            return sections['implementation_plan']

        # Look for bullet points that might be implementation steps
        if not body:
            return "_To be defined_"

        # Find bullet list sections that aren't acceptance criteria
        lines = body.split('\n')
        bullet_sections = []
        current_bullets = []
        in_criteria = False

        for line in lines:
            line_lower = line.strip().lower()

            # Check for acceptance criteria header
            if any(marker.lower() in line_lower for marker in self.SECTION_MARKERS['acceptance_criteria']):
                in_criteria = True
                if current_bullets:
                    bullet_sections.append('\n'.join(current_bullets))
                    current_bullets = []
                continue

            # Check for other section headers to exit criteria
            if line.strip().startswith('#'):
                in_criteria = False
                if current_bullets:
                    bullet_sections.append('\n'.join(current_bullets))
                    current_bullets = []
                continue

            # Collect non-checkbox bullets
            if not in_criteria and (line.strip().startswith('- ') or line.strip().startswith('* ')):
                if not line.strip().startswith('- [ ]') and not line.strip().startswith('- [x]'):
                    current_bullets.append(line)

        if current_bullets:
            bullet_sections.append('\n'.join(current_bullets))

        if bullet_sections:
            return bullet_sections[0]  # Return first bullet section

        return "_To be defined_"

    def format_acceptance_criteria(self, criteria: List[str]) -> str:
        """Format acceptance criteria as checkboxes.

        Args:
            criteria: List of criteria strings

        Returns:
            Formatted checkbox list
        """
        if not criteria:
            return "- [ ] _To be defined_"

        return '\n'.join(f"- [ ] {item}" for item in criteria)

    def format_links(self, task_id: str, task_link: str = "", pr_link: str = "") -> str:
        """Format links section.

        Args:
            task_id: Task ID for reference
            task_link: Optional link to task file
            pr_link: Optional link to PR

        Returns:
            Formatted links section
        """
        links = []
        links.append(f"- Task: `{task_id}`" if not task_link else f"- Task: [{task_id}]({task_link})")

        if pr_link:
            links.append(f"- PR: {pr_link}")
        else:
            links.append("- PR: _pending_")

        return '\n'.join(links)

    def format_metadata(self, data: CardDescriptionData) -> str:
        """Format metadata footer.

        Args:
            data: Card description data

        Returns:
            Formatted metadata line
        """
        parts = [
            f"Complexity: {data.complexity}",
            f"Priority: {data.priority}",
        ]
        if data.plan_title:
            parts.append(f"Plan: {data.plan_title}")

        return " | ".join(parts)

    def render(self, data: CardDescriptionData, body: str = "") -> str:
        """Render card description from data.

        Args:
            data: Card description data
            body: Optional task body for section extraction

        Returns:
            Rendered card description
        """
        # Extract sections from body
        sections = self.extract_sections(body)

        # Get or derive each section
        objective = data.objective or self.extract_objective(body, sections)
        implementation_plan = self.extract_implementation_plan(body, sections)
        acceptance_criteria = self.format_acceptance_criteria(data.acceptance_criteria)
        links = self.format_links(data.task_id, data.task_link, data.pr_link)
        metadata = self.format_metadata(data)

        # Build description using template
        description = self.template.format(
            objective=objective or "_No objective specified_",
            implementation_plan=implementation_plan,
            acceptance_criteria=acceptance_criteria,
            links=links,
            metadata=metadata,
        )

        # Clean up any double newlines
        description = re.sub(r'\n{3,}', '\n\n', description)

        return description.strip()

    @classmethod
    def from_task_data(cls, task_data: Any, template: Optional[str] = None) -> str:
        """Convenience method to render from TaskData.

        Args:
            task_data: TaskData object
            template: Optional custom template

        Returns:
            Rendered card description
        """
        renderer = cls(template)

        data = CardDescriptionData(
            task_id=task_data.id,
            title=task_data.title,
            objective="",  # Will be extracted from body
            acceptance_criteria=task_data.acceptance_criteria,
            complexity=task_data.complexity,
            priority=task_data.priority,
            plan_title=task_data.plan_title or "",
            tags=task_data.tags,
        )

        return renderer.render(data, body=task_data.description)


def should_preserve_description(existing_desc: str, generated_marker: str = "Created by: PairCoder") -> bool:
    """Check if an existing description was manually edited.

    Args:
        existing_desc: Existing card description
        generated_marker: Marker indicating auto-generated description

    Returns:
        True if description appears to be manually edited and should be preserved
    """
    if not existing_desc:
        return False

    # If it doesn't have our marker, it was probably manually created
    if generated_marker not in existing_desc:
        return True

    # Could add more heuristics here, e.g.:
    # - Check for specific user-added sections
    # - Compare structure to expected template

    return False
