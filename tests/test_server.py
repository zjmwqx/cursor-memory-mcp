"""
Cursor Memory MCP Server 的测试套件
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from cursor_memory_mcp.server import CreateMemoryRequest, CursorMemoryMCP


class TestCreateMemoryRequest:
    """测试CreateMemoryRequest模型"""

    def test_valid_request(self):
        """测试有效的请求数据"""
        with tempfile.TemporaryDirectory() as temp_dir:
            request = CreateMemoryRequest(
                task_summary="这是一个测试任务的总结",
                task_name="test_task",
                task_description="测试任务描述",
                project_path=temp_dir,
            )
            assert request.task_summary == "这是一个测试任务的总结"
            assert request.task_name == "test_task"
            assert request.task_description == "测试任务描述"
            assert request.project_path == str(Path(temp_dir).resolve())

    def test_task_name_validation(self):
        """测试任务名称验证"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 有效的任务名称
            valid_names = ["task1", "task_name", "task-name", "TASK123", "task_123-abc"]
            for name in valid_names:
                request = CreateMemoryRequest(
                    task_summary="测试总结", task_name=name, project_path=temp_dir
                )
                assert request.task_name == name

            # 无效的任务名称
            invalid_names = ["task name", "task.name", "task@name", "任务名称", ""]
            for name in invalid_names:
                with pytest.raises(ValidationError):
                    CreateMemoryRequest(
                        task_summary="测试总结", task_name=name, project_path=temp_dir
                    )

    def test_task_summary_validation(self):
        """测试任务总结验证"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 空字符串应该失败
            with pytest.raises(ValidationError):
                CreateMemoryRequest(
                    task_summary="", task_name="test_task", project_path=temp_dir
                )

            # 只有空格的字符串应该失败
            with pytest.raises(ValidationError):
                CreateMemoryRequest(
                    task_summary="   ", task_name="test_task", project_path=temp_dir
                )

            # 有效的总结（会被trim）
            request = CreateMemoryRequest(
                task_summary="  有效的总结  ",
                task_name="test_task",
                project_path=temp_dir,
            )
            assert request.task_summary == "有效的总结"

    def test_project_path_validation(self):
        """测试项目路径验证"""
        # 空路径应该失败
        with pytest.raises(ValidationError):
            CreateMemoryRequest(
                task_summary="测试总结",
                task_name="test_task",
                project_path="",
            )

        # 不存在的路径应该失败
        with pytest.raises(ValidationError):
            CreateMemoryRequest(
                task_summary="测试总结",
                task_name="test_task",
                project_path="/nonexistent/path/12345",
            )

        # 文件路径（非目录）应该失败
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            with pytest.raises(ValidationError):
                CreateMemoryRequest(
                    task_summary="测试总结",
                    task_name="test_task",
                    project_path=temp_file.name,
                )


class TestCursorMemoryMCP:
    """测试CursorMemoryMCP服务"""

    @pytest.fixture
    def mcp_server(self):
        """创建MCP服务器实例"""
        return CursorMemoryMCP()

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录用于测试"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    def test_generate_file_content(self, mcp_server):
        """测试文件内容生成"""
        content = mcp_server._generate_file_content("测试任务", "这是任务总结")
        expected = """---
description: "get the summary of previous step: 测试任务"
globs:
alwaysApply: false
---
这是任务总结"""
        assert content == expected

    @pytest.mark.asyncio
    async def test_create_cursor_memory_success(self, mcp_server, temp_dir):
        """测试成功创建记忆文件"""
        arguments = {
            "task_summary": "成功完成了用户登录功能的实现",
            "task_name": "user_login_implementation",
            "task_description": "实现用户登录系统",
            "project_path": str(temp_dir),
        }

        result = await mcp_server._create_cursor_memory(arguments)

        # 验证返回结果
        assert len(result) == 1
        response_text = result[0]["text"]
        response_data = json.loads(response_text)

        assert response_data["success"] is True
        assert response_data["message"] == "成功创建记忆文件"
        # 验证返回的是绝对路径，使用规范化路径进行比较
        cursor_dir = temp_dir / ".cursor" / "rules"
        expected_file_path = cursor_dir / "user_login_implementation.mdc"
        # 将两个路径都规范化后再比较
        assert (
            Path(response_data["file_path"]).resolve() == expected_file_path.resolve()
        )
        assert "created_at" in response_data

        # 验证文件是否创建
        assert cursor_dir.exists()

        file_path = cursor_dir / "user_login_implementation.mdc"
        assert file_path.exists()

        # 验证文件内容
        content = file_path.read_text(encoding="utf-8")
        expected_content = """---
