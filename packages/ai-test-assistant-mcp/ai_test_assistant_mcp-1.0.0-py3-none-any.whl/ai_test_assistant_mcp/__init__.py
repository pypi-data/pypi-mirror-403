"""
AI 测试助手 MCP Server
支持 VS Code Copilot、Cursor、Cherry Studio 等 MCP 客户端
"""

from .server import mcp, main

__version__ = "1.0.0"
__all__ = ["mcp", "main"]
