"""Model routing configuration.

Loads and uses the routing section from config.yaml to select
appropriate models based on task complexity.

This file contains the changes needed for tools/cli/bpsai_pair/core/config.py

Location: Add to tools/cli/bpsai_pair/core/config.py
"""
from dataclasses import dataclass, field
from typing import Optional


# ============================================================================
# ADD THESE DATACLASSES
# ============================================================================

@dataclass
class RoutingLevel:
    """Configuration for a complexity routing level."""
    max_score: int
    model: str
    
    @classmethod
    def from_dict(cls, data: dict) -> "RoutingLevel":
        return cls(
            max_score=data.get("max_score", 100),
            model=data.get("model", "claude-sonnet-4-5"),
        )


@dataclass
class RoutingConfig:
    """Model routing configuration.
    
    Determines which AI model to use based on task complexity
    or task type overrides.
    """
    by_complexity: dict[str, RoutingLevel] = field(default_factory=dict)
    overrides: dict[str, str] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: dict) -> "RoutingConfig":
        """Create RoutingConfig from config dict."""
        by_complexity = {}
        for name, level_data in data.get("by_complexity", {}).items():
            by_complexity[name] = RoutingLevel.from_dict(level_data)
        
        return cls(
            by_complexity=by_complexity,
            overrides=data.get("overrides", {}),
        )
    
    def get_model_for_complexity(self, score: int) -> str:
        """Get appropriate model for complexity score.
        
        Args:
            score: Complexity score (0-100)
            
        Returns:
            Model identifier string
        """
        if not self.by_complexity:
            return "claude-sonnet-4-5"  # Default
        
        # Sort levels by max_score and find appropriate level
        sorted_levels = sorted(
            self.by_complexity.items(),
            key=lambda x: x[1].max_score
        )
        
        for level_name, level in sorted_levels:
            if score <= level.max_score:
                return level.model
        
        # If score exceeds all levels, return most capable
        if sorted_levels:
            return sorted_levels[-1][1].model
        
        return "claude-opus-4-5"
    
    def get_model_for_task_type(self, task_type: str) -> Optional[str]:
        """Get model override for task type.
        
        Args:
            task_type: Type of task (security, architecture, etc.)
            
        Returns:
            Model identifier if override exists, None otherwise
        """
        return self.overrides.get(task_type)
    
    def get_model(self, complexity: int = 50, task_type: Optional[str] = None) -> str:
        """Get best model for given parameters.
        
        Task type overrides take precedence over complexity routing.
        
        Args:
            complexity: Task complexity score (0-100)
            task_type: Optional task type for override lookup
            
        Returns:
            Model identifier string
        """
        # Check for type override first
        if task_type:
            override = self.get_model_for_task_type(task_type)
            if override:
                return override
        
        # Fall back to complexity routing
        return self.get_model_for_complexity(complexity)


@dataclass
class EnforcementConfig:
    """Enforcement configuration settings."""
    state_machine: bool = False
    strict_mode: bool = True
    require_ac_verification: bool = True
    require_budget_check: bool = True
    
    @classmethod
    def from_dict(cls, data: dict) -> "EnforcementConfig":
        return cls(
            state_machine=data.get("state_machine", False),
            strict_mode=data.get("strict_mode", True),
            require_ac_verification=data.get("require_ac_verification", True),
            require_budget_check=data.get("require_budget_check", True),
        )


# ============================================================================
# MODIFY load_config() TO INCLUDE ROUTING
# ============================================================================

def load_config_with_routing(path=None):
    """Load config with routing configuration.
    
    This is the updated version of load_config that includes
    routing and enforcement sections.
    
    Example config.yaml:
    
    routing:
      by_complexity:
        trivial:   { max_score: 20,  model: claude-haiku-4-5 }
        simple:    { max_score: 40,  model: claude-haiku-4-5 }
        moderate:  { max_score: 60,  model: claude-sonnet-4-5 }
        complex:   { max_score: 80,  model: claude-opus-4-5 }
        epic:      { max_score: 100, model: claude-opus-4-5 }
      overrides:
        security: claude-opus-4-5
        architecture: claude-opus-4-5
    
    enforcement:
      state_machine: false
      strict_mode: true
      require_ac_verification: true
      require_budget_check: true
    """
    import yaml
    from pathlib import Path
    from .ops import find_paircoder_dir
    
    if path is None:
        paircoder_dir = find_paircoder_dir()
        if paircoder_dir:
            path = paircoder_dir / "config.yaml"
        else:
            path = Path(".paircoder/config.yaml")
    
    if not path.exists():
        return {
            "routing": RoutingConfig(),
            "enforcement": EnforcementConfig(),
        }
    
    with open(path, "r", encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}
    
    # Parse routing section
    routing_data = data.get("routing", {})
    routing = RoutingConfig.from_dict(routing_data)
    
    # Parse enforcement section
    enforcement_data = data.get("enforcement", {})
    enforcement = EnforcementConfig.from_dict(enforcement_data)
    
    # Return full config with parsed sections
    return {
        **data,
        "routing": routing,
        "enforcement": enforcement,
    }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_routing_config() -> RoutingConfig:
    """Get routing configuration from config.yaml."""
    config = load_config_with_routing()
    routing = config.get("routing")
    if isinstance(routing, RoutingConfig):
        return routing
    return RoutingConfig()


def get_model_for_task(complexity: int, task_type: Optional[str] = None) -> str:
    """Get appropriate model for a task.
    
    Convenience function that loads config and returns model.
    
    Args:
        complexity: Task complexity score (0-100)
        task_type: Optional task type for override lookup
        
    Returns:
        Model identifier string
    """
    routing = get_routing_config()
    return routing.get_model(complexity=complexity, task_type=task_type)
