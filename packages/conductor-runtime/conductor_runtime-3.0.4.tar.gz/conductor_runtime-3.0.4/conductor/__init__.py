"""
Conductor — Autonomous, Policy-Governed, Learning Orchestration Runtime.

SDK Public API:
    - Conductor: Main orchestrator class
    - ConductorConfig: Configuration
    - explore(): Quick exploration function
    - status(): Quick status check
    - bootstrap(): Create new project programmatically
"""
from conductor.conductor import Conductor
from conductor.config import ConductorConfig
import asyncio
from pathlib import Path


__version__ = "3.0.4"
__all__ = [
    "Conductor",
    "ConductorConfig",
    "explore",
    "status",
    "bootstrap",
    "__version__",
]


# ─────────────────────────────────────────────────────────────
# SDK PUBLIC API
# ─────────────────────────────────────────────────────────────

def explore(goal: str, project_root: str = ".", num_strategies: int = 2) -> str:
    """
    Explore a goal with multiple forked strategies.
    
    Args:
        goal: The goal to achieve
        project_root: Project directory (default: current)
        num_strategies: Number of parallel strategies (default: 2)
    
    Returns:
        Winner plan ID
    
    Example:
        >>> from conductor import explore
        >>> winner = explore("Create a REST API with auth")
    """
    config = ConductorConfig()
    conductor = Conductor(project_root, config)
    return asyncio.run(conductor.explore(goal, num_strategies))


def status(project_root: str = ".") -> dict:
    """
    Get current execution status.
    
    Args:
        project_root: Project directory (default: current)
    
    Returns:
        Status dict with plan_id, goal, status, steps, etc.
    
    Example:
        >>> from conductor import status
        >>> print(status()["goal"])
    """
    config = ConductorConfig(verbose=False)
    conductor = Conductor(project_root, config)
    return conductor.status()


def bootstrap(project_name: str, target_dir: str = ".") -> Path:
    """
    Create a new Conductor project programmatically.
    
    Creates a lightweight project that uses conductor as a pip package
    rather than copying the runtime. This enables shared runtime updates.
    
    Args:
        project_name: Name for the new project
        target_dir: Parent directory (default: current)
    
    Returns:
        Path to the created project
    
    Example:
        >>> from conductor import bootstrap
        >>> path = bootstrap("my-project")
    """
    import shutil
    
    target = Path(target_dir).absolute() / project_name
    template_root = Path(__file__).parent.parent
    
    if target.exists():
        raise FileExistsError(f"Directory already exists: {target}")
    
    target.mkdir(parents=True)
    
    # Copy project workspace (user-customizable context)
    src_project = template_root / "project"
    if src_project.exists():
        shutil.copytree(src_project, target / "project")
    
    # Create state directory
    (target / ".conductor").mkdir(exist_ok=True)
    
    # Copy policy example
    src_policy = template_root / ".conductor" / "policy.yaml.example"
    if src_policy.exists():
        shutil.copy2(src_policy, target / ".conductor" / "policy.yaml.example")
    
    # Create minimal pyproject.toml that depends on conductor
    pyproject_content = f'''[project]
name = "{project_name}"
version = "0.1.0"
dependencies = [
    "conductor-runtime",  # pip install conductor-runtime
]

[project.scripts]
conductor = "conductor.cli:main"
'''
    (target / "pyproject.toml").write_text(pyproject_content)
    
    # Create .env.example
    env_content = '''# Conductor Configuration
GEMINI_API_KEY=your_api_key_here
'''
    (target / ".env.example").write_text(env_content)
    
    # Create README
    readme_content = f'''# {project_name}

A Conductor-powered project.

## Setup

```bash
pip install conductor-runtime
cp .env.example .env
# Edit .env with your API key
```

## Usage

```bash
conductor explore "Your goal here"
conductor status
```
'''
    (target / "README.md").write_text(readme_content)
    
    return target

