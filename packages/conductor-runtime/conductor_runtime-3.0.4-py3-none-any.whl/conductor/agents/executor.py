"""
Executor Agent for Conductor.

RESPONSIBILITIES:
- Execute ONE step at a time
- Use MCP servers whenever possible (LLM mode)
- Use File-Based Handoff when configured (files mode)
- Produce concrete artifacts

OUTPUT CONTRACT:
- Actions taken
- Tools used
- Artifacts created

FORBIDDEN:
- Planning future steps
- Skipping MCP usage (in LLM mode)
- Making assumptions
"""
from typing import Optional, Any
from datetime import datetime, timedelta
import logging

from conductor.agents.base import BaseAgent, AgentResult
from conductor.db import Repository, Plan, Step, StepStatus
from conductor.mcp import MCPDiscovery
from conductor.config import ConductorConfig


logger = logging.getLogger("conductor.executor")


EXECUTOR_SYSTEM_PROMPT = """You are the Executor Agent in a production orchestration system.

## YOUR ROLE
Execute ONE step at a time. Produce concrete outputs.

## STRICT RULES
1. Execute ONLY the step provided
2. Use MCP servers when available (tool-first)
3. Report what was ACTUALLY done
4. If blocked, explain WHY

## MCP POLICY (MANDATORY)
MCP servers MUST be used when available:
- File operations → desktop-commander
- Documentation → context7
- HTTP requests → fetch
- Search → perplexity-ask → searxng → exa

## OUTPUT FORMAT
Return JSON:
{
    "success": true/false,
    "action": "What was done",
    "artifacts": ["files created"],
    "mcp_used": ["servers used"],
    "error": null or "message"
}

## FORBIDDEN
- DO NOT plan future steps
- DO NOT skip MCP when available
- DO NOT make assumptions
"""


