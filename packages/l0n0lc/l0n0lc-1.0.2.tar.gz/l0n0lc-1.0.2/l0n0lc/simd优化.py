"""
SIMD (Single Instruction Multiple Data) 向量化优化模块

提供 SIMD 指令的自动检测和向量化优化支持
"""

import os
import subprocess
import platform
from typing import Optional, List, Dict, Any
from .日志工具 import 日志


class CPU特性:
    """CPU SIMD 特性检测"""

    def __init__(self):
        self._特性缓存: Optional[Dict[str, bool]] = None

    def 检测特性(self) -> Dict[str, bool]:
        """
        检测 CPU 支持的 SIMD 特性

        Returns:
            特性字典，包含各种 SIMD 扩展的支持情况
        """
        if self._特性缓存 is not None:
            return self._特性缓存

        特性 = {
            'SSE': False,
            'SSE2': False,
            'SSE3': False,
            'SSE4_1': False,
            'SSE4_2': False,
            'AVX': False,
            'AVX2': False,
            'AVX512F': False,
            'NEON': False,  # ARM
        }

        系统 = platform.system()

        if 系统 == 'Linux':
            # Linux: 读取 /proc/cpuinfo
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    内容 = f.read()
                    特性.update(self._从cpuinfo解析(内容))
            except (FileNotFoundError, PermissionError, OSError) as e:
                日志.调试(f"无法读取 /proc/cpuinfo: {e}")
            except Exception as e:
                日志.调试(f"解析 cpuinfo 时出错: {e}")

            # 尝试通过 lscpu 获取更准确的信息
            try:
                结果 = subprocess.run(['lscpu'], capture_output=True, text=True, timeout=5)
                if 结果.returncode == 0:
                    特性.update(self._从lscpu解析(结果.stdout))
            except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError) as e:
                日志.调试(f"无法执行 lscpu: {e}")
            except Exception as e:
                日志.调试(f"解析 lscpu 输出时出错: {e}")

        elif 系统 == 'Darwin':  # macOS
            # macOS: 使用 sysctl
            try:
                结果 = subprocess.run(['sysctl', '-a'], capture_output=True, text=True, timeout=5)
                if 结果.returncode == 0:
                    特性.update(self._从sysctl解析(结果.stdout))
            except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError) as e:
                日志.调试(f"无法执行 sysctl: {e}")
            except Exception as e:
                日志.调试(f"解析 sysctl 输出时出错: {e}")

        elif 系统 == 'Windows':
            # Windows: 使用 wmic 或 systeminfo
            try:
                结果 = subprocess.run(
                    ['wmic', 'cpu', 'get', 'DataWidth', '/format:list'],
                    capture_output=True, text=True, timeout=5
                )
                if 结果.returncode == 0:
                    # Windows 上的简化检测，假设支持 SSE2+
                    特性['SSE2'] = True
            except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError) as e:
                日志.调试(f"无法执行 wmic: {e}")
            except Exception as e:
                日志.调试(f"解析 wmic 输出时出错: {e}")

        # ARM 架构特殊处理
        机器 = platform.machine()
        if 机器 and ('arm' in 机器.lower() or 'aarch64' in 机器.lower()):
            特性['NEON'] = True

        self._特性缓存 = 特性
        return 特性

    def _从cpuinfo解析(self, 内容: str) -> Dict[str, bool]:
        """从 /proc/cpuinfo 解析 CPU 特性"""
        特性 = {}

        for 行 in 内容.split('\n'):
            if 行.startswith('flags'):
                标志列表 = 行.split(':', 1)[1].strip().split()
                标志 = set(标志列表)

                特性['SSE'] = 'sse' in 标志
                特性['SSE2'] = 'sse2' in 标志
                特性['SSE3'] = 'sse3' in 标志 or 'pni' in 标志
                特性['SSE4_1'] = 'sse4_1' in 标志
                特性['SSE4_2'] = 'sse4_2' in 标志
                特性['AVX'] = 'avx' in 标志
                特性['AVX2'] = 'avx2' in 标志
                特性['AVX512F'] = 'avx512f' in 标志
                break

        return 特性

    def _从lscpu解析(self, 内容: str) -> Dict[str, bool]:
        """从 lscpu 输出解析 CPU 特性"""
        特性 = {}

        for 行 in 内容.split('\n'):
            if 'Flags:' in 行:
                标志列表 = 行.split(':', 1)[1].strip().split()
                标志 = set(标志列表)

                特性['SSE'] = 'sse' in 标志
                特性['SSE2'] = 'sse2' in 标志
                特性['SSE3'] = 'sse3' in 标志 or 'pni' in 标志
                特性['SSE4_1'] = 'sse4_1' in 标志
                特性['SSE4_2'] = 'sse4_2' in 标志
                特性['AVX'] = 'avx' in 标志
                特性['AVX2'] = 'avx2' in 标志
                特性['AVX512F'] = 'avx512f' in 标志
                break

        return 特性

    def _从sysctl解析(self, 内容: str) -> Dict[str, bool]:
        """从 sysctl 输出解析 CPU 特性（macOS）"""
        特性 = {}

        # macOS 通常在较新的 Intel 处理器上支持 AVX
        if 'machdep.cpu.features' in 内容:
            for 行 in 内容.split('\n'):
                if 'machdep.cpu.features:' in 行 or 'machdep.cpu.extfeatures:' in 行:
                    标志列表 = 行.split(':', 1)[1].strip().split()
                    标志 = set(标志列表)

                    特性['SSE'] = 'SSE' in 标志
                    特性['SSE2'] = 'SSE2' in 标志
                    特性['SSE3'] = 'SSE3' in 标志
                    特性['SSE4_1'] = 'SSE4.1' in 标志 or 'SSE4_1' in 标志
                    特性['SSE4_2'] = 'SSE4.2' in 标志 or 'SSE4_2' in 标志
                    特性['AVX'] = 'AVX' in 标志
                    特性['AVX2'] = 'AVX2' in 标志
                    特性['AVX512F'] = 'AVX512F' in 标志 or 'AVX512' in 标志
                    break

        return 特性

    def 获取最佳SIMD指令集(self) -> str:
        """
        获取 CPU 支持的最佳 SIMD 指令集

        Returns:
            最佳指令集名称 (SSE2, SSE4_2, AVX2, AVX512F, NEON)
        """
        特性 = self.检测特性()

        优先级 = ['AVX512F', 'AVX2', 'SSE4_2', 'SSE2', 'NEON']

        for 指令集 in 优先级:
            if 特性.get(指令集, False):
                return 指令集

        return 'SSE2'  # 默认回退


