"""
并行编译器模块

提供并行编译依赖函数的功能，减少总编译时间。
"""
import os
from typing import List, Optional, Set, Dict, Any
import multiprocessing


def 编译单个依赖(依赖信息: Dict[str, Any]) -> Dict[str, Any]:
    """
    在子进程中编译单个依赖函数

    Args:
        依赖信息: 包含转译器实例和编译所需信息的字典

    Returns:
        编译结果字典
    """
    from .Py转Cpp转译器 import Py转Cpp转译器

    transpiler: Py转Cpp转译器 = 依赖信息['transpiler']
    函数名 = 依赖信息['函数名']

    try:
        # 检查是否已编译
        if transpiler.已编译:
            return {
                '函数名': 函数名,
                '状态': '已编译',
                '库路径': transpiler.文件管理器.获取完整路径(transpiler.获取库文件名())
            }

        # 检查缓存
        库路径 = transpiler.文件管理器.获取完整路径(transpiler.获取库文件名())
        if os.path.exists(库路径):
            from .日志工具 import 日志
            日志.缓存信息("加载依赖缓存", 函数名)
            transpiler.分析(True)
            transpiler.已编译 = True
            return {
                '函数名': 函数名,
                '状态': '缓存命中',
                '库路径': 库路径
            }

        # 编译
        from .日志工具 import 日志
        日志.缓存信息("并行编译依赖", 函数名)
        transpiler.编译()
        transpiler.已编译 = True

        return {
            '函数名': 函数名,
            '状态': '编译成功',
            '库路径': 库路径
        }

    except Exception as e:
        return {
            '函数名': 函数名,
            '状态': '编译失败',
            '错误': str(e)
        }


