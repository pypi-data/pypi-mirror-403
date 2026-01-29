#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
并行编译测试

测试 JIT 编译器的并行编译功能。
"""
import sys
import pathlib
import time
import os
sys.path.append(str(pathlib.Path(__file__).parent.parent))

import l0n0lc as lc


def 清理缓存():
    """清理所有编译缓存"""
    import shutil
    缓存目录 = "l0n0lcoutput"
    if os.path.exists(缓存目录):
        shutil.rmtree(缓存目录)


def test_parallel_compilation():
    """测试并行编译多个独立函数"""
    print("\n=== 测试并行编译 ===")

    清理缓存()

    # 定义多个独立的依赖函数
    @lc.jit()
    def func_a(x: int) -> int:
        result = 0
        for i in range(x):
            result += i
        return result

    @lc.jit()
    def func_b(x: int) -> int:
        result = 1
        for i in range(1, x):
            result *= i
        return result

    @lc.jit()
    def func_c(x: int) -> int:
        result = 0
        for i in range(x):
            result += i * i
        return result

    # 定义调用这些依赖的主函数
    @lc.jit(启用并行编译=True)
    def main_func(x: int) -> int:
        a = func_a(x)
        b = func_b(x)
        c = func_c(x)
        return a + b + c

    # 调用主函数，触发并行编译
    result = main_func(10)
    print(f"✓ 并行编译结果: {result}")

    # 验证结果
    # func_a(10) = 0+1+2+...+9 = 45
    # func_b(10) = 1*1*2*...*9 = 362880
    # func_c(10) = 0^2+1^2+...+9^2 = 285
    expected = 45 + 362880 + 285
    assert result == expected, f"结果不匹配: {result} != {expected}"

    print("✓ 并行编译测试通过")


def test_disable_parallel_compilation():
    """测试禁用并行编译"""
    print("\n=== 测试禁用并行编译 ===")

    清理缓存()

    @lc.jit()
    def dep_func(x: int) -> int:
        return x * 2

    @lc.jit(启用并行编译=False)
    def main_func(x: int) -> int:
        return dep_func(x) + 1

    result = main_func(5)
    print(f"✓ 禁用并行编译结果: {result}")
    assert result == 11  # (5 * 2) + 1 = 11

    print("✓ 禁用并行编译测试通过")


def test_max_processes():
    """测试限制最大进程数"""
    print("\n=== 测试限制最大进程数 ===")

    清理缓存()

    @lc.jit()
    def func1(x: int) -> int:
        return x + 1

    @lc.jit()
    def func2(x: int) -> int:
        return x + 2

    @lc.jit()
    def func3(x: int) -> int:
        return x + 3

    @lc.jit(最大进程数=2)  # 限制最多使用 2 个进程
    def main_func(x: int) -> int:
        a = func1(x)
        b = func2(x)
        c = func3(x)
        return a + b + c

    result = main_func(10)
    print(f"✓ 限制进程数结果: {result}")
    assert result == (11 + 12 + 13)  # 10+1 + 10+2 + 10+3 = 36

    print("✓ 限制进程数测试通过")


def test_nested_dependencies():
    """测试嵌套依赖的并行编译"""
    print("\n=== 测试嵌套依赖 ===")

    清理缓存()

    @lc.jit()
    def base_func1(x: int) -> int:
        return x + 1

    @lc.jit()
    def base_func2(x: int) -> int:
        return x * 2

    @lc.jit()
    def mid_func(x: int) -> int:
        return base_func1(x) + base_func2(x)

    @lc.jit(启用并行编译=True)
    def top_func(x: int) -> int:
        return mid_func(x) + base_func1(x) + base_func2(x)

    result = top_func(5)
    print(f"✓ 嵌套依赖结果: {result}")
    # base_func1(5) = 6, base_func2(5) = 10
    # mid_func(5) = 6 + 10 = 16
    # top_func(5) = 16 + 6 + 10 = 32
    assert result == 32

    print("✓ 嵌套依赖测试通过")


def test_performance_comparison():
    """测试并行编译的性能对比"""
    print("\n=== 测试性能对比 ===")

    # 由于 JIT 函数的缓存机制，真正的性能对比需要重新创建函数
    # 这里只做基本的功能验证，不做循环测试

    # 清理缓存
    清理缓存()

    # 创建多个依赖函数
    @lc.jit()
    def dep0(x: int) -> int:
        result = 0
        for j in range(x):
            result += j * 0
        return result

    @lc.jit()
    def dep1(x: int) -> int:
        result = 0
        for j in range(x):
            result += j * 1
        return result

    @lc.jit()
    def dep2(x: int) -> int:
        result = 0
        for j in range(x):
            result += j * 2
        return result

    @lc.jit()
    def dep3(x: int) -> int:
        result = 0
        for j in range(x):
            result += j * 3
        return result

    @lc.jit()
    def dep4(x: int) -> int:
        result = 0
        for j in range(x):
            result += j * 4
        return result

    # 测试并行编译
    @lc.jit(启用并行编译=True)
    def main_parallel(x: int) -> int:
        total = 0
        total += dep0(x)
        total += dep1(x)
        total += dep2(x)
        total += dep3(x)
        total += dep4(x)
        return total

    # 验证并行编译功能正常
    result = main_parallel(100)
    expected = sum(i * 100 * (100 - 1) // 2 for i in range(5))  # sum of series
    print(f"✓ 并行编译结果正确: {result}")
    assert result == expected, f"结果不匹配: {result} != {expected}"

    # 注意：由于 JIT 函数的缓存机制，真正的性能对比（并行 vs 串行）
    # 需要在独立的环境中运行。这里只验证功能正确性。
    # 实际性能提升取决于：
    # 1. 依赖函数的数量
    # 2. 每个依赖函数的编译时间
    # 3. CPU 核心数
    # 4. C++ 编译器的并行能力

    print("\n性能说明:")
    print("  - 并行编译主要在多个独立依赖函数编译时发挥作用")
    print("  - 当依赖函数较少时，加速比不明显")
    print("  - 真正的加速比需要在包含多个依赖的实际场景中测试")
    print("  - 默认启用并行编译，对大多数场景都有益")
    print("✓ 性能对比测试完成")


def test_cache_hit():
    """测试缓存命中时的行为"""
    print("\n=== 测试缓存命中 ===")

    清理缓存()

    @lc.jit()
    def cached_dep(x: int) -> int:
        return x * 2

    @lc.jit(启用并行编译=True)
    def main1(x: int) -> int:
        return cached_dep(x)

    @lc.jit(启用并行编译=True)
    def main2(x: int) -> int:
        return cached_dep(x)

    # 第一次调用会编译
    result1 = main1(5)
    print(f"✓ 第一次调用: {result1}")

    # 第二次调用应该使用缓存
    result2 = main2(5)
    print(f"✓ 第二次调用（缓存）: {result2}")

    assert result1 == result2 == 10

    print("✓ 缓存命中测试通过")


def main():
    """主测试函数"""
    print("=" * 70)
    print("l0n0lc 并行编译测试")
    print("=" * 70)

    try:
        test_parallel_compilation()
        test_disable_parallel_compilation()
        test_max_processes()
        test_nested_dependencies()
        test_cache_hit()
        test_performance_comparison()

        print("\n" + "=" * 70)
        print("🎉 所有并行编译测试通过!")
        print("=" * 70)

        print("\n并行编译功能说明:")
        print("  - 默认启用并行编译（启用并行编译=True）")
        print("  - 可以通过 启用并行编译=False 禁用")
        print("  - 可以通过 最大进程数 限制并行进程数")
        print("  - 支持嵌套依赖的正确编译顺序")
        print("  - 缓存机制正常工作")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
