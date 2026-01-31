"""
类型推断工具模块 - 统一处理类型推断逻辑
消除代码中重复的类型推断和返回类型推断逻辑
"""

import ast
import inspect
import ctypes
from typing import Any, Optional, Set, Union, TYPE_CHECKING
from .工具 import 全局上下文
from .类型转换 import 类型转换器
from .通用工具 import 解析自定义类型, 统一抛出错误
from .日志工具 import 日志
from .cpp类型 import C变量

if TYPE_CHECKING:
    from _ctypes import _CData
else:
    # 运行时使用ctypes._SimpleCData作为类型替代
    _CData = ctypes._SimpleCData


class 类型推断工具:
    """统一的类型推断工具类"""
    
    @staticmethod
    def 从注解推断返回类型(node: ast.FunctionDef, transpiler) -> Optional[str]:
        """
        从函数注解推断返回类型
        
        Args:
            node: 函数定义节点
            transpiler: 转译器实例
            
        Returns:
            Optional[str]: C++返回类型，如果无法推断则返回None
        """
        if node.returns:
            return 解析自定义类型(node.returns, transpiler)
        return None
    
    @staticmethod
    def 从返回语句推断类型(return_nodes: list, transpiler) -> Optional[str]:
        """
        从返回语句推断类型
        
        Args:
            return_nodes: 返回语句节点列表
            transpiler: 转译器实例
            
        Returns:
            Optional[str]: 推断的C++类型
        """
        if not return_nodes:
            return None
            
        # 分析所有返回语句的值类型
        return_types = set()
        for ret_node in return_nodes:
            if ret_node.value:
                # 获取返回值的类型
                value_type = 类型推断工具._从表达式推断类型(ret_node.value, transpiler)
                if value_type:
                    return_types.add(value_type)
        
        # 如果所有返回值类型一致，返回该类型
        if len(return_types) == 1:
            return return_types.pop()
        
        # 如果有多种类型，返回默认类型
        return None
    
    @staticmethod
    def _从表达式推断类型(expr: ast.expr, transpiler) -> Optional[str]:
        """
        从表达式推断类型
        
        Args:
            expr: 表达式节点
            transpiler: 转译器实例
            
        Returns:
            Optional[str]: 推断的C++类型
        """
        if isinstance(expr, ast.Constant):
            # 常量类型推断
            if isinstance(expr.value, int):
                return "int"
            elif isinstance(expr.value, float):
                return "double"
            elif isinstance(expr.value, str):
                return "std::string"
            elif isinstance(expr.value, bool):
                return "bool"
        elif isinstance(expr, ast.Name):
            # 变量名类型推断
            var = transpiler.获取C变量(expr.id)
            if var:
                return var.类型
        elif isinstance(expr, ast.Call):
            # 函数调用类型推断
            return 类型推断工具._从函数调用推断类型(expr, transpiler)
        elif isinstance(expr, ast.BinOp):
            # 二元运算类型推断
            return 类型推断工具._从二元运算推断类型(expr, transpiler)
        
        return None
    
    @staticmethod
    def _从函数调用推断类型(call: ast.Call, transpiler) -> Optional[str]:
        """
        从函数调用推断返回类型
        
        Args:
            call: 函数调用节点
            transpiler: 转译器实例
            
        Returns:
            Optional[str]: 推断的C++类型
        """
        if isinstance(call.func, ast.Name):
            func_name = call.func.id
            
            # 检查是否是已知的内置函数
            if func_name in 全局上下文.Python内置映射:
                py_func = 全局上下文.Python内置映射[func_name]
                if hasattr(py_func, '__annotations__') and 'return' in py_func.__annotations__:
                    return 解析自定义类型(py_func.__annotations__['return'], transpiler)
            
            # 检查函数映射表
            for mapped_func, mapping in 全局上下文.函数映射表.items():
                if mapped_func.__name__ == func_name:
                    # 可以从映射中推断返回类型
                    if hasattr(mapped_func, '__annotations__') and 'return' in mapped_func.__annotations__:
                        return 解析自定义类型(mapped_func.__annotations__['return'], transpiler)
        
        return None
    
    @staticmethod
    def _从二元运算推断类型(binop: ast.BinOp, transpiler) -> Optional[str]:
        """
        从二元运算推断类型
        
        Args:
            binop: 二元运算节点
            transpiler: 转译器实例
            
        Returns:
            Optional[str]: 推断的C++类型
        """
        left_type = 类型推断工具._从表达式推断类型(binop.left, transpiler)
        right_type = 类型推断工具._从表达式推断类型(binop.right, transpiler)
        
        # 简单的类型提升规则
        if left_type and right_type:
            if left_type == right_type:
                return left_type
            elif left_type == "double" or right_type == "double":
                return "double"
            elif left_type == "int" and right_type == "int":
                return "int"
        
        return None
    
    @staticmethod
    def 推断函数返回类型(func: Any, transpiler) -> str:
        """
        推断函数的返回类型
        
        Args:
            func: 函数对象
            transpiler: 转译器实例
            
        Returns:
            str: C++返回类型
        """
        # 1. 检查类型注解
        if hasattr(func, '__annotations__') and 'return' in func.__annotations__:
            return 解析自定义类型(func.__annotations__['return'], transpiler)
        
        # 2. 检查函数映射
        mapped_type = 全局上下文.类型映射表.get(func)
        if mapped_type:
            return mapped_type.目标类型
        
        # 3. 默认返回类型
        return "void"
    
    @staticmethod
    def 解析类型注解(annotation: Any, transpiler) -> str:
        """
        解析类型注解
        
        Args:
            annotation: 类型注解
            transpiler: 转译器实例
            
        Returns:
            str: C++类型
        """
        if isinstance(annotation, str):
            # 字符串类型的注解
            return annotation
        else:
            # AST节点或类型对象
            return 解析自定义类型(annotation, transpiler)
    
    @staticmethod
    def 推断参数类型(node: ast.arg, transpiler) -> tuple[str, Any, Optional[_CData]]:
        """
        统一的参数类型推断逻辑
        
        Args:
            node: 参数节点
            transpiler: 转译器实例
            
        Returns:
            tuple: (C++类型, Python类型, ctypes类型)
        """
        name = node.arg
        
        if node.annotation is None:
            # 对于类方法的self/cls参数，不需要类型注解
            if hasattr(transpiler, '是类') and transpiler.是类 and name in ["self", "cls"]:
                # 类型转换：ctypes.c_voidp 继承自 _SimpleCData，而 _SimpleCData 继承自 _CData
                return "void*", type(None), ctypes.c_voidp  # type: ignore
            else:
                统一抛出错误(transpiler, f"Argument '{name}' must have type annotation", node)
        
        # 使用表达式访问者获取类型
        from .表达式处理 import 表达式访问者
        expr_visitor = 表达式访问者(transpiler)
        py_type = expr_visitor.获取值(node.annotation, is_type_annotation=True)
        
        # 处理字符串类型注解
        if isinstance(py_type, str) and py_type not in ["int", "float", "str", "bool", "void", "bytes"]:
            if py_type in transpiler.全局变量:
                potential_class = transpiler.全局变量[py_type]
                if inspect.isclass(potential_class):
                    py_type = potential_class
                    日志.类型推断信息(name, str(potential_class), potential_class.__name__)
        
        # 获取C++类型
        c_type = 解析自定义类型(py_type, transpiler)
        
        # 获取ctypes类型
        ctypes_type = 类型转换器.Python类型转ctypes(py_type) if not hasattr(transpiler, '可执行文件名') or not transpiler.可执行文件名 else None
        
        return c_type, py_type, ctypes_type
    
    @staticmethod
    def 处理列表参数类型(name: str, c_type: str, py_type: Any, transpiler) -> tuple:
        """
        处理列表参数类型的统一逻辑
        
        Args:
            name: 参数名
            c_type: C++类型
            py_type: Python类型
            transpiler: 转译器实例
            
        Returns:
            tuple: (指针变量, 长度变量, ctypes参数类型列表)
        """
        if not str(c_type).startswith("std::vector"):
            return None, None, []
        
        # 添加vector头文件
        transpiler.包含头文件.add("<vector>")
        
        # 提取基础类型
        base_type = str(c_type)[12:-1]  # std::vector<int> -> int
        
        # 创建指针和长度变量
        ptr_name = f"{name}_ptr"
        len_name = f"{name}_len"

        ptr_var = C变量(f"{base_type}*", ptr_name, True)
        len_var = C变量("int64_t", len_name, True)
        
        # 处理ctypes类型
        ctypes_types = []
        if not hasattr(transpiler, '可执行文件名') or not transpiler.可执行文件名:
            origin = getattr(py_type, "__origin__", None)
            args = getattr(py_type, "__args__", [])
            if origin is list and args:
                elem_type = args[0]
                ctypes_elem = 类型转换器.Python类型转ctypes(elem_type)
                ctypes_types = [ctypes.POINTER(ctypes_elem), ctypes.c_int64]
            else:
                统一抛出错误(transpiler, f"Complex list type {py_type} not supported for JIT args", None)  # type: ignore
        
        return ptr_var, len_var, ctypes_types
    
    @staticmethod
    def 检查并添加容器头文件(c_type: str, transpiler):
        """
        检查并添加容器类型的头文件
        
        Args:
            c_type: C++类型
            transpiler: 转译器实例
        """
        if str(c_type).startswith("std::unordered_set"):
            transpiler.包含头文件.add("<unordered_set>")
        elif str(c_type).startswith("std::unordered_map"):
            transpiler.包含头文件.add("<unordered_map>")
            # 如果键或值类型包含string，添加string头文件
            if "std::string" in str(c_type):
                transpiler.包含头文件.add("<string>")
        elif str(c_type).startswith("std::vector"):
            transpiler.包含头文件.add("<vector>")
        elif str(c_type).startswith("std::string"):
            transpiler.包含头文件.add("<string>")
    
    @staticmethod
    def 推断变量类型(node: ast.AST, transpiler) -> Optional[str]:
        """
        统一的变量类型推断
        
        Args:
            node: AST节点
            transpiler: 转译器实例
            
        Returns:
            Optional[str]: 推断的C++类型
        """
        # 类型检查：确保node是ast.expr类型
        if not isinstance(node, ast.expr):
            return None
        return 类型推断工具._从表达式推断类型(node, transpiler)
    
    @staticmethod
    def 验证类型一致性(types: Set[str], context: str, transpiler) -> bool:
        """
        验证类型一致性
        
        Args:
            types: 类型集合
            context: 上下文信息
            transpiler: 转译器实例
            
        Returns:
            bool: 类型是否一致
        """
        if len(types) <= 1:
            return True
        
        日志.警告(f"类型不一致 {context}: 发现 {len(types)} 种不同类型")
        return False
