import re
import os
import ctypes
import inspect
import threading
from typing import List, Optional, Any, Dict, Set, Callable, Union


def 十进制转进制(value: int, base: int, digits="0123456789ABCDEF") -> str:
    """将十进制整数转换为任意进制字符串"""
    if value == 0:
        return "0"
    result = ""
    is_negative = value < 0
    value = abs(value)
    while value > 0:
        value, remainder = divmod(value, base)
        result = digits[remainder] + result
    return ("-" if is_negative else "") + result


class Cpp函数映射:
    """
    存储 Python 函数到 C++ 函数的映射关系。
    包含目标函数名（或代码生成器）、头文件依赖和库文件依赖。
    """

    def __init__(
            self, 目标函数: Union[str, Callable],
            包含目录: Optional[List[str]] = None,
            库: Optional[List[str]] = None,
            库目录: Optional[List[str]] = None) -> None:
        self.目标函数 = 目标函数
        self.包含目录 = 包含目录 or []
        self.库 = 库 or []
        self.库目录 = 库目录 or []

    def __str__(self) -> str:
        if callable(self.目标函数):
            return f"<function {self.目标函数.__name__}>"
        return str(self.目标函数)


class Cpp类型映射:
    """
    存储 Python 类型到 C++ 类型的映射关系。
    包含目标类型名、ctypes 类型以及相关的编译依赖。
    """

    def __init__(
            self, 目标类型: str,
            包含目录: Optional[List[str]] = None,
            库: Optional[List[str]] = None,
            库目录: Optional[List[str]] = None,
            ctypes类型=None) -> None:
        self.目标类型 = 目标类型
        self.包含目录 = 包含目录 or []
        self.库 = 库 or []
        self.库目录 = 库目录 or []
        self.ctypes类型 = ctypes类型

    def __str__(self) -> str:
        return self.目标类型


class 全局上下文:
    """
    全局上下文，存储所有的函数/类型映射配置、内置函数列表以及全局编译设置。

    线程安全说明：
    - JIT 编译过程通常是单线程的，全局上下文主要用于管理和清理状态
    - 清理() 方法是线程安全的，可用于测试环境
    - 直接访问静态变量不是线程安全的，多线程环境需要外部同步
    """

    直接调用函数集: Set = set()  # 直接在 Python 端执行的函数集合 (如 range)
    函数映射表: Dict[Any, Cpp函数映射] = {}  # 函数映射表
    类型映射表: Dict[Any, Cpp类型映射] = {}  # 类型映射表
    反向类型映射表: Dict[Any, Any] = {}  # 类型映射表
    包含集合: Set = set()
    链接库集合: Set = set()
    最大变量ID = 0
    Python内置映射 = {}
    使用Unicode = True
    工作目录 = './l0n0lcoutput'  # 编译输出目录
    编译栈: Set = set()  # 全局编译栈，用于防止循环编译

    @staticmethod
    def 缓存直接调用():
        全局上下文.直接调用函数集.add(range)

    @staticmethod
    def 添加内置映射(v):
        全局上下文.Python内置映射[v.__name__] = v

    @staticmethod
    def 初始化内置():
        """初始化常用的 Python 内置函数映射"""
        # 初始化常用的 Python 内置函数映射
        for v in [int, float, bytes, str, bool, range, complex, set, tuple, list, dict,
                  print, input, abs, round, pow, divmod, sum, min, max,
                  isinstance, len, open, Exception, BaseException]:
            全局上下文.添加内置映射(v)

    @staticmethod
    def 清理():
        """
        清理全局状态，重置所有集合和映射。

        线程安全：使用锁保护，可在多线程环境中调用。

        用于测试或需要重置全局状态的场景。
        注意：这会清除所有已注册的映射和配置（不包括内置映射）。
        """
        with 全局上下文._lock:
            全局上下文.直接调用函数集.clear()
            全局上下文.函数映射表.clear()
            全局上下文.类型映射表.clear()
            全局上下文.反向类型映射表.clear()
            全局上下文.包含集合.clear()
            全局上下文.链接库集合.clear()
            全局上下文.编译栈.clear()
            全局上下文.最大变量ID = 0
            # 注意：不清空 Python内置映射 和工作目录，这些是配置

    # 类变量（仅用于清理方法）
    _lock = threading.RLock()  # 使用可重入锁


全局上下文.初始化内置()


