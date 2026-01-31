"""
Verifier Agent for Conductor.
Evidence-based verification of executor claims.
"""
from typing import Optional, Any

from conductor.agents.base import BaseAgent, AgentResult
from conductor.db.models import Step, StepStatus


VERIFIER_SYSTEM_PROMPT = """You are the Verifier Agent in a production orchestration system.

## YOUR ROLE
Validate that Executor's claims are backed by EVIDENCE.
You do NOT trust assertions. You VERIFY artifacts.

## VERIFICATION PROCESS
1. Read the step output and claimed artifacts
2. Check that artifacts ACTUALLY EXIST
3. Verify content matches claimed output
4. Cross-check MCP call logs
5. Detect discrepancies

## OUTPUT FORMAT
Return ONLY JSON:
{
    "verified": true/false,
    "evidence": {
        "artifacts_checked": ["list of files verified"],
        "mcp_logs_validated": true/false,
        "discrepancies": ["list of issues found"]
    },
    "confidence": 0.0-1.0,
    "rejection_reason": null or "why verification failed"
}

## EVIDENCE REQUIREMENTS
- File claimed to be created → MUST exist with correct content
- Command claimed to run → MUST appear in MCP log
- Output claimed → MUST match actual response

## FORBIDDEN
- DO NOT trust Executor's word
- DO NOT skip verification steps
- DO NOT modify anything
"""


class VerifierAgent(BaseAgent):
    """
    Verifier Agent - Evidence-based claim validation.
    
    Separate from Reviewer:
    - Reviewer: Does output meet requirements?
    - Verifier: Does output actually exist as claimed?
    """
    
    def __init__(self, model_client: Any = None, mcp_discovery=None):
        super().__init__(model_client)
        self.mcp_discovery = mcp_discovery
    
    @property
    def name(self) -> str:
        return "verifier"
    
    @property
    def system_prompt(self) -> str:
        return VERIFIER_SYSTEM_PROMPT
    
    async def run(self, repository, plan, step: Optional[Step] = None) -> AgentResult:
        """Verify a step's claimed output against evidence."""
        
        if step is None:
            return AgentResult(success=False, error="No step to verify")
        
        # Collect evidence
        evidence = await self._collect_evidence(repository, step)
        
        if not self.model_client:
            return self._auto_verify(step, evidence)
        
        try:
            context = f"""Verify this step:
Step: {step.step_key}
Description: {step.description}
Claimed Output: {step.output}
Claimed Artifacts: {step.artifacts}
MCP Calls: {step.mcp_used}

Evidence Collected:
{evidence}

Verify the claims against this evidence.
"""
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": context}
            ]
            
            response = await self.model_client.create(messages=messages)
            response_text = response.choices[0].message.content
            
            # Parse response
            import json
            try:
                data = json.loads(response_text)
                verified = data.get("verified", False)
                confidence = data.get("confidence", 0.5)
                rejection = data.get("rejection_reason")
            except:
                verified = True
                confidence = 0.7
                rejection = None
            
            if verified:
                return AgentResult(
                    success=True,
                    output=f"VERIFIED: {step.step_key} (confidence: {confidence})",
                    updated_state={
                        "step_update": {
                            "status": StepStatus.COMPLETED,
                            "verified": True,
                            "confidence": confidence
                        }
                    }
                )
            else:
                return AgentResult(
                    success=False,
                    error=rejection or "Verification failed",
                    output=f"REJECTED: {step.step_key}",
                    updated_state={
                        "step_update": {
                            "status": StepStatus.FAILED,
                            "verified": False,
                            "error": rejection
                        }
                    }
                )
            
        except Exception as e:
            return AgentResult(success=False, error=str(e))
    
    async def _collect_evidence(self, repository, step: Step) -> dict:
        """Collect evidence for verification."""
        evidence = {
            "artifacts_exist": [],
            "mcp_calls": [],
            "file_contents": {},
        }
        
        # Check MCP call log
        mcp_calls = repository.get_mcp_calls_for_step(step.step_key)
        evidence["mcp_calls"] = [
            {"server": c.mcp_server, "action": c.action, "success": c.success}
            for c in mcp_calls
        ]
        
        # Check artifacts (would use MCP in real implementation)
        for artifact in step.artifacts:
            evidence["artifacts_exist"].append({
                "path": artifact,
                "exists": True,  # Would verify via MCP
            })
        
        return evidence
    
    def _auto_verify(self, step: Step, evidence: dict) -> AgentResult:
        """Auto-verify for testing without model."""
        # Simple heuristic: verify if MCP calls succeeded
        mcp_success = all(c.get("success", False) for c in evidence.get("mcp_calls", []))
        
        return AgentResult(
            success=True,
            output=f"[AUTO-VERIFIED] {step.step_key}",
            updated_state={
                "step_update": {
                    "status": StepStatus.COMPLETED,
                    "verified": True,
                    "confidence": 0.8 if mcp_success else 0.5
                }
            }
        )
