"""
Database models for Conductor.
Includes exploratory execution, memory, and policies.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum
import json


# ═══════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════

class PlanStatus(str, Enum):
    EXPLORING = "exploring"    # Generating alternatives
    EXECUTING = "executing"    # Running steps
    COMPLETED = "completed"
    FAILED = "failed"
    HALTED = "halted"
    PRUNED = "pruned"          # Lost in fork competition
    WINNER = "winner"          # Won fork competition


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    HALTED = "halted"
    NEEDS_REVIEW = "needs_review"
    NEEDS_VERIFICATION = "needs_verification"
    SKIPPED = "skipped"


class AgentRole(str, Enum):
    PLANNER = "planner"
    EXECUTOR = "executor"
    REVIEWER = "reviewer"
    VERIFIER = "verifier"
    REPAIR = "repair"


class EventType(str, Enum):
    # Plan events
    PLAN_CREATED = "plan_created"
    PLAN_FORKED = "plan_forked"
    PLAN_COMPLETED = "plan_completed"
    PLAN_HALTED = "plan_halted"
    PLAN_RESUMED = "plan_resumed"
    PLAN_PRUNED = "plan_pruned"
    PLAN_WON = "plan_won"
    # Step events
    STEP_STARTED = "step_started"
    STEP_COMPLETED = "step_completed"
    STEP_FAILED = "step_failed"
    STEP_RETRIED = "step_retried"
    STEP_VERIFIED = "step_verified"
    STEP_REPAIRED = "step_repaired"
    # Agent events
    AGENT_INVOKED = "agent_invoked"
    AGENT_RESULT = "agent_result"
    # Policy events
    POLICY_EVALUATED = "policy_evaluated"
    POLICY_DENIED = "policy_denied"
    # Memory events
    MEMORY_RECALLED = "memory_recalled"
    MEMORY_STORED = "memory_stored"
    # MCP events
    MCP_CALL = "mcp_call"


class PolicyType(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"
    REQUIRE_VERIFICATION = "require_verification"


class PatternType(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    STRATEGY = "strategy"
    POLICY_OVERRIDE = "policy_override"


class RepairType(str, Enum):
    STEP_MODIFICATION = "step_modification"
    PLAN_MUTATION = "plan_mutation"
    STRATEGY_SWITCH = "strategy_switch"
    MODEL_SWITCH = "model_switch"


# ═══════════════════════════════════════════════════════════════
# CORE MODELS
# ═══════════════════════════════════════════════════════════════

@dataclass
class Plan:
    """Execution plan with fork support."""
    id: str
    goal: str
    status: PlanStatus = PlanStatus.EXPLORING
    parent_plan_id: Optional[str] = None
    fork_reason: Optional[str] = None
    strategy: Optional[str] = None
    score: Optional[float] = None
    halt_reason: Optional[str] = None
    consecutive_failures: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def is_fork(self) -> bool:
        return self.parent_plan_id is not None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "goal": self.goal,
            "status": self.status.value,
            "parent_plan_id": self.parent_plan_id,
            "strategy": self.strategy,
            "score": self.score,
        }


@dataclass
class Step:
    """Step with confidence and verification."""
    step_key: str
    plan_id: str
    sequence: int
    description: str
    agent: str
    status: StepStatus = StepStatus.PENDING
    confidence: float = 0.0
    verified: bool = False
    depends_on: list[str] = field(default_factory=list)
    attempt: int = 0
    max_retries: int = 3
    strategy: Optional[str] = None
    output: Optional[str] = None
    artifacts: list[str] = field(default_factory=list)
    mcp_used: list[str] = field(default_factory=list)
    last_error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    id: Optional[int] = None
    
    def can_retry(self) -> bool:
        return self.status == StepStatus.FAILED and self.attempt < self.max_retries
    
    def needs_verification(self) -> bool:
        return self.status == StepStatus.NEEDS_VERIFICATION or (
            self.status == StepStatus.COMPLETED and not self.verified
        )


@dataclass
class Event:
    """Enhanced event for replay support."""
    event_type: EventType
    plan_id: Optional[str] = None
    step_key: Optional[str] = None
    agent: Optional[str] = None
    payload: Optional[dict] = None
    state_snapshot: Optional[dict] = None
    created_at: Optional[datetime] = None
    id: Optional[int] = None


# ═══════════════════════════════════════════════════════════════
# MEMORY MODELS
# ═══════════════════════════════════════════════════════════════

@dataclass
class MemoryPattern:
    """Learned pattern for reuse."""
    pattern_type: PatternType
    goal_signature: str
    pattern_data: dict
    success_count: int = 1
    failure_count: int = 0
    last_used_at: Optional[datetime] = None
    id: Optional[int] = None
    
    def effectiveness(self) -> float:
        """Calculate pattern effectiveness score."""
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.5
        return self.success_count / total


@dataclass
class MemoryFailure:
    """Failure mode to avoid."""
    error_signature: str
    context_signature: Optional[str] = None
    avoidance_strategy: Optional[str] = None
    occurrence_count: int = 1
    last_seen_at: Optional[datetime] = None
    id: Optional[int] = None


@dataclass
class ModelMetrics:
    """Model performance tracking."""
    model_name: str
    role: str
    success_count: int = 0
    failure_count: int = 0
    avg_latency_ms: float = 0.0
    avg_confidence: float = 0.0
    last_failure_at: Optional[datetime] = None
    id: Optional[int] = None
    
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        if total == 0:
            return 1.0
        return self.success_count / total
    
    def score(self) -> float:
        """Composite score for model selection."""
        return (
            self.success_rate() * 0.5 +
            min(self.avg_confidence, 1.0) * 0.3 +
            (1.0 - min(self.avg_latency_ms / 10000, 1.0)) * 0.2
        )


# ═══════════════════════════════════════════════════════════════
# POLICY MODELS
# ═══════════════════════════════════════════════════════════════

@dataclass
class Policy:
    """Governance policy definition."""
    name: str
    policy_type: PolicyType
    scope: str  # 'mcp', 'step', 'plan', 'global'
    condition: dict  # JSON condition
    action: Optional[str] = None
    priority: int = 50
    enabled: bool = True
    id: Optional[int] = None
    
    def matches(self, context: dict) -> bool:
        """Evaluate if policy matches context."""
        for key, value in self.condition.items():
            if key not in context:
                return False
            if isinstance(value, list):
                if context[key] not in value:
                    return False
            elif context[key] != value:
                return False
        return True


@dataclass
class PolicyEvaluation:
    """Policy evaluation result."""
    policy_id: int
    step_key: Optional[str]
    plan_id: Optional[str]
    result: str  # 'allowed', 'denied', 'approval_required', 'verification_required'
    context: Optional[dict] = None
    id: Optional[int] = None


# ═══════════════════════════════════════════════════════════════
# REPAIR MODELS
# ═══════════════════════════════════════════════════════════════

@dataclass
class Repair:
    """Self-repair action record."""
    plan_id: str
    failure_pattern: str
    repair_action: str
    repair_type: RepairType
    step_key: Optional[str] = None
    success: Optional[bool] = None
    id: Optional[int] = None


@dataclass
class MCPCall:
    """MCP call with verification."""
    mcp_server: str
    action: str
    step_key: Optional[str] = None
    request: Optional[dict] = None
    response: Optional[dict] = None
    success: bool = True
    verified: bool = False
    evidence: Optional[str] = None
    duration_ms: Optional[int] = None
    id: Optional[int] = None
