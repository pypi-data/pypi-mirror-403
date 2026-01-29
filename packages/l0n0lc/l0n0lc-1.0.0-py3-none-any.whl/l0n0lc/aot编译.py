"""
AOT (Ahead-Of-Time) 预编译模块

允许用户在运行前批量预编译所有 @jit 装饰的函数，
从而消除首次调用时的编译延迟。
"""

import os
import ast
import sys
import argparse
import inspect
import importlib.util
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional, Callable, Any
from concurrent.futures import ProcessPoolExecutor, as_completed

from .Py转Cpp转译器 import Py转Cpp转译器
from .cpp编译器 import Cpp编译器
from .工具 import 全局上下文
from .日志工具 import 日志, 日志级别


class JIT函数信息:
    """存储 JIT 函数的元信息"""

    def __init__(
        self,
        函数名: str,
        函数对象: Callable,
        模块名: str,
        源文件路径: str,
        行号: int,
        装饰器参数: Optional[Dict[str, Any]] = None
    ):
        self.函数名 = 函数名
        self.函数对象 = 函数对象
        self.模块名 = 模块名
        self.源文件路径 = 源文件路径
        self.行号 = 行号
        self.装饰器参数 = 装饰器参数 or {}

    def __repr__(self):
        return f"JIT函数信息({self.模块名}.{self.函数名} @ {self.源文件路径}:{self.行号})"


