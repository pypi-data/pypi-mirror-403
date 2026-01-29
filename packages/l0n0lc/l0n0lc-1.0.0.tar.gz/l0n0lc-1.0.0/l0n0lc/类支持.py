import ast
import inspect
import sys
import traceback
from .工具 import 全局上下文
from .cpp类型 import C变量
from .异常 import Jit错误
from .代码生成 import 代码生成器, 参数处理器
from .基础混入 import 错误处理混入, 类型处理混入


class 类支持处理器(错误处理混入, 类型处理混入):
    """处理类定义相关的功能"""

    def __init__(self, transpiler):
        self.transpiler = transpiler

    def 处理类定义(self, node: ast.ClassDef):
        """处理类定义"""
        if node.name != self.transpiler.函数名:
            self.抛出错误(f"Nested classes not supported: {node.name}", node)

        # 0. 处理基类（继承）
        self.处理基类(node)

        # 1. 扫描成员变量（支持默认值）
        self.扫描成员变量(node)

        # 2. 访问方法
        self.处理类方法(node)

    def 处理基类(self, node: ast.ClassDef):
        """处理基类继承"""
        if node.bases:
            for base in node.bases:
                if isinstance(base, ast.Name):
                    base_class = self.transpiler.获取值(base)
                    if base_class and inspect.isclass(base_class):
                        self.transpiler.类基类列表.append(base_class)
                        # 将基类添加到依赖中
                        try:
                            base_transpiler = type(self.transpiler)(
                                base_class, self.transpiler.编译器
                            )
                            base_transpiler.编译()  # 需要编译基类以生成头文件和实现
                            self.transpiler.依赖函数.append(base_transpiler)
                        except Exception as e:
                            # 如果基类无法编译，记录警告但不阻止编译
                            print(
                                f"Warning: Failed to compile base class '{base_class.__name__}': {str(e)}",
                                file=sys.stderr,
                            )
                            if traceback.format_exc():
                                print(
                                    f"Base class compilation traceback:\n{traceback.format_exc()}",
                                    file=sys.stderr,
                                )

    def 扫描成员变量(self, node: ast.ClassDef):
        """扫描类的成员变量"""
        for stmt in node.body:
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                self.处理注解赋值(stmt)

            # 检测类变量（以'_'开头的变量，视为静态成员）
            elif isinstance(stmt, ast.Assign):
                self.处理赋值语句(stmt)

    def 处理注解赋值(self, stmt: ast.AnnAssign):
        """处理带有类型注解的赋值语句"""
        from .表达式处理 import 表达式访问者

        expr_visitor = 表达式访问者(self.transpiler)

        py_type = expr_visitor.获取值(stmt.annotation)
        c_type = self.解析类型(py_type)
        # 类型注解：我们已经检查过stmt.target是ast.Name类型
        member_name = stmt.target.id  # type: ignore[attr-defined]

        # 检查是否是以'_'开头的静态成员
        if member_name.startswith("_"):
            # 这是静态成员
            static_type = str(c_type)
            static_value = 0  # 默认值，如果没有显式赋值的话
            if stmt.value is not None:
                static_value = expr_visitor.获取值(stmt.value)
            self.transpiler.类静态成员[member_name] = (static_type, static_value)
        else:
            # 这是普通实例成员
            self.transpiler.类成员变量[member_name] = str(c_type)

            # 检查是否有默认值
            if stmt.value is not None:
                default_val = expr_visitor.获取值(stmt.value)
                self.transpiler.类成员默认值[member_name] = default_val

    def 处理赋值语句(self, stmt: ast.Assign):
        """处理赋值语句（用于类变量）"""
        from .表达式处理 import 表达式访问者

        expr_visitor = 表达式访问者(self.transpiler)

        for target in stmt.targets:
            if isinstance(target, ast.Name):
                # 检查变量名是否以'_'开头
                static_name = target.id  # type: ignore[attr-defined]
                if static_name.startswith("_"):
                    # 这是一个静态成员
                    static_value = expr_visitor.获取值(stmt.value)
                    # 尝试推断类型
                    if isinstance(static_value, bool):
                        static_type = "bool"
                    elif isinstance(static_value, int):
                        static_type = "int64_t"
                    elif isinstance(static_value, float):
                        static_type = "double"
                    elif isinstance(static_value, str):
                        static_type = "const char*"
                    else:
                        static_type = "auto"
                    self.transpiler.类静态成员[static_name] = (
                        static_type,
                        static_value,
                    )

    def 处理类方法(self, node: ast.ClassDef):
        """处理类方法"""
        for stmt in node.body:
            if isinstance(stmt, ast.FunctionDef):
                self.处理单个方法(stmt)

    def 处理单个方法(self, node: ast.FunctionDef):
        """处理单个类方法"""
        # 设置当前方法名
        self.transpiler.当前方法名 = node.name
        # 重置当前方法参数，避免方法间干扰
        self.transpiler.当前方法参数 = {}
        # 同时清空列表参数映射
        self.transpiler.列表参数映射 = {}

        # 处理方法
        self.访问方法节点(node)

    def 访问方法节点(self, node: ast.FunctionDef):
        """访问方法节点（类似于原visit_FunctionDef但针对类方法）"""
        is_init = node.name == "__init__"

        # 检测装饰器
        decorators = []
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                decorators.append(decorator.id)
                if decorator.id == "classmethod":
                    self.抛出错误("@classmethod is not supported", decorator)

        is_static = "staticmethod" in decorators
        is_property = "property" in decorators

        # 检测运算符重载
        operator_map = {
            "__add__": "operator+",
            "__sub__": "operator-",
            "__mul__": "operator*",
            "__truediv__": "operator/",
            "__mod__": "operator%",
            "__eq__": "operator==",
            "__ne__": "operator!=",
            "__lt__": "operator<",
            "__le__": "operator<=",
            "__gt__": "operator>",
            "__ge__": "operator>=",
            "__getitem__": "operator[]",
        }

        is_operator = node.name in operator_map
        method_name = operator_map.get(node.name, node.name)

        # 构造函数名为类名
        if is_init:
            method_name = self.transpiler.函数名

        c_ret_type = ""

        # 创建临时代码缓冲区用于方法体（使用 StringIO 优化性能）
        import io
        方法缓冲区 = io.StringIO()

        # 保存原始的参数变量字典（用于恢复）
        original_param_vars = self.transpiler.参数变量
        self.transpiler.参数变量 = {}  # 临时清空，让 visit_arguments 填充到这里

        # 参数处理
        args_node = node.args
        original_args = list(args_node.args)

        # 检查第一个参数 (self/cls)
        first_arg_name = None
        first_arg_type = None

        if not is_static and original_args:
            first_arg = original_args[0]
            first_arg_name = first_arg.arg

            # 实例方法：第一个参数是 self
            first_arg_type = f"{self.transpiler.函数名}*"

            # 从参数列表中移除 self，使其不出现在 C++ 参数签名中
            args_node.args = original_args[1:]

        # 为方法体创建新的作用域
        # 临时替换全局缓冲区为方法缓冲区
        原始缓冲区 = self.transpiler.代码缓冲区
        self.transpiler.代码缓冲区 = 方法缓冲区

        with self.transpiler.代码块上下文:
            # 注册 self 变量 (作为 this 指针)
            if first_arg_name and not is_static and first_arg_type:
                self_var = C变量(first_arg_type, first_arg_name, False)
                self_var.C名称 = "this"  # 实例方法映射到 C++ this
                self.transpiler.添加C变量(self_var)

            # 处理方法参数

            param_processor = 参数处理器(self.transpiler)
            param_processor.处理参数列表(args_node)

            # 将参数从 self.参数变量 复制到 self.当前方法参数
            self.transpiler.当前方法参数 = dict(self.transpiler.参数变量)

            for stmt in node.body:
                self.transpiler.visit(stmt)

        # 获取生成的代码块（从临时缓冲区）
        method_body = 方法缓冲区.getvalue().strip().split('\n') if 方法缓冲区.getvalue().strip() else []

        # 恢复原始缓冲区和参数变量
        self.transpiler.代码缓冲区 = 原始缓冲区
        self.transpiler.参数变量 = original_param_vars

        # 确定返回类型
        c_ret_type = self.推断返回类型(node, is_init)

        # 存储方法信息
        self.transpiler.类方法列表.append(
            {
                "name": method_name,
                "ret_type": c_ret_type,
                "body": method_body,
                "is_init": is_init,
                "is_static": is_static,
                "is_property": is_property,
                "is_operator": is_operator,
                "params": self._构建当前参数列表字符串(),
            }
        )

    def 推断返回类型(self, node: ast.FunctionDef, is_init: bool):
        """推断方法的返回类型"""
        if is_init:
            return ""  # 构造函数无返回类型部分

        from .表达式处理 import 表达式访问者

        expr_visitor = 表达式访问者(self.transpiler)

        ret_py_type = expr_visitor.获取值(node.returns, is_type_annotation=True)

        if isinstance(node.returns, ast.Name):
            # 处理名称类型注解（如 int, str, float 等）
            # 处理自定义类类型
            if inspect.isclass(ret_py_type):
                # 首先检查是否有类型映射
                mapped_type = 全局上下文.类型映射表.get(ret_py_type)
                if mapped_type:
                    # 使用映射的类型
                    c_ret_type = mapped_type.目标类型
                    # 添加需要包含的头文件
                    if mapped_type.包含目录:
                        self.transpiler.包含头文件.update(mapped_type.包含目录)
                elif ret_py_type.__module__ == "builtins":
                    c_ret_type = str(self.解析类型(ret_py_type))
                else:
                    # 用户自定义类
                    c_ret_type = ret_py_type.__name__
            else:
                c_ret_type = str(self.解析类型(ret_py_type))
        elif isinstance(node.returns, ast.Constant):
            # 处理字符串类型注解（如 'Vector2D'）
            if isinstance(ret_py_type, str) and ret_py_type not in [
                "int",
                "float",
                "str",
                "bool",
                "void",
            ]:
                # 尝试从全局变量中查找对应的类
                if ret_py_type in self.transpiler.全局变量:
                    potential_class = self.transpiler.全局变量[ret_py_type]
                    if inspect.isclass(potential_class):
                        ret_py_type = potential_class

            # 处理自定义类类型
            if inspect.isclass(ret_py_type):
                # 首先检查是否有类型映射
                mapped_type = 全局上下文.类型映射表.get(ret_py_type)
                if mapped_type:
                    # 使用映射的类型
                    c_ret_type = mapped_type.目标类型
                    # 添加需要包含的头文件
                    if mapped_type.包含目录:
                        self.transpiler.包含头文件.update(mapped_type.包含目录)
                elif ret_py_type.__module__ == "builtins":
                    c_ret_type = str(self.解析类型(ret_py_type))
                else:
                    # 用户自定义类
                    c_ret_type = ret_py_type.__name__
            else:
                c_ret_type = str(self.解析类型(ret_py_type))

        elif node.returns is None:
            # 没有类型注解，需要根据函数体推断返回类型
            # 检查函数体中是否有返回语句
            return_stmt = None
            for stmt in node.body:
                if isinstance(stmt, ast.Return):
                    return_stmt = stmt
                    break

            if return_stmt and return_stmt.value is not None:
                # 有返回语句但没有类型注解，尝试推断返回值类型
                if isinstance(return_stmt.value, ast.Call):
                    # 检查函数调用
                    call_node = return_stmt.value
                    if isinstance(call_node.func, ast.Name):
                        # 函数调用，如 Vector2D()
                        func_name = call_node.func.id
                        # 检查是否是当前类的构造函数调用
                        if func_name == self.transpiler.函数名:
                            # 构造函数调用返回当前类类型
                            c_ret_type = self.transpiler.函数名
                        else:
                            # 其他函数使用auto
                            c_ret_type = "auto"
                    else:
                        # 其他类型的调用使用auto
                        c_ret_type = "auto"
                elif isinstance(return_stmt.value, ast.Constant):
                    # 常量返回值
                    if isinstance(return_stmt.value.value, bool):
                        c_ret_type = "bool"
                    elif isinstance(return_stmt.value.value, int):
                        c_ret_type = "int64_t"
                    elif isinstance(return_stmt.value.value, float):
                        c_ret_type = "double"
                    else:
                        c_ret_type = "auto"
                else:
                    # 其他表达式使用auto
                    c_ret_type = "auto"
            else:
                # 没有返回语句或返回值为None，设为void
                c_ret_type = "void"
        else:
            c_ret_type = "auto"

        return c_ret_type

    def _构建当前参数列表字符串(self):
        """构建方法的参数列表字符串"""

        generator = 代码生成器(self.transpiler)
        return generator.构建当前参数列表字符串()