# 全局单例
_CPU特性实例: Optional[CPU特性] = None


def 获取CPU特性() -> CPU特性:
    """获取 CPU 特性检测器单例"""
    global _CPU特性实例
    if _CPU特性实例 is None:
        _CPU特性实例 = CPU特性()
    return _CPU特性实例


def 获取最佳SIMD指令集() -> str:
    """获取当前 CPU 支持的最佳 SIMD 指令集"""
    return 获取CPU特性().获取最佳SIMD指令集()


def 获取SIMD编译标志(指令集: Optional[str] = None) -> List[str]:
    """
    获取 SIMD 编译标志

    Args:
        指令集: 指定指令集，None 表示自动检测

    Returns:
        编译标志列表
    """
    if 指令集 is None:
        指令集 = 获取最佳SIMD指令集()

    标志映射 = {
        'SSE2': ['-msse2', '-mfpmath=sse'],
        'SSE4_2': ['-msse4.2', '-mfpmath=sse'],
        'AVX': ['-mavx'],
        'AVX2': ['-mavx2', '-mfma'],
        'AVX512F': ['-mavx512f', '-mavx512vl'],
        'NEON': [],  # ARM NEON 通常默认启用
    }

    return 标志映射.get(指令集, ['-msse2'])


def 启用自动向量化标志() -> List[str]:
    """
    获取启用编译器自动向量化的标志

    Returns:
        编译标志列表
    """
    return ['-ftree-vectorize', '-ffast-math']


def 获取向量化宏定义(指令集: Optional[str] = None) -> Dict[str, str]:
    """
    获取 SIMD 向量化相关的宏定义

    Args:
        指令集: 指定指令集，None 表示自动检测

    Returns:
        宏定义字典
    """
    if 指令集 is None:
        指令集 = 获取最佳SIMD指令集()

    宏定义 = {
        'L0N0LC_USE_SIMD': '1',
    }

    if 指令集 == 'AVX2':
        宏定义['L0N0LC_AVX2'] = '1'
    elif 指令集 == 'AVX512F':
        宏定义['L0N0LC_AVX512F'] = '1'
    elif 指令集 == 'NEON':
        宏定义['L0N0LC_NEON'] = '1'
    else:
        宏定义['L0N0LC_SSE'] = '1'

    return 宏定义
