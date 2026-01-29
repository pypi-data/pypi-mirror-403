from typing import Optional, Any, List, Dict, Union
import ast


class Jit错误(Exception):
    """JIT 基础异常类"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        """
        初始化JIT异常
        
        Args:
            message: 错误信息
            error_code: 错误代码
            context: 错误上下文信息
        """
        super().__init__(message)
        self.error_code = error_code
        self.context = context or {}
        
    def __str__(self):
        """返回格式化的错误信息"""
        base_msg = super().__str__()
        if self.error_code:
            base_msg = f"[{self.error_code}] {base_msg}"
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            base_msg += f" (Context: {context_str})"
        return base_msg


class 编译错误(Jit错误):
    """当 C++ 编译失败时抛出"""

    def __init__(self, message: str, compiler_output: Optional[str] = None, source_file: Optional[str] = None, python_source: Optional[str] = None):
        """
        初始化编译错误

        Args:
            message: 错误信息
            compiler_output: 编译器输出
            source_file: 源文件路径
            python_source: Python源码
        """
        context = {}
        if compiler_output:
            context['compiler_output'] = compiler_output
        if source_file:
            context['source_file'] = source_file
        if python_source:
            context['python_source'] = python_source
        super().__init__(message, "COMPILATION_ERROR", context)

    def __str__(self):
        """返回格式化的编译错误信息"""
        base_msg = super().__str__()

        # 尝试解析编译器输出中的行号
        cpp_line_info = self.提取C行号信息()

        result = f"❌ C++ 编译失败:\n"
        result += f"   {base_msg}\n"

        if cpp_line_info:
            result += f"   C++ 错误位置: {cpp_line_info}\n"

        if self.context.get('source_file'):
            result += f"   生成文件: {self.context['source_file']}\n"

        # 显示Python源码上下文
        python_source = self.context.get('python_source', '')
        if python_source and cpp_line_info:
            python_context = self.提取Python上下文(cpp_line_info)
            if python_context:
                result += f"\n🔍 对应的Python源码:\n"
                result += f"   {python_context}"

        # 显示详细的编译器输出
        if self.context.get('compiler_output'):
            result += f"\n📋 编译器详细输出:\n"
            compiler_output = self.context['compiler_output']
            # 只显示关键错误信息，避免冗余
            lines = compiler_output.split('\n')
            error_lines = [line for line in lines if 'error:' in line.lower() or '错误' in line]
            if error_lines:
                for line in error_lines[-3:]:  # 只显示最后3个错误
                    result += f"   {line}\n"
            else:
                # 如果没有找到error行，显示最后几行
                for line in lines[-5:]:
                    result += f"   {line}\n"

        return result

    def 提取C行号信息(self) -> Optional[str]:
        """从编译器输出中提取C++行号信息"""
        compiler_output = self.context.get('compiler_output', '')
        if not compiler_output:
            return None

        import re
        # 匹配常见的编译器错误格式: file.cpp:line:column: error:
        patterns = [
            r'^([^:]+):(\d+):(\d+): error:',
            r'^([^:]+):(\d+): error:',
        ]

        for line in compiler_output.split('\n'):
            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    file_path = match.group(1)
                    line_num = match.group(2)
                    col_num = match.group(3) if len(match.groups()) >= 3 else "?"
                    # 提取文件名
                    file_name = file_path.split('/')[-1]
                    return f"{file_name}:{line_num}:{col_num}"

        return None

    def 提取Python上下文(self, cpp_line_info: str) -> Optional[str]:
        """根据C++错误行号提取对应的Python源码上下文"""
        try:
            # 从cpp_line_info中提取行号
            import re
            match = re.search(r':(\d+):', cpp_line_info)
            if not match:
                return None

            cpp_line_num = int(match.group(1))
            python_source = self.context.get('python_source', '')
            if not python_source:
                return None

            python_lines = python_source.split('\n')

            # 简单的启发式：C++中的函数体通常从Python函数体开始后几行开始
            # 找到第一个非空、非注释的Python行作为起点
            for i, line in enumerate(python_lines):
                stripped = line.strip()
                if stripped and not stripped.startswith('#') and not stripped.startswith('"""') and not stripped.startswith("'''"):
                    # 显示这一行作为可能的错误位置
                    line_display = min(i + 1, len(python_lines))
                    return f"第{line_display}行: {stripped}"

            return None
        except (ValueError, AttributeError, KeyError, IndexError, TypeError):
            return None
        except KeyboardInterrupt:
            raise


