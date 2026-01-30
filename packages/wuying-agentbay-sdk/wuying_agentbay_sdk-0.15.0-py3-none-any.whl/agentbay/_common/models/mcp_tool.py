from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class McpTool:
    """
    Represents an MCP tool with complete information.
    """

    name: str
    server: str

    def get_name(self) -> str:
        """Return the tool name."""
        return self.name

    def get_server(self) -> str:
        """Return the server name that provides this tool."""
        return self.server
