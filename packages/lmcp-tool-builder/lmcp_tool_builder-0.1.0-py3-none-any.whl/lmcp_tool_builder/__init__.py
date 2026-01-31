"""
LMCP Tool Builder - 简化 LangChain 工具加载和集成

主要功能:
1. 从 LMCP 服务器发现工具
2. 构建工具模块
3. 加载工具函数
4. 与 LangChain 集成
"""

from .builder import LMCPToolBuilder

__version__ = "0.1.0"
__author__ = "LMCP Team"
__email__ = "support@lmcp.dev"

__all__ = [
    "LMCPToolBuilder",
]
