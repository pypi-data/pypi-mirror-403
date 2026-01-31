"""Parse PairCoder config XML from Claude's guided setup responses.

Extracts ``<paircoder_config>`` blocks and returns validated field
dictionaries that the wizard review step can consume.

Supports multiple formats:
1. Raw XML: <paircoder_config>...</paircoder_config>
2. Fenced code blocks: ```xml\n<paircoder_config>...</paircoder_config>\n```
3. Markdown summary fallback: **Project Name:** ..., **Description:** ..., etc.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

# Fields the parser recognises — unknown tags are silently dropped.
_KNOWN_FIELDS = frozenset({
    "project_name",
    "description",
    "primary_goal",
    "preset",
    "enforcement",
    "coverage_target",
})

# Pattern to extract the first <paircoder_config>…</paircoder_config> block.
_CONFIG_PATTERN = re.compile(
    r"<paircoder_config>(.*?)</paircoder_config>",
    re.DOTALL,
)

# Pattern to extract XML from fenced code blocks
_FENCED_XML_PATTERN = re.compile(
    r"```(?:xml)?\s*\n(<paircoder_config>.*?</paircoder_config>)\s*\n```",
    re.DOTALL | re.IGNORECASE,
)

# Patterns for markdown summary fallback
_MD_PATTERNS = {
    "project_name": re.compile(r"\*\*Project Name:\*\*\s*(.+?)(?:\n|$)", re.IGNORECASE),
    "description": re.compile(r"\*\*Description:\*\*\s*(.+?)(?:\n|$)", re.IGNORECASE),
    "primary_goal": re.compile(r"\*\*Primary Goal:\*\*\s*(.+?)(?:\n|$)", re.IGNORECASE),
    "preset": re.compile(r"\*\*Preset:\*\*\s*(\w+)", re.IGNORECASE),
    "enforcement": re.compile(r"\*\*Enforcement:\*\*\s*(\w+)", re.IGNORECASE),
    "coverage_target": re.compile(r"\*\*Coverage Target:\*\*\s*(\d+)", re.IGNORECASE),
}


class ConfigParseError(ValueError):
    """Raised when a config block is found but cannot be parsed."""


def _parse_xml_config(xml_str: str) -> dict[str, str]:
    """Parse XML string into config dict."""
    try:
        root = ET.fromstring(xml_str)
    except ET.ParseError as exc:
        raise ConfigParseError(f"Malformed config XML: {exc}") from exc

    config: dict[str, str] = {}
    for child in root:
        tag = child.tag
        if tag in _KNOWN_FIELDS:
            text = (child.text or "").strip()
            if text:
                config[tag] = text

    return config


def _parse_markdown_summary(response: str) -> dict[str, str] | None:
    """Fallback: extract config from markdown summary format.

    Looks for patterns like:
    **Project Name:** My App
    **Description:** A cool app
    """
    config: dict[str, str] = {}

    for field, pattern in _MD_PATTERNS.items():
        match = pattern.search(response)
        if match:
            value = match.group(1).strip()
            if value:
                config[field] = value

    # Must have at least project_name to be valid
    if "project_name" not in config:
        return None

    return config if config else None


def parse_config_from_response(
    response: str,
) -> dict[str, str] | None:
    """Extract a ``paircoder_config`` XML block from *response*.

    Tries multiple extraction strategies:
    1. XML in fenced code block (```xml ... ```)
    2. Raw XML (<paircoder_config>...</paircoder_config>)
    3. Markdown summary fallback (**Project Name:** etc.)

    Args:
        response: Full text of a Claude response that may contain an
            embedded ``<paircoder_config>`` XML block.

    Returns:
        Dictionary of known field names to their string values,
        or ``None`` if no config block is present.

    Raises:
        ConfigParseError: If a config block is found but the XML is
            malformed or cannot be parsed.
    """
    if not response:
        return None

    # Strategy 1: Try fenced code block first (most reliable)
    fenced_match = _FENCED_XML_PATTERN.search(response)
    if fenced_match:
        xml_str = fenced_match.group(1)
        return _parse_xml_config(xml_str)

    # Strategy 2: Try raw XML
    raw_match = _CONFIG_PATTERN.search(response)
    if raw_match:
        xml_str = raw_match.group(0)  # full match including tags
        return _parse_xml_config(xml_str)

    # Strategy 3: Fallback to markdown summary
    md_config = _parse_markdown_summary(response)
    if md_config:
        return md_config

    return None