class 运行时错误(Jit错误):
    """当运行时发生错误时抛出"""
    
    def __init__(self, message: str, function_name: Optional[str] = None, args: Optional[tuple] = None):
        """
        初始化运行时错误
        
        Args:
            message: 错误信息
            function_name: 函数名
            args: 函数参数
        """
        context = {}
        if function_name:
            context['function_name'] = function_name
        if args:
            context['args'] = args
        super().__init__(message, "RUNTIME_ERROR", context)


class 类型不匹配错误(Jit错误):
    """当类型不匹配预期时抛出"""
    
    def __init__(self, message: str, expected_type: Optional[str] = None, actual_type: Optional[str] = None, value: Any = None):
        """
        初始化类型不匹配错误
        
        Args:
            message: 错误信息
            expected_type: 期望的类型
            actual_type: 实际的类型
            value: 相关值
        """
        context = {}
        if expected_type:
            context['expected_type'] = expected_type
        if actual_type:
            context['actual_type'] = actual_type
        if value is not None:
            context['value'] = str(value)
        super().__init__(message, "TYPE_MISMATCH", context)


class 类型不一致错误(Jit错误):
    """当容器（如列表）中的元素类型不一致时抛出"""
    
    def __init__(self, message: str, container_type: Optional[str] = None, found_types: Optional[List[type]] = None):
        """
        初始化类型不一致错误
        
        Args:
            message: 错误信息
            container_type: 容器类型
            found_types: 找到的类型列表
        """
        context = {}
        if container_type:
            context['container_type'] = container_type
        if found_types:
            context['found_types'] = [str(t) for t in found_types]
        super().__init__(message, "TYPE_INCONSISTENCY", context)


class 安全错误(Jit错误):
    """当安全限制被触发时抛出"""
    
    def __init__(self, message: str, limit_type: Optional[str] = None, limit_value: Any = None, actual_value: Any = None):
        """
        初始化安全错误
        
        Args:
            message: 错误信息
            limit_type: 限制类型
            limit_value: 限制值
            actual_value: 实际值
        """
        context = {}
        if limit_type:
            context['limit_type'] = limit_type
        if limit_value is not None:
            context['limit_value'] = limit_value
        if actual_value is not None:
            context['actual_value'] = actual_value
        super().__init__(message, "SECURITY_ERROR", context)


class 依赖错误(Jit错误):
    """当依赖解析失败时抛出"""
    
    def __init__(self, message: str, dependency_name: Optional[str] = None, dependency_type: Optional[str] = None):
        """
        初始化依赖错误
        
        Args:
            message: 错误信息
            dependency_name: 依赖名称
            dependency_type: 依赖类型
        """
        context = {}
        if dependency_name:
            context['dependency_name'] = dependency_name
        if dependency_type:
            context['dependency_type'] = dependency_type
        super().__init__(message, "DEPENDENCY_ERROR", context)


class 配置错误(Jit错误):
    """当配置错误时抛出"""
    
    def __init__(self, message: str, config_key: Optional[str] = None, config_value: Any = None):
        """
        初始化配置错误
        
        Args:
            message: 错误信息
            config_key: 配置键
            config_value: 配置值
        """
        context = {}
        if config_key:
            context['config_key'] = config_key
        if config_value is not None:
            context['config_value'] = str(config_value)
        super().__init__(message, "CONFIG_ERROR", context)


# 错误码映射表
ERROR_CODE_MAP = {
    "COMPILATION_ERROR": "C001",
    "RUNTIME_ERROR": "R001", 
    "TYPE_MISMATCH": "T001",
    "TYPE_INCONSISTENCY": "T002",
    "SECURITY_ERROR": "S001",
    "DEPENDENCY_ERROR": "D001",
    "CONFIG_ERROR": "CF001"
}


def get_error_code_description(error_code: str) -> str:
    """
    获取错误码描述
    
    Args:
        error_code: 错误码
        
    Returns:
        str: 错误码描述
    """
    descriptions = {
        "C001": "编译错误",
        "R001": "运行时错误",
        "T001": "类型不匹配",
        "T002": "类型不一致",
        "S001": "安全限制触发",
        "D001": "依赖解析失败",
        "CF001": "配置错误"
    }
    return descriptions.get(error_code, "未知错误")


