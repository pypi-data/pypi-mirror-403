"""
Exploration Engine for Conductor.
Manages forked execution paths and winner selection.
"""
import uuid
from typing import Optional
from dataclasses import dataclass

from conductor.db.models import Plan, Step, PlanStatus, StepStatus


@dataclass
class ForkResult:
    """Result of fork comparison."""
    winner_plan_id: str
    winner_score: float
    pruned_plan_ids: list[str]
    comparison_criteria: dict


class ExplorationEngine:
    """
    Manages exploratory/speculative orchestration.
    
    Capabilities:
    - Fork plans into alternative strategies
    - Execute forks in parallel
    - Score and compare outcomes
    - Select winner and prune losers
    """
    
    def __init__(self, repository):
        self.repository = repository
    
    def fork_plan(
        self,
        parent_plan: Plan,
        strategies: list[str],
        fork_reason: str = "Explore alternatives"
    ) -> list[Plan]:
        """
        Fork a plan into multiple alternative versions.
        
        Each fork uses a different strategy.
        """
        forks = []
        
        for strategy in strategies:
            fork_id = f"{parent_plan.id}_fork_{uuid.uuid4().hex[:6]}"
            
            fork = Plan(
                id=fork_id,
                goal=parent_plan.goal,
                parent_plan_id=parent_plan.id,
                fork_reason=fork_reason,
                strategy=strategy,
                status=PlanStatus.EXPLORING,
            )
            
            self.repository.create_plan(fork)
            forks.append(fork)
        
        # Mark parent as exploring
        parent_plan.status = PlanStatus.EXPLORING
        self.repository.update_plan(parent_plan)
        
        return forks
    
    def get_forks(self, parent_plan_id: str) -> list[Plan]:
        """Get all forks of a plan."""
        return self.repository.get_forks(parent_plan_id)
    
    def score_plan(self, plan: Plan) -> float:
        """
        Calculate score for a completed plan.
        
        Scoring criteria:
        - Steps completed successfully
        - Average confidence
        - Verification rate
        - Time to completion
        - Retry count
        """
        steps = self.repository.get_steps(plan.id)
        
        if not steps:
            return 0.0
        
        # Calculate metrics
        completed = sum(1 for s in steps if s.status == StepStatus.COMPLETED)
        total = len(steps)
        completion_rate = completed / total if total > 0 else 0
        
        avg_confidence = sum(s.confidence for s in steps) / len(steps) if steps else 0
        verified_rate = sum(1 for s in steps if s.verified) / len(steps) if steps else 0
        
        total_attempts = sum(s.attempt for s in steps)
        retry_penalty = 1.0 / (1 + total_attempts * 0.1)
        
        # Composite score
        score = (
            completion_rate * 0.4 +
            avg_confidence * 0.25 +
            verified_rate * 0.25 +
            retry_penalty * 0.1
        )
        
        # Update plan score
        plan.score = score
        self.repository.update_plan(plan)
        
        return score
    
    def compare_forks(self, parent_plan_id: str) -> Optional[ForkResult]:
        """
        Compare all forks and select winner.
        
        Only compares when all forks have completed or failed.
        """
        forks = self.get_forks(parent_plan_id)
        
        if not forks:
            return None
        
        # Check if all forks are done
        active_forks = [
            f for f in forks
            if f.status in (PlanStatus.EXPLORING, PlanStatus.EXECUTING)
        ]
        
        if active_forks:
            return None  # Still running
        
        # Score completed forks
        scored = []
        for fork in forks:
            if fork.status in (PlanStatus.COMPLETED, PlanStatus.FAILED):
                score = self.score_plan(fork)
                scored.append((fork, score))
        
        if not scored:
            return None
        
        # Sort by score (highest first)
        scored.sort(key=lambda x: -x[1])
        
        winner, winner_score = scored[0]
        losers = [f for f, _ in scored[1:]]
        
        # Mark winner
        winner.status = PlanStatus.WINNER
        self.repository.update_plan(winner)
        
        # Prune losers
        pruned_ids = []
        for loser in losers:
            loser.status = PlanStatus.PRUNED
            self.repository.update_plan(loser)
            pruned_ids.append(loser.id)
        
        return ForkResult(
            winner_plan_id=winner.id,
            winner_score=winner_score,
            pruned_plan_ids=pruned_ids,
            comparison_criteria={
                "completion_weight": 0.4,
                "confidence_weight": 0.25,
                "verification_weight": 0.25,
                "retry_penalty_weight": 0.1,
            }
        )
    
    def suggest_strategies(self, goal: str, memory_store=None) -> list[str]:
        """
        Suggest alternative strategies for a goal.
        
        Uses memory to inform suggestions.
        """
        strategies = ["default"]
        
        if memory_store:
            context = memory_store.get_planner_context(goal)
            
            # Add recommended strategy
            if context.get("recommended_strategy"):
                strategies.insert(0, context["recommended_strategy"])
            
            # Add alternative strategies from patterns
            for pattern in context.get("recalled_patterns", [])[:2]:
                if pattern.get("strategy") and pattern["strategy"] not in strategies:
                    strategies.append(pattern["strategy"])
            
            # Remove strategies to avoid
            for avoid in context.get("avoid_strategies", []):
                if avoid in strategies:
                    strategies.remove(avoid)
        
        # Ensure we have at least 2 strategies for exploration
        if len(strategies) < 2:
            strategies.append("alternative")
        
        return strategies[:3]  # Max 3 forks
    
    def is_exploring(self, plan_id: str) -> bool:
        """Check if a plan has active forks."""
        forks = self.get_forks(plan_id)
        return any(f.status in (PlanStatus.EXPLORING, PlanStatus.EXECUTING) for f in forks)