class 包扫描器:
    """
    扫描 Python 包，提取所有 @jit 装饰的函数
    """

    def __init__(self, 根目录: str):
        """
        初始化包扫描器

        Args:
            根目录: 要扫描的根目录（包的根目录）
        """
        self.根目录 = Path(根目录).resolve()
        if not self.根目录.exists():
            raise ValueError(f"目录不存在: {根目录}")

    def 扫描目录(
        self,
        递归: bool = True,
        排除目录: Optional[Set[str]] = None,
        包含测试: bool = False
    ) -> List[JIT函数信息]:
        """
        扫描目录下所有 Python 文件，提取 JIT 函数

        Args:
            递归: 是否递归扫描子目录
            排除目录: 要排除的目录名集合
            包含测试: 是否包含测试文件（test_*.py）

        Returns:
            JIT 函数信息列表
        """
        排除目录 = 排除目录 or {
            "__pycache__",
            ".git",
            ".venv",
            "venv",
            "env",
            "build",
            "dist",
            ".eggs",
            "*.egg-info",
        }

        jit函数列表 = []

        # 查找所有 Python 文件
        模式 = "**/*.py" if 递归 else "*.py"
        for py文件 in self.根目录.rglob(模式):
            # 检查是否应该跳过此文件
            if not self._应该包含文件(py文件, 排除目录, 包含测试):
                continue

            # 从文件中提取 JIT 函数
            文件函数 = self._扫描文件(str(py文件))
            jit函数列表.extend(文件函数)

        日志.信息(f"扫描完成，找到 {len(jit函数列表)} 个 JIT 函数")
        return jit函数列表

    def _应该包含文件(
        self,
        文件路径: Path,
        排除目录: Set[str],
        包含测试: bool
    ) -> bool:
        """判断文件是否应该被扫描"""
        # 检查文件名
        if not 包含测试 and 文件路径.name.startswith("test_"):
            return False

        # 检查父目录是否在排除列表中
        for 父目录 in 文件路径.parents:
            if 父目录.name in 排除目录:
                return False

        return True

    def _扫描文件(self, 文件路径: str) -> List[JIT函数信息]:
        """
        扫描单个 Python 文件，提取 JIT 函数

        Args:
            文件路径: Python 文件路径

        Returns:
            JIT 函数信息列表
        """
        try:
            with open(文件路径, "r", encoding="utf-8") as f:
                源代码 = f.read()
        except Exception as e:
            日志.警告(f"无法读取文件 {文件路径}: {e}")
            return []

        try:
            树 = ast.parse(源代码, filename=文件路径)
        except SyntaxError as e:
            日志.警告(f"文件 {文件路径} 语法错误: {e}")
            return []

        jit函数列表 = []
        模块名 = Path(文件路径).stem

        for 节点 in ast.walk(树):
            if isinstance(节点, ast.FunctionDef):
                # 检查是否使用了 @jit 或 @即时编译 装饰器
                if self._是jit函数(节点):
                    # 尝试从实际模块中导入函数对象
                    函数对象 = self._导入函数(文件路径, 节点.name)

                    装饰器参数 = self._提取装饰器参数(节点)

                    信息 = JIT函数信息(
                        函数名=节点.name,
                        函数对象=函数对象, # type: ignore
                        模块名=模块名,
                        源文件路径=文件路径,
                        行号=节点.lineno,
                        装饰器参数=装饰器参数
                    )
                    jit函数列表.append(信息)

        return jit函数列表

    def _是jit函数(self, 函数节点: ast.FunctionDef) -> bool:
        """检查函数是否使用了 @jit 或 @即时编译 装饰器"""
        for 装饰器 in 函数节点.decorator_list:
            # 检查 @jit
            if isinstance(装饰器, ast.Name) and 装饰器.id in ("jit", "即时编译"):
                return True
            # 检查 @lc.jit() 形式
            if isinstance(装饰器, ast.Call):
                if isinstance(装饰器.func, ast.Attribute):
                    if 装饰器.func.attr in ("jit", "即时编译"):
                        return True
                elif isinstance(装饰器.func, ast.Name):
                    if 装饰器.func.id in ("jit", "即时编译"):
                        return True
        return False

    def _提取装饰器参数(
        self, 函数节点: ast.FunctionDef
    ) -> Dict[str, Any]:
        """
        从装饰器中提取参数

        Returns:
            装饰器参数字典
        """
        参数 = {}

        for 装饰器 in 函数节点.decorator_list:
            if isinstance(装饰器, ast.Call):
                尝试从调用提取参数(装饰器, 参数)

        return 参数

    def _导入函数(self, 文件路径: str, 函数名: str) -> Optional[Callable]:
        """
        从文件中导入函数对象

        注意：这可能需要正确设置 Python 路径
        """
        try:
            # 获取文件的目录和模块名
            文件目录 = os.path.dirname(文件路径)
            模块名 = Path(文件路径).stem

            # 添加目录到 sys.path
            原路径 = sys.path[:]
            if 文件目录 not in sys.path:
                sys.path.insert(0, 文件目录)

            try:
                # 动态导入模块
                spec = importlib.util.spec_from_file_location(模块名, 文件路径)
                if spec and spec.loader:
                    模块 = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(模块)

                    # 获取函数对象（可能是 Py转Cpp转译器 对象）
                    if hasattr(模块, 函数名):
                        对象 = getattr(模块, 函数名)
                        # 如果是 JIT 装饰器返回的转译器对象，提取原始函数
                        if isinstance(对象, Py转Cpp转译器):
                            return 对象.目标函数
                        return 对象
            finally:
                # 恢复 sys.path
                sys.path[:] = 原路径

        except Exception as e:
            日志.调试(f"无法导入函数 {文件路径}:{函数名}: {e}")

        return None


def 尝试从调用提取参数(装饰器: ast.Call, 参数字典: Dict[str, Any]):
    """尝试从装饰器调用中提取参数"""
    for 关键字 in 装饰器.keywords:
        if isinstance(关键字.value, ast.Constant):
            参数字典[关键字.arg] = 关键字.value.value # type: ignore
        elif isinstance(关键字.value, ast.NameConstant):
            参数字典[关键字.arg] = 关键字.value.value # type: ignore
        elif isinstance(关键字.value, ast.Name):
            参数字典[关键字.arg] = 关键字.value.id # type: ignore
        elif isinstance(关键字.value, ast.Str):
            参数字典[关键字.arg] = 关键字.value.s # type: ignore
        elif isinstance(关键字.value, ast.Num):
            参数字典[关键字.arg] = 关键字.value.n # type: ignore