class 错误处理器:
    """
    统一的错误处理接口

    提供格式化错误信息、抛出异常的统一方法。
    确保所有错误都包含源码位置和上下文信息。
    """

    @staticmethod
    def 格式化错误信息(
        消息: str,
        节点: Optional[ast.AST] = None,
        源代码: Optional[str] = None,
        上下文: str = ""
    ) -> str:
        """
        格式化错误信息，包含源码位置

        Args:
            消息: 错误消息
            节点: AST节点（可选），用于获取行号和列号
            源代码: Python源代码（可选）
            上下文: 额外的上下文信息

        Returns:
            格式化的错误信息
        """
        if 节点:
            line_no = getattr(节点, "lineno", "?")
            col_offset = getattr(节点, "col_offset", "?")

            result = f"❌ 转译错误 (第{line_no}行，第{col_offset}列):\n"
            result += f"   {消息}\n"

            # 添加源码上下文
            if 源代码 and isinstance(line_no, int):
                source_lines = 源代码.split('\n')
                if 0 < line_no <= len(source_lines):
                    context_line = source_lines[line_no - 1].strip()
                    result += f"   源码: {context_line}\n"

                    # 尝试显示错误位置指示器
                    if isinstance(col_offset, int) and col_offset >= 0:
                        indent = len(context_line[:col_offset].lstrip())
                        pointer = " " * (4 + indent) + "↑"
                        result += f"{pointer}\n"

            # 添加额外上下文
            if 上下文:
                result += f"   上下文: {上下文}\n"

            return result
        else:
            # 没有节点信息，返回简单格式
            result = f"❌ 转译错误:\n   {消息}\n"
            if 上下文:
                result += f"   上下文: {上下文}\n"
            return result

    @staticmethod
    def 抛出错误(
        消息: str,
        节点: Optional[ast.AST] = None,
        源代码: Optional[str] = None,
        上下文: str = "",
        错误代码: Optional[str] = None
    ):
        """
        抛出格式化的 JIT 错误

        Args:
            消息: 错误消息
            节点: AST节点（可选）
            源代码: Python源代码（可选）
            上下文: 额外的上下文信息
            错误代码: 错误代码（可选）

        Raises:
            Jit错误: 包含格式化错误信息的异常
        """
        error_msg = 错误处理器.格式化错误信息(消息, 节点, 源代码, 上下文)
        raise Jit错误(error_msg, error_code=错误代码)

    @staticmethod
    def 抛出类型错误(
        消息: str,
        期望类型: str,
        实际类型: str,
        节点: Optional[ast.AST] = None,
        源代码: Optional[str] = None
    ):
        """
        抛出类型不匹配错误

        Args:
            消息: 错误消息
            期望类型: 期望的类型
            实际类型: 实际的类型
            节点: AST节点（可选）
            源代码: Python源代码（可选）

        Raises:
            类型不匹配错误: 包含类型信息的异常
        """
        # 使用格式化错误信息，然后创建类型不匹配错误
        上下文 = f"期望类型: {期望类型}, 实际类型: {实际类型}"
        formatted_msg = 错误处理器.格式化错误信息(消息, 节点, 源代码, 上下文)
        raise 类型不匹配错误(formatted_msg, 期望类型, 实际类型)

    @staticmethod
    def 抛出编译错误(
        消息: str,
        编译器输出: Optional[str] = None,
        源文件: Optional[str] = None,
        Python源码: Optional[str] = None
    ):
        """
        抛出编译错误

        Args:
            消息: 错误消息
            编译器输出: 编译器输出（可选）
            源文件: 源文件路径（可选）
            Python源码: Python源代码（可选）

        Raises:
            编译错误: 包含编译信息的异常
        """
        raise 编译错误(消息, 编译器输出, 源文件, Python源码)

    @staticmethod
    def 抛出不支持错误(
        特性名称: str,
        节点: Optional[ast.AST] = None,
        源代码: Optional[str] = None
    ):
        """
        抛出不支持的特性错误

        Args:
            特性名称: 不支持的特性名称
            节点: AST节点（可选）
            源代码: Python源代码（可选）

        Raises:
            Jit错误: 包含不支持特性信息的异常
        """
        消息 = f"不支持的特性: {特性名称}"
        raise 错误处理器.抛出错误(消息, 节点, 源代码, "NOT_SUPPORTED")


def 抛出错误(消息: str, 节点: Optional[ast.AST] = None, 源代码: Optional[str] = None, 上下文: str = ""):
    """
    便捷函数：抛出格式化的 JIT 错误

    Args:
        消息: 错误消息
        节点: AST节点（可选）
        源代码: Python源代码（可选）
        上下文: 额外的上下文信息
    """
    错误处理器.抛出错误(消息, 节点, 源代码, 上下文)
