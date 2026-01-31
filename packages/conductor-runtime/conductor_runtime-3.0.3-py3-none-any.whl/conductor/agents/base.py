"""
Base Agent class for Conductor.
Strict contract enforcement.
"""
from abc import ABC, abstractmethod
from typing import Any, Optional
from conductor.db import Repository, Plan, Step


class AgentResult:
    """
    Agent execution result.
    
    OUTPUT CONTRACT:
    - success: bool
    - output: Any - the agent's output
    - error: Optional[str] - error message if failed
    - updated_state: dict - state updates to apply
    """
    
    def __init__(
        self,
        success: bool,
        output: Any = None,
        error: Optional[str] = None,
        updated_state: Optional[dict] = None,
    ):
        self.success = success
        self.output = output
        self.error = error
        self.updated_state = updated_state or {}
    
    def __repr__(self):
        return f"AgentResult(success={self.success})"


class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    
    Contract enforcement:
    - Must read state before acting
    - Must return structured AgentResult
    - Must NOT modify state directly
    """
    
    def __init__(self, model_client: Any = None):
        self.model_client = model_client
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Agent name identifier."""
        pass
    
    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """System prompt for the agent."""
        pass
    
    @abstractmethod
    async def run(self, repository: Repository, plan: Plan, step: Optional[Step] = None) -> AgentResult:
        """
        Execute the agent's function.
        
        Args:
            repository: Database access layer (read-only for most agents)
            plan: Current plan
            step: Optional step to process
        
        Returns:
            AgentResult with success/failure and updates
        """
        pass
    
    def _read_context_files(self, project_root: str) -> dict:
        """Read context files from project root."""
        from pathlib import Path
        
        context = {}
        files = ["projectbrief.md", "techContext.md", "systemPatterns.md"]
        
        for filename in files:
            path = Path(project_root) / filename
            if path.exists():
                context[filename] = path.read_text(encoding="utf-8")
        
        return context
