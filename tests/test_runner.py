"""
测试运行器

提供不同级别的测试执行选项：
- 快速测试：基本功能测试
- 完整测试：包含边界情况和性能测试
- 压力测试：长时间运行的压力测试
"""

import argparse
import os
import sys
import time
import unittest
from pathlib import Path

# 添加源代码目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入测试模块
from tests.test_cursor_memory_mcp import (
    TestCursorMemoryMCP,
    TestCursorMemoryMCPPerformance,
)
from tests.test_edge_cases import TestEdgeCases, TestStressTests
from tests.test_mcp_tools import TestMCPServerIntegration, TestMCPToolCalls


class CustomTestResult(unittest.TestResult):
    """自定义测试结果类，提供更详细的输出"""

    def __init__(self, stream=None, descriptions=None, verbosity=1):
        super().__init__()
        self.stream = stream or sys.stdout
        self.descriptions = descriptions
        self.verbosity = verbosity
        self.start_time = None
        self.test_times = {}

    def startTest(self, test):
        super().startTest(test)
        self.start_time = time.time()
        if self.verbosity > 1:
            self.stream.write(f"运行测试: {test._testMethodName} ... ")
            self.stream.flush()

    def stopTest(self, test):
        super().stopTest(test)
        if self.start_time:
            duration = time.time() - self.start_time
            self.test_times[test._testMethodName] = duration

    def addSuccess(self, test):
        super().addSuccess(test)
        if self.verbosity > 1:
            duration = self.test_times.get(test._testMethodName, 0)
            self.stream.write(f"通过 ({duration:.3f}s)\n")

    def addError(self, test, err):
        super().addError(test, err)
        if self.verbosity > 1:
            self.stream.write("错误\n")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        if self.verbosity > 1:
            self.stream.write("失败\n")

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        if self.verbosity > 1:
            self.stream.write(f"跳过: {reason}\n")


class TestRunner:
    """测试运行器类"""

    def __init__(self):
        self.total_tests = 0
        self.total_time = 0

    def create_test_suite(self, test_level="basic"):
        """根据测试级别创建测试套件"""
        suite = unittest.TestSuite()

        if test_level in ["basic", "full", "stress"]:
            # 基本功能测试
            suite.addTest(
                unittest.TestLoader().loadTestsFromTestCase(TestCursorMemoryMCP)
            )
            suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestMCPToolCalls))

        if test_level in ["full", "stress"]:
            # 完整测试（包含性能和集成测试）
            suite.addTest(
                unittest.TestLoader().loadTestsFromTestCase(
                    TestCursorMemoryMCPPerformance
                )
            )
            suite.addTest(
                unittest.TestLoader().loadTestsFromTestCase(TestMCPServerIntegration)
            )
            suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestEdgeCases))

        if test_level == "stress":
            # 压力测试
            suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestStressTests))

        return suite

    def run_tests(self, test_level="basic", verbosity=2, failfast=False):
        """运行测试"""
        print("=== Cursor Memory MCP 测试运行器 ===")
        print(f"测试级别: {test_level}")
        print(f"详细程度: {verbosity}")
        print("=" * 50)

        # 创建测试套件
        suite = self.create_test_suite(test_level)

        # 创建测试运行器
        runner = unittest.TextTestRunner(
            verbosity=verbosity, failfast=failfast, resultclass=CustomTestResult
        )

        # 记录开始时间
        start_time = time.time()

        # 运行测试
        result = runner.run(suite)

        # 记录结束时间
        end_time = time.time()
        self.total_time = end_time - start_time

        # 输出测试结果摘要
        self.print_test_summary(result)

        return result.wasSuccessful()

    def print_test_summary(self, result):
        """打印测试结果摘要"""
        print("\n" + "=" * 50)
        print("测试结果摘要")
        print("=" * 50)

        total_tests = result.testsRun
        failures = len(result.failures)
        errors = len(result.errors)
        skipped = len(result.skipped)
        successful = total_tests - failures - errors - skipped

        print(f"总测试数: {total_tests}")
        print(f"成功: {successful}")
        print(f"失败: {failures}")
        print(f"错误: {errors}")
        print(f"跳过: {skipped}")
        print(f"总耗时: {self.total_time:.2f}秒")

        if total_tests > 0:
            success_rate = (successful / total_tests) * 100
            print(f"成功率: {success_rate:.1f}%")

        # 如果有失败或错误，显示详情
        if failures:
            print(f"\n失败的测试 ({len(failures)}):")
            for test, traceback in result.failures:
                print(f"  - {test}")

        if errors:
            print(f"\n错误的测试 ({len(errors)}):")
            for test, traceback in result.errors:
                print(f"  - {test}")

        print("=" * 50)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Cursor Memory MCP 测试运行器")

    parser.add_argument(
        "--level",
        "-l",
        choices=["basic", "full", "stress"],
        default="basic",
        help="测试级别 (默认: basic)",
    )

    parser.add_argument(
        "--verbosity",
        "-v",
        type=int,
        choices=[0, 1, 2],
        default=2,
        help="输出详细程度 (0=静默, 1=简单, 2=详细, 默认: 2)",
    )

    parser.add_argument(
        "--failfast", "-f", action="store_true", help="遇到第一个失败就停止"
    )

    parser.add_argument(
        "--specific", "-s", help="运行特定的测试类 (例如: TestCursorMemoryMCP)"
    )

    parser.add_argument(
        "--method",
        "-m",
        help="运行特定的测试方法 (例如: test_successful_file_creation)",
    )

    args = parser.parse_args()

    # 如果指定了特定测试，运行特定测试
    if args.specific or args.method:
        suite = unittest.TestSuite()

        if args.specific and args.method:
            # 运行特定类的特定方法
            test_class = globals().get(args.specific)
            if test_class:
                suite.addTest(test_class(args.method))
            else:
                print(f"错误: 找不到测试类 {args.specific}")
                return 1

        elif args.specific:
            # 运行特定类的所有测试
            test_class = globals().get(args.specific)
            if test_class:
                suite.addTest(unittest.TestLoader().loadTestsFromTestCase(test_class))
            else:
                print(f"错误: 找不到测试类 {args.specific}")
                return 1

        runner = unittest.TextTestRunner(
            verbosity=args.verbosity, failfast=args.failfast
        )
        result = runner.run(suite)
        return 0 if result.wasSuccessful() else 1

    # 运行完整测试套件
    test_runner = TestRunner()
    success = test_runner.run_tests(
        test_level=args.level, verbosity=args.verbosity, failfast=args.failfast
    )

    return 0 if success else 1


if __name__ == "__main__":
    # 设置环境变量
    os.environ["PYTHONPATH"] = str(project_root)

    # 运行测试
    exit_code = main()
    sys.exit(exit_code)
