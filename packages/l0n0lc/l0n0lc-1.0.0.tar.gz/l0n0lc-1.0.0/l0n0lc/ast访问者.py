import ast
from typing import Any, Union
from .cpp类型 import *
from .容器构建器 import 容器构建器
from .异常 import Jit错误
from .std_map import 标准无序映射
from .std_set import 标准集合
from .基础混入 import 错误处理混入, 参数处理混入, 类型处理混入

class AST访问者基类(错误处理混入, 参数处理混入, 类型处理混入):
    """AST节点访问的基类，提供基础的访问方法"""

    def __init__(self, transpiler):
        self.transpiler = transpiler

    def 计算比较(self, node: ast.Compare) -> Any:
        """处理比较运算 (==, !=, <, >, <=, >=, in, not in)"""
        # 调用transpiler的获取值方法
        left = self.transpiler.获取值(node.left)
        comparisons = []

        curr_left = left

        for op, comp in zip(node.ops, node.comparators):
            curr_right = self.transpiler.获取值(comp)

            op_str = ""
            if isinstance(op, ast.Eq):
                op_str = "=="
            elif isinstance(op, ast.NotEq):
                op_str = "!="
            elif isinstance(op, ast.Lt):
                op_str = "<"
            elif isinstance(op, ast.LtE):
                op_str = "<="
            elif isinstance(op, ast.Gt):
                op_str = ">"
            elif isinstance(op, ast.GtE):
                op_str = ">="

            if op_str:
                comparisons.append(f"({curr_left} {op_str} {curr_right})")
            elif isinstance(op, (ast.In, ast.NotIn)):
                # Check optimized contains
                contains_expr = None
                # Try to use __contains__ if available on the wrapper object
                if hasattr(curr_right, "__contains__"):
                    try:
                        contains_expr = curr_right.__contains__(curr_left)
                    except (AttributeError, TypeError, ValueError):
                        pass
                    except KeyboardInterrupt:
                        raise

                if not contains_expr:
                    # Generic std::find fallback
                    self.transpiler.包含头文件.add("<algorithm>")
                    self.transpiler.包含头文件.add("<iterator>")
                    contains_expr = f"(std::find(std::begin({curr_right}), std::end({curr_right}), {curr_left}) != std::end({curr_right}))"

                if isinstance(op, ast.In):
                    comparisons.append(f"({contains_expr})")
                else:
                    comparisons.append(f"!({contains_expr})")
            else:
                self.抛出错误(
                    f"Unsupported comparison operator: {type(op).__name__}", node
                )

            curr_left = curr_right

        if len(comparisons) == 1:
            return comparisons[0]
        return f'({" && ".join(comparisons)})'

    def 计算二元运算(self, node: Union[ast.BinOp, ast.AugAssign]):
        """处理二元运算 (+, -, *, /, %, <<, >>, &, |, ^)"""
        if isinstance(node, ast.BinOp):
            left = self.transpiler.获取值(node.left)
            right = self.transpiler.获取值(node.right)
            op = node.op
        elif isinstance(node, ast.AugAssign):
            left = self.transpiler.获取值(node.target)
            right = self.transpiler.获取值(node.value)
            op = node.op
        else:
            return None

        op_str = ""
        if isinstance(op, ast.Add):
            op_str = "+"
        elif isinstance(op, ast.Sub):
            op_str = "-"
        elif isinstance(op, ast.Mult):
            op_str = "*"
        elif isinstance(op, (ast.Div, ast.FloorDiv)):
            op_str = "/"
        elif isinstance(op, ast.Mod):
            op_str = "%"
        elif isinstance(op, ast.BitAnd):
            op_str = "&"
        elif isinstance(op, ast.BitOr):
            op_str = "|"
        elif isinstance(op, ast.BitXor):
            op_str = "^"
        elif isinstance(op, ast.LShift):
            op_str = "<<"
        elif isinstance(op, ast.RShift):
            op_str = ">>"

        if op_str:
            return f"({left} {op_str} {right})"

        self.抛出错误(f"Unsupported operator: {type(op).__name__}", node)


    def 处理super调用(self, node: ast.Call):
        """处理super()调用"""
        if not self.transpiler.是否为类:
            self.抛出错误("super() can only be used inside a class", node)

        # 检查是否有基类
        if not self.transpiler.类基类列表:
            self.抛出错误("super() requires at least one base class", node)

        # 获取第一个基类（Python的super()通常指MRO中的下一个类）
        base_class = self.transpiler.类基类列表[0]
        base_name = base_class.__name__

        # 返回一个特殊的SuperCall对象，用于后续的属性访问处理
        return SuperCallWrapper(base_name, self.transpiler)


