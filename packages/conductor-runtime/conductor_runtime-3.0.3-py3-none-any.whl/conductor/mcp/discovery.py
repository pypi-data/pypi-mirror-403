"""
MCP Discovery Layer for Conductor.
Dynamically detects available MCP servers.
"""
from typing import Optional
from enum import Enum


class MCPCapability(str, Enum):
    """Known MCP capabilities."""
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    FILE_DELETE = "file_delete"
    SHELL_EXEC = "shell_exec"
    HTTP_GET = "http_get"
    HTTP_POST = "http_post"
    SEARCH = "search"
    GIT_COMMIT = "git_commit"
    GIT_PUSH = "git_push"
    DATABASE = "database"


class MCPServer:
    """Represents a discovered MCP server."""
    
    def __init__(
        self,
        name: str,
        capabilities: list[MCPCapability],
        priority: int = 50,
        available: bool = True
    ):
        self.name = name
        self.capabilities = capabilities
        self.priority = priority  # Higher = prefer
        self.available = available
    
    def supports(self, capability: MCPCapability) -> bool:
        return capability in self.capabilities


class MCPDiscovery:
    """
    Dynamically discovers available MCP servers.
    
    MCP usage is MANDATORY when a server can handle the task.
    """
    
    # Default MCP server definitions based on global rules
    KNOWN_SERVERS = {
        "desktop-commander": [
            MCPCapability.FILE_READ,
            MCPCapability.FILE_WRITE,
            MCPCapability.FILE_DELETE,
            MCPCapability.SHELL_EXEC,
        ],
        "context7": [
            MCPCapability.SEARCH,  # Documentation search
        ],
        "fetch": [
            MCPCapability.HTTP_GET,
            MCPCapability.HTTP_POST,
        ],
        "perplexity-ask": [
            MCPCapability.SEARCH,
        ],
        "searxng": [
            MCPCapability.SEARCH,
        ],
        "exa": [
            MCPCapability.SEARCH,
        ],
        "github-official": [
            MCPCapability.GIT_COMMIT,
            MCPCapability.GIT_PUSH,
        ],
    }
    
    # Search priority chain from global rules
    SEARCH_PRIORITY = ["perplexity-ask", "searxng", "exa"]
    
    def __init__(self):
        self._servers: dict[str, MCPServer] = {}
        self._discover_servers()
    
    def _discover_servers(self):
        """
        Discover available MCP servers.
        In production, this would probe endpoints or read config.
        """
        for name, caps in self.KNOWN_SERVERS.items():
            self._servers[name] = MCPServer(
                name=name,
                capabilities=caps,
                priority=100 if name == "desktop-commander" else 50,
                available=True
            )
    
    def get_server(self, name: str) -> Optional[MCPServer]:
        """Get server by name."""
        return self._servers.get(name)
    
    def get_server_for_capability(self, capability: MCPCapability) -> Optional[MCPServer]:
        """
        Get the best available server for a capability.
        Returns highest priority server that supports the capability.
        """
        candidates = [
            s for s in self._servers.values()
            if s.available and s.supports(capability)
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda s: s.priority)
    
    def get_search_chain(self) -> list[MCPServer]:
        """Get search servers in priority order."""
        return [
            self._servers[name]
            for name in self.SEARCH_PRIORITY
            if name in self._servers and self._servers[name].available
        ]
    
    def list_available(self) -> list[str]:
        """List available MCP server names."""
        return [s.name for s in self._servers.values() if s.available]
    
    def mark_unavailable(self, name: str):
        """Mark a server as unavailable."""
        if name in self._servers:
            self._servers[name].available = False
    
    def explain_selection(self, capability: MCPCapability) -> str:
        """Explain why a server was selected for a capability."""
        server = self.get_server_for_capability(capability)
        if server:
            return f"Using {server.name} for {capability.value} (priority: {server.priority})"
        return f"No MCP server available for {capability.value}"
