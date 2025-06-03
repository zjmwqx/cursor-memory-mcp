"""
Cursor Memory MCP - Cursor项目记忆文件创建器

一个MCP（Model Context Protocol）服务，用于在当前项目的.cursor/目录下自动创建.mdc文件，
以保存任务执行的上下文记忆。
"""

__version__ = "0.1.1"
__author__ = "zjmwqx"
__email__ = "zjmaspire@gmail.com"

from .server import main

__all__ = ["main"]
