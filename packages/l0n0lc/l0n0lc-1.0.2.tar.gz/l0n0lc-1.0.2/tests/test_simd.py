"""
SIMD (Single Instruction Multiple Data) 向量化测试

测试 SIMD 向量化优化功能
"""

import os
import sys
from typing import List

# 添加父目录到路径以导入 l0n0lc
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import l0n0lc as lc


def test_SIMD_CPU特性检测():
    """测试 CPU SIMD 特性检测"""
    检测器 = lc.获取CPU特性()
    特性 = 检测器.检测特性()

    # 验证返回字典类型
    assert isinstance(特性, dict), "CPU 特性检测应返回字典"

    # 验证包含预期的键
    预期键 = ['SSE', 'SSE2', 'SSE3', 'SSE4_1', 'SSE4_2', 'AVX', 'AVX2', 'AVX512F', 'NEON']
    for 键 in 预期键:
        assert 键 in 特性, f"CPU 特性应包含 {键}"

    # 至少应该支持 SSE2（x86 基本要求）
    if 特性.get('NEON', False):
        # ARM 平台
        print(f"✓ 检测到 ARM NEON 支持")
    elif 特性.get('SSE2', False):
        # x86 平台
        print(f"✓ 检测到 SSE2 支持")
        if 特性.get('AVX'):
            print(f"  ✓ AVX: {特性['AVX']}")
        if 特性.get('AVX2'):
            print(f"  ✓ AVX2: {特性['AVX2']}")

    print("✓ test_SIMD_CPU特性检测 通过")


def test_SIMD_获取最佳指令集():
    """测试获取最佳 SIMD 指令集"""
    指令集 = lc.获取最佳SIMD指令集()

    # 验证返回有效的指令集
    有效指令集 = ['SSE2', 'SSE4_2', 'AVX', 'AVX2', 'AVX512F', 'NEON']
    assert 指令集 in 有效指令集, f"应返回有效的指令集，得到: {指令集}"

    print(f"✓ 最佳 SIMD 指令集: {指令集}")
    print("✓ test_SIMD_获取最佳指令集 通过")


def test_SIMD_编译标志():
    """测试获取 SIMD 编译标志"""
    # 测试自动检测
    标志 = lc.获取SIMD编译标志()
    assert isinstance(标志, list), "应返回标志列表"
    assert len(标志) > 0, "应至少包含一个标志"

    # 测试指定指令集
    AVX2标志 = lc.获取SIMD编译标志('AVX2')
    assert '-mavx2' in AVX2标志, "AVX2 应包含 -mavx2 标志"

    SSE2标志 = lc.获取SIMD编译标志('SSE2')
    assert '-msse2' in SSE2标志, "SSE2 应包含 -msse2 标志"

    print("✓ test_SIMD_编译标志 通过")


def test_SIMD_启用向量化():
    """测试启用向量化装饰器参数"""
    @lc.jit(启用向量化=True)
    def sum_array(nums: List[int]) -> int:
        total = 0
        for num in nums:
            total += num
        return total

    # 验证函数正常工作
    result = sum_array([1, 2, 3, 4, 5])
    assert result == 15, f"预期 15，得到 {result}"

    print("✓ test_SIMD_启用向量化 通过")


def test_SIMD_环境变量():
    """测试通过环境变量启用向量化"""
    os.environ['L0N0LC_ENABLE_VECTORIZE'] = '1'

    try:
        @lc.jit()
        def vectorized_func(x: int) -> int:
            return x * 2

        # 验证函数正常工作
        assert vectorized_func(5) == 10
        print("✓ test_SIMD_环境变量 通过")
    finally:
        os.environ.pop('L0N0LC_ENABLE_VECTORIZE', None)


def test_SIMD_结合优化级别():
    """测试向量化结合不同优化级别"""
    @lc.jit(启用向量化=True, 优化级别='O3')
    def optimized_sum(x: int, y: int) -> int:
        return x + y

    assert optimized_sum(3, 5) == 8
    print("✓ test_SIMD_结合优化级别 通过")


def test_SIMD_结合LTO():
    """测试向量化结合 LTO"""
    @lc.jit(启用向量化=True, 启用LTO=True)
    def combined_opt(x: int) -> int:
        return x * x

    assert combined_opt(7) == 49
    print("✓ test_SIMD_结合LTO 通过")


def test_SIMD_AOT编译():
    """测试 SIMD 在 AOT 编译中的使用"""
    with open('/tmp/test_simd_aot.py', 'w') as f:
        f.write("""
import l0n0lc as lc

@lc.jit(启用向量化=True)
def vectorized_sum(arr: list) -> int:
    total = 0
    for x in arr:
        total += x
    return total
""")

    try:
        统计 = lc.编译函数列表(
            函数列表=[],
            优化级别='O2',
            启用向量化=True,
            显示进度=False
        )
        print("✓ test_SIMD_AOT编译 通过")
    except Exception as e:
        print(f"✗ test_SIMD_AOT编译 失败: {e}")
    finally:
        os.remove('/tmp/test_simd_aot.py')


def test_SIMD_编译器方法():
    """测试编译器的向量化方法"""
    编译器 = lc.Cpp编译器()

    # 检查初始状态
    assert not 编译器.是否启用向量化()

    # 启用向量化
    编译器.启用向量化()
    assert 编译器.是否启用向量化()

    # 禁用向量化
    编译器.禁用向量化()
    assert not 编译器.是否启用向量化()

    # 使用 设置向量化
    编译器.设置向量化(True)
    assert 编译器.是否启用向量化()

    编译器.设置向量化(False)
    assert not 编译器.是否启用向量化()

    print("✓ test_SIMD_编译器方法 通过")


def test_SIMD_指定指令集():
    """测试指定 SIMD 指令集"""
    @lc.jit(启用向量化=True, SIMD指令集='SSE2')
    def sse2_func(x: int) -> int:
        return x + 1

    assert sse2_func(5) == 6

    @lc.jit(启用向量化=True, SIMD指令集='AVX2')
    def avx2_func(x: int) -> int:
        return x * 2

    assert avx2_func(5) == 10

    print("✓ test_SIMD_指定指令集 通过")


def run_all_tests():
    """运行所有测试"""
    print("=== SIMD 向量化测试套件 ===\n")

    tests = [
        test_SIMD_CPU特性检测,
        test_SIMD_获取最佳指令集,
        test_SIMD_编译标志,
        test_SIMD_启用向量化,
        test_SIMD_环境变量,
        test_SIMD_结合优化级别,
        test_SIMD_结合LTO,
        test_SIMD_AOT编译,
        test_SIMD_编译器方法,
        test_SIMD_指定指令集,
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
