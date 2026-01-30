"""Discord MCP Agent - MCP server for Discord-based AI agent-user communication."""

__version__ = "1.0.0"

from .server import main, main_sync

__all__ = ["main", "main_sync", "__version__"]