description: "get the summary of previous step: 实现用户登录系统"
globs:
alwaysApply: false
---
成功完成了用户登录功能的实现"""
        assert content == expected_content

    @pytest.mark.asyncio
    async def test_create_cursor_memory_duplicate_filename(self, mcp_server, temp_dir):
        """测试重复文件名处理"""
        # 先创建一个文件
        cursor_dir = temp_dir / ".cursor" / "rules"
        cursor_dir.mkdir(parents=True)
        existing_file = cursor_dir / "test_task.mdc"
        existing_file.write_text("existing content")

        arguments = {
            "task_summary": "这是第二个任务",
            "task_name": "test_task",
            "project_path": str(temp_dir),
        }

        # 模拟当前时间
        mock_time = datetime(2024, 1, 1, 12, 0, 0)
        with patch("cursor_memory_mcp.server.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_time
            mock_datetime.strftime = mock_time.strftime

            result = await mcp_server._create_cursor_memory(arguments)

        # 验证返回结果
        response_data = json.loads(result[0]["text"])
        assert response_data["success"] is True
        assert "文件名已调整为" in response_data["message"]

        # 验证新文件被创建
        new_file = cursor_dir / "test_task_20240101_120000.mdc"
        assert new_file.exists()

    @pytest.mark.asyncio
    async def test_create_cursor_memory_validation_error(self, mcp_server):
        """测试参数验证错误"""
        arguments = {
            "task_summary": "",  # 空的总结
            "task_name": "invalid name",  # 包含空格的名称
            "project_path": "/nonexistent/path",  # 不存在的路径
        }

        result = await mcp_server._create_cursor_memory(arguments)

        # 验证错误响应
        response_data = json.loads(result[0]["text"])
        assert "error" in response_data
        assert "参数验证失败" in response_data["error"]

    @pytest.mark.asyncio
    async def test_create_cursor_memory_default_description(self, mcp_server, temp_dir):
        """测试默认描述设置"""
        arguments = {
            "task_summary": "任务总结",
            "task_name": "test_task",
            "project_path": str(temp_dir),
            # 没有提供task_description
        }

        result = await mcp_server._create_cursor_memory(arguments)

        # 验证文件内容使用了task_name作为默认描述
        cursor_dir = temp_dir / ".cursor" / "rules"
        file_path = cursor_dir / "test_task.mdc"
        content = file_path.read_text(encoding="utf-8")

        assert 'description: "get the summary of previous step: test_task"' in content

    @pytest.mark.asyncio
    async def test_create_cursor_memory_permission_error(self, mcp_server, temp_dir):
        """测试权限错误处理"""
        arguments = {
            "task_summary": "任务总结",
            "task_name": "test_task",
            "project_path": str(temp_dir),
        }

        # 模拟无法创建目录的情况
        with patch(
            "pathlib.Path.mkdir", side_effect=PermissionError("Permission denied")
        ):
            result = await mcp_server._create_cursor_memory(arguments)

            # 验证错误响应
            response_data = json.loads(result[0]["text"])
            assert "error" in response_data
            assert "文件操作失败" in response_data["error"]


@pytest.mark.asyncio
async def test_tool_listing():
    """测试工具列表功能"""
    mcp_server = CursorMemoryMCP()

    # 直接调用list_tools方法可能需要特殊处理，因为它是装饰器
    # 这里我们验证服务器是否正确初始化
    assert mcp_server.server is not None
    assert mcp_server.server.name == "cursor-memory-mcp"


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