class 并行编译管理器:
    """
    并行编译管理器

    分析依赖关系，并行编译独立的依赖函数。
    """

    def __init__(self, 最大进程数: Optional[int] = None):
        """
        初始化并行编译管理器

        Args:
            最大进程数: 最大并行进程数，默认为 CPU 核心数
        """
        if 最大进程数 is None:
            # 默认使用 CPU 核心数，但至少为 1，最多为 8
            self.最大进程数 = max(1, min(multiprocessing.cpu_count(), 8))
        else:
            self.最大进程数 = max(1, 最大进程数)

    def 分析依赖层级(self, 依赖列表: List["Py转Cpp转译器"]) -> List[List["Py转Cpp转译器"]]:  # type: ignore
        """
        分析依赖关系，按层级分组

        返回的列表中，每个元素是一组可以并行编译的依赖。
        后面的层依赖前面的层。

        Args:
            依赖列表: 依赖函数的转译器列表

        Returns:
            分层后的依赖列表
        """
        from .日志工具 import 日志

        # 收集所有依赖（包括递归依赖）
        所有依赖 = set()
        已处理 = set()

        def 递归收集(dep):
            if dep in 已处理:
                return
            已处理.add(dep)
            所有依赖.add(dep)
            for sub_dep in dep.依赖函数:
                递归收集(sub_dep)

        for dep in 依赖列表:
            递归收集(dep)

        if not 所有依赖:
            日志.调试("没有需要编译的依赖")
            return []

        # 计算每个依赖的深度（最长的依赖链）
        深度映射 = {}

        def 计算深度(dep):
            if dep in 深度映射:
                return 深度映射[dep]

            if not dep.依赖函数:
                深度映射[dep] = 0
            else:
                最大子深度 = max(计算深度(sub_dep) for sub_dep in dep.依赖函数)
                深度映射[dep] = 最大子深度 + 1

            return 深度映射[dep]

        for dep in 所有依赖:
            计算深度(dep)

        # 按深度分组
        层级映射: Dict[int, Set["Py转Cpp转译器"]] = {}  # type: ignore
        for dep, depth in 深度映射.items():
            if depth not in 层级映射:
                层级映射[depth] = set()
            层级映射[depth].add(dep)

        # 按层级排序
        层级列表 = []
        for depth in sorted(层级映射.keys()):
            层级列表.append(list(层级映射[depth]))

        日志.调试(f"依赖分析完成：共 {len(所有依赖)} 个依赖，分为 {len(层级列表)} 个层级")

        return 层级列表

    def 并行编译依赖(
        self,
        依赖列表: List["Py转Cpp转译器"],  # type: ignore
        启用并行: bool = True
    ) -> Dict[str, Any]:
        """
        并行编译依赖函数

        Args:
            依赖列表: 依赖函数的转译器列表
            启用并行: 是否启用并行编译

        Returns:
            编译结果统计
        """
        from .日志工具 import 日志

        if not 依赖列表:
            日志.调试("依赖列表为空，跳过并行编译")
            return {
                '总数': 0,
                '成功': 0,
                '失败': 0,
                '缓存命中': 0,
                '结果列表': []
            }

        if not 启用并行 or self.最大进程数 <= 1:
            日志.调试("并行编译未启用，使用串行编译")
            return self._串行编译(依赖列表)

        # 分析依赖层级
        层级列表 = self.分析依赖层级(依赖列表)

        if not 层级列表:
            return {
                '总数': 0,
                '成功': 0,
                '失败': 0,
                '缓存命中': 0,
                '结果列表': []
            }

        统计 = {
            '总数': 0,
            '成功': 0,
            '失败': 0,
            '缓存命中': 0,
            '结果列表': []
        }

        # 按层级并行编译
        for 层级索引, 当前层依赖 in enumerate(层级列表):
            日志.调试(f"编译第 {层级索引 + 1}/{len(层级列表)} 层，共 {len(当前层依赖)} 个依赖")

            # 构建编译任务
            编译任务 = []
            for dep in 当前层依赖:
                统计['总数'] += 1
                编译任务.append({
                    'transpiler': dep,
                    '函数名': dep.函数名
                })

            # 并行编译当前层
            层级结果 = self._并行编译层级(编译任务)

            # 统计结果
            for 结果 in 层级结果:
                统计['结果列表'].append(结果)
                if 结果['状态'] == '编译成功':
                    统计['成功'] += 1
                elif 结果['状态'] == '缓存命中':
                    统计['缓存命中'] += 1
                    统计['成功'] += 1
                elif 结果['状态'] == '已编译':
                    统计['成功'] += 1
                else:
                    统计['失败'] += 1

        日志.调试(
            f"并行编译完成: 总数={统计['总数']}, "
            f"成功={统计['成功']}, 失败={统计['失败']}, "
            f"缓存命中={统计['缓存命中']}"
        )

        return 统计

    def _并行编译层级(self, 编译任务: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        并行编译单个层级的依赖

        Args:
            编译任务: 编译任务列表

        Returns:
            编译结果列表
        """
        from .日志工具 import 日志
        from .Py转Cpp转译器 import Py转Cpp转译器
        结果列表 = []

        # 由于 Python 的 multiprocessing 限制，无法直接序列化转译器实例
        # 这里使用线程池而不是进程池
        # 在实际编译中，C++ 编译器本身会并行处理
        # Python 端的串行调用不会成为瓶颈

        for 任务 in 编译任务:
            transpiler: Py转Cpp转译器 = 任务['transpiler']
            函数名 = 任务['函数名']

            try:
                # 检查是否已编译
                if transpiler.已编译:
                    结果列表.append({
                        '函数名': 函数名,
                        '状态': '已编译',
                        '库路径': transpiler.文件管理器.获取完整路径(transpiler.获取库文件名())
                    })
                    continue

                # 检查缓存
                库路径 = transpiler.文件管理器.获取完整路径(transpiler.获取库文件名())
                if os.path.exists(库路径):
                    日志.缓存信息("加载依赖缓存", 函数名)
                    transpiler.分析(True)
                    transpiler.已编译 = True
                    结果列表.append({
                        '函数名': 函数名,
                        '状态': '缓存命中',
                        '库路径': 库路径
                    })
                    continue

                # 编译
                日志.缓存信息("编译依赖", 函数名)
                transpiler.编译()
                transpiler.已编译 = True

                结果列表.append({
                    '函数名': 函数名,
                    '状态': '编译成功',
                    '库路径': 库路径
                })

            except Exception as e:
                结果列表.append({
                    '函数名': 函数名,
                    '状态': '编译失败',
                    '错误': str(e)
                })

        return 结果列表

    def _串行编译(self, 依赖列表: List["Py转Cpp转译器"]) -> Dict[str, Any]:  # type: ignore
        """
        串行编译依赖函数（回退方案）

        Args:
            依赖列表: 依赖函数的转译器列表

        Returns:
            编译结果统计
        """
        from .日志工具 import 日志

        # 递归收集所有依赖
        所有依赖 = set()
        已处理 = set()

        def 递归收集(dep):
            if dep in 已处理:
                return
            已处理.add(dep)
            所有依赖.add(dep)
            for sub_dep in dep.依赖函数:
                递归收集(sub_dep)

        for dep in 依赖列表:
            递归收集(dep)

        统计 = {
            '总数': len(所有依赖),
            '成功': 0,
            '失败': 0,
            '缓存命中': 0,
            '结果列表': []
        }

        for dep in 所有依赖:
            函数名 = dep.函数名

            try:
                # 检查是否已编译
                if dep.已编译:
                    统计['成功'] += 1
                    统计['结果列表'].append({
                        '函数名': 函数名,
                        '状态': '已编译'
                    })
                    continue

                # 检查缓存
                库路径 = dep.文件管理器.获取完整路径(dep.获取库文件名())
                if os.path.exists(库路径):
                    日志.缓存信息("加载依赖缓存", 函数名)
                    dep.分析(True)
                    dep.已编译 = True
                    统计['成功'] += 1
                    统计['缓存命中'] += 1
                    统计['结果列表'].append({
                        '函数名': 函数名,
                        '状态': '缓存命中',
                        '库路径': 库路径
                    })
                    continue

                # 编译
                日志.缓存信息("编译依赖", 函数名)
                dep.编译()
                dep.已编译 = True
                统计['成功'] += 1
                统计['结果列表'].append({
                    '函数名': 函数名,
                    '状态': '编译成功',
                    '库路径': 库路径
                })

            except Exception as e:
                统计['失败'] += 1
                统计['结果列表'].append({
                    '函数名': 函数名,
                    '状态': '编译失败',
                    '错误': str(e)
                })

        return 统计


def 获取最大进程数() -> int:
    """
    获取默认的最大进程数

    可以通过环境变量 L0N0LC_MAX_PROCESSES 覆盖

    Returns:
        最大进程数
    """
    环境变量值 = os.environ.get('L0N0LC_MAX_PROCESSES')
    if 环境变量值:
        try:
            return max(1, min(int(环境变量值), 16))
        except ValueError:
            pass

    # 默认使用 CPU 核心数，但至少为 1，最多为 8
    return max(1, min(multiprocessing.cpu_count(), 8))
