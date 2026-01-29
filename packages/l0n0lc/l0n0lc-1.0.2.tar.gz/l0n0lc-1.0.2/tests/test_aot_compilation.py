"""
AOT (Ahead-Of-Time) 预编译测试

测试包扫描、批量编译、CLI 工具等功能
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# 添加父目录到路径以导入 l0n0lc
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import l0n0lc as lc


def test_包扫描器_基础():
    """测试包扫描器基础功能"""
    # 创建临时目录和测试文件
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建测试文件
        test_file = Path(tmpdir) / "test_module.py"
        test_file.write_text("""
import l0n0lc as lc

@lc.jit()
def func1(x: int) -> int:
    return x * 2

@lc.jit()
def func2(x: int, y: int) -> int:
    return x + y

def normal_func(x: int) -> int:
    return x + 1
""")

        # 扫描目录
        扫描器 = lc.包扫描器(tmpdir)
        jit函数列表 = 扫描器.扫描目录(递归=True, 包含测试=True)

        # 验证结果
        assert len(jit函数列表) == 2, f"应该找到 2 个 JIT 函数，实际找到 {len(jit函数列表)}"

        函数名列表 = [f.函数名 for f in jit函数列表]
        assert "func1" in 函数名列表
        assert "func2" in 函数名列表
        assert "normal_func" not in 函数名列表

        print("✓ test_包扫描器_基础 通过")


def test_包扫描器_排除目录():
    """测试包扫描器排除目录功能"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建主文件
        (Path(tmpdir) / "main.py").write_text("""
import l0n0lc as lc

@lc.jit()
def main_func(x: int) -> int:
    return x
""")

        # 创建排除目录中的文件
        排除目录 = Path(tmpdir) / "venv"
        排除目录.mkdir()
        (排除目录 / "excluded.py").write_text("""
import l0n0lc as lc

@lc.jit()
def excluded_func(x: int) -> int:
    return x
""")

        # 扫描目录
        扫描器 = lc.包扫描器(tmpdir)
        jit函数列表 = 扫描器.扫描目录(递归=True)

        # 验证只找到主文件中的函数
        assert len(jit函数列表) == 1
        assert jit函数列表[0].函数名 == "main_func"

        print("✓ test_包扫描器_排除目录 通过")


def test_包扫描器_排除测试文件():
    """测试包扫描器排除测试文件功能"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建普通文件
        (Path(tmpdir) / "module.py").write_text("""
import l0n0lc as lc

@lc.jit()
def normal_func(x: int) -> int:
    return x
""")

        # 创建测试文件
        (Path(tmpdir) / "test_module.py").write_text("""
import l0n0lc as lc

@lc.jit()
def test_func(x: int) -> int:
    return x
""")

        # 扫描目录（不包含测试）
        扫描器 = lc.包扫描器(tmpdir)
        jit函数列表 = 扫描器.扫描目录(递归=True, 包含测试=False)

        # 验证只找到普通文件中的函数
        assert len(jit函数列表) == 1
        assert jit函数列表[0].函数名 == "normal_func"

        print("✓ test_包扫描器_排除测试文件 通过")


def test_AOT编译器_单函数():
    """测试 AOT 编译器编译单个函数"""
    @lc.jit()
    def test_func(x: int) -> int:
        return x * 2

    # 创建 AOT 编译器
    编译器 = lc.AOT编译器(优化级别="O0", 启用并行编译=False)

    # 手动创建 JIT 函数信息
    信息 = lc.JIT函数信息(
        函数名="test_func",
        函数对象=test_func,
        模块名=__name__,
        源文件路径=__file__,
        行号=1
    )

    # 编译函数
    结果 = 编译器._编译单个函数(信息)

    # 验证编译成功
    assert 结果["状态"] == "成功", f"编译失败: {结果.get('错误')}"
    assert 结果["函数名"] == "test_func"

    # 验证可以调用
    assert test_func(5) == 10

    print("✓ test_AOT编译器_单函数 通过")


def test_AOT编译器_批量编译():
    """测试 AOT 编译器批量编译"""
    # 定义多个 JIT 函数
    @lc.jit()
    def func_a(x: int) -> int:
        return x + 1

    @lc.jit()
    def func_b(x: int) -> int:
        return x * 2

    @lc.jit()
    def func_c(x: int) -> int:
        return x - 1

    # 创建 JIT 函数信息列表
    jit函数列表 = [
        lc.JIT函数信息(
            函数名="func_a",
            函数对象=func_a,
            模块名=__name__,
            源文件路径=__file__,
            行号=1
        ),
        lc.JIT函数信息(
            函数名="func_b",
            函数对象=func_b,
            模块名=__name__,
            源文件路径=__file__,
            行号=10
        ),
        lc.JIT函数信息(
            函数名="func_c",
            函数对象=func_c,
            模块名=__name__,
            源文件路径=__file__,
            行号=20
        ),
    ]

    # 创建 AOT 编译器并编译
    编译器 = lc.AOT编译器(优化级别="O0", 启用并行编译=False)
    统计 = 编译器.编译函数列表(jit函数列表, 显示进度=False)

    # 验证编译统计
    assert 统计["总数"] == 3
    assert 统计["成功"] == 3
    assert 统计["失败"] == 0

    # 验证函数可以调用
    assert func_a(5) == 6
    assert func_b(5) == 10
    assert func_c(5) == 4

    print("✓ test_AOT编译器_批量编译 通过")


def test_编译包_简单场景():
    """测试编译包的简单场景"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建测试文件
        test_file = Path(tmpdir) / "simple.py"
        test_file.write_text("""
import l0n0lc as lc

@lc.jit()
def add(x: int, y: int) -> int:
    return x + y

@lc.jit()
def multiply(x: int, y: int) -> int:
    return x * y
""")

        # 编译包
        统计 = lc.编译包(
            根目录=tmpdir,
            递归=True,
            包含测试=True,
            优化级别="O0",
            启用并行编译=False,
            显示进度=False
        )

        # 验证编译结果
        assert 统计["总数"] == 2
        assert 统计["成功"] == 2
        assert 统计["失败"] == 0

        print("✓ test_编译包_简单场景 通过")


