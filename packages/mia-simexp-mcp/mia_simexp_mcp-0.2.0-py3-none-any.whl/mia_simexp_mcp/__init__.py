"""
MIA SimExp MCP Server

An MCP (Model Context Protocol) server that exposes all mia-simexp functionality
for use with Claude and other AI agents.

Features:
- Session management (start, list, info, clear, write, read, etc.)
- Collaborative sharing and publishing
- Content extraction and archiving
- A2A communication via mia-anemoi
- Reflection and wisdom extraction
- Browser-based authentication
"""

__version__ = "0.2.0"
__author__ = "Mia Isabelle"
__email__ = "mia@example.com"

from mia_simexp_mcp.server import main

__all__ = ["main", "__version__"]
