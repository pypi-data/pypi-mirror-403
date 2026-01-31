"""
Multi-model configuration for Conductor.
Allows role-based model selection and execution mode switching.
"""
from dataclasses import dataclass, field
from typing import Optional, Any, Literal
import os


# ─────────────────────────────────────────────────────────────
# HANDOFF MODE
# ─────────────────────────────────────────────────────────────

HandoffMode = Literal["files", "llm"]


@dataclass
class ModelConfig:
    """Configuration for a single model."""
    model_name: str
    base_url: Optional[str] = None
    api_key_env: str = "GEMINI_API_KEY"
    temperature: float = 0.7
    max_tokens: int = 4096
    
    def get_api_key(self) -> Optional[str]:
        return os.environ.get(self.api_key_env)


@dataclass
class ConductorConfig:
    """
    Configuration for Conductor system.
    Supports role-based model selection.
    """
    # Database
    db_path: str = ".conductor/conductor.db"
    
    # Execution limits
    max_consecutive_failures: int = 5
    max_iterations: int = 100
    step_timeout_seconds: int = 300
    
    # Model configuration per role
    planner_model: ModelConfig = field(default_factory=lambda: ModelConfig(
        model_name="models/gemini-2.5-flash",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        temperature=0.3,  # Lower for more deterministic planning
    ))
    
    executor_model: ModelConfig = field(default_factory=lambda: ModelConfig(
        model_name="models/gemini-2.5-flash",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        temperature=0.7,
    ))
    
    reviewer_model: ModelConfig = field(default_factory=lambda: ModelConfig(
        model_name="models/gemini-2.5-flash",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        temperature=0.1,  # Very deterministic for review
    ))
    
    # Sandbox settings
    sandbox_enabled: bool = False  # Enable for production
    sandbox_memory_limit_mb: int = 512
    sandbox_cpu_limit: float = 1.0
    
    # Logging
    verbose: bool = True
    log_file: Optional[str] = ".conductor/conductor.log"
    
    # ─────────────────────────────────────────────────────────────
    # HANDOFF CONFIGURATION
    # ─────────────────────────────────────────────────────────────
    
    # Execution mode: "files" = File-Based Handoff, "llm" = direct LLM API
    handoff_mode: HandoffMode = "llm"  # Default to LLM for backward compatibility
    
    # Handoff settings (used when handoff_mode = "files")
    handoff_poll_interval_seconds: float = 2.0
    handoff_max_retries: int = 3
    handoff_max_diff_lines: int = 500
    handoff_timeout_buffer_seconds: int = 60  # Extra time before task expires
    
    def get_model_for_role(self, role: str) -> ModelConfig:
        """Get model configuration for a role."""
        return {
            "planner": self.planner_model,
            "executor": self.executor_model,
            "reviewer": self.reviewer_model,
        }.get(role, self.executor_model)


def load_config_from_env() -> ConductorConfig:
    """Load configuration from environment variables."""
    config = ConductorConfig()
    
    # Override from env
    if os.environ.get("CONDUCTOR_DB_PATH"):
        config.db_path = os.environ["CONDUCTOR_DB_PATH"]
    
    if os.environ.get("CONDUCTOR_MAX_FAILURES"):
        config.max_consecutive_failures = int(os.environ["CONDUCTOR_MAX_FAILURES"])
    
    if os.environ.get("CONDUCTOR_VERBOSE"):
        config.verbose = os.environ["CONDUCTOR_VERBOSE"].lower() == "true"
    
    return config
