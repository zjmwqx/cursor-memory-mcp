#!/usr/bin/env python3
"""
Cursor Memory MCP Server

该MCP服务用于在项目的.cursor/目录中创建任务记忆文件
"""

import asyncio
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool
from pydantic import BaseModel, Field, ValidationError, field_validator

# 设置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CreateMemoryRequest(BaseModel):
    """创建记忆文件的请求模型"""

    task_summary: str = Field(
        ..., description="当前任务执行的详细上下文总结", min_length=1
    )
    task_name: str = Field(
        ..., description="当前任务的简短名称，用作文件名", min_length=1, max_length=50
    )
    project_path: str = Field(..., description="当前项目的绝对路径")
    task_description: Optional[str] = Field(None, description="任务的详细描述")

    @field_validator("task_name")
    def validate_task_name(cls, v):
        """验证任务名称格式"""
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("task_name只允许字母、数字、下划线、连字符")
        return v

    @field_validator("task_summary")
    def validate_task_summary(cls, v):
        """验证任务总结不为空"""
        if not v or not v.strip():
            raise ValueError("task_summary不能为空字符串")
        return v.strip()

    @field_validator("project_path")
    def validate_project_path(cls, v):
        """验证项目路径是否存在"""
        if not v or not v.strip():
            raise ValueError("project_path不能为空")

        path = Path(v.strip())
        if not path.exists():
            raise ValueError(f"项目路径不存在: {v}")
        if not path.is_dir():
            raise ValueError(f"项目路径必须是一个目录: {v}")

        return str(path.resolve())


class CursorMemoryMCP:
    """Cursor Memory MCP 服务实现"""

    def __init__(self):
        self.server = Server("cursor-memory-mcp")
        self._setup_tools()

    def _setup_tools(self):
        """设置MCP工具"""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """列出可用的工具"""
            return [
                Tool(
                    name="create_cursor_memory",
                    description="在项目的.cursor/目录中创建任务记忆文件",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "task_summary": {
                                "type": "string",
                                "description": "当前任务执行的详细上下文总结",
                                "minLength": 1,
                            },
                            "task_name": {
                                "type": "string",
                                "description": "当前任务的简短名称，用作文件名",
                                "minLength": 1,
                                "maxLength": 50,
                                "pattern": "^[a-zA-Z0-9_-]+$",
                            },
                            "project_path": {
                                "type": "string",
                                "description": "当前项目的绝对路径",
                            },
                            "task_description": {
                                "type": "string",
                                "description": "任务的详细描述（可选）",
                            },
                        },
                        "required": ["task_summary", "task_name", "project_path"],
                    },
                )
            ]

        @self.server.call_tool()
        async def call_tool(
            name: str, arguments: Dict[str, Any]
        ) -> list[Dict[str, Any]]:
            """处理工具调用"""
            if name == "create_cursor_memory":
                return await self._create_cursor_memory(arguments)
            else:
                raise ValueError(f"未知工具: {name}")

    async def _create_cursor_memory(
        self, arguments: Dict[str, Any]
    ) -> list[Dict[str, Any]]:
        """创建Cursor记忆文件的主要逻辑"""
        try:
            # 参数验证
            request = CreateMemoryRequest(**arguments)

            # 设置默认task_description
            if not request.task_description:
                request.task_description = request.task_name

            # 使用传入的项目路径而不是当前工作目录
            project_root = Path(request.project_path)
            cursor_dir = project_root / ".cursor" / "rules"

            # 确保.cursor/rules目录存在
            try:
                cursor_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"确保.cursor/rules目录存在: {cursor_dir}")
            except Exception as e:
                error_msg = f"无法创建.cursor/rules目录: {e}"
                logger.error(error_msg)
                return [
                    {
                        "type": "text",
                        "text": json.dumps(
                            {"error": f"文件操作失败: {error_msg}"},
                            ensure_ascii=False,
                            indent=2,
                        ),
                    }
                ]

            # 生成文件名（处理重复文件名）
            filename = f"{request.task_name}.mdc"
            file_path = cursor_dir / filename

            # 检查文件是否已存在，如果存在则添加时间戳
            if file_path.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{request.task_name}_{timestamp}.mdc"
                file_path = cursor_dir / filename
                logger.info(f"文件已存在，使用时间戳文件名: {filename}")

            # 生成文件内容
            content = self._generate_file_content(
                request.task_description, request.task_summary
            )

            # 写入文件
            try:
                # 使用临时文件确保原子操作
                temp_file = file_path.with_suffix(".tmp")
                with open(temp_file, "w", encoding="utf-8") as f:
                    f.write(content)

                # 重命名临时文件
                temp_file.rename(file_path)

                logger.info(f"成功创建记忆文件: {file_path}")

                # 构建成功响应
                response = {
                    "success": True,
                    "message": "成功创建记忆文件",
                    "file_path": str(file_path),
                    "created_at": datetime.now().isoformat(),
                }

                if filename != f"{request.task_name}.mdc":
                    response["message"] += f"，文件名已调整为: {filename}"

                return [
                    {
                        "type": "text",
                        "text": json.dumps(response, ensure_ascii=False, indent=2),
                    }
                ]

            except Exception as e:
                error_msg = f"写入文件失败: {e}"
                logger.error(error_msg)
                return [
                    {
                        "type": "text",
                        "text": json.dumps(
                            {"error": f"文件操作失败: {error_msg}"},
                            ensure_ascii=False,
                            indent=2,
                        ),
                    }
                ]

        except ValidationError as e:
            error_details = []
            for error in e.errors():
                field = ".".join(str(loc) for loc in error["loc"])
                error_details.append(f"{field}: {error['msg']}")

            error_msg = f"参数验证失败: {'; '.join(error_details)}"
            logger.error(error_msg)
            return [
                {
                    "type": "text",
                    "text": json.dumps(
                        {"error": error_msg}, ensure_ascii=False, indent=2
                    ),
                }
            ]

        except Exception as e:
            error_msg = f"服务内部错误: {e}"
            logger.error(error_msg, exc_info=True)
            return [
                {
                    "type": "text",
                    "text": json.dumps(
                        {"error": error_msg}, ensure_ascii=False, indent=2
                    ),
                }
            ]

    def _generate_file_content(self, task_description: str, task_summary: str) -> str:
        """生成文件内容"""
        return f"""---
description: "get the summary of previous step: {task_description}"
globs:
alwaysApply: false
---
{task_summary}"""

    async def run(self):
        """运行MCP服务器"""
        logger.info("启动Cursor Memory MCP服务器...")
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream, write_stream, self.server.create_initialization_options()
            )


def main():
    """主函数"""
    try:
        mcp_server = CursorMemoryMCP()
        asyncio.run(mcp_server.run())
    except KeyboardInterrupt:
        logger.info("服务器已停止")
    except Exception as e:
        logger.error(f"服务器运行错误: {e}", exc_info=True)


if __name__ == "__main__":
    main()
