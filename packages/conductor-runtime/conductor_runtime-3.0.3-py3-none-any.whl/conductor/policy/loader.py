"""
Policy Loader for Conductor.

Loads project-level policies from .conductor/policy.yaml
and provides constraint inheritance/merge functionality.
"""
import yaml
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
import logging


logger = logging.getLogger("conductor.policy")


# ─────────────────────────────────────────────────────────────
# POLICY SCHEMA
# ─────────────────────────────────────────────────────────────

@dataclass
class FileRules:
    """Rules about which files can be modified."""
    protected: list[str] = field(default_factory=list)
    allowed_patterns: list[str] = field(default_factory=list)


@dataclass
class BehaviorSettings:
    """Behavioral limits and preferences."""
    max_diff_lines: int = 500
    timeout_seconds: int = 300


@dataclass
class ProjectPolicy:
    """
    Project-level policy loaded from .conductor/policy.yaml
    
    Example policy.yaml:
    ```yaml
    version: "1.0"
    
    global_constraints:
      - "Do NOT modify files in /core"
      - "Do NOT delete any file without explicit instruction"
    
    file_rules:
      protected:
        - "*.lock"
        - "*.env"
      allowed_patterns:
        - "src/**/*.py"
    
    behavior:
      max_diff_lines: 300
      timeout_seconds: 600
    ```
    """
    version: str = "1.0"
    global_constraints: list[str] = field(default_factory=list)
    file_rules: FileRules = field(default_factory=FileRules)
    behavior: BehaviorSettings = field(default_factory=BehaviorSettings)


# ─────────────────────────────────────────────────────────────
# LOADER
# ─────────────────────────────────────────────────────────────

def load_policy(project_root: str) -> ProjectPolicy:
    """
    Load project policy from .conductor/policy.yaml.
    
    Returns default policy if file doesn't exist or is invalid.
    """
    policy_path = Path(project_root) / ".conductor" / "policy.yaml"
    
    if not policy_path.exists():
        logger.debug(f"No policy file at {policy_path}, using defaults")
        return ProjectPolicy()
    
    try:
        with open(policy_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        
        return _parse_policy(data)
    
    except yaml.YAMLError as e:
        logger.warning(f"Invalid YAML in {policy_path}: {e}")
        return ProjectPolicy()
    
    except Exception as e:
        logger.warning(f"Error loading policy from {policy_path}: {e}")
        return ProjectPolicy()


def _parse_policy(data: dict) -> ProjectPolicy:
    """Parse policy dict into ProjectPolicy dataclass."""
    
    # File rules
    file_rules_data = data.get("file_rules", {})
    file_rules = FileRules(
        protected=file_rules_data.get("protected", []),
        allowed_patterns=file_rules_data.get("allowed_patterns", []),
    )
    
    # Behavior
    behavior_data = data.get("behavior", {})
    behavior = BehaviorSettings(
        max_diff_lines=behavior_data.get("max_diff_lines", 500),
        timeout_seconds=behavior_data.get("timeout_seconds", 300),
    )
    
    return ProjectPolicy(
        version=data.get("version", "1.0"),
        global_constraints=data.get("global_constraints", []),
        file_rules=file_rules,
        behavior=behavior,
    )


# ─────────────────────────────────────────────────────────────
# MERGE
# ─────────────────────────────────────────────────────────────

def merge_constraints(
    project_constraints: list[str],
    plan_constraints: list[str],
    step_constraints: list[str],
) -> list[str]:
    """
    Merge constraints from multiple levels.
    
    Order: project (first) + plan + step (last)
    Duplicates are removed while preserving order.
    
    Returns:
        Combined list of unique constraints
    """
    seen = set()
    merged = []
    
    for constraint in project_constraints + plan_constraints + step_constraints:
        if constraint not in seen:
            seen.add(constraint)
            merged.append(constraint)
    
    return merged


def merge_allowed_files(
    project_patterns: list[str],
    task_files: list[str],
) -> list[str]:
    """
    Determine final allowed files list.
    
    If task specifies allowed_files, use those (more specific).
    Otherwise, fall back to project patterns.
    
    Returns:
        Final list of allowed files/patterns
    """
    if task_files:
        return task_files
    return project_patterns
