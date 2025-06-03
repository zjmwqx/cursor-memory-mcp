"""
pytest配置文件

配置pytest测试环境和fixture
"""

import shutil
import tempfile
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def test_project_root():
    """创建临时项目根目录"""
    temp_dir = tempfile.mkdtemp(prefix="cursor_mcp_test_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="function")
def temp_cursor_dir(test_project_root):
    """为每个测试创建临时.cursor目录"""
    cursor_dir = Path(test_project_root) / ".cursor"
    cursor_dir.mkdir(exist_ok=True)
    yield cursor_dir
    if cursor_dir.exists():
        shutil.rmtree(cursor_dir)


@pytest.fixture(scope="function")
def sample_task_params():
    """提供示例任务参数"""
    return {
        "task_name": "test_task",
        "task_summary": "这是一个测试任务的摘要",
        "task_description": "测试任务的详细描述",
    }


@pytest.fixture(scope="function")
def mcp_request_format():
    """提供标准MCP请求格式"""
    return {
        "method": "tools/call",
        "params": {"name": "create_cursor_memory", "arguments": {}},
    }


# pytest配置选项
def pytest_addoption(parser):
    """添加自定义pytest命令行选项"""
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="运行慢速测试（压力测试和性能测试）",
    )

    parser.addoption(
        "--run-integration", action="store_true", default=False, help="运行集成测试"
    )


def pytest_configure(config):
    """配置pytest标记"""
    config.addinivalue_line("markers", "slow: 标记慢速测试（压力测试、性能测试）")
    config.addinivalue_line("markers", "integration: 标记集成测试")
    config.addinivalue_line("markers", "edge_case: 标记边界情况测试")


def pytest_collection_modifyitems(config, items):
    """根据命令行选项修改测试收集"""
    if not config.getoption("--run-slow"):
        skip_slow = pytest.mark.skip(reason="需要 --run-slow 选项来运行慢速测试")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)

    if not config.getoption("--run-integration"):
        skip_integration = pytest.mark.skip(
            reason="需要 --run-integration 选项来运行集成测试"
        )
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)
