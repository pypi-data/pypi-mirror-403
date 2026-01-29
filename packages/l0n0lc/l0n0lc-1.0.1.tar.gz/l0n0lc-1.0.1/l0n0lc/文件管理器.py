"""
文件管理器模块

统一管理文件路径构建、文件清理和缓存管理操作。
消除重复代码，提供一致的文件操作接口。
"""

import os
import glob
import time
from typing import List, Optional, Set


class 文件管理器:
    """
    统一管理文件路径和清理操作

    负责处理所有与文件系统相关的操作，包括：
    - 文件路径构建
    - 临时文件清理
    - 缓存管理
    - 目录操作
    """

    def __init__(self, 工作目录: str):
        """
        初始化文件管理器

        Args:
            工作目录: 编译输出目录
        """
        self.工作目录 = 工作目录

    def 获取完整路径(self, 文件名: str) -> str:
        """
        获取文件的完整路径

        Args:
            文件名: 文件名（不含路径）

        Returns:
            完整路径: 工作目录/文件名
        """
        return f"{self.工作目录}/{文件名}"

    def 确保目录存在(self):
        """确保工作目录存在，不存在则创建"""
        if not os.path.exists(self.工作目录):
            try:
                os.makedirs(self.工作目录, exist_ok=True)
            except OSError as e:
                raise RuntimeError(f"无法创建工作目录 {self.工作目录}: {e}")

    def 清理临时文件(self, 基础名称: str):
        """
        清理编译产生的临时文件

        Args:
            基础名称: 文件的基础名称（不含扩展名）
        """
        temp_patterns = [
            f"{self.工作目录}/{基础名称}*.o",
            f"{self.工作目录}/{基础名称}*.tmp",
            f"{self.工作目录}/{基础名称}*.bak"
        ]

        self._删除文件按模式(temp_patterns)

    def 清理编译文件(self, 文件名列表: List[str]):
        """
        清理指定的编译文件

        Args:
            文件名列表: 需要清理的文件名列表
        """
        for 文件名 in 文件名列表:
            file_path = self.获取完整路径(文件名)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    pass  # 忽略删除失败

    def 清理所有缓存(self, 过期时间: Optional[float] = None) -> int:
        """
        清理所有缓存文件

        Args:
            过期时间: 可选，只清理超过此时间（秒）的文件
                     如果为 None，则清理所有缓存

        Returns:
            清理的文件数量
        """
        patterns = [
            os.path.join(self.工作目录, "*.so"),
            os.path.join(self.工作目录, "*.o"),
            os.path.join(self.工作目录, "*.tmp"),
            os.path.join(self.工作目录, "*.bak"),
            os.path.join(self.工作目录, "*.cpp"),
            os.path.join(self.工作目录, "*.h"),
            os.path.join(self.工作目录, "*.hash"),
            os.path.join(self.工作目录, "*.dylib"),  # macOS
            os.path.join(self.工作目录, "*.dll")     # Windows
        ]

        cleaned_count = 0
        当前时间 = time.time()

        for pattern in patterns:
            for file_path in glob.glob(pattern):
                try:
                    # 检查文件是否过期
                    if 过期时间 is not None:
                        file_mtime = os.path.getmtime(file_path)
                        if 当前时间 - file_mtime <= 过期时间:
                            continue

                    os.remove(file_path)
                    cleaned_count += 1
                except OSError:
                    pass

        return cleaned_count

    def 清理旧文件(self, 文件前缀: str):
        """
        清理具有指定前缀的所有旧文件

        Args:
            文件前缀: 文件名前缀
        """
        if not os.path.exists(self.工作目录):
            return

        for fname in os.listdir(self.工作目录):
            if fname.startswith(文件前缀):
                file_path = os.path.join(self.工作目录, fname)
                try:
                    os.remove(file_path)
                except OSError:
                    pass

    def 文件是否存在(self, 文件名: str) -> bool:
        """
        检查文件是否存在

        Args:
            文件名: 文件名

        Returns:
            文件是否存在
        """
        return os.path.exists(self.获取完整路径(文件名))

    def 文件是否可读(self, 文件名: str) -> bool:
        """
        检查文件是否可读

        Args:
            文件名: 文件名

        Returns:
            文件是否可读
        """
        file_path = self.获取完整路径(文件名)
        return os.path.exists(file_path) and os.access(file_path, os.R_OK)

    def 获取文件大小(self, 文件名: str) -> int:
        """
        获取文件大小

        Args:
            文件名: 文件名

        Returns:
            文件大小（字节）
        """
        file_path = self.获取完整路径(文件名)
        if os.path.exists(file_path):
            return os.path.getsize(file_path)
        return 0

    def 获取文件修改时间(self, 文件名: str) -> float:
        """
        获取文件修改时间

        Args:
            文件名: 文件名

        Returns:
            文件修改时间（时间戳）
        """
        file_path = self.获取完整路径(文件名)
        if os.path.exists(file_path):
            return os.path.getmtime(file_path)
        return 0

    def 写入文件(self, 文件名: str, 内容: str):
        """
        写入内容到文件

        Args:
            文件名: 文件名
            内容: 文件内容
        """
        self.确保目录存在()
        file_path = self.获取完整路径(文件名)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(内容)

    def 读取文件(self, 文件名: str) -> Optional[str]:
        """
        读取文件内容

        Args:
            文件名: 文件名

        Returns:
            文件内容，如果文件不存在返回 None
        """
        file_path = self.获取完整路径(文件名)
        if not os.path.exists(file_path):
            return None

        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def 列出文件(self, 模式: str = "*") -> List[str]:
        """
        列出工作目录中匹配模式的文件

        Args:
            模式: 文件匹配模式（如 "*.cpp"）

        Returns:
            文件列表
        """
        if not os.path.exists(self.工作目录):
            return []

        pattern = os.path.join(self.工作目录, 模式)
        return glob.glob(pattern)

    def _删除文件按模式(self, 模式列表: List[str]):
        """
        根据模式列表删除文件

        Args:
            模式列表: 文件模式列表
        """
        for pattern in 模式列表:
            for file_path in glob.glob(pattern):
                try:
                    os.remove(file_path)
                except OSError:
                    pass  # 忽略删除失败

    def 获取状态摘要(self) -> dict:
        """
        获取文件管理器的状态摘要

        Returns:
            包含当前状态的字典
        """
        状态信息 = {
            "工作目录": self.工作目录,
            "目录是否存在": os.path.exists(self.工作目录)
        }

        if 状态信息["目录是否存在"]:
            # 统计各类文件数量
            文件统计 = {
                "cpp文件": len(glob.glob(os.path.join(self.工作目录, "*.cpp"))),
                "头文件": len(glob.glob(os.path.join(self.工作目录, "*.h"))),
                "共享库": len(glob.glob(os.path.join(self.工作目录, "*.so"))) +
                         len(glob.glob(os.path.join(self.工作目录, "*.dylib"))) +
                         len(glob.glob(os.path.join(self.工作目录, "*.dll"))),
                "对象文件": len(glob.glob(os.path.join(self.工作目录, "*.o"))),
                "临时文件": len(glob.glob(os.path.join(self.工作目录, "*.tmp"))) +
                          len(glob.glob(os.path.join(self.工作目录, "*.bak")))
            }
            状态信息["文件统计"] = 文件统计

        return 状态信息
