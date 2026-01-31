"""
Policy Engine for Conductor.
Declarative governance as code.
"""
import json
import re
from typing import Optional
from dataclasses import dataclass

from conductor.db.models import Policy, PolicyType, PolicyEvaluation


@dataclass
class PolicyResult:
    """Result of policy evaluation."""
    allowed: bool
    policy_name: Optional[str] = None
    policy_type: Optional[PolicyType] = None
    reason: Optional[str] = None
    requires_approval: bool = False
    requires_verification: bool = False


class PolicyEngine:
    """
    Evaluates declarative policies before and after actions.
    
    Policies are evaluated in priority order.
    First matching policy determines the result.
    """
    
    # Built-in policies
    DEFAULT_POLICIES = [
        Policy(
            name="deny_sudo",
            policy_type=PolicyType.DENY,
            scope="mcp",
            condition={"mcp_server": "desktop-commander", "action_contains": "sudo"},
            action="Reject commands with sudo",
            priority=100,
        ),
        Policy(
            name="deny_rm_rf",
            policy_type=PolicyType.DENY,
            scope="mcp",
            condition={"mcp_server": "desktop-commander", "action_contains": "rm -rf"},
            action="Reject destructive delete commands",
            priority=100,
        ),
        Policy(
            name="require_approval_git_push_main",
            policy_type=PolicyType.REQUIRE_APPROVAL,
            scope="mcp",
            condition={"mcp_server": "github-official", "action": "git_push", "branch": "main"},
            action="Require human approval for main branch push",
            priority=90,
        ),
        Policy(
            name="require_verification_file_write",
            policy_type=PolicyType.REQUIRE_VERIFICATION,
            scope="mcp",
            condition={"mcp_server": "desktop-commander", "action": "file_write"},
            action="Verify file writes with Verifier agent",
            priority=50,
        ),
        Policy(
            name="allow_file_read",
            policy_type=PolicyType.ALLOW,
            scope="mcp",
            condition={"action": "file_read"},
            action="Allow all file reads",
            priority=10,
        ),
    ]
    
    def __init__(self, repository=None):
        self.repository = repository
        self._policies: list[Policy] = list(self.DEFAULT_POLICIES)
        self._load_custom_policies()
    
    def _load_custom_policies(self):
        """Load policies from database."""
        if self.repository:
            # Will be implemented in repository
            pass
    
    def add_policy(self, policy: Policy):
        """Add a runtime policy."""
        self._policies.append(policy)
        self._policies.sort(key=lambda p: -p.priority)
    
    def evaluate(self, context: dict) -> PolicyResult:
        """
        Evaluate policies against context.
        
        Context should include:
        - scope: 'mcp', 'step', 'plan', 'global'
        - mcp_server: (if scope=mcp)
        - action: what is being done
        - step_key, plan_id: identifiers
        - Additional metadata
        """
        scope = context.get("scope", "global")
        
        # Evaluate policies in priority order
        for policy in self._policies:
            if not policy.enabled:
                continue
            
            if policy.scope != scope and policy.scope != "global":
                continue
            
            if self._matches(policy, context):
                return self._policy_to_result(policy, context)
        
        # Default: allow if no policy matches
        return PolicyResult(allowed=True, reason="No matching policy")
    
    def _matches(self, policy: Policy, context: dict) -> bool:
        """Check if policy condition matches context."""
        condition = policy.condition
        
        for key, value in condition.items():
            # Handle special operators
            if key.endswith("_contains"):
                actual_key = key[:-9]
                actual_value = context.get(actual_key, "")
                if value not in str(actual_value):
                    return False
            elif key.endswith("_regex"):
                actual_key = key[:-6]
                actual_value = context.get(actual_key, "")
                if not re.search(value, str(actual_value)):
                    return False
            elif key.endswith("_in"):
                actual_key = key[:-3]
                actual_value = context.get(actual_key)
                if actual_value not in value:
                    return False
            else:
                # Exact match
                if context.get(key) != value:
                    return False
        
        return True
    
    def _policy_to_result(self, policy: Policy, context: dict) -> PolicyResult:
        """Convert matched policy to result."""
        if policy.policy_type == PolicyType.ALLOW:
            return PolicyResult(
                allowed=True,
                policy_name=policy.name,
                policy_type=policy.policy_type,
                reason=policy.action,
            )
        
        elif policy.policy_type == PolicyType.DENY:
            return PolicyResult(
                allowed=False,
                policy_name=policy.name,
                policy_type=policy.policy_type,
                reason=policy.action,
            )
        
        elif policy.policy_type == PolicyType.REQUIRE_APPROVAL:
            return PolicyResult(
                allowed=False,
                policy_name=policy.name,
                policy_type=policy.policy_type,
                reason=policy.action,
                requires_approval=True,
            )
        
        elif policy.policy_type == PolicyType.REQUIRE_VERIFICATION:
            return PolicyResult(
                allowed=True,  # Allowed but must be verified
                policy_name=policy.name,
                policy_type=policy.policy_type,
                reason=policy.action,
                requires_verification=True,
            )
        
        return PolicyResult(allowed=True)
    
    def explain(self, context: dict) -> str:
        """Explain which policies apply to a context."""
        result = self.evaluate(context)
        
        lines = [f"Policy Evaluation for: {context}"]
        lines.append(f"  Result: {'ALLOWED' if result.allowed else 'DENIED'}")
        
        if result.policy_name:
            lines.append(f"  Matched Policy: {result.policy_name}")
            lines.append(f"  Reason: {result.reason}")
        
        if result.requires_approval:
            lines.append("  ** REQUIRES HUMAN APPROVAL **")
        
        if result.requires_verification:
            lines.append("  ** REQUIRES VERIFIER CONFIRMATION **")
        
        return "\n".join(lines)
