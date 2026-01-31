"""Configuration helper utilities for PairCoder.

This module contains utility functions for validating paths, domains,
and configuration file contents.
"""
from __future__ import annotations

from pathlib import Path
from typing import List


class ConfigError(Exception):
    """Error raised when config validation fails."""

    pass


def validate_path(path: str, field_name: str) -> str:
    """Validate a filesystem path string.

    Args:
        path: The path string to validate.
        field_name: Name of the field for error messages.

    Returns:
        The validated path string.

    Raises:
        ValueError: If the path is invalid.
    """
    if not path:
        raise ValueError(f"{field_name} cannot contain empty path strings")
    if "\x00" in path:
        raise ValueError(f"{field_name} cannot contain paths with null bytes")
    return path


def validate_domain(domain: str) -> str:
    """Validate a network domain string.

    Args:
        domain: The domain string to validate.

    Returns:
        The validated domain string.

    Raises:
        ValueError: If the domain is invalid.
    """
    if not domain:
        raise ValueError("allow_network cannot contain empty domain strings")

    # Check for protocol prefix
    if domain.startswith(("http://", "https://", "ftp://")):
        raise ValueError(
            f"Domain '{domain}' should not include protocol prefix (http/https)"
        )

    # Check for path (anything after first /)
    # Allow ports like example.com:8080 but reject paths like example.com/path
    if "/" in domain:
        raise ValueError(
            f"Domain '{domain}' should not include path. Use domain only."
        )

    return domain


def validate_no_unrendered_templates(config_path: Path) -> None:
    """Raise error if config contains unrendered cookiecutter variables.

    Args:
        config_path: Path to the config file to validate

    Raises:
        ConfigError: If config contains {{ cookiecutter.xxx }} patterns
    """
    try:
        content = config_path.read_text(encoding="utf-8")
        if "{{" in content and "cookiecutter" in content:
            raise ConfigError(
                f"Config file contains unrendered template variables: {config_path}\n"
                "This happens when bundled templates are copied without rendering.\n"
                "Run 'bpsai-pair init' again to regenerate the config file,\n"
                "or manually replace {{ cookiecutter.xxx }} values."
            )
    except ConfigError:
        raise
    except Exception:
        # If we can't read the file, let yaml.safe_load handle it later
        pass


def validate_path_list(paths: List[str], field_name: str) -> List[str]:
    """Validate a list of filesystem paths.

    Args:
        paths: List of path strings to validate.
        field_name: Name of the field for error messages.

    Returns:
        The validated list of paths.

    Raises:
        ValueError: If any path is invalid.
    """
    validated = []
    for path in paths:
        validated.append(validate_path(path, field_name))
    return validated


def validate_domain_list(domains: List[str]) -> List[str]:
    """Validate a list of network domains.

    Args:
        domains: List of domain strings to validate.

    Returns:
        The validated list of domains.

    Raises:
        ValueError: If any domain is invalid.
    """
    validated = []
    for domain in domains:
        validated.append(validate_domain(domain))
    return validated