class AOT编译器:
    """
    AOT (Ahead-Of-Time) 编译器

    批量预编译多个 JIT 函数，消除首次调用延迟
    """

    def __init__(
        self,
        优化级别: str = "O2",
        启用并行编译: bool = True,
        最大进程数: Optional[int] = None,
        启用LTO: bool = False,
        启用向量化: bool = False,
        SIMD指令集: Optional[str] = None
    ):
        """
        初始化 AOT 编译器

        Args:
            优化级别: 编译优化级别（O0/O1/O2/O3/Os/Ofast/Og/Oz）
            启用并行编译: 是否启用并行编译
            最大进程数: 最大并行进程数
            启用LTO: 是否启用链接时优化（LTO）
            启用向量化: 是否启用 SIMD 向量化优化
            SIMD指令集: 指定 SIMD 指令集（None 表示自动检测）
        """
        self.优化级别 = 优化级别
        self.启用并行编译 = 启用并行编译
        self.最大进程数 = 最大进程数
        self.启用LTO = 启用LTO
        self.启用向量化 = 启用向量化
        self.SIMD指令集 = SIMD指令集
        self.编译结果: List[Dict[str, Any]] = []

    def 编译函数列表(
        self,
        函数列表: List[JIT函数信息],
        显示进度: bool = True
    ) -> Dict[str, Any]:
        """
        批量编译 JIT 函数列表

        Args:
            函数列表: JIT 函数信息列表
            显示进度: 是否显示编译进度

        Returns:
            编译统计信息
        """
        总数 = len(函数列表)
        成功数 = 0
        失败数 = 0
        跳过数 = 0  # 缓存命中
        结果列表 = []

        日志.信息(f"开始 AOT 编译 {总数} 个函数...")

        for 索引, 信息 in enumerate(函数列表, 1):
            if 显示进度:
                日志.信息(f"[{索引}/{总数}] 编译 {信息.模块名}.{信息.函数名}...")

            结果 = self._编译单个函数(信息)
            结果列表.append(结果)

            if 结果["状态"] == "成功":
                成功数 += 1
                if 显示进度 and 结果.get("使用缓存"):
                    日志.信息(f"  ✓ 缓存命中")
                elif 显示进度:
                    日志.信息(f"  ✓ 编译成功")
            elif 结果["状态"] == "跳过":
                跳过数 += 1
                if 显示进度:
                    日志.信息(f"  - 跳过（{结果.get('原因', '未知原因')}）")
            else:  # 失败
                失败数 += 1
                日志.错误(f"  ✗ 编译失败: {结果.get('错误', '未知错误')}")

        统计 = {
            "总数": 总数,
            "成功": 成功数,
            "失败": 失败数,
            "跳过": 跳过数,
            "结果列表": 结果列表
        }

        日志.信息(
            f"AOT 编译完成: {成功数} 成功, {失败数} 失败, {跳过数} 跳过"
        )

        return 统计

    def _编译单个函数(self, 信息: JIT函数信息) -> Dict[str, Any]:
        """
        编译单个 JIT 函数

        Returns:
            编译结果字典
        """
        if 信息.函数对象 is None:
            return {
                "函数名": 信息.函数名,
                "模块名": 信息.模块名,
                "状态": "跳过",
                "原因": "无法导入函数对象"
            }

        # 如果传入的是已装饰的转译器对象，提取原始函数
        原始函数 = 信息.函数对象
        if isinstance(原始函数, Py转Cpp转译器):
            原始函数 = 原始函数.目标函数

        try:
            # 创建编译器实例，传入 LTO 和向量化设置
            编译器实例 = Cpp编译器(
                优化级别=self.优化级别,
                启用LTO=self.启用LTO,
                启用向量化=self.启用向量化,
                SIMD指令集=self.SIMD指令集
            )

            # 创建转译器实例
            转译器实例 = Py转Cpp转译器(
                原始函数,
                编译器实例,
                可执行文件名=信息.装饰器参数.get("可执行文件名"),
                总是重编=False,  # AOT 不强制重编，利用缓存
                启用并行编译=self.启用并行编译,
                最大进程数=self.最大进程数
            )

            # 检查是否已有缓存
            库文件名 = 转译器实例.获取库文件名()
            库路径 = os.path.join(全局上下文.工作目录, 库文件名)
            使用缓存 = os.path.exists(库路径)

            if not 使用缓存:
                # 执行编译
                转译器实例.编译()

            return {
                "函数名": 信息.函数名,
                "模块名": 信息.模块名,
                "源文件": 信息.源文件路径,
                "行号": 信息.行号,
                "状态": "成功",
                "使用缓存": 使用缓存,
                "库文件": 库文件名
            }

        except Exception as e:
            return {
                "函数名": 信息.函数名,
                "模块名": 信息.模块名,
                "状态": "失败",
                "错误": str(e)
            }


