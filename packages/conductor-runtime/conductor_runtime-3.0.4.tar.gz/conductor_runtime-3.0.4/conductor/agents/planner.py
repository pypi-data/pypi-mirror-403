"""
Planner Agent for Conductor.

RESPONSIBILITIES:
- Read ALL persistent state
- Produce a strict, step-by-step execution plan

OUTPUT CONTRACT:
- Structured JSON plan only
- No prose, no tools, no execution
- MUST contain at least one step

FORBIDDEN:
- Writing code
- Using tools
- Executing steps
"""
import json
import re
import logging
from typing import Optional, Any
from datetime import datetime

from conductor.agents.base import BaseAgent, AgentResult
from conductor.db import Repository, Plan, Step


# Configure debug logger
logger = logging.getLogger("conductor.planner")


# ─────────────────────────────────────────────────────────────
# STRICT JSON SCHEMA
# ─────────────────────────────────────────────────────────────

STEP_SCHEMA = {
    "required": ["id", "description", "agent"],
    "optional": ["depends_on", "tooling", "expected_output"],
    "agent_values": ["executor", "reviewer"],
}


def validate_step(step: dict, index: int) -> list[str]:
    """Validate a single step against the schema."""
    errors = []
    
    for field in STEP_SCHEMA["required"]:
        if field not in step:
            errors.append(f"Step {index}: missing required field '{field}'")
    
    if "agent" in step and step["agent"] not in STEP_SCHEMA["agent_values"]:
        errors.append(f"Step {index}: agent must be one of {STEP_SCHEMA['agent_values']}")
    
    if "id" in step and not isinstance(step["id"], str):
        errors.append(f"Step {index}: 'id' must be a string")
    
    if "description" in step and not isinstance(step["description"], str):
        errors.append(f"Step {index}: 'description' must be a string")
    
    return errors


def validate_plan_output(data: dict) -> tuple[bool, list[str], list[dict]]:
    """
    Validate the full planner output.
    
    Returns: (is_valid, errors, steps)
    """
    errors = []
    
    if not isinstance(data, dict):
        return False, ["Output must be a JSON object"], []
    
    if "steps" not in data:
        return False, ["Output must contain 'steps' array"], []
    
    steps = data.get("steps", [])
    
    if not isinstance(steps, list):
        return False, ["'steps' must be an array"], []
    
    if len(steps) == 0:
        return False, ["'steps' array must not be empty"], []
    
    for i, step in enumerate(steps):
        errors.extend(validate_step(step, i))
    
    return len(errors) == 0, errors, steps


def extract_json_from_response(text: str) -> tuple[Optional[dict], str]:
    """
    Extract JSON from LLM response, handling markdown code blocks.
    
    Returns: (parsed_dict, extraction_method)
    """
    # Try 1: Direct parse
    try:
        return json.loads(text), "direct"
    except json.JSONDecodeError:
        pass
    
    # Try 2: Extract from ```json ... ``` block
    json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1)), "markdown_block"
        except json.JSONDecodeError:
            pass
    
    # Try 3: Find JSON object in text
    brace_match = re.search(r'\{.*\}', text, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0)), "extracted_braces"
        except json.JSONDecodeError:
            pass
    
    return None, "failed"


# ─────────────────────────────────────────────────────────────
# SYSTEM PROMPT (Hardened)
# ─────────────────────────────────────────────────────────────

PLANNER_SYSTEM_PROMPT = """You are the Planner Agent in a production orchestration system.

## YOUR ROLE
Decompose a goal into concrete, executable steps.

## STRICT CONTRACT
You MUST return ONLY valid JSON. No markdown, no prose, no explanation.

## REQUIRED OUTPUT FORMAT
```json
{
    "steps": [
        {"id": "step_1", "description": "Analyze requirements and define scope", "agent": "executor", "depends_on": []},
        {"id": "step_2", "description": "Review analysis", "agent": "reviewer", "depends_on": ["step_1"]},
        {"id": "step_3", "description": "Implement the solution", "agent": "executor", "depends_on": ["step_2"]},
        {"id": "step_4", "description": "Final review", "agent": "reviewer", "depends_on": ["step_3"]}
    ]
}
```

## RULES
1. Each step needs: "id" (string), "description" (string), "agent" ("executor" or "reviewer")
2. "depends_on" is optional, defaults to depending on previous step
3. Include at least 3 steps
4. Include at least 1 reviewer step after major actions
5. Steps must be concrete and verifiable

## FORBIDDEN
- NO prose or explanation outside JSON
- NO markdown formatting around JSON
- NO empty steps array
- NO code in the response

Return the JSON object now:"""


# ─────────────────────────────────────────────────────────────
# PLANNER AGENT
# ─────────────────────────────────────────────────────────────

