"""
编译上下文模块

提供编译实例的上下文，代替部分全局状态。
每个转译器实例拥有独立的编译上下文，避免全局状态滥用。
"""

from typing import Set, Dict, Any


class 编译上下文:
    """
    编译实例的上下文

    每个转译器实例拥有独立的编译上下文，用于管理：
    - 编译栈：防止循环编译
    - 变量ID生成
    - 包含头文件
    - 链接库

    相比全局上下文，这些状态应该是实例级别的，而不是全局的。
    """

    def __init__(self, 工作目录: str = "./l0n0lcoutput"):
        """
        初始化编译上下文

        Args:
            工作目录: 编译输出目录
        """
        self.工作目录 = 工作目录
        self.编译栈: Set[str] = set()  # 防止循环编译的栈
        self.最大变量ID = 0  # 变量ID生成器
        self.包含头文件: Set[str] = set()  # 需要包含的头文件
        self.链接库: Set[str] = set()  # 需要链接的库
        self.库搜索目录: Set[str] = set()  # 库搜索目录

    def 生成变量ID(self) -> int:
        """
        生成唯一的变量ID

        Returns:
            新的变量ID
        """
        self.最大变量ID += 1
        return self.最大变量ID

    def 添加包含头文件(self, 头文件: str):
        """
        添加需要包含的头文件

        Args:
            头文件: 头文件路径，如 <stdint.h> 或 "myheader.h"
        """
        self.包含头文件.add(头文件)

    def 添加链接库(self, 库名: str):
        """
        添加需要链接的库

        Args:
            库名: 库名称，如 "m" (数学库)
        """
        self.链接库.add(库名)

    def 添加库搜索目录(self, 目录: str):
        """
        添加库搜索目录

        Args:
            目录: 库搜索目录路径
        """
        self.库搜索目录.add(目录)

    def 入栈编译(self, 标识: str):
        """
        将函数标识压入编译栈

        Args:
            标识: 函数的唯一标识

        Raises:
            RuntimeError: 如果检测到循环编译
        """
        if 标识 in self.编译栈:
            raise RuntimeError(f"检测到循环编译: {标识}")
        self.编译栈.add(标识)

    def 出栈编译(self, 标识: str):
        """
        将函数标识从编译栈弹出

        Args:
            标识: 函数的唯一标识
        """
        self.编译栈.discard(标识)

    def 是否正在编译(self, 标识: str) -> bool:
        """
        检查函数是否正在编译

        Args:
            标识: 函数的唯一标识

        Returns:
            是否正在编译
        """
        return 标识 in self.编译栈

    def 重置(self):
        """重置编译上下文（用于重复使用）"""
        self.编译栈.clear()
        self.最大变量ID = 0
        self.包含头文件.clear()
        self.链接库.clear()
        self.库搜索目录.clear()

    def 获取状态摘要(self) -> Dict[str, Any]:
        """
        获取编译上下文的当前状态摘要

        Returns:
            包含当前状态的字典
        """
        return {
            "工作目录": self.工作目录,
            "编译栈大小": len(self.编译栈),
            "最大变量ID": self.最大变量ID,
            "包含头文件数量": len(self.包含头文件),
            "链接库数量": len(self.链接库),
            "库搜索目录数量": len(self.库搜索目录),
        }