def 可直接调用(fn):
    """
    装饰器：注册一个 Python 函数为"直接调用"模式。
    转译器遇到此函数时不会尝试转换为 C++ 调用，而是回调 Python 解释器执行。
    """
    全局上下文.直接调用函数集.add(fn)
    return fn


def 映射函数(
        mapped_function,
        包含目录: Optional[List[str]] = None,
        库: Optional[List[str]] = None,
        库目录: Optional[List[str]] = None):
    """
    装饰器：将 Python 函数映射到 C++ 代码片段或函数。

    :param mapped_function: 被映射的原 Python 函数
    :param 包含目录: 需要包含的头文件
    """
    def decorator(target):
        全局上下文.函数映射表[mapped_function] = Cpp函数映射(target, 包含目录, 库, 库目录)
        return target
    return decorator


def 映射类型(mapped_type,
         包含目录: Optional[List[str]] = None,
         库: Optional[List[str]] = None,
         库目录: Optional[List[str]] = None,
         ctypes类型=None):
    """
    装饰器：将 Python 类型映射到 C++ 类型。
    """
    def decorator(target):
        类型映射 = Cpp类型映射(mapped_type, 包含目录, 库, 库目录, ctypes类型)
        全局上下文.类型映射表[target] = 类型映射
        全局上下文.反向类型映射表[mapped_type] = target
        return target
    return decorator


def 含非ASCII字符(s: str) -> bool:
    """检查字符串是否包含非 ASCII 字符（如中文）"""
    return bool(re.search(r'[^A-Za-z0-9_]', s))


def 生成变量ID(original_name: Optional[str] = None) -> str:
    """
    生成合法的 C++ 变量/函数标识符。
    如果 original_name 是 ASCII 且 use_unicode=True 则直接使用，
    否则生成唯一的临时 ID。
    """
    if original_name is not None and (全局上下文.使用Unicode or not 含非ASCII字符(original_name)):
        return original_name
    ret = f'_{全局上下文.最大变量ID}'
    全局上下文.最大变量ID += 1
    return ret

def 转C字符串(v) -> str:
    """将 Python 值转换为 C++ 字符串表示"""
    if isinstance(v, (str, bytes)):
        return f'u8"{v}"'
    return str(v)




# ==================== 优化后的映射函数实现 ====================

def 映射函数到(
    cpp: str,
    headers: Optional[List[str]] = None,
    libraries: Optional[List[str]] = None,
    library_dirs: Optional[List[str]] = None,
    validate: bool = True,
    **kwargs
):
    """
    优化的函数映射装饰器

    Args:
        cpp: C++代码模板，使用{参数名}作为占位符
        headers: 需要包含的头文件列表
        libraries: 需要链接的库列表
        library_dirs: 库搜索目录列表
        validate: 是否验证参数匹配
        **kwargs: 额外的模板变量，如模板参数T等

    Example:
        @映射到(
            cpp='strlen({text})',
            headers=['<cstring>']
        )
        def strlen(text: bytes) -> int:
            \"\"\"计算字符串长度\"\"\"
            pass
    """
    def decorator(func):
        # 获取函数签名
        sig = inspect.signature(func)
        param_names = list(sig.parameters.keys())

        # 参数验证
        if validate:
            # 从模板中提取参数引用
            template_refs = set(re.findall(r'\{(\w+)\}', cpp))

            # 分离函数参数和额外参数
            func_params = set(param_names)
            extra_params = set(kwargs.keys())

            # 检查模板中引用的参数
            missing = template_refs - func_params - extra_params
            if missing:
                raise ValueError(
                    f"模板引用了未定义的参数: {missing}. "
                    f"可用参数: 函数参数={func_params}, 额外参数={extra_params}"
                )

        # 创建代码生成函数
        def code_generator(*args, **call_kwargs):
            # 合并函数参数和额外参数
            all_kwargs = {}
            all_kwargs.update(kwargs)  # 额外参数如T='int'

            # 添加调用时的函数参数
            for i, arg in enumerate(args):
                if i < len(param_names):
                    all_kwargs[param_names[i]] = arg

            # 添加关键字参数
            all_kwargs.update(call_kwargs)

            # 替换模板
            result = cpp
            for name, value in all_kwargs.items():
                result = result.replace(f'{{{name}}}', str(value))

            return result

        # 注册到全局上下文
        全局上下文.函数映射表[func] = Cpp函数映射(
            code_generator,
            headers or [],
            libraries or [],
            library_dirs or []
        )

        return func

    return decorator

