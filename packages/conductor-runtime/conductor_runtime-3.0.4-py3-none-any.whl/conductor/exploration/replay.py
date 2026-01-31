"""
Replay Engine for Conductor.
Time-travel debugging and simulation.
"""
from typing import Optional
from datetime import datetime

from conductor.db.models import Plan, Step, Event, StepStatus, PlanStatus


class ReplayEngine:
    """
    Enables replay, time-travel, and simulation.
    
    Uses the event log to reconstruct state at any point.
    """
    
    def __init__(self, repository):
        self.repository = repository
    
    def get_state_at(self, plan_id: str, timestamp: datetime) -> dict:
        """
        Reconstruct state at a specific timestamp.
        
        Replays events up to timestamp.
        """
        events = self.repository.get_events_before(plan_id, timestamp)
        
        # Reconstruct state from events
        state = {
            "plan": None,
            "steps": {},
            "completed": [],
            "failed": [],
        }
        
        for event in events:
            if event.event_type.value == "plan_created":
                state["plan"] = event.payload
            elif event.event_type.value == "step_completed":
                if event.step_key:
                    state["steps"][event.step_key] = "completed"
                    state["completed"].append(event.step_key)
            elif event.event_type.value == "step_failed":
                if event.step_key:
                    state["steps"][event.step_key] = "failed"
                    state["failed"].append(event.step_key)
        
        return state
    
    def get_state_at_step(self, plan_id: str, step_key: str) -> dict:
        """Reconstruct state just before a specific step."""
        step = self.repository.get_step(step_key)
        if not step or not step.started_at:
            return {}
        
        return self.get_state_at(plan_id, step.started_at)
    
    def replay_to(self, plan_id: str, step_key: str) -> list[Event]:
        """
        Get all events leading up to a step.
        
        Useful for understanding how we got here.
        """
        step = self.repository.get_step(step_key)
        if not step or not step.started_at:
            return []
        
        return self.repository.get_events_before(plan_id, step.started_at)
    
    def simulate(self, plan_id: str, modifications: dict) -> dict:
        """
        Simulate 'what if' scenarios.
        
        modifications: {
            "skip_steps": ["step_1"],
            "force_success": ["step_2"],
            "change_strategy": {"step_3": "alt_strategy"}
        }
        
        Returns projected outcome.
        """
        steps = self.repository.get_steps(plan_id)
        
        # Apply modifications to simulate
        result = {
            "projected_outcome": "completed",
            "steps_affected": [],
            "warnings": [],
        }
        
        skip = set(modifications.get("skip_steps", []))
        force_success = set(modifications.get("force_success", []))
        strategy_changes = modifications.get("change_strategy", {})
        
        for step in steps:
            if step.step_key in skip:
                result["steps_affected"].append({
                    "step": step.step_key,
                    "modification": "skipped",
                })
                # Check dependencies
                for other in steps:
                    if step.step_key in other.depends_on:
                        result["warnings"].append(
                            f"Skipping {step.step_key} breaks dependency for {other.step_key}"
                        )
            
            elif step.step_key in force_success:
                result["steps_affected"].append({
                    "step": step.step_key,
                    "modification": "forced_success",
                })
            
            elif step.step_key in strategy_changes:
                result["steps_affected"].append({
                    "step": step.step_key,
                    "modification": f"strategy changed to {strategy_changes[step.step_key]}",
                })
        
        # Project outcome
        failed_steps = [
            s for s in steps
            if s.status == StepStatus.FAILED and s.step_key not in force_success
        ]
        
        if failed_steps:
            result["projected_outcome"] = "failed"
        
        return result
    
    def explain_failure(self, step_key: str) -> dict:
        """
        Explain why a step failed with full context.
        
        Returns causal chain leading to failure.
        """
        step = self.repository.get_step(step_key)
        if not step:
            return {"error": "Step not found"}
        
        explanation = {
            "step": step_key,
            "description": step.description,
            "error": step.last_error,
            "attempts": step.attempt,
            "causal_chain": [],
            "mcp_calls": [],
            "related_events": [],
        }
        
        # Get MCP calls for this step
        mcp_calls = self.repository.get_mcp_calls_for_step(step_key)
        for call in mcp_calls:
            explanation["mcp_calls"].append({
                "server": call.mcp_server,
                "action": call.action,
                "success": call.success,
            })
        
        # Check if dependency failed
        for dep_key in step.depends_on:
            dep = self.repository.get_step(dep_key)
            if dep and dep.status == StepStatus.FAILED:
                explanation["causal_chain"].append({
                    "step": dep_key,
                    "type": "dependency_failure",
                    "error": dep.last_error,
                })
        
        return explanation