def test_编译函数列表():
    """测试编译函数列表 API"""
    # 定义几个函数
    @lc.jit()
    def square(x: int) -> int:
        return x * x

    @lc.jit()
    def cube(x: int) -> int:
        return x * x * x

    # 编译函数列表
    统计 = lc.编译函数列表(
        函数列表=[square, cube],
        优化级别="O0",
        启用并行编译=False,
        显示进度=False
    )

    # 验证编译结果
    assert 统计["总数"] == 2
    assert 统计["成功"] == 2
    assert 统计["失败"] == 0

    # 验证函数可以正常调用
    assert square(3) == 9
    assert cube(3) == 27

    print("✓ test_编译函数列表 通过")


def test_JIT函数信息_带装饰器参数():
    """测试 JIT 函数信息提取装饰器参数"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建带装饰器参数的测试文件
        test_file = Path(tmpdir) / "params.py"
        test_file.write_text("""
import l0n0lc as lc

@lc.jit(优化级别="O3")
def optimized_func(x: int) -> int:
    return x * 2

@lc.jit(总是重编=True)
def recompile_func(x: int) -> int:
    return x + 1
""")

        # 扫描文件
        扫描器 = lc.包扫描器(tmpdir)
        jit函数列表 = 扫描器.扫描目录(递归=True, 包含测试=True)

        # 验证找到了函数
        assert len(jit函数列表) == 2

        # 验证装饰器参数被提取
        函数映射 = {f.函数名: f for f in jit函数列表}
        assert "optimized_func" in 函数映射
        assert "recompile_func" in 函数映射

        print("✓ test_JIT函数信息_带装饰器参数 通过")


def test_AOT_缓存命中():
    """测试 AOT 编译使用缓存"""
    @lc.jit()
    def cached_func(x: int) -> int:
        return x + 1

    # 第一次编译
    信息1 = lc.JIT函数信息(
        函数名="cached_func",
        函数对象=cached_func,
        模块名=__name__,
        源文件路径=__file__,
        行号=1
    )
    编译器1 = lc.AOT编译器(优化级别="O0")
    结果1 = 编译器1._编译单个函数(信息1)

    # 验证第一次编译成功
    assert 结果1["状态"] == "成功"
    assert 结果1.get("使用缓存", False) == False

    # 第二次"编译"（应该使用缓存）
    信息2 = lc.JIT函数信息(
        函数名="cached_func",
        函数对象=cached_func,
        模块名=__name__,
        源文件路径=__file__,
        行号=1
    )
    编译器2 = lc.AOT编译器(优化级别="O0")
    结果2 = 编译器2._编译单个函数(信息2)

    # 验证使用了缓存
    assert 结果2["状态"] == "成功"
    assert 结果2.get("使用缓存", False) == True

    print("✓ test_AOT_缓存命中 通过")


def run_all_tests():
    """运行所有测试"""
    print("=== AOT 编译测试套件 ===\n")

    tests = [
        test_包扫描器_基础,
        test_包扫描器_排除目录,
        test_包扫描器_排除测试文件,
        test_AOT编译器_单函数,
        test_AOT编译器_批量编译,
        test_编译包_简单场景,
        test_编译函数列表,
        test_JIT函数信息_带装饰器参数,
        test_AOT_缓存命中,
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
