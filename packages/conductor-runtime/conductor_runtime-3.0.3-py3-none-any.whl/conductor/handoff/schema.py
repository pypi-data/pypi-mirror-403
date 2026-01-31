"""
File-Based Handoff - Schema Definitions.

Defines the contract between Conductor (orchestrator) and Antigravity (executor).
All communication happens via these file structures.
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from enum import Enum


# ─────────────────────────────────────────────────────────────
# CONTRACT VERSION
# ─────────────────────────────────────────────────────────────

CONTRACT_VERSION = "1.0.0"


# ─────────────────────────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────────────────────────

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    FAILED = "failed"
    PARTIAL = "partial"
    BLOCKED = "blocked"
    EXPIRED = "expired"


class HandoffMode(str, Enum):
    FILES = "files"      # File-Based Handoff to Antigravity
    LLM = "llm"          # Direct LLM execution via API


# ─────────────────────────────────────────────────────────────
# TASK FILE SCHEMA
# ─────────────────────────────────────────────────────────────

class TaskFile(BaseModel):
    """
    Task file written by Conductor for Antigravity to execute.
    
    Location: .conductor/handoff/plan_<id>/fork_<id>/pending/<task_id>.task.json
    """
    
    # Metadata
    contract_version: str = Field(default=CONTRACT_VERSION)
    task_id: str = Field(..., description="Unique task identifier")
    plan_id: str = Field(..., description="Parent plan ID")
    fork_id: str = Field(..., description="Fork ID for parallel strategies")
    
    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(..., description="Task becomes invalid after this time")
    timeout_seconds: int = Field(default=300, description="Max execution time")
    
    # Instruction
    instruction: str = Field(..., description="What to do (single step, no planning)")
    
    # File Scope
    allowed_files: list[str] = Field(
        default_factory=list,
        description="Whitelist of files that MAY be modified. Empty = no restrictions."
    )
    
    # Constraints (HARD - must not violate)
    constraints: list[str] = Field(
        default_factory=lambda: [
            "Do NOT modify files outside allowed_files",
            "Do NOT run shell commands unless explicitly instructed",
            "Do NOT access external URLs",
            "Do NOT plan next steps - execute ONLY this task",
        ]
    )
    
    # Rules (SOFT - preferences)
    rules: list[str] = Field(
        default_factory=lambda: [
            "Prefer minimal changes",
            "Follow existing code style",
            "Add comments for complex logic",
        ]
    )
    
    # Context
    context: dict = Field(
        default_factory=dict,
        description="Additional context (project type, patterns, etc.)"
    )
    
    # Expected Output
    expected_output: Optional[str] = Field(
        default=None,
        description="What success looks like (for verification)"
    )
    
    # Safety Limits
    max_diff_lines: int = Field(
        default=500,
        description="Maximum lines of diff allowed"
    )
    
    # Integrity
    checksum: Optional[str] = Field(
        default=None,
        description="MD5 hash of instruction field for integrity validation"
    )
    
    # Pre-execution confidence (computed by adapter)
    confidence: Optional[dict] = Field(
        default=None,
        description="Pre-execution confidence score and factors"
    )
    
    def compute_checksum(self) -> str:
        """Compute checksum of instruction for integrity validation."""
        import hashlib
        return hashlib.md5(self.instruction.encode()).hexdigest()


# ─────────────────────────────────────────────────────────────
# RESULT FILE SCHEMA
# ─────────────────────────────────────────────────────────────

class FileChange(BaseModel):
    """Record of a single file change."""
    path: str
    action: Literal["created", "modified", "deleted"]
    lines_added: int = 0
    lines_removed: int = 0


class ResultFile(BaseModel):
    """
    Result file written by Antigravity after execution.
    
    Location: .conductor/handoff/plan_<id>/fork_<id>/completed/<task_id>.result.json
    """
    
    # Metadata
    contract_version: str = Field(default=CONTRACT_VERSION)
    task_id: str = Field(..., description="Matching task ID")
    
    # Status
    status: TaskStatus = Field(..., description="Execution outcome")
    
    # Timing
    completed_at: datetime = Field(default_factory=datetime.utcnow)
    execution_time_ms: int = Field(default=0)
    
    # Changes
    files_changed: list[FileChange] = Field(default_factory=list)
    total_lines_added: int = Field(default=0)
    total_lines_removed: int = Field(default=0)
    
    # Output
    summary: str = Field(default="", description="Brief description of what was done")
    
    # Error (if failed)
    error: Optional[str] = Field(default=None)
    attempted_actions: list[str] = Field(default_factory=list)
    suggestion: Optional[str] = Field(default=None)
    
    # Notes
    notes: Optional[str] = Field(default=None)


# ─────────────────────────────────────────────────────────────
# FAILURE PATTERN (for learning)
# ─────────────────────────────────────────────────────────────

class FailurePattern(BaseModel):
    """
    Lightweight failure record for future planning awareness.
    
    Location: .conductor/handoff/plan_<id>/fork_<id>/audit.log (append-only)
    """
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    task_id: str
    task_type: str = Field(default="unknown", description="e.g., 'create_file', 'refactor'")
    failure_reason: str
    retry_count: int = Field(default=0)
    resolution: Literal["repaired", "escalated", "abandoned"] = Field(default="abandoned")


# ─────────────────────────────────────────────────────────────
# HANDOFF METRICS (observability)
# ─────────────────────────────────────────────────────────────

class HandoffMetrics(BaseModel):
    """
    Lightweight metrics counter for handoff observability.
    
    Location: .conductor/handoff/metrics.json
    """
    
    # Counters
    tasks_created: int = Field(default=0)
    tasks_completed: int = Field(default=0)
    tasks_failed: int = Field(default=0)
    tasks_timeout: int = Field(default=0)
    tasks_expired: int = Field(default=0)
    
    # Timing
    total_execution_time_ms: int = Field(default=0)
    avg_execution_time_ms: float = Field(default=0.0)
    
    # Last update
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    def record_created(self) -> None:
        self.tasks_created += 1
        self.last_updated = datetime.utcnow()
    
    def record_completed(self, execution_time_ms: int) -> None:
        self.tasks_completed += 1
        self.total_execution_time_ms += execution_time_ms
        if self.tasks_completed > 0:
            self.avg_execution_time_ms = self.total_execution_time_ms / self.tasks_completed
        self.last_updated = datetime.utcnow()
    
    def record_failed(self) -> None:
        self.tasks_failed += 1
        self.last_updated = datetime.utcnow()
    
    def record_timeout(self) -> None:
        self.tasks_timeout += 1
        self.last_updated = datetime.utcnow()
    
    @property
    def success_rate(self) -> float:
        total = self.tasks_completed + self.tasks_failed + self.tasks_timeout
        if total == 0:
            return 0.0
        return self.tasks_completed / total

# ─────────────────────────────────────────────────────────────
# PROVENANCE RECORD (audit/trust)
# ─────────────────────────────────────────────────────────────

class ProvenanceRecord(BaseModel):
    """
    Cryptographic provenance chain for audit compliance.
    
    Records integrity hashes and execution context for every task.
    Location: .conductor/handoff/plan_<id>/fork_<id>/completed/<task_id>.provenance.json
    """
    
    # Identity
    task_id: str
    plan_id: str
    fork_id: str
    
    # Input integrity
    task_hash: str = Field(description="SHA-256 of task.json content")
    constraint_hash: str = Field(description="SHA-256 of constraints list")
    
    # Execution context
    executor: Literal["antigravity", "llm"] = Field(default="antigravity")
    started_at: Optional[datetime] = None
    completed_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Output integrity
    result_hash: str = Field(description="SHA-256 of result.json content")
    
    # Chain (for multi-step plans)
    previous_hash: Optional[str] = Field(
        default=None,
        description="Hash of previous provenance record (for chaining)"
    )
    
    # Metadata
    contract_version: str = Field(default=CONTRACT_VERSION)
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ─────────────────────────────────────────────────────────────
# CONFIDENCE SCORE (pre-execution trust calibration)
# ─────────────────────────────────────────────────────────────

class ConfidenceLevel(str, Enum):
    HIGH = "high"      # 0.8-1.0: Fully autonomous
    MEDIUM = "medium"  # 0.5-0.8: Proceed cautiously
    LOW = "low"        # 0-0.5: Human review recommended


class ConfidenceScore(BaseModel):
    """
    Pre-execution confidence score for a task.
    
    Helps calibrate trust before running a task.
    """
    
    # Score
    score: float = Field(ge=0.0, le=1.0, description="Confidence score 0.0-1.0")
    level: ConfidenceLevel = Field(description="Confidence level category")
    
    # Breakdown
    factors: dict = Field(
        default_factory=dict,
        description="Breakdown of score components"
    )
    
    # Context
    computed_at: datetime = Field(default_factory=datetime.utcnow)
    
    @classmethod
    def from_score(cls, score: float, factors: dict = None) -> "ConfidenceScore":
        """Create a ConfidenceScore from a raw score value."""
        if score >= 0.8:
            level = ConfidenceLevel.HIGH
        elif score >= 0.5:
            level = ConfidenceLevel.MEDIUM
        else:
            level = ConfidenceLevel.LOW
        
        return cls(score=score, level=level, factors=factors or {})


# ─────────────────────────────────────────────────────────────
# EXAMPLE TASK FILE
# ─────────────────────────────────────────────────────────────

EXAMPLE_TASK = """
{
  "contract_version": "1.0.0",
  "task_id": "step_001",
  "plan_id": "plan_abc123",
  "fork_id": "fork_default",
  "created_at": "2026-01-28T14:00:00Z",
  "expires_at": "2026-01-28T14:10:00Z",
  "timeout_seconds": 300,
  
  "instruction": "Create a Python function that validates email addresses using regex. Add it to src/utils/validators.py",
  
  "allowed_files": [
    "src/utils/validators.py"
  ],
  
  "constraints": [
    "Do NOT modify files outside allowed_files",
    "Do NOT run shell commands",
    "Do NOT plan next steps"
  ],
  
  "rules": [
    "Follow existing code style in validators.py",
    "Use re.match, not re.search"
  ],
  
  "context": {
    "project_type": "python",
    "python_version": "3.11"
  },
  
  "expected_output": "Function named validate_email(s: str) -> bool",
  "max_diff_lines": 50
}
"""

# ─────────────────────────────────────────────────────────────
# EXAMPLE RESULT FILE
# ─────────────────────────────────────────────────────────────

EXAMPLE_RESULT = """
{
  "contract_version": "1.0.0",
  "task_id": "step_001",
  "status": "done",
  "completed_at": "2026-01-28T14:02:15Z",
  "execution_time_ms": 12500,
  
  "files_changed": [
    {
      "path": "src/utils/validators.py",
      "action": "modified",
      "lines_added": 15,
      "lines_removed": 0
    }
  ],
  
  "total_lines_added": 15,
  "total_lines_removed": 0,
  
  "summary": "Added validate_email function with RFC 5322 simplified regex pattern",
  
  "error": null,
  "notes": "Used re.match for anchored matching"
}
"""
