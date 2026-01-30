"""
百度AI搜索 MCP服务

在Cursor等支持MCP的应用中使用百度AI搜索功能。
"""

from .server import mcp, main
from .client import BaiduAIClient, BaiduAIClientSync, AISearchResult, SearchReference

__version__ = "0.1.0"
__all__ = [
    "mcp",
    "main",
    "BaiduAIClient",
    "BaiduAIClientSync", 
    "AISearchResult",
    "SearchReference",
]