class ExecutorAgent(BaseAgent):
    """Executor Agent - runs individual steps via LLM or File-Based Handoff."""
    
    def __init__(
        self,
        model_client: Any = None,
        mcp_discovery: MCPDiscovery = None,
        config: ConductorConfig = None,
        project_root: str = ".",
    ):
        super().__init__(model_client)
        self.mcp_discovery = mcp_discovery or MCPDiscovery()
        self.config = config or ConductorConfig()
        self.project_root = project_root
        
        # Lazy-init handoff adapter
        self._handoff_adapter = None
    
    @property
    def handoff_adapter(self):
        """Lazy-load HandoffAdapter to avoid import issues."""
        if self._handoff_adapter is None:
            from conductor.handoff import HandoffAdapter
            self._handoff_adapter = HandoffAdapter(self.project_root)
        return self._handoff_adapter
    
    @property
    def name(self) -> str:
        return "executor"
    
    @property
    def system_prompt(self) -> str:
        return EXECUTOR_SYSTEM_PROMPT
    
    async def run(self, repository: Repository, plan: Plan, step: Optional[Step] = None) -> AgentResult:
        """Execute a single step using configured mode."""
        
        if step is None:
            return AgentResult(success=False, error="No step provided")
        
        # Route based on HANDOFF_MODE
        if self.config.handoff_mode == "files":
            return await self._run_handoff(repository, plan, step)
        else:
            return await self._run_llm(repository, plan, step)
    
    # ─────────────────────────────────────────────────────────────
    # MODE: LLM (existing behavior)
    # ─────────────────────────────────────────────────────────────
    
    async def _run_llm(self, repository: Repository, plan: Plan, step: Step) -> AgentResult:
        """Execute step via LLM API (original behavior)."""
        
        if not self.model_client:
            return self._simulate_execution(step)
        
        try:
            # Build context with available MCPs
            mcp_info = f"Available MCP servers: {', '.join(self.mcp_discovery.list_available())}"
            
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"{mcp_info}\n\nExecute step:\nID: {step.step_key}\nDescription: {step.description}"}
            ]
            
            response = await self.model_client.create(messages=messages)
            response_text = response.choices[0].message.content
            
            return AgentResult(
                success=True,
                output=response_text,
                updated_state={
                    "step_update": {
                        "status": StepStatus.NEEDS_REVIEW,
                        "output": response_text
                    }
                }
            )
            
        except Exception as e:
            return AgentResult(
                success=False,
                error=str(e),
                updated_state={
                    "step_update": {
                        "status": StepStatus.FAILED,
                        "error": str(e)
                    }
                }
            )
    
    # ─────────────────────────────────────────────────────────────
    # MODE: FILES (File-Based Handoff)
    # ─────────────────────────────────────────────────────────────
    
    async def _run_handoff(self, repository: Repository, plan: Plan, step: Step) -> AgentResult:
        """Execute step via File-Based Handoff to Antigravity."""
        
        logger.info(f"[{step.step_key}] Using File-Based Handoff")
        
        # Extract allowed files from step context (if any)
        allowed_files = step.context.get("allowed_files", []) if step.context else []
        
        try:
            # 1. Write task file
            task_path = self.handoff_adapter.write_task(
                task_id=step.step_key,
                plan_id=plan.id,
                fork_id=plan.active_fork_id or "fork_default",
                instruction=step.description,
                allowed_files=allowed_files,
                timeout_seconds=self.config.step_timeout_seconds,
                context={
                    "plan_goal": plan.goal,
                    "step_dependencies": step.depends_on if hasattr(step, 'depends_on') else [],
                },
                max_diff_lines=self.config.handoff_max_diff_lines,
            )
            
            logger.info(f"[{step.step_key}] Task written to {task_path}")
            
            # 2. Poll for result
            result = self.handoff_adapter.poll_result(
                task_id=step.step_key,
                plan_id=plan.id,
                fork_id=plan.active_fork_id or "fork_default",
                timeout_seconds=self.config.step_timeout_seconds,
            )
            
            # 3. Handle timeout
            if result is None:
                logger.warning(f"[{step.step_key}] Handoff timeout")
                return AgentResult(
                    success=False,
                    error="Handoff timeout: Antigravity agent did not respond",
                    updated_state={
                        "step_update": {
                            "status": StepStatus.FAILED,
                            "error": "Handoff timeout"
                        }
                    }
                )
            
            # 4. Handle result status
            if result.status.value == "done":
                return AgentResult(
                    success=True,
                    output=result.summary,
                    updated_state={
                        "step_update": {
                            "status": StepStatus.NEEDS_REVIEW,
                            "output": result.summary,
                            "files_changed": [fc.path for fc in result.files_changed],
                            "handoff_mode": "files",
                        }
                    }
                )
            
            elif result.status.value in ("failed", "blocked"):
                return AgentResult(
                    success=False,
                    error=result.error or "Handoff failed",
                    updated_state={
                        "step_update": {
                            "status": StepStatus.FAILED,
                            "error": result.error,
                            "suggestion": result.suggestion,
                        }
                    }
                )
            
            elif result.status.value == "partial":
                return AgentResult(
                    success=True,  # Partial success
                    output=result.summary,
                    updated_state={
                        "step_update": {
                            "status": StepStatus.NEEDS_REVIEW,
                            "output": f"PARTIAL: {result.summary}",
                            "notes": result.notes,
                        }
                    }
                )
            
            else:
                # Unknown status
                return AgentResult(
                    success=False,
                    error=f"Unknown handoff status: {result.status}",
                    updated_state={
                        "step_update": {
                            "status": StepStatus.FAILED,
                        }
                    }
                )
            
        except Exception as e:
            logger.error(f"[{step.step_key}] Handoff error: {e}")
            return AgentResult(
                success=False,
                error=f"Handoff error: {str(e)}",
                updated_state={
                    "step_update": {
                        "status": StepStatus.FAILED,
                        "error": str(e)
                    }
                }
            )
    
    # ─────────────────────────────────────────────────────────────
    # SIMULATION (testing)
    # ─────────────────────────────────────────────────────────────
    
    def _simulate_execution(self, step: Step) -> AgentResult:
        """Simulate execution for testing."""
        return AgentResult(
            success=True,
            output=f"[SIMULATED] Executed: {step.description}",
            updated_state={
                "step_update": {
                    "status": StepStatus.NEEDS_REVIEW,
                    "output": f"Simulated: {step.description}",
                    "mcp_used": ["simulation"]
                }
            }
        )

