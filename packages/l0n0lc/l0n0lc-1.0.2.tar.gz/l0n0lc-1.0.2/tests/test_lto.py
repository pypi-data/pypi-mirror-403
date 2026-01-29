"""
LTO (Link-Time Optimization) 测试

测试链接时优化功能
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import List

# 添加父目录到路径以导入 l0n0lc
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import l0n0lc as lc


def test_LTO_基础功能():
    """测试 LTO 基础功能"""
    @lc.jit(启用LTO=True)
    def add_with_lto(x: int, y: int) -> int:
        return x + y

    @lc.jit(启用LTO=False)
    def add_without_lto(x: int, y: int) -> int:
        return x + y

    # 验证两个函数都能正常工作
    assert add_with_lto(3, 5) == 8
    assert add_without_lto(3, 5) == 8

    print("✓ test_LTO_基础功能 通过")


def test_LTO_环境变量():
    """测试通过环境变量启用 LTO"""
    # 设置环境变量
    os.environ['L0N0LC_ENABLE_LTO'] = '1'

    try:
        @lc.jit()
        def func_with_env(x: int) -> int:
            return x * 2

        # 验证函数正常工作
        assert func_with_env(5) == 10
        print("✓ test_LTO_环境变量 通过")
    finally:
        # 清理环境变量
        os.environ.pop('L0N0LC_ENABLE_LTO', None)


def test_LTO_环境变量_false():
    """测试环境变量设置为 false"""
    os.environ['L0N0LC_ENABLE_LTO'] = '0'

    try:
        @lc.jit()
        def func_with_env_false(x: int) -> int:
            return x * 3

        assert func_with_env_false(5) == 15
        print("✓ test_LTO_环境变量_false 通过")
    finally:
        os.environ.pop('L0N0LC_ENABLE_LTO', None)


def test_LTO_装饰器参数优先():
    """测试装饰器参数优先于环境变量"""
    os.environ['L0N0LC_ENABLE_LTO'] = '1'

    try:
        # 装饰器参数 False 应该覆盖环境变量 True
        @lc.jit(启用LTO=False)
        def func_override(x: int) -> int:
            return x + 1

        assert func_override(5) == 6
        print("✓ test_LTO_装饰器参数优先 通过")
    finally:
        os.environ.pop('L0N0LC_ENABLE_LTO', None)


def test_LTO_结合优化级别():
    """测试 LTO 结合不同优化级别"""
    @lc.jit(优化级别='O0', 启用LTO=True)
    def o0_lto(x: int) -> int:
        return x * x

    @lc.jit(优化级别='O3', 启用LTO=True)
    def o3_lto(x: int) -> int:
        return x * x

    @lc.jit(优化级别='O2', 启用LTO=False)
    def o2_no_lto(x: int) -> int:
        return x * x

    # 验证所有组合都能正常工作
    assert o0_lto(5) == 25
    assert o3_lto(5) == 25
    assert o2_no_lto(5) == 25

    print("✓ test_LTO_结合优化级别 通过")


def test_LTO_依赖函数():
    """测试 LTO 与依赖函数的交互"""
    @lc.jit()
    def helper(x: int) -> int:
        return x + 1

    @lc.jit(启用LTO=True)
    def use_helper(x: int) -> int:
        return helper(x) * 2

    # 验证函数调用依赖函数正常工作
    assert use_helper(5) == 12  # helper(5) = 6, 6 * 2 = 12
    print("✓ test_LTO_依赖函数 通过")


def test_LTO_多次调用():
    """测试 LTO 函数的多次调用"""
    @lc.jit(启用LTO=True)
    def repeated_call(x: int) -> int:
        return x + x

    # 多次调用确保缓存正常工作
    for i in range(10):
        result = repeated_call(i)
        expected = i + i
        assert result == expected, f"expected {expected}, got {result}"

    print("✓ test_LTO_多次调用 通过")


def test_LTO_不同类型():
    """测试 LTO 与不同类型参数"""
    @lc.jit(启用LTO=True)
    def int_func(x: int) -> int:
        return x * 2

    @lc.jit(启用LTO=True)
    def float_func(x: float) -> float:
        return x * 2.0

    assert int_func(5) == 10
    assert float_func(2.5) == 5.0

    print("✓ test_LTO_不同类型 通过")


def test_LTO_列表参数():
    """测试 LTO 与列表参数"""
    @lc.jit(启用LTO=True)
    def sum_list(nums: List[int]) -> int:
        total = 0
        for num in nums:
            total += num
        return total

    assert sum_list([1, 2, 3, 4, 5]) == 15

    print("✓ test_LTO_列表参数 通过")


def test_LTO_AOT编译():
    """测试 LTO 在 AOT 编译中的使用"""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "lto_test.py"
        test_file.write_text("""
import l0n0lc as lc

@lc.jit(启用LTO=True)
def lto_func(x: int) -> int:
    return x * x

@lc.jit(启用LTO=False)
def no_lto_func(x: int) -> int:
    return x * x
""")

        # 使用 AOT 编译
        统计 = lc.编译包(
            根目录=tmpdir,
            递归=True,
            包含测试=True,
            优化级别="O2",
            启用LTO=True,
            显示进度=False
        )

        # 验证编译成功
        assert 统计["成功"] == 2
        assert 统计["失败"] == 0

        print("✓ test_LTO_AOT编译 通过")


def test_LTO_编译器方法():
    """测试编译器的 LTO 方法"""
    # 创建编译器实例
    编译器 = lc.Cpp编译器(优化级别='O2', 启用LTO=False)

    # 检查初始状态
    assert not 编译器.是否启用LTO()

    # 启用 LTO
    编译器.启用LTO()
    assert 编译器.是否启用LTO()

    # 禁用 LTO
    编译器.禁用LTO()
    assert not 编译器.是否启用LTO()

    # 使用 设置LTO
    编译器.设置LTO(True)
    assert 编译器.是否启用LTO()

    编译器.设置LTO(False)
    assert not 编译器.是否启用LTO()

    print("✓ test_LTO_编译器方法 通过")


def run_all_tests():
    """运行所有测试"""
    print("=== LTO 测试套件 ===\n")

    tests = [
        test_LTO_基础功能,
        test_LTO_环境变量,
        test_LTO_环境变量_false,
        test_LTO_装饰器参数优先,
        test_LTO_结合优化级别,
        test_LTO_依赖函数,
        test_LTO_多次调用,
        test_LTO_不同类型,
        test_LTO_列表参数,
        test_LTO_AOT编译,
        test_LTO_编译器方法,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} 失败: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} 错误: {e}")
            failed += 1

    print(f"\n=== 测试结果: {passed} 通过, {failed} 失败 ===")
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
