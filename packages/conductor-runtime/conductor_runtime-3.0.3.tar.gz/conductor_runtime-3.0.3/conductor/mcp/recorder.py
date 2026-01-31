"""
MCP Call Recorder for Conductor.
Logs all MCP server interactions for audit trail.
"""
import time
from typing import Any, Optional
from functools import wraps

from conductor.db.models import MCPCall, EventType, Event
from conductor.db.repository import Repository


class MCPRecorder:
    """
    Records all MCP server calls for audit trail.
    Every MCP call MUST be logged.
    """
    
    def __init__(self, repository: Repository):
        self.repository = repository
        self._current_step_key: Optional[str] = None
    
    def set_step_context(self, step_key: str):
        """Set current step for MCP call attribution."""
        self._current_step_key = step_key
    
    def clear_step_context(self):
        """Clear step context."""
        self._current_step_key = None
    
    def record_call(
        self,
        mcp_server: str,
        action: str,
        request: dict = None,
        response: dict = None,
        success: bool = True,
        duration_ms: int = None
    ):
        """Record an MCP call."""
        call = MCPCall(
            mcp_server=mcp_server,
            action=action,
            step_key=self._current_step_key,
            request=request,
            response=response,
            success=success,
            duration_ms=duration_ms
        )
        self.repository.log_mcp_call(call)
        
        # Also log as event
        self.repository.log_event(Event(
            event_type=EventType.MCP_CALL,
            step_key=self._current_step_key,
            payload={
                "server": mcp_server,
                "action": action,
                "success": success,
                "duration_ms": duration_ms
            }
        ))
    
    def wrap_mcp_call(self, mcp_server: str, action: str):
        """Decorator to wrap and record MCP calls."""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start = time.time()
                try:
                    result = await func(*args, **kwargs)
                    duration_ms = int((time.time() - start) * 1000)
                    self.record_call(
                        mcp_server=mcp_server,
                        action=action,
                        request={"args": str(args)[:200], "kwargs": str(kwargs)[:200]},
                        response={"result": str(result)[:200]},
                        success=True,
                        duration_ms=duration_ms
                    )
                    return result
                except Exception as e:
                    duration_ms = int((time.time() - start) * 1000)
                    self.record_call(
                        mcp_server=mcp_server,
                        action=action,
                        request={"args": str(args)[:200]},
                        response={"error": str(e)[:200]},
                        success=False,
                        duration_ms=duration_ms
                    )
                    raise
            return wrapper
        return decorator
