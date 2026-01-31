"""
Repair Agent for Conductor.
Autonomous self-repair without human intervention.
"""
from typing import Optional, Any

from conductor.agents.base import BaseAgent, AgentResult
from conductor.db.models import Step, Plan, StepStatus, RepairType, Repair


REPAIR_SYSTEM_PROMPT = """You are the Repair Agent in a production orchestration system.

## YOUR ROLE
Analyze recurring failures and apply automatic repairs.
You make the system self-healing.

## REPAIR STRATEGIES
1. STEP_MODIFICATION: Change step description or parameters
2. PLAN_MUTATION: Insert/remove/reorder steps
3. STRATEGY_SWITCH: Try a different approach
4. MODEL_SWITCH: Use a different model

## ANALYSIS PROCESS
1. Examine failure history
2. Identify pattern (same error, same step type, same context)
3. Determine root cause
4. Propose repair action
5. Apply if safe, otherwise escalate

## OUTPUT FORMAT
{
    "repair_type": "step_modification|plan_mutation|strategy_switch|model_switch",
    "diagnosis": "What went wrong",
    "repair_action": "What to change",
    "safe_to_apply": true/false,
    "modified_step": {...} or null,
    "new_steps": [...] or null
}

## SAFETY RULES
- DO NOT apply repairs that could cause data loss
- DO NOT repair without understanding root cause
- DO NOT retry more than 2 times with same repair
- ALWAYS log repair actions
"""


class RepairAgent(BaseAgent):
    """
    Repair Agent - Autonomous self-healing.
    
    Analyzes failure patterns and applies fixes automatically.
    """
    
    def __init__(self, model_client: Any = None, memory_store=None):
        super().__init__(model_client)
        self.memory_store = memory_store
    
    @property
    def name(self) -> str:
        return "repair"
    
    @property
    def system_prompt(self) -> str:
        return REPAIR_SYSTEM_PROMPT
    
    async def run(self, repository, plan: Plan, step: Optional[Step] = None) -> AgentResult:
        """Analyze failures and propose/apply repairs."""
        
        if step is None:
            return AgentResult(success=False, error="No failed step to repair")
        
        # Analyze failure history
        failure_history = self._analyze_failures(repository, plan, step)
        
        if not self.model_client:
            return self._auto_repair(step, failure_history)
        
        try:
            context = f"""Repair this failure:
Step: {step.step_key}
Description: {step.description}
Error: {step.last_error}
Attempts: {step.attempt}

Failure History:
{failure_history}

Analyze and propose a repair.
"""
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": context}
            ]
            
            response = await self.model_client.create(messages=messages)
            response_text = response.choices[0].message.content
            
            # Parse repair action
            import json
            try:
                data = json.loads(response_text)
                repair_type = RepairType(data.get("repair_type", "step_modification"))
                safe = data.get("safe_to_apply", False)
                action = data.get("repair_action", "Retry with modifications")
            except:
                repair_type = RepairType.STEP_MODIFICATION
                safe = True
                action = "Retry step"
            
            # Log repair
            repair = Repair(
                plan_id=plan.id,
                step_key=step.step_key,
                failure_pattern=step.last_error or "unknown",
                repair_action=action,
                repair_type=repair_type,
            )
            repository.log_repair(repair)
            
            if safe:
                return AgentResult(
                    success=True,
                    output=f"REPAIR APPLIED: {repair_type.value} - {action}",
                    updated_state={
                        "repair": {
                            "type": repair_type.value,
                            "action": action,
                            "step_key": step.step_key,
                        },
                        "step_update": {
                            "status": StepStatus.PENDING,  # Reset for retry
                        }
                    }
                )
            else:
                return AgentResult(
                    success=False,
                    error="Repair requires human approval",
                    output=f"REPAIR PROPOSED (needs approval): {action}",
                    updated_state={
                        "requires_approval": True,
                        "proposed_repair": {
                            "type": repair_type.value,
                            "action": action,
                        }
                    }
                )
            
        except Exception as e:
            return AgentResult(success=False, error=str(e))
    
    def _analyze_failures(self, repository, plan: Plan, step: Step) -> dict:
        """Analyze failure patterns for this step and similar steps."""
        history = {
            "this_step_failures": step.attempt,
            "similar_failures": [],
            "recurring_patterns": [],
        }
        
        # Check memory for similar failures
        if self.memory_store and step.last_error:
            avoidance = self.memory_store.should_avoid(step.last_error)
            if avoidance:
                history["memory_recommendation"] = avoidance
        
        return history
    
    def _auto_repair(self, step: Step, history: dict) -> AgentResult:
        """Auto-repair for testing without model."""
        # Simple strategy: switch strategy on retry
        repair_type = RepairType.STRATEGY_SWITCH
        action = f"Switch strategy for step {step.step_key}"
        
        return AgentResult(
            success=True,
            output=f"[AUTO-REPAIR] {repair_type.value}: {action}",
            updated_state={
                "repair": {
                    "type": repair_type.value,
                    "action": action,
                    "step_key": step.step_key,
                },
                "step_update": {
                    "status": StepStatus.PENDING,
                    "strategy": f"alt_strategy_{step.attempt + 1}",
                }
            }
        )
