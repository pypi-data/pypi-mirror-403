"""
MCP Router - Routes actions to appropriate MCP servers.

MCP servers are preferred over reasoning-only answers.
This module provides a unified interface to MCP capabilities.
"""
from typing import Optional, Any
from enum import Enum


class MCPServer(str, Enum):
    """Available MCP servers from global rules."""
    DESKTOP_COMMANDER = "desktop-commander"  # File operations
    CONTEXT7 = "context7"                    # Documentation lookup
    FETCH = "fetch"                          # HTTP requests
    SEQUENTIAL_THINKING = "sequentialthinking"  # Logical validation
    PERPLEXITY = "perplexity-ask"            # Primary search
    SEARXNG = "searxng"                      # Fallback search
    EXA = "exa"                              # Last-resort search


class ActionType(str, Enum):
    """Types of actions that can be routed to MCP servers."""
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    FILE_DELETE = "file_delete"
    HTTP_GET = "http_get"
    HTTP_POST = "http_post"
    SEARCH = "search"
    DOCS_LOOKUP = "docs_lookup"
    VALIDATE_LOGIC = "validate_logic"


class MCPRouter:
    """
    Routes actions to appropriate MCP servers.
    
    Priority rules from global spec:
    1. MCP servers are ALWAYS preferred over reasoning-only answers
    2. If an MCP server can handle an action, it MUST be used
    3. Search priority: perplexity-ask → searxng → exa
    """
    
    # Mapping of action types to primary MCP servers
    ACTION_TO_MCP = {
        ActionType.FILE_READ: MCPServer.DESKTOP_COMMANDER,
        ActionType.FILE_WRITE: MCPServer.DESKTOP_COMMANDER,
        ActionType.FILE_DELETE: MCPServer.DESKTOP_COMMANDER,
        ActionType.HTTP_GET: MCPServer.FETCH,
        ActionType.HTTP_POST: MCPServer.FETCH,
        ActionType.SEARCH: MCPServer.PERPLEXITY,  # Primary
        ActionType.DOCS_LOOKUP: MCPServer.CONTEXT7,
        ActionType.VALIDATE_LOGIC: MCPServer.SEQUENTIAL_THINKING,
    }
    
    # Search fallback chain
    SEARCH_PRIORITY = [
        MCPServer.PERPLEXITY,
        MCPServer.SEARXNG,
        MCPServer.EXA,
    ]
    
    def __init__(self):
        self._available_servers: set[MCPServer] = set(MCPServer)
    
    def route(self, action_type: ActionType) -> Optional[MCPServer]:
        """
        Get the appropriate MCP server for an action type.
        
        Args:
            action_type: The type of action to perform
        
        Returns:
            The MCP server to use, or None if no server available
        """
        server = self.ACTION_TO_MCP.get(action_type)
        if server and server in self._available_servers:
            return server
        return None
    
    def get_search_chain(self) -> list[MCPServer]:
        """
        Get the search priority chain (perplexity → searxng → exa).
        
        Returns:
            Ordered list of search MCPs to try
        """
        return [s for s in self.SEARCH_PRIORITY if s in self._available_servers]
    
    def explain_choice(self, action_type: ActionType) -> str:
        """
        Explain why a specific MCP server was chosen.
        
        Args:
            action_type: The action type
        
        Returns:
            Human-readable explanation
        """
        server = self.route(action_type)
        if server is None:
            return f"No MCP server available for {action_type.value}"
        
        explanations = {
            MCPServer.DESKTOP_COMMANDER: "File operations are validated by desktop-commander for safety and compliance",
            MCPServer.CONTEXT7: "Documentation lookups use context7 for accurate, up-to-date information",
            MCPServer.FETCH: "HTTP requests are centralized through fetch MCP for timeout and domain control",
            MCPServer.SEQUENTIAL_THINKING: "Logical validation uses sequentialthinking to detect inconsistencies",
            MCPServer.PERPLEXITY: "Search uses perplexity-ask as primary for verified information",
        }
        
        return explanations.get(server, f"Using {server.value} for {action_type.value}")
    
    def mark_unavailable(self, server: MCPServer) -> None:
        """Mark an MCP server as unavailable."""
        self._available_servers.discard(server)
    
    def mark_available(self, server: MCPServer) -> None:
        """Mark an MCP server as available."""
        self._available_servers.add(server)
