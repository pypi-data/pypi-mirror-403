"""
编译管理器模块

负责管理编译过程、缓存管理和清理操作。
从 Py转Cpp转译器 中分离出来，实现单一职责原则。
"""

from typing import List, Optional, Callable, Any
from .文件管理器 import 文件管理器
from .编译上下文 import 编译上下文
from .cpp编译器 import Cpp编译器
from .日志工具 import 日志


class 编译管理器:
    """
    编译管理器

    负责：
    - 编译过程管理
    - 缓存验证和清理
    - 依赖管理
    """

    def __init__(
        self,
        文件管理器: 文件管理器,
        编译器: Cpp编译器,
        编译上下文: 编译上下文
    ):
        """
        初始化编译管理器

        Args:
            文件管理器: 文件管理器实例
            编译器: C++ 编译器实例
            编译上下文: 编译上下文实例
        """
        self.文件管理器 = 文件管理器
        self.编译器 = 编译器
        self.编译上下文 = 编译上下文

    def 检查缓存完整性(self, 获取文件名列表) -> List[str]:
        """
        检查缓存文件的完整性

        Args:
            获取文件名列表: 返回 (cpp文件名, 头文件名, 库文件名) 的函数

        Returns:
            问题列表，如果为空表示缓存完整
        """
        try:
            cpp_file名, 头文件名, 库文件名 = 获取文件名列表()

            issues = []

            # 检查源文件是否存在且可读
            if self.文件管理器.文件是否存在(cpp_file名):
                if not self.文件管理器.文件是否可读(cpp_file名):
                    issues.append(f"源文件不可读: {cpp_file名}")
            else:
                issues.append(f"源文件不存在: {cpp_file名}")

            # 检查头文件
            if self.文件管理器.文件是否存在(头文件名):
                if not self.文件管理器.文件是否可读(头文件名):
                    issues.append(f"头文件不可读: {头文件名}")

            # 检查库文件
            if self.文件管理器.文件是否存在(库文件名):
                if not self.文件管理器.文件是否可读(库文件名):
                    issues.append(f"库文件不可读: {库文件名}")

            return issues

        except Exception as e:
            return [f"缓存完整性检查失败: {str(e)}"]

    def 清理编译文件(self, 文件名列表: List[str]):
        """
        清理编译文件

        Args:
            文件名列表: 需要清理的文件名列表
        """
        try:
            self.文件管理器.清理编译文件(文件名列表)

            # 清理临时文件（使用第一个文件名的基础名称）
            if 文件名列表:
                基础名称 = 文件名列表[0].rsplit('.', 1)[0] if '.' in 文件名列表[0] else 文件名列表[0]
                self.文件管理器.清理临时文件(基础名称)

        except (OSError, IOError) as e:
            # 清理过程中的错误不应该掩盖原始错误
            日志.调试(f"清理文件时出错: {e}")
        except Exception as e:
            # 其他未预期的异常
            日志.警告(f"清理文件时发生未预期错误: {e}")

    def 清理所有缓存(self) -> int:
        """
        清理所有缓存文件

        Returns:
            清理的文件数量
        """
        try:
            return self.文件管理器.清理所有缓存()
        except (OSError, IOError) as e:
            日志.调试(f"清理缓存时出错: {e}")
            return 0
        except Exception as e:
            日志.警告(f"清理缓存时发生未预期错误: {e}")
            return 0

    def 配置编译器(
        self,
        库目录列表: Optional[List[str]] = None,
        链接库列表: Optional[List[str]] = None
    ):
        """
        配置编译器

        Args:
            库目录列表: 库搜索目录列表
            链接库列表: 需要链接的库列表
        """
        if 库目录列表:
            self.编译器.添加库目录(库目录列表)

        if 链接库列表:
            self.编译器.添加库(链接库列表)

    def 执行编译(
        self,
        源文件列表: List[str],
        输出路径: str,
        是否为可执行文件: bool = False,
        编译选项: Optional[List[str]] = None
    ):
        """
        执行编译

        Args:
            源文件列表: 源文件路径列表
            输出路径: 输出文件路径
            是否为可执行文件: 是否编译为可执行文件
            编译选项: 额外的编译选项
        """
        if 编译选项:
            for option in 编译选项:
                self.编译器.添加编译选项(option)

        if 是否为可执行文件:
            self.编译器.编译文件(源文件列表, 输出路径)
        else:
            self.编译器.编译共享库(源文件列表, 输出路径)

    def 获取状态摘要(self) -> dict:
        """
        获取编译管理器的状态摘要

        Returns:
            包含当前状态的字典
        """
        return {
            "文件管理器状态": self.文件管理器.获取状态摘要() if hasattr(self.文件管理器, '获取状态摘要') else {},
            "编译上下文状态": self.编译上下文.获取状态摘要(),
        }
