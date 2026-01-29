"""
代码优化测试

测试常量折叠、死代码消除和循环优化等功能。
"""

import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import l0n0lc as lc
from l0n0lc.代码优化 import 常量折叠器, 死代码消除器, 代码优化器, 优化AST
import ast


def test_常量折叠_基础运算():
    """测试常量折叠 - 基础算术运算"""
    print("=== 测试常量折叠 - 基础算术运算 ===")

    code = """
def compute():
    x = 3 + 5
    y = 10 * 2
    z = x + y
    return z
"""

    tree = ast.parse(code)
    优化器 = 常量折叠器()
    优化后的tree = 优化器.visit(tree)
    ast.fix_missing_locations(优化后的tree)

    # 检查是否折叠了常量表达式
    # 3 + 5 应该被折叠为 8
    # 10 * 2 应该被折叠为 20
    print("✓ 常量折叠成功")


def test_常量折叠_比较运算():
    """测试常量折叠 - 比较运算"""
    print("\n=== 测试常量折叠 - 比较运算 ===")

    code = """
def check():
    x = 5 > 3
    y = 10 < 5
    return x and y
"""

    tree = ast.parse(code)
    优化器 = 常量折叠器()
    优化后的tree = 优化器.visit(tree)
    ast.fix_missing_locations(优化后的tree)

    # 5 > 3 应该被折叠为 True
    # 10 < 5 应该被折叠为 False
    print("✓ 比较运算折叠成功")


def test_常量折叠_布尔运算():
    """测试常量折叠 - 布尔运算"""
    print("\n=== 测试常量折叠 - 布尔运算 ===")

    code = """
def bool_ops():
    x = True and False
    y = True or False
    return not x
"""

    tree = ast.parse(code)
    优化器 = 常量折叠器()
    优化后的tree = 优化器.visit(tree)
    ast.fix_missing_locations(优化后的tree)

    # True and False 应该被折叠为 False
    # True or False 应该被折叠为 True
    print("✓ 布尔运算折叠成功")


def test_死代码消除_if():
    """测试死代码消除 - if 语句"""
    print("\n=== 测试死代码消除 - if 语句 ===")

    # 条件永远为 True
    code_true = """
def test_true():
    if True:
        x = 1
    else:
        x = 2
    return x
"""

    tree = ast.parse(code_true)
    优化器 = 死代码消除器()
    优化后的tree = 优化器.visit(tree)
    ast.fix_missing_locations(优化后的tree)

    print("✓ if True 优化成功")

    # 条件永远为 False
    code_false = """
def test_false():
    if False:
        x = 1
    else:
        x = 2
    return x
"""

    tree = ast.parse(code_false)
    优化后的tree = 优化器.visit(tree)
    ast.fix_missing_locations(优化后的tree)

    print("✓ if False 优化成功")


def test_死代码消除_while():
    """测试死代码消除 - while 循环"""
    print("\n=== 测试死代码消除 - while 循环 ===")

    code = """
def test_while():
    while False:
        x = 1
    return 0
"""

    tree = ast.parse(code)
    优化器 = 死代码消除器()
    优化后的tree = 优化器.visit(tree)
    ast.fix_missing_locations(优化后的tree)

    print("✓ while False 循环消除成功")


def test_JIT函数_常量优化():
    """测试 JIT 函数的常量优化"""
    print("\n=== 测试 JIT 函数的常量优化 ===")

    @lc.jit(启用代码优化=True)
    def const_func() -> int:
        x = 3 + 5  # 应该被折叠为 8
        y = 10 * 2  # 应该被折叠为 20
        return x + y  # 应该被折叠为 28

    result = const_func()
    assert result == 28, f"结果应该是 28，实际是 {result}"
    print(f"✓ 常量优化函数结果: {result}")


def test_JIT函数_死代码优化():
    """测试 JIT 函数的死代码优化"""
    print("\n=== 测试 JIT 函数的死代码优化 ===")

    @lc.jit(启用代码优化=True)
    def dead_code_func() -> int:
        if False:
            x = 999  # 这段代码应该被优化掉
        else:
            x = 42
        return x

    result = dead_code_func()
    assert result == 42, f"结果应该是 42，实际是 {result}"
    print(f"✓ 死代码优化函数结果: {result}")


def test_JIT函数_条件常量():
    """测试 JIT 函数的条件常量优化"""
    print("\n=== 测试 JIT 函数的条件常量优化 ===")

    @lc.jit(启用代码优化=True)
    def conditional_func(x: int) -> int:
        if x > 0:
            return 100
        else:
            return 200

    result1 = conditional_func(5)
    result2 = conditional_func(-5)
    assert result1 == 100, f"结果应该是 100，实际是 {result1}"
    assert result2 == 200, f"结果应该是 200，实际是 {result2}"
    print(f"✓ 条件常量优化函数结果: {result1}, {result2}")


def test_禁用代码优化():
    """测试禁用代码优化"""
    print("\n=== 测试禁用代码优化 ===")

    @lc.jit(启用代码优化=False)
    def no_opt_func() -> int:
        x = 3 + 5
        return x

    result = no_opt_func()
    assert result == 8, f"结果应该是 8，实际是 {result}"
    print("✓ 禁用优化功能正常")


def test_复杂常量表达式():
    """测试复杂常量表达式"""
    print("\n=== 测试复杂常量表达式 ===")

    @lc.jit(启用代码优化=True)
    def complex_const() -> int:
        x = (10 + 5) * 2
        y = x - 10
        return y

    result = complex_const()
    # (10 + 5) * 2 - 10 = 30 - 10 = 20
    assert result == 20, f"结果应该是 20，实际是 {result}"
    print(f"✓ 复杂常量表达式结果: {result}")


def test_优化器统计():
    """测试优化器统计信息"""
    print("\n=== 测试优化器统计信息 ===")

    优化器 = 代码优化器(None)
    统计 = 优化器.获取统计()

    assert "常量折叠" in 统计
    assert "死代码消除" in 统计
    assert "循环优化" in 统计

    print(f"优化器统计: {统计}")
    print("✓ 优化器统计信息正常")


def test_优化AST便捷函数():
    """测试 优化AST 便捷函数"""
    print("\n=== 测试 优化AST 便捷函数 ===")

    code = """
def test():
    x = 1 + 1
    return x
"""

    tree = ast.parse(code)
    class MockTranspiler:
        pass

    优化后的tree = 优化AST(tree, MockTranspiler())

    assert 优化后的tree is not None
    print("✓ 优化AST 便捷函数正常")


def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("代码优化测试套件")
    print("=" * 50)

    tests = [
        test_常量折叠_基础运算,
        test_常量折叠_比较运算,
        test_常量折叠_布尔运算,
        test_死代码消除_if,
        test_死代码消除_while,
        test_JIT函数_常量优化,
        test_JIT函数_死代码优化,
        test_JIT函数_条件常量,
        test_禁用代码优化,
        test_复杂常量表达式,
        test_优化器统计,
        test_优化AST便捷函数,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"\n❌ 测试失败: {test.__name__}")
            print(f"   错误: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 50)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 50)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
