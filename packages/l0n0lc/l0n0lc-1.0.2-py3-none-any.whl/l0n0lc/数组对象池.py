"""
数组对象池模块

提供高效的 ctypes 数组对象池，用于减少运行时参数转换开销。
"""

import ctypes
import os
from collections import OrderedDict
from typing import Type, Tuple, Optional, Dict, Any
from threading import Lock


def 获取默认池大小() -> int:
    """获取默认对象池大小"""
    return int(os.environ.get("L0N0LC_ARRAY_POOL_SIZE", "128"))


def 获取是否启用对象池() -> bool:
    """获取是否启用对象池"""
    return os.environ.get("L0N0LC_ENABLE_ARRAY_POOL", "1") == "1"


class 数组对象池统计:
    """对象池统计信息"""

    def __init__(self):
        self.命中次数 = 0
        self.未命中次数 = 0
        self.分配次数 = 0
        self.释放次数 = 0
        self.缓存数组数 = 0

    def 重置(self):
        """重置统计信息"""
        self.命中次数 = 0
        self.未命中次数 = 0
        self.分配次数 = 0
        self.释放次数 = 0
        self.缓存数组数 = 0

    def 获取命中率(self) -> float:
        """获取缓存命中率"""
        总次数 = self.命中次数 + self.未命中次数
        if 总次数 == 0:
            return 0.0
        return self.命中次数 / 总次数

    def __repr__(self) -> str:
        return (
            f"数组对象池统计(命中={self.命中次数}, 未命中={self.未命中次数}, "
            f"命中率={self.获取命中率():.2%}, 分配={self.分配次数}, "
            f"释放={self.释放次数}, 缓存={self.缓存数组数})"
        )


class 数组对象池:
    """
    ctypes 数组对象池

    使用 LRU 缓存策略管理已分配的数组对象，减少重复分配开销。
    """

    def __init__(self, 最大大小: Optional[int] = None):
        """
        初始化对象池

        Args:
            最大大小: 最大缓存条目数，None 表示使用默认值
        """
        self._最大大小 = 最大大小 or 获取默认池大小()
        self._缓存: OrderedDict[Tuple[Type, int], Any] = OrderedDict()
        self._锁 = Lock()
        self._统计 = 数组对象池统计()
        self._是否启用 = 获取是否启用对象池()

    def 获取(self, 元素类型: Type[Any], 大小: int) -> Optional[Any]:
        """
        从对象池获取数组

        Args:
            元素类型: ctypes 元素类型（如 ctypes.c_int64）
            大小: 数组大小

        Returns:
            缓存的数组对象，如果未命中则返回 None
        """
        if not self._是否启用:
            return None

        key = (元素类型, 大小)

        with self._锁:
            if key in self._缓存:
                # LRU: 移到末尾
                self._缓存.move_to_end(key)
                array = self._缓存[key]
                self._统计.命中次数 += 1
                self._统计.缓存数组数 = len(self._缓存)
                return array
            else:
                self._统计.未命中次数 += 1
                return None

    def 分配(self, 元素类型: Type[Any], 大小: int) -> Any:
        """
        分配新数组

        Args:
            元素类型: ctypes 元素类型
            大小: 数组大小

        Returns:
            新分配的数组对象
        """
        array_type = 元素类型 * 大小  # type: ignore
        array = array_type()

        with self._锁:
            self._统计.分配次数 += 1

        return array

    def 释放(self, 元素类型: Type[Any], 大小: int, 数组: Any) -> None:
        """
        释放数组回对象池

        Args:
            元素类型: ctypes 元素类型
            大小: 数组大小
            数组: 要释放的数组对象
        """
        if not self._是否启用:
            return

        key = (元素类型, 大小)

        with self._锁:
            # 如果缓存已满，移除最旧的条目
            if len(self._缓存) >= self._最大大小:
                self._缓存.popitem(last=False)

            self._缓存[key] = 数组
            self._缓存.move_to_end(key)
            self._统计.释放次数 += 1
            self._统计.缓存数组数 = len(self._缓存)

    def 获取或分配(self, 元素类型: Type[Any], 大小: int) -> Tuple[Any, bool]:
        """
        获取或分配数组

        Args:
            元素类型: ctypes 元素类型
            大小: 数组大小

        Returns:
            (数组对象, 是否从缓存获取)
        """
        cached = self.获取(元素类型, 大小)
        if cached is not None:
            return cached, True

        new_array = self.分配(元素类型, 大小)
        return new_array, False

    def 清空(self) -> None:
        """清空对象池"""
        with self._锁:
            self._缓存.clear()

    def 获取统计(self) -> 数组对象池统计:
        """获取统计信息副本"""
        with self._锁:
            # 返回统计信息的副本
            统计 = 数组对象池统计()
            统计.命中次数 = self._统计.命中次数
            统计.未命中次数 = self._统计.未命中次数
            统计.分配次数 = self._统计.分配次数
            统计.释放次数 = self._统计.释放次数
            统计.缓存数组数 = len(self._缓存)
            return 统计

    def 设置启用(self, 启用: bool) -> None:
        """设置是否启用对象池"""
        self._是否启用 = 启用

    def 是否启用(self) -> bool:
        """获取是否启用对象池"""
        return self._是否启用

    def 获取缓存大小(self) -> int:
        """获取当前缓存条目数"""
        with self._锁:
            return len(self._缓存)

    def 获取最大大小(self) -> int:
        """获取最大缓存大小"""
        return self._最大大小


# 全局对象池实例
_全局对象池: Optional[数组对象池] = None
_全局池锁 = Lock()


def 获取全局对象池() -> 数组对象池:
    """获取全局对象池实例（单例）"""
    global _全局对象池

    if _全局对象池 is None:
        with _全局池锁:
            if _全局对象池 is None:
                _全局对象池 = 数组对象池()

    return _全局对象池


def 重置全局对象池(最大大小: Optional[int] = None) -> 数组对象池:
    """
    重置全局对象池

    Args:
        最大大小: 新的最大缓存大小，None 表示保持默认

    Returns:
        新创建的全局对象池实例
    """
    global _全局对象池

    with _全局池锁:
        _全局对象池 = 数组对象池(最大大小=最大大小)

    return _全局对象池


def 获取全局池统计() -> 数组对象池统计:
    """获取全局对象池统计信息"""
    return 获取全局对象池().获取统计()


def 清空全局对象池() -> None:
    """清空全局对象池"""
    获取全局对象池().清空()


def 设置全局池启用(启用: bool) -> None:
    """设置全局对象池是否启用"""
    获取全局对象池().设置启用(启用)
