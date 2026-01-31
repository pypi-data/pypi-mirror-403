"""Configuration loading and saving for PairCoder.

This module contains the Config dataclass and functions for loading
and saving configuration from YAML files.
"""
from __future__ import annotations

import os
import json
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import yaml

from .config_defaults import (
    DEFAULT_PROJECT_NAME,
    DEFAULT_PRIMARY_GOAL,
    DEFAULT_COVERAGE_TARGET,
    DEFAULT_BRANCH_TYPE,
    DEFAULT_MAIN_BRANCH,
    DEFAULT_CONTEXT_DIR,
    DEFAULT_PACK_NAME,
    DEFAULT_PACK_EXCLUDES,
    DEFAULT_PYTHON_FORMATTER,
    DEFAULT_NODE_FORMATTER,
    ENV_MAPPINGS,
)
from .config_helpers import validate_no_unrendered_templates
from .config_validator import ContainmentConfig, ArchitectureConfig


@dataclass
class Config:
    """PairCoder configuration."""

    # Project settings
    project_name: str = DEFAULT_PROJECT_NAME
    primary_goal: str = DEFAULT_PRIMARY_GOAL
    coverage_target: int = DEFAULT_COVERAGE_TARGET

    # Branch settings
    default_branch_type: str = DEFAULT_BRANCH_TYPE
    main_branch: str = DEFAULT_MAIN_BRANCH

    # Context settings
    context_dir: str = DEFAULT_CONTEXT_DIR

    # Pack settings
    default_pack_name: str = DEFAULT_PACK_NAME
    pack_excludes: list[str] = field(default_factory=lambda: DEFAULT_PACK_EXCLUDES.copy())

    # CI settings
    python_formatter: str = DEFAULT_PYTHON_FORMATTER
    node_formatter: str = DEFAULT_NODE_FORMATTER

    # Containment settings (contained autonomy mode)
    containment: ContainmentConfig = field(default_factory=lambda: ContainmentConfig())

    # Architecture enforcement settings
    architecture: ArchitectureConfig = field(default_factory=lambda: ArchitectureConfig())

    @classmethod
    def find_config_file(cls, root: Path) -> Optional[Path]:
        """Find the config file, preferring v2 .paircoder/ folder over legacy .paircoder.yml."""
        # v2 config: .paircoder/config.yaml (preferred)
        v2_config = root / ".paircoder" / "config.yaml"
        if v2_config.exists():
            return v2_config

        # Also check .yml extension for v2
        v2_config_yml = root / ".paircoder" / "config.yml"
        if v2_config_yml.exists():
            return v2_config_yml

        # Legacy: .paircoder.yml (fallback)
        legacy_config = root / ".paircoder.yml"
        if legacy_config.exists():
            return legacy_config

        return None

    @classmethod
    def load(cls, root: Path) -> "Config":
        """Load configuration from .paircoder/config.yaml, .paircoder.yml, or environment.

        Config resolution order:
        1. .paircoder/config.yaml (v2 preferred)
        2. .paircoder/config.yml (v2 alternate)
        3. .paircoder.yml (legacy fallback)
        4. Environment variables (override all)

        Raises:
            ConfigError: If config contains unrendered cookiecutter templates
        """
        config_file = cls.find_config_file(root)

        data = {}
        if config_file and config_file.exists():
            # Validate no unrendered templates before loading
            validate_no_unrendered_templates(config_file)

            with open(config_file, encoding="utf-8") as f:
                yaml_data = yaml.safe_load(f) or {}

                # Handle both flat and nested structures
                if "version" in yaml_data:
                    # New nested structure
                    if "project" in yaml_data:
                        project = yaml_data["project"]
                        data["project_name"] = project.get("name", DEFAULT_PROJECT_NAME)
                        data["primary_goal"] = project.get("primary_goal", DEFAULT_PRIMARY_GOAL)
                        data["coverage_target"] = project.get("coverage_target", DEFAULT_COVERAGE_TARGET)

                    if "workflow" in yaml_data:
                        workflow = yaml_data["workflow"]
                        data["default_branch_type"] = workflow.get("default_branch_type", DEFAULT_BRANCH_TYPE)
                        data["main_branch"] = workflow.get("main_branch", DEFAULT_MAIN_BRANCH)
                        data["context_dir"] = workflow.get("context_dir", DEFAULT_CONTEXT_DIR)

                    if "pack" in yaml_data:
                        pack = yaml_data["pack"]
                        data["default_pack_name"] = pack.get("default_name", DEFAULT_PACK_NAME)
                        data["pack_excludes"] = pack.get("excludes", [])

                    if "ci" in yaml_data:
                        ci = yaml_data["ci"]
                        data["python_formatter"] = ci.get("python_formatter", DEFAULT_PYTHON_FORMATTER)
                        data["node_formatter"] = ci.get("node_formatter", DEFAULT_NODE_FORMATTER)

                    # Load containment config (contained autonomy mode)
                    if "containment" in yaml_data:
                        containment_data = yaml_data["containment"]
                        if isinstance(containment_data, dict):
                            data["containment"] = ContainmentConfig.from_dict(containment_data)

                    # Load architecture config
                    if "architecture" in yaml_data:
                        architecture_data = yaml_data["architecture"]
                        if isinstance(architecture_data, dict):
                            data["architecture"] = ArchitectureConfig.from_dict(architecture_data)
                else:
                    # Old flat structure (backwards compatibility)
                    data = yaml_data

        # Override with environment variables
        for env_var, config_key in ENV_MAPPINGS.items():
            if env_value := os.getenv(env_var):
                data[config_key] = env_value

        # Create config with collected data
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})

    def save(self, root: Path, use_v2: bool = False, legacy: bool = False) -> Path:
        """Save configuration to config file.

        Args:
            root: Project root directory
            use_v2: If True, save to .paircoder/config.yaml (v2 format)
            legacy: If True, force save to .paircoder.yml (legacy format)

        Returns:
            Path to the saved config file

        Priority:
        1. If legacy=True, use .paircoder.yml
        2. If use_v2=True or .paircoder/ exists, use .paircoder/config.yaml
        3. Otherwise use .paircoder.yml (legacy default for compatibility)

        Note:
            V2 format uses the "minimal" preset as a base to ensure all
            sections are present (models, routing, hooks, trello, etc.),
            with instance values overriding the defaults.
        """
        if legacy:
            config_file = root / ".paircoder.yml"
        elif use_v2 or (root / ".paircoder").exists():
            config_dir = root / ".paircoder"
            config_dir.mkdir(exist_ok=True)
            config_file = config_dir / "config.yaml"
        else:
            config_file = root / ".paircoder.yml"

        is_v2 = config_file.parent.name == ".paircoder"

        if is_v2 and not legacy:
            # Use preset for complete config structure (v2.9.3 format)
            data = self._build_v2_config()
        else:
            # Legacy format (backwards compatibility)
            data = self._build_legacy_config()

        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        return config_file

    def _build_v2_config(self) -> Dict[str, Any]:
        """Build complete v2.9.3 config using minimal preset as base.

        Returns:
            Complete config dictionary with all sections
        """
        from .presets import get_preset

        # Get minimal preset as base
        minimal_preset = get_preset("minimal")
        if minimal_preset is None:
            # Fallback if preset not found
            return self._build_legacy_config()

        # Generate base config from preset
        data = minimal_preset.to_config_dict(
            project_name=self.project_name,
            primary_goal=self.primary_goal,
            description=f"{self.project_name} project",
        )

        # Override with instance values
        data["project"]["coverage_target"] = self.coverage_target

        data["workflow"]["default_branch_type"] = self.default_branch_type
        data["workflow"]["main_branch"] = self.main_branch
        data["workflow"]["context_dir"] = self.context_dir

        data["pack"]["default_name"] = self.default_pack_name
        data["pack"]["excludes"] = self.pack_excludes

        # CI section (preset doesn't have this, so add it)
        data["ci"] = {
            "python_formatter": self.python_formatter,
            "node_formatter": self.node_formatter,
        }

        # Override containment with instance values
        data["containment"] = self.containment.to_dict()

        # Override architecture with instance values
        data["architecture"] = self.architecture.to_dict()

        return data

    def _build_legacy_config(self) -> Dict[str, Any]:
        """Build legacy config format (minimal sections).

        Returns:
            Legacy config dictionary
        """
        return {
            "version": "0.1.3",
            "project": {
                "name": self.project_name,
                "primary_goal": self.primary_goal,
                "coverage_target": self.coverage_target,
            },
            "workflow": {
                "default_branch_type": self.default_branch_type,
                "main_branch": self.main_branch,
                "context_dir": self.context_dir,
            },
            "pack": {
                "default_name": self.default_pack_name,
                "excludes": self.pack_excludes,
            },
            "ci": {
                "python_formatter": self.python_formatter,
                "node_formatter": self.node_formatter,
            },
            "containment": self.containment.to_dict(),
            "architecture": self.architecture.to_dict(),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


def load_raw_config(root: Path) -> Tuple[Optional[Dict[str, Any]], Optional[Path]]:
    """Load raw config dictionary from file.

    Args:
        root: Project root directory

    Returns:
        Tuple of (config dict, config file path) or (None, None) if not found

    Raises:
        ConfigError: If config contains unrendered cookiecutter templates
    """
    config_file = Config.find_config_file(root)
    if not config_file or not config_file.exists():
        return None, None

    # Validate no unrendered templates before loading
    validate_no_unrendered_templates(config_file)

    with open(config_file, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    return data, config_file


def save_raw_config(root: Path, config: Dict[str, Any]) -> Path:
    """Save raw config dictionary to file.

    Args:
        root: Project root directory
        config: Config dictionary to save

    Returns:
        Path to saved config file
    """
    config_file = Config.find_config_file(root)
    if not config_file:
        # Default to v2 location
        config_dir = root / ".paircoder"
        config_dir.mkdir(exist_ok=True)
        config_file = config_dir / "config.yaml"

    with open(config_file, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    return config_file
