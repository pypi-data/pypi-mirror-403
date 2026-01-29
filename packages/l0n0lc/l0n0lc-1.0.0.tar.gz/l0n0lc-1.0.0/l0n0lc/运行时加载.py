import ctypes
from typing import Tuple, Any, Optional
import sys
import os

# 安全限制配置
MAX_ARRAY_SIZE = 10**6  # 最大数组大小
MAX_NESTING_DEPTH = 100  # 最大嵌套深度

# 导入对象池
from .数组对象池 import 获取全局对象池, 获取全局池统计, 数组对象池


class 运行时加载器:
    """处理编译后库的加载和调用"""

    def __init__(self, transpiler):
        self.transpiler = transpiler

    def 递归加载依赖(self, transpiler, loaded_deps, depth=0):
        """递归加载所有依赖的类库"""
        # 检查嵌套深度，防止无限递归
        if depth > MAX_NESTING_DEPTH:
            raise RuntimeError(f"依赖嵌套深度超过限制 {MAX_NESTING_DEPTH}")
        
        for dep in transpiler.依赖函数:
            if dep in loaded_deps:
                continue
            
            # 验证依赖对象
            if not hasattr(dep, '是否为类') or not hasattr(dep, '获取库文件名'):
                raise ValueError(f"无效的依赖对象: {dep}")
                
            loaded_deps.add(dep)

            if dep.是否为类:
                # 递归加载依赖的依赖
                self.递归加载依赖(dep, loaded_deps, depth + 1)
                # 加载当前依赖的库
                dep_lib_path = dep.文件管理器.获取完整路径(dep.获取库文件名())

                # 验证库文件路径
                if not os.path.exists(dep_lib_path):
                    raise FileNotFoundError(f"依赖库文件不存在: {dep_lib_path}")

                ctypes.CDLL(dep_lib_path, mode=ctypes.RTLD_GLOBAL)

    def 加载库(self):
        """加载编译好的动态库（直接设置到转译器实例）"""
        if self.transpiler.可执行文件名:
            return

        # 递归加载所有依赖的类库
        loaded_deps = set()
        self.递归加载依赖(self.transpiler, loaded_deps)

        # 加载主库
        lib_path = self.transpiler.文件管理器.获取完整路径(self.transpiler.获取库文件名())

        # 如果是类，只加载库到全局命名空间，不获取函数符号
        self.transpiler.目标库 = ctypes.CDLL(lib_path, mode=ctypes.RTLD_GLOBAL)
        if self.transpiler.是否为类:
            # 类只需要加载库，使符号对其他编译单元可见
            self.transpiler.cpp函数 = None
        else:
            # 普通函数需要获取函数符号
            self.transpiler.cpp函数 = self.transpiler.目标库[self.transpiler.C函数名]
            self.transpiler.cpp函数.argtypes = self.transpiler.ctypes参数类型
            self.transpiler.cpp函数.restype = self.transpiler.ctypes返回类型

    def 处理参数转换(self, args: tuple) -> Tuple[list, list, list]:
        """
        处理参数转换，特别是列表参数的拆分

        优化说明:
        - 使用对象池复用 ctypes 数组，减少内存分配
        - 使用 memcpy 快速复制数据（避免逐元素赋值）
        - 支持零拷贝（当输入已经是 ctypes 数组时）

        Returns:
            (转换后的参数列表, 需要保持的引用列表, 需要释放的数组信息列表)
            释放信息格式: [(数组, 元素类型, 大小), ...]
        """
        new_args = []
        keep_alive = []
        to_release = []  # 需要释放回池的数组信息
        pool = 获取全局对象池()

        if not self.transpiler.列表参数映射:
            # 没有列表参数，直接返回
            return list(args), [], []

        # 遍历预期参数 (按名称)
        param_names = list(self.transpiler.参数变量.keys())
        arg_idx = 0

        for i, arg in enumerate(args):
            if i >= len(param_names):
                break

            param_name = param_names[i]

            if param_name in self.transpiler.列表参数映射:
                if not isinstance(arg, (list, tuple)):
                    raise TypeError(
                        f"Argument '{param_name}' expected list, got {type(arg)}"
                    )

                length = len(arg)

                # 检查数组大小限制
                if length > MAX_ARRAY_SIZE:
                    raise ValueError(
                        f"参数 '{param_name}' 的数组大小 {length} 超过限制 {MAX_ARRAY_SIZE}"
                    )

                # 空数组是允许的
                if length == 0:
                    pointer_type = self.transpiler.ctypes参数类型[arg_idx]
                    array_type = pointer_type._type_ * 0
                    c_array = array_type()
                    keep_alive.append(c_array)
                    new_args.append(c_array)
                    new_args.append(0)
                    arg_idx += 2
                    continue

                # ctypes参数类型[arg_idx] 是对应的指针类型
                pointer_type = self.transpiler.ctypes参数类型[arg_idx]
                element_type = pointer_type._type_

                # 验证数组元素类型
                for j, element in enumerate(arg):
                    if not isinstance(element, (int, float, str, bool)):
                        raise TypeError(
                            f"参数 '{param_name}' 的第 {j} 个元素类型不支持: {type(element)}"
                        )

                # 尝试从对象池获取或分配新数组
                c_array, from_pool = pool.获取或分配(element_type, length)

                # 使用 memcpy 快速复制数据
                try:
                    # 将 Python list 转为 ctypes 数组后复制
                    temp_array = (element_type * length)(*arg)
                    ctypes.memmove(ctypes.addressof(c_array), ctypes.addressof(temp_array), length * ctypes.sizeof(element_type))
                except (TypeError, ValueError) as e:
                    raise ValueError(
                        f"无法为参数 '{param_name}' 创建C数组: {e}"
                    ) from e

                keep_alive.append(c_array)
                to_release.append((c_array, element_type, length))

                new_args.append(c_array)
                new_args.append(length)

                arg_idx += 2
            else:
                new_args.append(arg)
                arg_idx += 1

        return new_args, keep_alive, to_release

    def 获取对象池(self) -> Optional[数组对象池]:
        """获取当前使用的对象池"""
        return 获取全局对象池()

    def 获取对象池统计(self):
        """获取对象池统计信息"""
        return 获取全局池统计()

    def 调用函数(self, *args, **kwargs):
        """调用编译后的函数"""
        if self.transpiler.cpp函数 is None:
            raise Exception(f"{self.transpiler.目标函数} cpp函数 is None!")

        if self.transpiler.可执行文件名:
            executable_path = self.transpiler.文件管理器.获取完整路径(self.transpiler.可执行文件名)
            raise RuntimeError(
                f"Cannot call executable directly. Run {executable_path}"
            )

        if self.transpiler.列表参数映射:
            pool = 获取全局对象池()
            new_args, keep_alive, to_release = self.处理参数转换(args)
            try:
                result = self.transpiler.cpp函数(*new_args)
            finally:
                # 释放数组回对象池
                if pool.是否启用():
                    for arr, elem_type, size in to_release:
                        pool.释放(elem_type, size, arr)
            return result

        # 处理字符串参数转换
        converted_args = []
        for i, arg in enumerate(args):
            # 检查对应的ctypes参数类型
            if i < len(self.transpiler.ctypes参数类型):
                expected_type = self.transpiler.ctypes参数类型[i]
                # 如果期望的是c_char_p且参数是字符串，转换为字节
                if expected_type == ctypes.c_char_p and isinstance(arg, str):
                    # UTF-8编码字节字符串
                    converted_args.append(arg.encode("utf-8"))
                else:
                    converted_args.append(arg)
            else:
                converted_args.append(arg)

        return self.transpiler.cpp函数(*converted_args)

    def 获取函数地址(self):
        """获取编译后的函数地址（用于其他模块调用）"""
        if self.transpiler.cpp函数 is None:
            return None
        return ctypes.cast(self.transpiler.cpp函数, ctypes.c_void_p).value