class PlannerAgent(BaseAgent):
    """
    Planner Agent - creates execution plans.
    
    Features:
    - Raw LLM response logging
    - Strict JSON validation
    - Retry with error feedback
    - Fail-fast on empty plans
    """
    
    MAX_RETRIES = 3
    
    @property
    def name(self) -> str:
        return "planner"
    
    @property
    def system_prompt(self) -> str:
        return PLANNER_SYSTEM_PROMPT
    
    async def run(self, repository: Repository, plan: Plan, step: Optional[Step] = None) -> AgentResult:
        """Generate execution steps for the plan with retry and validation."""
        
        if not self.model_client:
            logger.warning(f"[{plan.id}] No model client - using fallback steps")
            return self._create_fallback_steps(plan)
        
        last_error = None
        last_raw_response = None
        
        for attempt in range(1, self.MAX_RETRIES + 1):
            logger.info(f"[{plan.id}] Planner attempt {attempt}/{self.MAX_RETRIES}")
            
            result = await self._attempt_planning(repository, plan, attempt, last_error)
            
            if result.success:
                steps = result.updated_state.get("new_steps", [])
                if len(steps) > 0:
                    logger.info(f"[{plan.id}] Created {len(steps)} steps on attempt {attempt}")
                    return result
                else:
                    last_error = "Empty steps array after validation"
                    logger.warning(f"[{plan.id}] Empty steps on attempt {attempt}")
            else:
                last_error = result.error
                last_raw_response = result.updated_state.get("raw_response", "")
                logger.warning(f"[{plan.id}] Attempt {attempt} failed: {last_error}")
        
        # All retries exhausted - FAIL FAST
        logger.error(f"[{plan.id}] All {self.MAX_RETRIES} attempts failed. Last error: {last_error}")
        
        return AgentResult(
            success=False,
            error=f"PLANNER_FAILED: {last_error} (after {self.MAX_RETRIES} attempts)",
            updated_state={
                "raw_response": last_raw_response,
                "attempts": self.MAX_RETRIES,
                "plan_status": "failed",
            }
        )
    
    async def _attempt_planning(
        self,
        repository: Repository,
        plan: Plan,
        attempt: int,
        previous_error: Optional[str] = None,
    ) -> AgentResult:
        """Single planning attempt with error feedback on retry."""
        
        try:
            # Build messages
            messages = [
                {"role": "system", "content": self.system_prompt},
            ]
            
            # Add error feedback on retry
            if attempt > 1 and previous_error:
                messages.append({
                    "role": "user",
                    "content": f"""Your previous response was invalid.
Error: {previous_error}

REMINDER: Return ONLY a JSON object with a non-empty "steps" array.
No prose, no markdown, no explanation.

Goal: {plan.goal}"""
                })
            else:
                messages.append({
                    "role": "user",
                    "content": f"Create a step-by-step plan for this goal:\n\n{plan.goal}"
                })
            
            # Call LLM
            response = await self.model_client.create(messages=messages)
            raw_response = response.choices[0].message.content
            
            # Log raw response
            logger.debug(f"[{plan.id}] Raw LLM response:\n{raw_response}")
            self._log_to_file(plan.id, attempt, raw_response)
            
            # Extract JSON
            data, method = extract_json_from_response(raw_response)
            
            if data is None:
                return AgentResult(
                    success=False,
                    error=f"Could not extract JSON from response (tried: direct, markdown_block, extracted_braces)",
                    updated_state={"raw_response": raw_response[:500]}
                )
            
            logger.info(f"[{plan.id}] JSON extracted via: {method}")
            
            # Validate schema
            is_valid, errors, steps = validate_plan_output(data)
            
            if not is_valid:
                return AgentResult(
                    success=False,
                    error=f"Schema validation failed: {'; '.join(errors)}",
                    updated_state={"raw_response": raw_response[:500]}
                )
            
            # Ensure IDs and defaults
            for i, step in enumerate(steps):
                if "id" not in step:
                    step["id"] = f"step_{i+1}"
                if "depends_on" not in step:
                    step["depends_on"] = [steps[i-1]["id"]] if i > 0 else []
            
            return AgentResult(
                success=True,
                output=f"Created {len(steps)} steps (attempt {attempt}, extraction: {method})",
                updated_state={
                    "new_steps": steps,
                    "raw_response": raw_response[:200],
                    "extraction_method": method,
                }
            )
            
        except Exception as e:
            logger.exception(f"[{plan.id}] Exception during planning")
            return AgentResult(
                success=False,
                error=f"Exception: {str(e)}",
                updated_state={}
            )
    
    def _log_to_file(self, plan_id: str, attempt: int, raw_response: str) -> None:
        """Log raw response to debug file."""
        try:
            from pathlib import Path
            log_dir = Path(".conductor/logs")
            log_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = log_dir / f"planner_{plan_id}_{timestamp}_attempt{attempt}.txt"
            log_file.write_text(raw_response, encoding="utf-8")
        except Exception:
            pass  # Don't fail on logging errors
    
    def _create_fallback_steps(self, plan: Plan) -> AgentResult:
        """Create fallback steps when no model available."""
        steps = [
            {"id": "step_1", "description": "Analyze requirements and define scope", "agent": "executor", "depends_on": []},
            {"id": "step_2", "description": "Review analysis", "agent": "reviewer", "depends_on": ["step_1"]},
            {"id": "step_3", "description": "Implement the solution", "agent": "executor", "depends_on": ["step_2"]},
            {"id": "step_4", "description": "Test implementation", "agent": "executor", "depends_on": ["step_3"]},
            {"id": "step_5", "description": "Final review", "agent": "reviewer", "depends_on": ["step_4"]},
        ]
        
        return AgentResult(
            success=True,
            output=f"Created {len(steps)} fallback steps (no model client)",
            updated_state={"new_steps": steps, "fallback": True}
        )
