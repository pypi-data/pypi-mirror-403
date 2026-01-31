"""
Long-term Memory Store for Conductor.
Persists patterns, failures, and strategies across plans.
"""
import hashlib
import json
from datetime import datetime
from typing import Optional

from conductor.db.models import MemoryPattern, MemoryFailure, ModelMetrics, PatternType


class MemoryStore:
    """
    Long-term memory that persists beyond single plans.
    Influences Planner behavior and strategy selection.
    """
    
    def __init__(self, repository):
        self.repository = repository
    
    # ─────────────────────────────────────────────────────────────
    # GOAL SIGNATURES
    # ─────────────────────────────────────────────────────────────
    
    def _goal_signature(self, goal: str) -> str:
        """Create normalized signature for goal matching."""
        # Normalize: lowercase, strip, remove punctuation
        normalized = goal.lower().strip()
        normalized = "".join(c for c in normalized if c.isalnum() or c.isspace())
        normalized = " ".join(normalized.split())
        
        # Extract key terms (simple approach)
        terms = sorted(set(normalized.split()))
        signature = " ".join(terms[:10])  # Top 10 terms
        
        return hashlib.md5(signature.encode()).hexdigest()[:16]
    
    def _error_signature(self, error: str) -> str:
        """Create normalized signature for error matching."""
        # Remove variable parts (line numbers, paths, etc.)
        normalized = error.lower().strip()
        # Remove file paths
        normalized = " ".join(
            word for word in normalized.split()
            if not ("/" in word or "\\" in word)
        )
        # Remove numbers
        normalized = "".join(c if not c.isdigit() else "#" for c in normalized)
        
        return hashlib.md5(normalized.encode()).hexdigest()[:16]
    
    # ─────────────────────────────────────────────────────────────
    # PATTERN STORAGE
    # ─────────────────────────────────────────────────────────────
    
    def store_success(self, goal: str, steps: list[dict], strategy: str = None):
        """Store a successful execution pattern."""
        signature = self._goal_signature(goal)
        
        pattern = MemoryPattern(
            pattern_type=PatternType.SUCCESS,
            goal_signature=signature,
            pattern_data={
                "goal": goal,
                "steps": steps,
                "strategy": strategy,
            },
            last_used_at=datetime.now()
        )
        
        self.repository.store_memory_pattern(pattern)
    
    def store_failure(self, error: str, context: str = None, avoidance: str = None):
        """Store a failure mode to avoid."""
        signature = self._error_signature(error)
        
        failure = MemoryFailure(
            error_signature=signature,
            context_signature=self._goal_signature(context) if context else None,
            avoidance_strategy=avoidance,
            last_seen_at=datetime.now()
        )
        
        self.repository.store_memory_failure(failure)
    
    def store_strategy(self, goal: str, strategy: str, success: bool):
        """Store strategy outcome for a goal type."""
        signature = self._goal_signature(goal)
        
        pattern = MemoryPattern(
            pattern_type=PatternType.STRATEGY,
            goal_signature=signature,
            pattern_data={
                "strategy": strategy,
                "success": success,
            },
            success_count=1 if success else 0,
            failure_count=0 if success else 1,
        )
        
        self.repository.store_memory_pattern(pattern)
    
    # ─────────────────────────────────────────────────────────────
    # PATTERN RECALL
    # ─────────────────────────────────────────────────────────────
    
    def recall_patterns(self, goal: str, limit: int = 5) -> list[MemoryPattern]:
        """Recall relevant patterns for a goal."""
        signature = self._goal_signature(goal)
        return self.repository.recall_memory_patterns(signature, limit)
    
    def recall_failures(self, error: str) -> list[MemoryFailure]:
        """Recall similar failure modes."""
        signature = self._error_signature(error)
        return self.repository.recall_memory_failures(signature)
    
    def get_best_strategy(self, goal: str) -> Optional[str]:
        """Get the most successful strategy for a goal type."""
        patterns = self.recall_patterns(goal)
        
        strategy_scores = {}
        for pattern in patterns:
            if pattern.pattern_type == PatternType.STRATEGY:
                strategy = pattern.pattern_data.get("strategy")
                if strategy:
                    score = pattern.effectiveness()
                    if strategy not in strategy_scores or score > strategy_scores[strategy]:
                        strategy_scores[strategy] = score
        
        if strategy_scores:
            return max(strategy_scores.items(), key=lambda x: x[1])[0]
        
        return None
    
    def should_avoid(self, error: str) -> Optional[str]:
        """Check if this error pattern should be avoided and return avoidance strategy."""
        failures = self.recall_failures(error)
        
        for failure in failures:
            if failure.occurrence_count >= 3 and failure.avoidance_strategy:
                return failure.avoidance_strategy
        
        return None
    
    # ─────────────────────────────────────────────────────────────
    # MODEL METRICS
    # ─────────────────────────────────────────────────────────────
    
    def update_model_metrics(
        self,
        model_name: str,
        role: str,
        success: bool,
        latency_ms: float = 0,
        confidence: float = 0.5
    ):
        """Update model performance metrics."""
        self.repository.update_model_metrics(
            model_name, role, success, latency_ms, confidence
        )
    
    def get_best_model(self, role: str) -> Optional[str]:
        """Get the best-performing model for a role."""
        metrics = self.repository.get_model_metrics_for_role(role)
        
        if not metrics:
            return None
        
        # Score and sort
        scored = [(m, m.score()) for m in metrics]
        scored.sort(key=lambda x: -x[1])
        
        return scored[0][0].model_name if scored else None
    
    # ─────────────────────────────────────────────────────────────
    # PLANNER CONTEXT
    # ─────────────────────────────────────────────────────────────
    
    def get_planner_context(self, goal: str) -> dict:
        """Get memory-based context for the Planner."""
        context = {
            "recalled_patterns": [],
            "known_failures": [],
            "recommended_strategy": None,
            "avoid_strategies": [],
        }
        
        # Recall successful patterns
        patterns = self.recall_patterns(goal)
        for pattern in patterns:
            if pattern.pattern_type == PatternType.SUCCESS and pattern.effectiveness() > 0.7:
                context["recalled_patterns"].append({
                    "steps": pattern.pattern_data.get("steps", []),
                    "strategy": pattern.pattern_data.get("strategy"),
                    "effectiveness": pattern.effectiveness(),
                })
        
        # Get strategy recommendation
        context["recommended_strategy"] = self.get_best_strategy(goal)
        
        # Get strategies to avoid
        for pattern in patterns:
            if pattern.pattern_type == PatternType.STRATEGY and pattern.effectiveness() < 0.3:
                context["avoid_strategies"].append(pattern.pattern_data.get("strategy"))
        
        return context
