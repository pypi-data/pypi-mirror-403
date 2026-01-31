"""
Reviewer Agent for Conductor.

RESPONSIBILITIES:
- Validate executor outputs
- Detect bugs, gaps, violations
- Decide PASS / FAIL

OUTPUT CONTRACT:
- Verdict
- Reasons
- Required fixes if failed

FORBIDDEN:
- Executing steps
- Modifying state
"""
import json
from typing import Optional

from conductor.agents.base import BaseAgent, AgentResult
from conductor.db import Repository, Plan, Step, StepStatus


REVIEWER_SYSTEM_PROMPT = """You are the Reviewer Agent in a production orchestration system.

## YOUR ROLE
Validate executed step output. You are the quality gate.

## STRICT RULES
1. Review ONLY the step output provided
2. Check correctness, completeness, consistency
3. Provide actionable feedback if failing

## OUTPUT FORMAT
Return ONLY JSON:
{
    "verdict": "PASS" or "FAIL",
    "issues": ["list of issues"],
    "requires_reexecution": true/false
}

## DECISION CRITERIA
- PASS: Step completed correctly
- FAIL + requires_reexecution=true: Can be fixed by retry
- FAIL + requires_reexecution=false: Needs human intervention

## FORBIDDEN
- DO NOT execute steps
- DO NOT modify state
- DO NOT use tools
"""


class ReviewerAgent(BaseAgent):
    """Reviewer Agent - validates step outputs."""
    
    @property
    def name(self) -> str:
        return "reviewer"
    
    @property
    def system_prompt(self) -> str:
        return REVIEWER_SYSTEM_PROMPT
    
    async def run(self, repository: Repository, plan: Plan, step: Optional[Step] = None) -> AgentResult:
        """Review a step's output."""
        
        if step is None:
            return AgentResult(success=False, error="No step provided")
        
        if step.status != StepStatus.NEEDS_REVIEW:
            return AgentResult(success=False, error=f"Step not awaiting review: {step.status}")
        
        if not self.model_client:
            return self._auto_pass(step)
        
        try:
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Review step:\nID: {step.step_key}\nDescription: {step.description}\nOutput: {step.output}"}
            ]
            
            response = await self.model_client.create(messages=messages)
            response_text = response.choices[0].message.content
            
            # Parse verdict
            try:
                data = json.loads(response_text)
                verdict = data.get("verdict", "PASS")
                requires_reexec = data.get("requires_reexecution", False)
                issues = data.get("issues", [])
            except json.JSONDecodeError:
                verdict = "PASS"
                requires_reexec = False
                issues = []
            
            if verdict == "PASS":
                return AgentResult(
                    success=True,
                    output=f"PASS: {step.step_key}",
                    updated_state={
                        "step_update": {
                            "status": StepStatus.COMPLETED,
                            "output": step.output
                        }
                    }
                )
            else:
                error_msg = "; ".join(issues) if issues else "Review failed"
                new_status = StepStatus.PENDING if requires_reexec else StepStatus.FAILED
                
                return AgentResult(
                    success=False,
                    output=f"FAIL: {step.step_key}",
                    error=error_msg,
                    updated_state={
                        "step_update": {
                            "status": new_status,
                            "error": error_msg
                        }
                    }
                )
            
        except Exception as e:
            return AgentResult(success=False, error=str(e))
    
    def _auto_pass(self, step: Step) -> AgentResult:
        """Auto-pass for testing."""
        return AgentResult(
            success=True,
            output=f"[AUTO-PASS] {step.step_key}",
            updated_state={
                "step_update": {
                    "status": StepStatus.COMPLETED,
                    "output": step.output
                }
            }
        )
