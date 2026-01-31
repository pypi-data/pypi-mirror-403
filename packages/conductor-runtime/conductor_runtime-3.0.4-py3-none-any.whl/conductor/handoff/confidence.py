"""
Confidence Scoring for Conductor Handoff.

Computes pre-execution confidence scores based on:
- Historical success rate
- Constraint coverage
- Task complexity indicators
"""
from typing import Optional

from conductor.handoff.schema import (
    TaskFile,
    HandoffMetrics,
    ConfidenceScore,
    ConfidenceLevel,
)


# ─────────────────────────────────────────────────────────────
# WEIGHTS
# ─────────────────────────────────────────────────────────────

WEIGHT_HISTORICAL = 0.40   # Historical success rate
WEIGHT_CONSTRAINTS = 0.30  # Constraint coverage
WEIGHT_COMPLEXITY = 0.20   # Task complexity (inverse)
WEIGHT_NOVELTY = 0.10      # Novelty penalty


# ─────────────────────────────────────────────────────────────
# SCORING FUNCTIONS
# ─────────────────────────────────────────────────────────────

def compute_historical_factor(metrics: HandoffMetrics) -> float:
    """
    Compute historical success factor.
    
    Returns 1.0 if no history (benefit of the doubt),
    otherwise returns success rate.
    """
    total = metrics.tasks_completed + metrics.tasks_failed + metrics.tasks_timeout
    
    if total == 0:
        # No history = neutral confidence
        return 0.7
    
    if total < 3:
        # Not enough data = conservative
        return 0.5 + (metrics.success_rate * 0.3)
    
    return metrics.success_rate


def compute_constraint_factor(task: TaskFile) -> float:
    """
    Compute constraint coverage factor.
    
    More explicit constraints = higher confidence (more guardrails).
    """
    num_constraints = len(task.constraints)
    num_rules = len(task.rules)
    
    # Base score for having any constraints
    if num_constraints == 0:
        return 0.5  # No constraints = medium risk
    
    # More constraints = more confidence (up to a point)
    constraint_score = min(1.0, 0.6 + (num_constraints * 0.1))
    
    # Rules add slight bonus
    rule_bonus = min(0.1, num_rules * 0.03)
    
    return min(1.0, constraint_score + rule_bonus)


def compute_complexity_factor(task: TaskFile) -> float:
    """
    Compute inverse complexity factor.
    
    Simpler tasks = higher confidence.
    """
    instruction_length = len(task.instruction)
    
    # Very short instructions might be unclear
    if instruction_length < 20:
        return 0.6
    
    # Moderate length = optimal
    if instruction_length < 200:
        return 0.9
    
    # Long instructions = more complex
    if instruction_length < 500:
        return 0.7
    
    # Very long = high complexity
    return 0.5


def compute_novelty_factor(task: TaskFile, metrics: HandoffMetrics) -> float:
    """
    Compute novelty penalty.
    
    New task patterns get lower confidence until proven.
    """
    # If we have good history, reduce novelty penalty
    if metrics.tasks_completed >= 5 and metrics.success_rate >= 0.8:
        return 0.9  # Proven track record
    
    if metrics.tasks_completed >= 3:
        return 0.7  # Some experience
    
    return 0.5  # Novel territory


def compute_confidence(
    task: TaskFile,
    metrics: Optional[HandoffMetrics] = None,
) -> ConfidenceScore:
    """
    Compute pre-execution confidence score for a task.
    
    Args:
        task: The task to score
        metrics: Historical execution metrics (optional)
    
    Returns:
        ConfidenceScore with score, level, and factor breakdown
    """
    metrics = metrics or HandoffMetrics()
    
    # Compute individual factors
    historical = compute_historical_factor(metrics)
    constraints = compute_constraint_factor(task)
    complexity = compute_complexity_factor(task)
    novelty = compute_novelty_factor(task, metrics)
    
    # Weighted sum
    score = (
        WEIGHT_HISTORICAL * historical +
        WEIGHT_CONSTRAINTS * constraints +
        WEIGHT_COMPLEXITY * complexity +
        WEIGHT_NOVELTY * novelty
    )
    
    # Clamp to valid range
    score = max(0.0, min(1.0, score))
    
    # Build factors breakdown
    factors = {
        "historical_success": round(historical, 3),
        "constraint_coverage": round(constraints, 3),
        "complexity_inverse": round(complexity, 3),
        "novelty_factor": round(novelty, 3),
        "weights": {
            "historical": WEIGHT_HISTORICAL,
            "constraints": WEIGHT_CONSTRAINTS,
            "complexity": WEIGHT_COMPLEXITY,
            "novelty": WEIGHT_NOVELTY,
        },
        "metrics_summary": {
            "tasks_completed": metrics.tasks_completed,
            "tasks_failed": metrics.tasks_failed,
            "success_rate": round(metrics.success_rate, 3),
        }
    }
    
    return ConfidenceScore.from_score(score, factors)
