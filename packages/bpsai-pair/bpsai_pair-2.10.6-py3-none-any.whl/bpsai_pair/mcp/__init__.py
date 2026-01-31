"""
MCP (Model Context Protocol) Server Module

Exposes PairCoder CLI functionality as callable tools for Claude and other
MCP-compatible agents.
"""

from .server import create_server, run_server

__all__ = ["create_server", "run_server"]