class 语句访问者(AST访问者基类):
    """处理所有语句类型的访问者"""

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        # 这个方法会在TranspilerCore中重写
        pass

    def visit_ClassDef(self, node: ast.ClassDef) -> Any:
        # 这个方法会在ClassSupport中处理
        pass

    def visit_Return(self, node: ast.Return) -> Any:
        ret_val = self.transpiler.获取值(node.value) if node.value is not None else ""
        self.transpiler.添加代码带行号(f"return {ret_val};", node)

    def visit_If(self, node: ast.If) -> Any:
        test = self.transpiler.获取值(node.test)
        self.transpiler.添加代码带行号(f"if ({test})", node)

        with self.transpiler.代码块上下文:
            for stmt in node.body:
                self.transpiler.visit(stmt)

        if node.orelse:
            self.transpiler.添加代码带行号("else", node)
            with self.transpiler.代码块上下文:
                for stmt in node.orelse:
                    self.transpiler.visit(stmt)

    def visit_For(self, node: ast.For) -> Any:
        iter_node = node.iter

        # 特殊处理：Dict.items() 遍历
        if isinstance(iter_node, ast.Call) and isinstance(
            iter_node.func, ast.Attribute
        ):
            attr_node = iter_node.func
            if attr_node.attr == "items":
                # 检查目标是否为元组解包 (key, value)
                if isinstance(node.target, ast.Tuple) and len(node.target.elts) == 2:
                    # 获取字典对象
                    dict_obj = self.transpiler.获取值(attr_node.value)

                    # 获取键和值的变量名
                    key_target = node.target.elts[0]
                    value_target = node.target.elts[1]

                    if not isinstance(key_target, ast.Name) or not isinstance(
                        value_target, ast.Name
                    ):
                        self.抛出错误("Dict.items() target must be two names", node)

                    key_var = C变量("auto", key_target.id, False) # type: ignore
                    value_var = C变量("auto", value_target.id, False) # type: ignore

                    # 使用 C++17 结构化绑定
                    code = (
                        f"for (auto& [{key_var.C名称}, {value_var.C名称}] : {dict_obj})"
                    )

                    self.transpiler.添加代码(code)
                    with self.transpiler.代码块上下文:
                        # 注册键和值变量
                        self.transpiler.添加C变量(key_var)
                        self.transpiler.添加C变量(value_var)
                        for stmt in node.body:
                            self.transpiler.visit(stmt)
                    return

            # 特殊处理：Dict.keys() 遍历
            elif attr_node.attr == "keys":
                dict_obj = self.transpiler.获取值(attr_node.value)

                # 对于循环目标，检查是否是已存在的变量
                if isinstance(node.target, ast.Name):
                    target = self.transpiler.获取C变量(node.target.id)
                    if target is None:
                        # 创建新变量
                        target = C变量("auto", node.target.id, False)
                        self.transpiler.添加C变量(target)
                else:
                    self.抛出错误("For loop target must be a name", node)

                # 遍历键：使用结构化绑定但只使用第一个元素
                code = f"for (auto& [{target.C名称}, _] : {dict_obj})"

                self.transpiler.添加代码(code)
                with self.transpiler.代码块上下文:
                    for stmt in node.body:
                        self.transpiler.visit(stmt)
                return

            # 特殊处理：Dict.values() 遍历
            elif attr_node.attr == "values":
                dict_obj = self.transpiler.获取值(attr_node.value)

                # 对于循环目标，检查是否是已存在的变量
                if isinstance(node.target, ast.Name):
                    target = self.transpiler.获取C变量(node.target.id)
                    if target is None:
                        # 创建新变量
                        target = C变量("auto", node.target.id, False)
                        self.transpiler.添加C变量(target)
                else:
                    self.抛出错误("For loop target must be a name", node)

                # 遍历值：使用结构化绑定但只使用第二个元素
                code = f"for (auto& [_, {target.C名称}] : {dict_obj})"

                self.transpiler.添加代码(code)
                with self.transpiler.代码块上下文:
                    for stmt in node.body:
                        self.transpiler.visit(stmt)
                return

        # 原有逻辑：处理其他类型的循环
        # 特殊处理：元组解包目标 (如 for k, v in dict)
        if isinstance(node.target, ast.Tuple):
            # 为元组的每个元素创建变量
            targets = []
            for elt in node.target.elts:
                if isinstance(elt, ast.Name):
                    var = C变量("auto", elt.id, False)
                    self.transpiler.添加C变量(var)
                    targets.append(var)
                else:
                    self.抛出错误(
                        "For loop target must be a name in tuple unpacking", node
                    )
            target = targets
        else:
            # 对于for循环目标，先检查是否是已存在的变量
            if isinstance(node.target, ast.Name):
                target = self.transpiler.获取C变量(node.target.id)
                if target is None:
                    # 不存在，创建新变量
                    target = C变量("auto", node.target.id, False)
                    self.transpiler.添加C变量(target)
            else:
                # 非简单名称的情况，尝试获取值
                target = self.transpiler.获取值(node.target)
                if target is None:
                    self.抛出错误("For loop target must be a name", node)

        # 处理 range() 循环
        if isinstance(iter_node, ast.Call):
            func = self.transpiler.获取值(iter_node.func)
            if func is range:
                args = [self.transpiler.获取值(arg) for arg in iter_node.args]
                if len(args) == 1:
                    code = (
                        f"for (int64_t {target} = 0; {target} < {args[0]}; ++{target})"
                    )
                elif len(args) == 2:
                    code = f"for (int64_t {target} = {args[0]}; {target} < {args[1]}; ++{target})"
                elif len(args) == 3:
                    code = f"for (int64_t {target} = {args[0]}; {target} < {args[1]}; {target} += {args[2]})"
                else:
                    self.抛出错误("Invalid range arguments", node)
            else:
                # 泛型迭代器
                from .表达式处理 import 表达式访问者

                expr_visitor = 表达式访问者(self.transpiler)
                call_code = expr_visitor.处理调用(iter_node)
                code = f"for (auto {target} : {call_code})"
        # 处理列表/元组字面量循环
        elif isinstance(iter_node, (ast.List, ast.Tuple)):
            l = [self.transpiler.获取值(e) for e in iter_node.elts]
            init_list = 容器构建器._从列表构建初始化列表(l)
            code = f"for (auto {target} : {init_list})"
        else:
            # 处理可迭代对象循环（包括直接遍历 Dict）
            iter_obj = self.transpiler.获取值(iter_node)

            # 检查是否为 Dict 类型的直接遍历
            if isinstance(iter_obj, 标准无序映射):
                # 直接遍历 Dict 时，遍历键
                if isinstance(target, list) and len(target) == 2:
                    # 元组解包：k, v in dict
                    code = f"for (auto& [{target[0].C名称}, {target[1].C名称}] : {iter_obj})"
                else:
                    # 单变量：k in dict
                    target_name = (
                        target.C名称 if not isinstance(target, list) else str(target)
                    )
                    code = f"for (auto& [{target_name}, _] : {iter_obj})"
            else:
                if isinstance(target, list):
                    # 列表遍历的元组解包
                    target_names = ", ".join([t.C名称 for t in target])
                    code = f"for (auto& [{target_names}] : {iter_obj})"
                else:
                    code = f"for (auto {target} : {iter_obj})"

        self.transpiler.添加代码(code)
        with self.transpiler.代码块上下文:
            for stmt in node.body:
                self.transpiler.visit(stmt)

    def visit_Break(self, node: ast.Break):
        self.transpiler.添加代码("break;")

    def visit_Continue(self, node: ast.Continue):
        self.transpiler.添加代码("continue;")

    def visit_While(self, node: ast.While):
        test = self.transpiler.获取值(node.test)
        self.transpiler.添加代码(f"while ({test})")
        with self.transpiler.代码块上下文:
            for stmt in node.body:
                self.transpiler.visit(stmt)

    def visit_Try(self, node: ast.Try):
        self.transpiler.添加代码("try")
        with self.transpiler.代码块上下文:
            for stmt in node.body:
                self.transpiler.visit(stmt)

        for handler in node.handlers:
            if handler.type:
                # Catch specific exception
                exc_type = self.transpiler.获取值(handler.type)
                # Map Python exceptions to C++ exceptions if needed
                # For now, we assume standard std::exception or custom C++ classes

                # Check for 'Exception' which is the base class
                if exc_type == Exception or (
                    isinstance(exc_type, str) and exc_type == "Exception"
                ):
                    c_exc_type = "const std::exception&"
                else:
                    # Attempt to resolve type
                    c_exc_type = (
                        self.解析类型(exc_type)
                        if not isinstance(exc_type, str)
                        else exc_type
                    )
                    if not c_exc_type.endswith("&") and not c_exc_type.endswith("*"):
                        c_exc_type = f"const {c_exc_type}&"

                if handler.name:
                    # e.g., except Exception as e:
                    self.transpiler.添加代码(f"catch ({c_exc_type} {handler.name})")
                    # Register the exception variable in the scope
                    # Note: We are entering a scope manually
                else:
                    self.transpiler.添加代码(f"catch ({c_exc_type})")
            else:
                # Catch all: except:
                self.transpiler.添加代码("catch (...)")

            with self.transpiler.代码块上下文:
                if handler.name:
                    # If we have a named exception, we need to register it
                    # The C++ variable is already declared in the catch clause
                    self.transpiler.添加C变量(C变量(c_exc_type, handler.name, False))

                for stmt in handler.body:
                    self.transpiler.visit(stmt)

        if node.finalbody:
            # C++ doesn't have 'finally', but we can simulate it with RAII or just executing code after try-catch
            self.transpiler.添加代码(
                "// Note: finally block executed here. Warning: does not handle returns inside try/catch correcty without RAII."
            )
            for stmt in node.finalbody:
                self.transpiler.visit(stmt)

    def visit_Raise(self, node: ast.Raise):
        if node.exc:
            msg = ""
            if isinstance(node.exc, ast.Call):
                # raise Exception("msg")
                func_name = self.transpiler.获取值(node.exc.func)
                if func_name == Exception or (
                    isinstance(func_name, str) and func_name == "Exception"
                ):
                    if node.exc.args:
                        msg_val = self.transpiler.获取值(node.exc.args[0])
                        self.transpiler.添加代码(
                            f"throw std::runtime_error({msg_val});"
                        )
                        self.transpiler.包含头文件.add("<stdexcept>")
                        return
            elif isinstance(node.exc, ast.Name):
                # raise e
                val = self.transpiler.获取值(node.exc)
                self.transpiler.添加代码(f"throw {val};")
                return

            # Fallback
            val = self.transpiler.获取值(node.exc)
            self.transpiler.添加代码(f"throw {val};")
        else:
            # re-raise
            self.transpiler.添加代码("throw;")

    def visit_Assign(self, node: ast.Assign):
        from .代码生成 import 代码生成器

        generator = 代码生成器(self.transpiler)
        value = self.transpiler.获取值(node.value)
        for target in node.targets:
            generator._assign(target, value, node)

    def visit_AugAssign(self, node: ast.AugAssign):
        from .代码生成 import 代码生成器

        generator = 代码生成器(self.transpiler)
        value = self.计算二元运算(node)
        generator._assign(node.target, value, node)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        from .代码生成 import 代码生成器
        generator = 代码生成器(self.transpiler)

        target_py_type = self.transpiler.获取值(
            node.annotation, is_type_annotation=True
        )
        c_type = self.解析类型(target_py_type)
        c_type_str = str(c_type)

        # 特殊处理：Set 和 Map 类型
        # 对于这些类型，我们需要使用类型注解来创建正确的变量包装器
        if c_type_str.startswith("std::unordered_set"):
            # 处理 s: Set[T] = set() 或 s: Set[T] = {1, 2, 3}
            if not isinstance(node.target, ast.Name):
                self.抛出错误("Assignment target must be a name", node)

            # 获取元素类型
            origin = getattr(target_py_type, "__origin__", None)
            args = getattr(target_py_type, "__args__", [])
            if origin is set and args:
                elem_type_str = str(self.解析类型(args[0]))
            else:
                elem_type_str = "int64_t"  # fallback

            # 处理值
            if isinstance(node.value, ast.Call):
                func = self.transpiler.获取值(node.value.func)
                if func is set:
                    # s: Set[T] = set() -> 空集合
                    value = "{}"
                else:
                    value = self.transpiler.获取值(node.value)
            else:
                value = self.transpiler.获取值(node.value)

            # 创建集合初始化列表（如果值还不是）
            if isinstance(value, str):
                init_list = 集合初始化列表(value, elem_type_str)
            else:
                init_list = value

            target_var = 标准集合(init_list, node.target.id, False) # type: ignore
            self.transpiler.包含头文件.add("<unordered_set>")
            self.transpiler.添加代码(target_var.初始化代码(value, None))
            self.transpiler.添加C变量(target_var)
            return

        elif c_type_str.startswith("std::unordered_map"):
            # 处理 m: Dict[K, V] = {} 或 m: Dict[K, V] = {k: v, ...}
            if not isinstance(node.target, ast.Name):
                self.抛出错误("Assignment target must be a name", node)

            # 获取键值类型
            origin = getattr(target_py_type, "__origin__", None)
            args = getattr(target_py_type, "__args__", [])
            if origin is dict and len(args) == 2:
                key_type_str = str(self.解析类型(args[0]))
                val_type_str = str(self.解析类型(args[1]))
            else:
                key_type_str = "int64_t"  # fallback
                val_type_str = "int64_t"

            value = self.transpiler.获取值(node.value)

            # 创建字典初始化列表（如果值还不是）
            if isinstance(value, str):
                init_list = 字典初始化列表(value, key_type_str, val_type_str)
            elif isinstance(value, 字典初始化列表):
                # 如果已经是字典初始化列表但类型是 auto，需要用正确的类型重新创建
                if value.键类型名 == "auto" or value.值类型名 == "auto":
                    init_list = 字典初始化列表(value.代码, key_type_str, val_type_str)
                else:
                    init_list = value
            else:
                init_list = value

            target_var = 标准无序映射(init_list, node.target.id, False) # type: ignore
            self.transpiler.包含头文件.add("<unordered_map>")
            # 如果键或值类型包含string，添加string头文件
            if "std::string" in str(target_var.类型名):
                self.transpiler.包含头文件.add("<string>")
            self.transpiler.添加代码(
                target_var.初始化代码(
                    (
                        init_list.代码
                        if isinstance(init_list, 字典初始化列表)
                        else init_list
                    ),
                    None,
                )
            )
            self.transpiler.添加C变量(target_var)
            return

        # 特殊处理：List[T] 类型（std::vector）
        if c_type_str.startswith("std::vector"):
            if not isinstance(node.target, ast.Name):
                self.抛出错误("Assignment target must be a name", node)

            # 获取元素类型
            origin = getattr(target_py_type, "__origin__", None)
            args = getattr(target_py_type, "__args__", [])
            if origin is list and args:
                elem_type_str = str(self.解析类型(args[0]))
            else:
                # 从 c_type_str 中提取类型，例如 "std::vector<int>" -> "int"
                if c_type_str.startswith("std::vector<") and c_type_str.endswith(">"):
                    elem_type_str = c_type_str[12:-1]  # 去掉 "std::vector<" 和 ">"
                else:
                    elem_type_str = "int64_t"  # fallback

            # 处理值
            value = self.transpiler.获取值(node.value)

            # 如果是空列表或类型是 auto，需要使用正确的元素类型
            from .cpp类型 import 列表初始化列表
            if isinstance(value, 列表初始化列表):
                if value.类型名 == "auto" or not value.代码.strip():
                    # 创建带有正确类型的空列表初始化
                    value = 列表初始化列表("{}", elem_type_str, 0)

            # 创建列表变量
            from .std_vector import 标准列表
            target_var = 标准列表(value, node.target.id, False)  # type: ignore
            self.transpiler.包含头文件.add("<vector>")
            self.transpiler.添加代码(
                target_var.初始化代码(
                    value.代码 if isinstance(value, 列表初始化列表) else value,
                    None,
                )
            )
            self.transpiler.添加C变量(target_var)
            return

        # 其他类型正常处理
        value = self.transpiler.获取值(node.value)
        generator._assign(node.target, value, node, c_type_str)

    def visit_Expr(self, node: ast.Expr):
        # 处理独立表达式，如函数调用语句
        if isinstance(node.value, ast.Call):
            from .表达式处理 import 表达式访问者

            expr_visitor = 表达式访问者(self.transpiler)
            code = expr_visitor.处理调用(node.value)
            self.transpiler.添加代码(f"{code};")

    def visit_arguments(self, node: ast.arguments) -> Any:
        from .代码生成 import 参数处理器

        processor = 参数处理器(self.transpiler)
        processor.处理参数列表(node)
