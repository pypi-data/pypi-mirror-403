
import os
import inspect
from typing import Callable, Optional
from .Py转Cpp转译器 import Py转Cpp转译器
from .cpp编译器 import Cpp编译器
from .工具 import 全局上下文
from .日志工具 import 日志


def _从环境变量获取LTO设置() -> bool:
    """
    从环境变量获取 LTO 设置

    环境变量 L0N0LC_ENABLE_LTO:
    - "1", "true", "True", "TRUE" -> 启用 LTO
    - "0", "false", "False", "FALSE" 或未设置 -> 禁用 LTO

    Returns:
        是否启用 LTO
    """
    环境变量值 = os.environ.get('L0N0LC_ENABLE_LTO', '').strip()
    if 环境变量值:
        return 环境变量值.lower() in ('1', 'true')
    return False


def _从环境变量获取向量化设置() -> bool:
    """
    从环境变量获取向量化设置

    环境变量 L0N0LC_ENABLE_VECTORIZE:
    - "1", "true", "True", "TRUE" -> 启用向量化
    - "0", "false", "False", "FALSE" 或未设置 -> 禁用向量化

    Returns:
        是否启用向量化
    """
    环境变量值 = os.environ.get('L0N0LC_ENABLE_VECTORIZE', '').strip()
    if 环境变量值:
        return 环境变量值.lower() in ('1', 'true')
    return False


def 即时编译(
    转译器类=None,
    编译器类=None,
    总是重编: bool = False,
    可执行文件名: Optional[str] = None,
    优化级别: str = 'O2',
    启用并行编译: bool = True,
    最大进程数: Optional[int] = None,
    启用LTO: Optional[bool] = None,
    启用向量化: Optional[bool] = None,
    SIMD指令集: Optional[str] = None,
    启用代码优化: bool = True
):
    """
    JIT (即时编译) 装饰器。

    能够将受支持的 Python 函数转换为 C++ 代码，编译为动态库并加载执行。
    大大提高计算密集型任务的性能。

    注意：编译延迟到函数首次调用时才执行（可执行文件除外）。

    Args:
        转译器类: 自定义转译器类 (可选)
        编译器类: 自定义编译器类 (可选)
        总是重编: 是否每次运行都强制重新编译 (默认为 False，利用缓存)
        可执行文件名: 如果指定，将编译为独立的可执行文件而不是动态库
        优化级别: 编译优化级别，默认为 'O2'
            - O0: 无优化，编译最快，运行最慢
            - O1: 基础优化
            - O2: 标准优化（默认）
            - O3: 最大优化，编译较慢，运行最快
            - Os: 优化代码大小
            - Ofast: 激进优化（可能破坏标准合规）
            - Og: 调试优化
            - Oz: 最小代码大小
        启用并行编译: 是否启用并行编译依赖函数（默认为 True）
        最大进程数: 并行编译的最大进程数（None 表示自动检测 CPU 核心数）
        启用LTO: 是否启用链接时优化（LTO），默认为 None（自动检测环境变量）
            - None: 检查环境变量 L0N0LC_ENABLE_LTO
            - True: 强制启用 LTO
            - False: 强制禁用 LTO
            LTO 可以提升运行时性能 10-30%，但会增加编译时间
        启用向量化: 是否启用 SIMD 向量化优化，默认为 None（自动检测环境变量）
            - None: 检查环境变量 L0N0LC_ENABLE_VECTORIZE
            - True: 强制启用向量化
            - False: 强制禁用向量化
            向量化可以提升数组操作性能 2-8x，适用于计算密集型循环
        SIMD指令集: 指定 SIMD 指令集，None 表示自动检测
            可选值: SSE2, SSE4_2, AVX, AVX2, AVX512F, NEON
        启用代码优化: 是否启用代码优化（默认为 True）
            - 常量折叠：编译时计算常量表达式
            - 死代码消除：移除永远不会执行的代码
            - 循环优化：使用范围循环替代索引循环
            可以提升运行时性能 20-50%，代码体积减少 10-30%

    Examples:
        >>> @jit()
        >>> def func(x: int) -> int:
        >>>     return x * 2

        >>> @jit(优化级别='O3')
        >>> def performance_critical(x: int) -> int:
        >>>     return x ** 2

        >>> @jit(优化级别='O0')
        >>> def fast_compile(x: int) -> int:
        >>>     return x + 1

        >>> @jit(启用并行编译=False)  # 禁用并行编译
        >>> def serial_compile(x: int) -> int:
        >>>     return x + 1

        >>> @jit(最大进程数=2)  # 限制最多使用 2 个进程
        >>> def limited_parallel(x: int) -> int:
        >>>     return x * 2

        >>> @jit(启用LTO=True)  # 启用链接时优化
        >>> def lto_func(x: int) -> int:
        >>>     return x * x

        >>> @jit(启用向量化=True)  # 启用 SIMD 向量化
        >>> def vectorized_func(arr: List[int]) -> int:
        >>>     total = 0
        >>>     for x in arr:
        >>>         total += x
        >>>     return total
    """
    def 装饰器(fn: Callable):
        # 输入验证
        if not callable(fn):
            raise TypeError(
                f"@jit 装饰器只能用于函数或类，得到: {type(fn).__name__}\n"
                f"请确保 @jit 装饰器应用在函数定义上，例如：\n"
                f"  @jit()\n"
                f"  def my_function():\n"
                f"      pass"
            )

        # 检查是否为异步函数
        if inspect.iscoroutinefunction(fn):
            raise NotImplementedError("暂不支持异步函数 (async/await)，请使用同步函数")

        _编译器类 = 编译器类 or Cpp编译器
        _转译器类 = 转译器类 or Py转Cpp转译器

        # 确定 LTO 设置（优先使用参数，其次使用环境变量）
        实际LTO设置: bool
        if 启用LTO is None:
            实际LTO设置 = _从环境变量获取LTO设置()
        else:
            实际LTO设置 = 启用LTO

        # 确定向量化设置（优先使用参数，其次使用环境变量）
        实际向量化设置: bool
        if 启用向量化 is None:
            实际向量化设置 = _从环境变量获取向量化设置()
        else:
            实际向量化设置 = 启用向量化

        # 创建编译器实例，传入所有优化参数
        编译器实例 = _编译器类(
            优化级别=优化级别,
            启用LTO=实际LTO设置,
            启用向量化=实际向量化设置,
            SIMD指令集=SIMD指令集
        )

        # 创建转译器实例，传递参数（包括并行编译参数和代码优化参数）
        转译器实例 = _转译器类(fn, 编译器实例, 可执行文件名, 总是重编, 启用并行编译, 最大进程数, 启用代码优化)

        # 可执行文件需要立即编译
        if 可执行文件名 is not None:
            库文件名 = 转译器实例.获取库文件名()
            库路径 = f'{全局上下文.工作目录}/{库文件名}'

            if 总是重编 or not os.path.exists(库路径):
                日志.缓存信息("编译", fn.__name__ if hasattr(fn, '__name__') else "unknown")
                转译器实例.编译()

        # 将转译器对象添加到目标函数的全局变量中，以便其他JIT函数可以调用它
        if hasattr(fn, '__name__'):
            转译器实例.全局变量[fn.__name__] = 转译器实例

        return 转译器实例
    return 装饰器


jit = 即时编译
