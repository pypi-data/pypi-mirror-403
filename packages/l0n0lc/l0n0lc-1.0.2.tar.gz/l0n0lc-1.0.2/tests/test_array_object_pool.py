"""
数组对象池测试

测试数组对象池的功能、统计信息和性能。
"""

import ctypes
import os
import sys
import time
from typing import List

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import l0n0lc as lc
from l0n0lc.数组对象池 import 数组对象池, 数组对象池统计


def test_对象池基础功能():
    """测试对象池基础功能"""
    print("=== 测试对象池基础功能 ===")

    pool = 数组对象池(最大大小=10)

    # 测试获取空池
    result = pool.获取(ctypes.c_int64, 100)
    assert result is None, "空池应该返回 None"
    print("✓ 空池获取返回 None")

    # 测试分配
    arr = pool.分配(ctypes.c_int64, 10)
    assert arr is not None, "分配应该返回数组"
    assert len(arr) == 10, "数组大小应该是 10"
    print("✓ 分配成功")

    # 测试释放
    pool.释放(ctypes.c_int64, 10, arr)
    print("✓ 释放成功")

    # 测试缓存命中
    cached = pool.获取(ctypes.c_int64, 10)
    assert cached is not None, "应该从缓存获取"
    print("✓ 缓存命中")

    # 测试获取或分配（新大小，第一次未命中）
    arr2, from_pool = pool.获取或分配(ctypes.c_int64, 20)
    assert not from_pool, "新分配不应该来自池"
    # 释放以便下次使用
    pool.释放(ctypes.c_int64, 20, arr2)

    # 第二次应该从池获取
    arr3, from_pool2 = pool.获取或分配(ctypes.c_int64, 20)
    assert from_pool2, "第二次应该从池获取"
    print("✓ 获取或分配功能正常")


def test_对象池统计():
    """测试对象池统计信息"""
    print("\n=== 测试对象池统计信息 ===")

    pool = 数组对象池(最大大小=10)

    # 初始统计
    统计 = pool.获取统计()
    assert 统计.命中次数 == 0, "初始命中次数应该是 0"
    assert 统计.未命中次数 == 0, "初始未命中次数应该是 0"
    print(f"初始统计: {统计}")

    # 分配并释放
    arr1 = pool.分配(ctypes.c_int64, 10)
    pool.释放(ctypes.c_int64, 10, arr1)

    # 命中测试
    pool.获取(ctypes.c_int64, 10)
    统计 = pool.获取统计()
    assert 统计.命中次数 == 1, "命中次数应该是 1"
    print(f"命中后统计: {统计}")

    # 未命中测试
    pool.获取(ctypes.c_int64, 999)
    统计 = pool.获取统计()
    assert 统计.未命中次数 == 1, "未命中次数应该是 1"
    print(f"未命中后统计: {统计}")

    # 命中率测试
    命中率 = 统计.获取命中率()
    assert 命中率 == 0.5, f"命中率应该是 0.5，实际是 {命中率}"
    print(f"命中率: {命中率:.2%}")


def test_LRU淘汰():
    """测试 LRU 淘汰策略"""
    print("\n=== 测试 LRU 淘汰策略 ===")

    pool = 数组对象池(最大大小=3)

    # 填满池
    arr1 = pool.分配(ctypes.c_int64, 10)
    arr2 = pool.分配(ctypes.c_int64, 20)
    arr3 = pool.分配(ctypes.c_int64, 30)

    pool.释放(ctypes.c_int64, 10, arr1)
    pool.释放(ctypes.c_int64, 20, arr2)
    pool.释放(ctypes.c_int64, 30, arr3)

    assert pool.获取缓存大小() == 3, "缓存大小应该是 3"
    print(f"✓ 缓存已填满，大小: {pool.获取缓存大小()}")

    # 访问第一个，移到末尾
    pool.获取(ctypes.c_int64, 10)

    # 添加第四个，应该淘汰第二个
    arr4 = pool.分配(ctypes.c_int64, 40)
    pool.释放(ctypes.c_int64, 40, arr4)

    assert pool.获取缓存大小() == 3, "缓存大小应该还是 3"
    print(f"✓ LRU 淘汰后缓存大小: {pool.获取缓存大小()}")

    # 验证第二个已被淘汰
    result = pool.获取(ctypes.c_int64, 20)
    assert result is None, "第二个数组应该被淘汰"
    print("✓ LRU 淘汰策略正确")


def test_全局对象池():
    """测试全局对象池"""
    print("\n=== 测试全局对象池 ===")

    # 获取全局对象池（单例）
    pool1 = lc.获取全局对象池()
    pool2 = lc.获取全局对象池()
    assert pool1 is pool2, "全局对象池应该是单例"
    print("✓ 全局对象池是单例")

    # 清空
    lc.清空全局对象池()
    print("✓ 清空全局对象池")

    # 重置
    new_pool = lc.重置全局对象池(最大大小=50)
    assert new_pool.获取最大大小() == 50, "新池大小应该是 50"
    print("✓ 重置全局对象池")

    # 启用/禁用
    lc.设置全局池启用(False)
    assert not new_pool.是否启用(), "应该禁用"
    lc.设置全局池启用(True)
    assert new_pool.是否启用(), "应该启用"
    print("✓ 启用/禁用功能正常")