def 编译包(
    根目录: str,
    递归: bool = True,
    排除目录: Optional[Set[str]] = None,
    包含测试: bool = False,
    优化级别: str = "O2",
    启用并行编译: bool = True,
    最大进程数: Optional[int] = None,
    启用LTO: bool = False,
    启用向量化: bool = False,
    SIMD指令集: Optional[str] = None,
    显示进度: bool = True
) -> Dict[str, Any]:
    """
    扫描并编译包中的所有 JIT 函数

    Args:
        根目录: 包的根目录
        递归: 是否递归扫描子目录
        排除目录: 要排除的目录名集合
        包含测试: 是否包含测试文件
        优化级别: 编译优化级别
        启用并行编译: 是否启用并行编译
        最大进程数: 最大并行进程数
        启用LTO: 是否启用链接时优化（LTO）
        启用向量化: 是否启用 SIMD 向量化优化
        SIMD指令集: 指定 SIMD 指令集（None 表示自动检测）
        显示进度: 是否显示编译进度

    Returns:
        编译统计信息
    """
    扫描器 = 包扫描器(根目录)
    jit函数列表 = 扫描器.扫描目录(递归, 排除目录, 包含测试)

    if not jit函数列表:
        日志.警告("未找到任何 JIT 函数")
        return {"总数": 0, "成功": 0, "失败": 0, "跳过": 0, "结果列表": []}

    编译器 = AOT编译器(优化级别, 启用并行编译, 最大进程数, 启用LTO, 启用向量化, SIMD指令集)
    return 编译器.编译函数列表(jit函数列表, 显示进度)


def 编译函数列表(
    函数列表: List[Callable],
    优化级别: str = "O2",
    启用并行编译: bool = True,
    最大进程数: Optional[int] = None,
    启用LTO: bool = False,
    启用向量化: bool = False,
    SIMD指令集: Optional[str] = None,
    显示进度: bool = True
) -> Dict[str, Any]:
    """
    编译给定的函数列表

    Args:
        函数列表: 要编译的函数列表（可以是普通函数或 JIT 装饰后的转译器对象）
        优化级别: 编译优化级别
        启用并行编译: 是否启用并行编译
        最大进程数: 最大并行进程数
        启用LTO: 是否启用链接时优化（LTO）
        启用向量化: 是否启用 SIMD 向量化优化
        SIMD指令集: 指定 SIMD 指令集（None 表示自动检测）
        显示进度: 是否显示编译进度

    Returns:
        编译统计信息
    """
    jit函数信息列表 = []

    for 函数 in 函数列表:
        # 处理 Py转Cpp转译器 对象（已通过 @jit 装饰的函数）
        if isinstance(函数, Py转Cpp转译器):
            try:
                # 从转译器中获取原始函数信息
                原始函数 = 函数.目标函数
                信息 = JIT函数信息(
                    函数名=函数.函数名,
                    函数对象=原始函数,  # 使用原始函数对象进行编译
                    模块名=原始函数.__module__,
                    源文件路径=inspect.getfile(原始函数),
                    行号=inspect.getsourcelines(原始函数)[1]
                )
                jit函数信息列表.append(信息)
            except Exception as e:
                日志.警告(f"无法获取转译器 {函数.函数名} 的信息: {e}")
            continue

        # 处理普通函数（未通过 @jit 装饰）
        if not callable(函数):
            continue

        try:
            信息 = JIT函数信息(
                函数名=函数.__name__,
                函数对象=函数,
                模块名=函数.__module__,
                源文件路径=inspect.getfile(函数),
                行号=inspect.getsourcelines(函数)[1]
            )
            jit函数信息列表.append(信息)
        except Exception as e:
            日志.警告(f"无法获取函数 {函数} 的信息: {e}")

    编译器 = AOT编译器(优化级别, 启用并行编译, 最大进程数, 启用LTO, 启用向量化, SIMD指令集)
    return 编译器.编译函数列表(jit函数信息列表, 显示进度)


