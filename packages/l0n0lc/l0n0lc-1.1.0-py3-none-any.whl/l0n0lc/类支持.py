import ast
import inspect
import sys
import traceback
from .工具 import 全局上下文, 模板
from .cpp类型 import C变量
from .异常 import Jit错误
from .代码生成 import 代码生成器, 参数处理器
from .基础混入 import 错误处理混入, 类型处理混入
from .类方法信息 import 类方法信息

# 检测运算符重载
运算符函数映射 = {
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

class 类支持处理器(错误处理混入, 类型处理混入):
    """处理类定义相关的功能"""

    def __init__(self, transpiler):
        from .Py转Cpp转译器 import Py转Cpp转译器
        self.transpiler: Py转Cpp转译器 = transpiler

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
        for base in node.bases:
            base_class = self.transpiler.获取值(base)
            if not base_class or not inspect.isclass(base_class):
                continue
            self.transpiler.类基类列表.append(base_class)
            base_transpiler = type(self.transpiler)(
                base_class, self.transpiler.编译器
            )
            self.transpiler.添加依赖(base_transpiler)

    def 扫描成员变量(self, node: ast.ClassDef):
        """扫描类的成员变量"""
        for stmt in node.body:
            if isinstance(stmt, ast.AnnAssign):
                self.处理注解赋值(stmt)
            elif isinstance(stmt, ast.Assign):
                self.抛出错误('类定义必须表明类型', stmt)            

    def 处理注解赋值(self, stmt: ast.AnnAssign):
        if not isinstance(stmt.target, ast.Name):
            return
        py类型 =  self.transpiler.获取值(stmt.annotation, True)
        c类型 = self.解析类型(py类型)
        # 类型注解：我们已经检查过stmt.target是ast.Name类型
        成员名字 = stmt.target.id
        默认值 = None
        if stmt.value is not None:
            默认值 = self.transpiler.获取值(stmt.value)
        # 检查是否是以'_'开头的静态成员
        if 成员名字.startswith("_"):
            # 这是静态成员
    
            self.transpiler.类静态成员[成员名字] = (c类型, 默认值)
        else:
            # 这是普通实例成员
            self.transpiler.类成员变量[成员名字] = c类型
            # 检查是否有默认值
            if 默认值 is not None:
                self.transpiler.类成员默认值[成员名字] = 默认值

    def 处理类方法(self, node: ast.ClassDef):
        """处理类方法"""
        for stmt in node.body:
            if isinstance(stmt, ast.FunctionDef):
                self.处理单个方法(stmt)

    def 处理单个方法(self, node: ast.FunctionDef):
        """处理单个类方法"""
        # 设置当前方法名
        self.transpiler.当前方法名 = node.name # type: ignore
        # 重置当前方法参数，避免方法间干扰
        self.transpiler.当前方法参数 = {}
        # 处理方法
        self.访问方法节点(node)

    def 访问方法节点(self, node: ast.FunctionDef):
        """访问方法节点（类似于原visit_FunctionDef但针对类方法）"""
        是构造函数 = node.name == "__init__"
        是模板函数 = False
        是静态的 = False
        是一个属性 = False
        # 检测装饰器
        for decorator in node.decorator_list:
            装饰器 = self.transpiler.获取值(decorator)
            if 装饰器 is classmethod:
                self.抛出错误("不支持`@classmethod`", decorator)
            elif 装饰器 is 模板:
                是模板函数 = True
            elif 装饰器 is staticmethod:
                是静态的 = True
            elif 装饰器 is property:
                是一个属性 = True

        是运算符 = node.name in 运算符函数映射
        函数名 = 运算符函数映射.get(node.name, node.name)
        # 构造函数名为类名
        if 是构造函数:
            函数名 = self.transpiler.函数名
        c返回类型 = ""
  
        # 保存原始的参数变量字典（用于恢复）
        原始参数变量 = self.transpiler.参数变量
        self.transpiler.参数变量 = {}  # 临时清空，让 visit_arguments 填充到这里

        # 参数处理
        参数节点 = node.args
        原始参数 = list(参数节点.args)

        # 检查第一个参数 (self/cls)
        第一个参数名 = None
        第一个参数类型 = None
        if not 是静态的 and 原始参数:
            第一个参数 = 原始参数[0]
            第一个参数名 = 第一个参数.arg
            # 实例方法：第一个参数是 self
            第一个参数类型 = f"{self.transpiler.函数名}*"
            # 从参数列表中移除 self，使其不出现在 C++ 参数签名中
            参数节点.args = 原始参数[1:]

        # 为方法体创建新的作用域
        # 临时替换全局缓冲区为方法缓冲区
        # 创建临时代码缓冲区用于方法体（使用 StringIO 优化性能）
        import io
        方法缓冲区 = io.StringIO()
        原始缓冲区 = self.transpiler.代码缓冲区
        self.transpiler.代码缓冲区 = 方法缓冲区

        with self.transpiler.代码块上下文:
            # 注册 self 变量 (作为 this 指针)
            if 第一个参数名 and not 是静态的 and 第一个参数类型:
                self变量 = C变量(第一个参数类型, 第一个参数名, False)
                self变量.C名称 = "this"  # 实例方法映射到 C++ this
                self.transpiler.添加C变量(self变量)

            # 处理方法参数
            参数处理器(self.transpiler).处理参数列表(参数节点)
            # 将参数从 self.参数变量 复制到 self.当前方法参数
            self.transpiler.当前方法参数 = dict(self.transpiler.参数变量)

            for stmt in node.body:
                self.transpiler.visit(stmt)

        # 获取生成的代码块（从临时缓冲区）
        生成的代码 = 方法缓冲区.getvalue().strip().split(
            '\n') if 方法缓冲区.getvalue().strip() else []

        # 恢复原始缓冲区和参数变量
        self.transpiler.代码缓冲区 = 原始缓冲区
        self.transpiler.参数变量 = 原始参数变量

        # 确定返回类型
        c返回类型 = self.推断返回类型(node, 是构造函数)

        # 存储方法信息
        self.transpiler.类方法列表.append(
            类方法信息(
                名称=函数名,
                返回类型=c返回类型,
                方法体=生成的代码,
                是构造函数=是构造函数,
                是静态方法=是静态的,
                是属性=是一个属性,
                是运算符=是运算符,
                参数列表=self._构建当前参数列表字符串(),
            )
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

        return self.transpiler.代码生成器.构建当前参数列表字符串()