def test_JIT函数调用对象池():
    """测试 JIT 函数调用使用对象池"""
    print("\n=== 测试 JIT 函数调用使用对象池 ===")

    # 清空统计
    lc.清空全局对象池()

    @lc.jit()
    def sum_list(nums: List[int]) -> int:
        total = 0
        for num in nums:
            total += num
        return total

    # 第一次调用（编译 + 缓存未命中）
    result1 = sum_list([1, 2, 3, 4, 5])
    assert result1 == 15, f"结果应该是 15，实际是 {result1}"
    print("✓ 第一次调用成功")

    # 多次调用相同大小数组（测试缓存命中）
    for _ in range(10):
        sum_list([1, 2, 3, 4, 5])

    # 获取统计
    统计 = lc.获取全局池统计()
    print(f"对象池统计: {统计}")
    print(f"命中率: {统计.获取命中率():.2%}")


def test_不同大小数组():
    """测试不同大小数组的缓存"""
    print("\n=== 测试不同大小数组的缓存 ===")

    pool = 数组对象池(最大大小=5)

    # 不同大小的数组
    大小列表 = [10, 20, 30, 40, 50]

    for 大小 in 大小列表:
        arr = pool.分配(ctypes.c_int64, 大小)
        pool.释放(ctypes.c_int64, 大小, arr)

    assert pool.获取缓存大小() == 5, "应该缓存 5 个不同大小的数组"
    print(f"✓ 缓存了 {pool.获取缓存大小()} 个不同大小的数组")

    # 验证每个大小都能命中
    for 大小 in 大小列表:
        cached = pool.获取(ctypes.c_int64, 大小)
        assert cached is not None, f"大小 {大小} 应该命中"


def test_不同类型数组():
    """测试不同类型数组的缓存"""
    print("\n=== 测试不同类型数组的缓存 ===")

    pool = 数组对象池(最大大小=10)

    # 不同类型的数组
    arr_int = pool.分配(ctypes.c_int64, 100)
    arr_double = pool.分配(ctypes.c_double, 100)

    pool.释放(ctypes.c_int64, 100, arr_int)
    pool.释放(ctypes.c_double, 100, arr_double)

    assert pool.获取缓存大小() == 2, "应该缓存 2 个不同类型的数组"
    print("✓ 不同类型数组分别缓存")

    # 验证类型区分
    cached_int = pool.获取(ctypes.c_int64, 100)
    cached_double = pool.获取(ctypes.c_double, 100)

    assert cached_int is not None, "int64 应该命中"
    assert cached_double is not None, "double 应该命中"
    print("✓ 类型区分正确")


def test_环境变量控制():
    """测试环境变量控制"""
    print("\n=== 测试环境变量控制 ===")

    # 设置池大小
    os.environ["L0N0LC_ARRAY_POOL_SIZE"] = "200"
    pool = lc.重置全局对象池()
    assert pool.获取最大大小() == 200, "环境变量应该控制池大小"
    print(f"✓ 池大小设置为 {pool.获取最大大小()}")

    # 恢复默认
    del os.environ["L0N0LC_ARRAY_POOL_SIZE"]
    pool = lc.重置全局对象池()
    print(f"✓ 恢复默认池大小: {pool.获取最大大小()}")


def test_性能对比():
    """测试性能对比（对象池 vs 无池）"""
    print("\n=== 性能对比测试 ===")

    @lc.jit()
    def sum_large_array(nums: List[int]) -> int:
        total = 0
        for num in nums:
            total += num
        return total

    # 预热
    sum_large_array(list(range(1000)))

    # 测试数组大小
    数组大小 = 10000
    迭代次数 = 1000

    # 启用对象池
    lc.设置全局池启用(True)
    lc.清空全局对象池()

    开始 = time.perf_counter()
    for _ in range(迭代次数):
        sum_large_array(list(range(数组大小)))
    启用耗时 = time.perf_counter() - 开始

    统计 = lc.获取全局池统计()
    print(f"启用对象池: {启用耗时*1000:.2f}ms, 统计: {统计}")

    # 禁用对象池
    lc.设置全局池启用(False)
    lc.清空全局对象池()

    开始 = time.perf_counter()
    for _ in range(迭代次数):
        sum_large_array(list(range(数组大小)))
    禁用耗时 = time.perf_counter() - 开始

    print(f"禁用对象池: {禁用耗时*1000:.2f}ms")

    if 启用耗时 < 禁用耗时:
        加速比 = 禁用耗时 / 启用耗时
        print(f"✓ 对象池加速比: {加速比:.2f}x")
    else:
        print(f"注意: 对象池未带来性能提升（可能需要更多迭代）")

    # 恢复启用
    lc.设置全局池启用(True)


def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("数组对象池测试套件")
    print("=" * 50)

    tests = [
        test_对象池基础功能,
        test_对象池统计,
        test_LRU淘汰,
        test_全局对象池,
        test_JIT函数调用对象池,
        test_不同大小数组,
        test_不同类型数组,
        test_环境变量控制,
        test_性能对比,
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