def main():
    """CLI 入口点"""
    parser = argparse.ArgumentParser(
        description="l0n0lc AOT 预编译工具 - 批量预编译 JIT 函数",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 编译当前目录下的所有 JIT 函数
  l0n0lc-aot-compile

  # 编译指定目录
  l0n0lc-aot-compile --path /path/to/project

  # 使用 O3 优化级别
  l0n0lc-aot-compile --optimization O3

  # 启用链接时优化（LTO）
  l0n0lc-aot-compile --enable-lto

  # 启用 SIMD 向量化优化
  l0n0lc-aot-compile --enable-vectorize

  # 指定 SIMD 指令集
  l0n0lc-aot-compile --enable-vectorize --simd AVX2

  # 包含测试文件
  l0n0lc-aot-compile --include-tests

  # 禁用并行编译
  l0n0lc-aot-compile --no-parallel

  # 组合多个优化选项
  l0n0lc-aot-compile --optimization O3 --enable-lto --enable-vectorize
        """
    )

    parser.add_argument(
        "--path", "-p",
        default=".",
        help="要扫描的目录路径（默认为当前目录）"
    )

    parser.add_argument(
        "--optimization", "-O",
        choices=["O0", "O1", "O2", "O3", "Os", "Ofast", "Og", "Oz"],
        default="O2",
        help="编译优化级别（默认为 O2）"
    )

    parser.add_argument(
        "--no-parallel",
        action="store_true",
        help="禁用并行编译"
    )

    parser.add_argument(
        "--max-processes",
        type=int,
        default=None,
        help="最大并行进程数（默认为 CPU 核心数）"
    )

    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="包含测试文件（test_*.py）"
    )

    parser.add_argument(
        "--exclude",
        action="append",
        help="要排除的目录名（可多次使用）"
    )

    parser.add_argument(
        "--enable-lto",
        action="store_true",
        help="启用链接时优化（LTO），可提升运行时性能 10-30%%，但会增加编译时间"
    )

    parser.add_argument(
        "--enable-vectorize",
        action="store_true",
        help="启用 SIMD 向量化优化，可提升数组操作性能 2-8x"
    )

    parser.add_argument(
        "--simd",
        choices=["SSE2", "SSE4_2", "AVX", "AVX2", "AVX512F", "NEON"],
        default=None,
        help="指定 SIMD 指令集（默认为自动检测）"
    )

    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="静默模式，减少输出"
    )

    parser.add_argument(
        "--version", "-v",
        action="version",
        version="l0n0lc AOT 编译器 v0.3.0"
    )

    args = parser.parse_args()

    # 设置日志级别
    if args.quiet:
        日志.设置级别(日志级别.警告)

    # 构建排除目录集合
    默认排除目录 = {
        "__pycache__",
        ".git",
        ".venv",
        "venv",
        "env",
        "build",
        "dist",
        ".eggs",
        "*.egg-info",
    }
    if args.exclude:
        默认排除目录.update(args.exclude)

    # 执行编译
    统计 = 编译包(
        根目录=args.path,
        递归=True,
        排除目录=默认排除目录,
        包含测试=args.include_tests,
        优化级别=args.optimization,
        启用并行编译=not args.no_parallel,
        最大进程数=args.max_processes,
        启用LTO=args.enable_lto,
        启用向量化=args.enable_vectorize,
        SIMD指令集=args.simd,
        显示进度=not args.quiet
    )

    # 返回适当的退出码
    if 统计["失败"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
