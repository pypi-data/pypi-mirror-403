import ast
import inspect
import traceback
from typing import Any, List, Callable
from .工具 import 全局上下文, 转C字符串
from .cpp类型 import (
    C变量, Cpp类型, C获取下标, C获取属性,
    C函数调用, C布尔,
)
from .容器构建器 import 容器构建器
from .异常 import 类型不一致错误
from .ast访问者 import *
from .基础混入 import 错误处理混入, 类型处理混入, 参数处理混入

class 表达式访问者(错误处理混入, 类型处理混入, 参数处理混入):
    """处理表达式求值的访问者"""

    def __init__(self, transpiler):
        self.transpiler = transpiler

    def 获取值(self, value, is_type_annotation=False):
        """
        将 AST 节点转换为对应的值或 C++ 表达式字符串。
        处理常量、变量名、属性访问、函数调用、运算表达式等。
        """
        if isinstance(value, ast.Constant):
            if isinstance(value.value, bool):
                return C布尔(value.value)
            if isinstance(value.value, str):
                # 如果是类型注解上下文，返回原始字符串而不是C字符串
                if is_type_annotation:
                    return value.value
                return CString常量(value.value)
            if isinstance(value.value, bytes):
                return CBytes常量(value.value)
            if isinstance(value.value, int):
                return CInt常量(value.value)
            if isinstance(value.value, float):
                return CFloat常量(value.value)            
            return value.value

        if isinstance(value, ast.Name):
            # 1. 查找 Python 内置对象
            v = 全局上下文.Python内置映射.get(value.id)
            if v is not None:
                return v
            # 2. 查找本地 Python 变量 (直接执行时使用)
            v = self.transpiler.本地变量.get(value.id)
            if v is not None:
                return v
            # 3. 查找 C 变量
            v = self.transpiler.获取C变量(value.id)
            if v is not None:
                return v
            # 4. 查找参数变量
            v = self.transpiler.参数变量.get(value.id)
            if v is not None:
                return v
            # 5. 查找全局变量
            v = self.transpiler.全局变量.get(value.id)
            if v is not None:
                return v

            # 如果所有地方都找不到该变量，抛出错误
            self.抛出错误(f"未定义的变量 '{value.id}'", value)

        if isinstance(value, ast.Attribute):
            obj = self.获取值(value.value)

            # Prioritize explicitly defined methods on CVariable wrappers (e.g. standard_set.add)
            if isinstance(obj, C变量) and hasattr(obj, value.attr):
                attr = getattr(obj, value.attr)
                if inspect.ismethod(attr):
                    return attr

            # 检查是否是类属性访问（静态成员或静态方法）
            if isinstance(value.value, ast.Name) and inspect.isclass(obj):
                class_name = value.value.id
                attr_name = value.attr
                attr_obj = getattr(obj, attr_name, None)

                # 检查这个类是否有这个静态成员
                if self.transpiler.是否为类 and class_name == self.transpiler.函数名 and attr_name in self.transpiler.类静态成员:
                    # 返回静态成员访问：ClassName::static_member
                    return f"{class_name}::{attr_name}"
                elif hasattr(obj, attr_name):
                    if inspect.isfunction(attr_obj) or inspect.ismethod(attr_obj):
                        # 静态方法，返回C静态调用对象
                        return C静态调用(class_name, attr_name)
                    else:
                        # 其他静态成员
                        return f"{class_name}::{attr_name}"

            if isinstance(obj, (C变量, Cpp类型)):
                return C获取属性(obj, value.attr)
            if obj is None:
                self.抛出错误(f'Name not found: {value.value}', value)
            return getattr(obj, value.attr)

        if isinstance(value, ast.UnaryOp):
            operand = self.获取值(value.operand)
            if isinstance(value.op, ast.UAdd):
                return f'(+{operand})'
            if isinstance(value.op, ast.USub):
                return f'(-{operand})'
            if isinstance(value.op, ast.Not):
                return f'(!{operand})'
            if isinstance(value.op, ast.Invert):
                return f'(~{operand})'

        if isinstance(value, ast.BoolOp):
            values = [f'({self.获取值(v)})' for v in value.values]
            if isinstance(value.op, ast.And):
                return '&&'.join(values)
            if isinstance(value.op, ast.Or):
                return '||'.join(values)

        if isinstance(value, ast.IfExp):
            test = self.获取值(value.test)
            body = self.获取值(value.body)
            orelse = self.获取值(value.orelse)
            return f'(({test}) ? ({body}) : ({orelse}))'

        if isinstance(value, ast.Compare):
            from .ast访问者 import AST访问者基类
            visitor = AST访问者基类(self.transpiler)
            return visitor.计算比较(value)

        if isinstance(value, ast.BinOp):
            from .ast访问者 import AST访问者基类
            visitor = AST访问者基类(self.transpiler)
            return visitor.计算二元运算(value)

        # 处理 List 字面量
        if isinstance(value, ast.List):
            l = [self.获取值(e) for e in value.elts]
            try:
                return 容器构建器._从列表构建初始化列表(l)
            except 类型不一致错误 as e:
                self.抛出错误(str(e), value)

        # 处理 Tuple 字面量
        if isinstance(value, ast.Tuple):
            l = [self.获取值(e) for e in value.elts]
            if not self.transpiler.正在构建参数:
                # Try to make a vector (homogenous)
                try:
                    return 容器构建器._从列表构建初始化列表(l)
                except 类型不一致错误:
                    pass

                # Fallback to std::pair or std::tuple
                self.transpiler.包含头文件.add('<tuple>')
                self.transpiler.包含头文件.add('<utility>')
                elements = [str(x) for x in l]
                if len(elements) == 2:
                    return f'std::make_pair({elements[0]}, {elements[1]})'
                return f'std::make_tuple({", ".join(elements)})'

            self.transpiler.包含头文件.add('<tuple>')
            self.transpiler.包含头文件.add('<utility>')
            elements = [str(x) for x in l]
            if len(elements) == 2:
                return f'std::make_pair({elements[0]}, {elements[1]})'
            return f'std::make_tuple({", ".join(elements)})'

        # 处理 Dict 字面量
        if isinstance(value, ast.Dict):
            d = {self.获取值(k): self.获取值(v)
                 for k, v in zip(value.keys, value.values)}
            try:
                return 容器构建器._从字典构建初始化列表(d)
            except 类型不一致错误 as e:
                self.抛出错误(str(e), value)

        if isinstance(value, ast.ListComp):
            return self.visit_ListComp_Expr(value)

        # 处理 Set 字面量
        if isinstance(value, ast.Set):
            l = [self.获取值(e) for e in value.elts]
            try:
                return 容器构建器._从集合构建初始化列表(set(l))
            except 类型不一致错误 as e:
                self.抛出错误(str(e), value)

        if isinstance(value, ast.Call):
            return self.处理调用(value)

        if isinstance(value, ast.Subscript):
            return self.获取下标(value)

        return None

    def 获取下标(self, node: ast.Subscript):
        """处理下标访问 obj[index]"""
        obj = self.获取值(node.value)
        slice_node = node.slice

        if isinstance(slice_node, ast.Slice):
            self.抛出错误("Slicing not supported for C++ vectors yet", node)

        # 特殊处理：Dict[K, V] 类型注解
        # 当 slice 是 Tuple 且 obj 是 Dict 时，直接处理元组元素
        from typing import Dict, List, Set, Union
        if obj is Dict and isinstance(slice_node, ast.Tuple):
            if len(slice_node.elts) == 2:
                key_type = self.获取值(slice_node.elts[0])
                val_type = self.获取值(slice_node.elts[1])
                return Dict[key_type, val_type]
            else:
                self.抛出错误("Dict type annotation requires exactly 2 type parameters", node)

        index = self.获取值(slice_node)

        # 处理类型提示中的下标, 如 Union[int, float]
        if obj is Union:
            return Union[index]
        if obj is List:
            return List[index]
        if obj is Set:
            return Set[index]
        if obj is Dict:
            # Dict类型注解应该总是有两个参数：Dict[K, V]
            # 如果只有一个参数，这是一个不完整的类型提示
            if isinstance(index, tuple) and len(index) == 2:
                return Dict[index[0], index[1]]
            # 如果只有一个参数，这可能是错误的类型提示
            return Dict[index, Any]  # type: ignore[arg-type]

        # C++ 数组/Vector 下标访问
        return C获取下标(obj, index)

    def 处理调用(self, node: ast.Call):
        func = self.获取值(node.func)

        # 0. 处理 super() 调用
        if isinstance(node.func, ast.Name) and node.func.id == 'super':
            from .ast访问者 import AST访问者基类
            visitor = AST访问者基类(self.transpiler)
            return visitor.处理super调用(node)

        # 1. 类型实例化 (例如 CppVectorInt())
        if inspect.isclass(func):
            c_type_map = 全局上下文.类型映射表.get(func)
            if c_type_map:
                self.transpiler.包含头文件.update(c_type_map.包含目录)
                self.transpiler.链接库.update(c_type_map.库)
                self.transpiler.库搜索目录.update(c_type_map.库目录)
                args_str = self.构建参数字符串(node.args)
                # 构造函数调用
                return C函数调用(c_type_map.目标类型, args_str, c_type_map.目标类型)

        # 2. 直接调用 (例如 range(), print()) - 缓存在 GlobalContext 中
        if func in 全局上下文.直接调用函数集:
            args = [self.获取值(arg) for arg in node.args]
            self.transpiler.正在直接调用 = True
            try:
                return func(*args)
            except Exception as e:
                # 保留原始异常信息和堆栈跟踪
                error_msg = f"Error during direct call to {func.__name__}: {str(e)}"
                if traceback.format_exc():
                    error_msg += f"\nOriginal traceback:\n{traceback.format_exc()}"
                self.抛出错误(error_msg, node)

        # 2b. Special builtin handling: print
        if func == print:
            self.transpiler.包含头文件.add('<iostream>')
            arg_vals = [self.获取值(arg) for arg in node.args]

            # Create a C++ expression using a lambda to print and return 0
            print_stmts = []
            for val in arg_vals:
                print_stmts.append(f'std::cout << {val} << " ";')
            print_stmts.append('std::cout << std::endl;')

            joined_stmts = " ".join(print_stmts)
            code = f'([&](){{ {joined_stmts} return 0; }}())'
            return code

        # 2c. Special builtin handling: len
        if func == len:
            if len(node.args) != 1:
                self.抛出错误("len() takes exactly one argument", node)
            arg_val = self.获取值(node.args[0])
            return f'({arg_val}.size())'

        # 3. 映射的 C++ 函数
        mapped_func = 全局上下文.函数映射表.get(func)
        if mapped_func:
            args = [self.获取值(arg) for arg in node.args]
            self.transpiler.包含头文件.update(mapped_func.包含目录)
            self.transpiler.链接库.update(mapped_func.库)
            self.transpiler.库搜索目录.update(mapped_func.库目录)

            # 如果目标是可调用的 (如宏函数生成器)，则直接调用生成代码
            if callable(mapped_func.目标函数):
                return mapped_func.目标函数(*args)
            return C函数调用(mapped_func.目标函数, self.构建参数字符串(node.args))

        if not callable(func) and not isinstance(func, C获取属性) and not isinstance(func, C静态调用):
            self.抛出错误(
                f"Cannot call object '{ast.dump(node.func)}'", node)

        # Handle bound methods of CVariables (e.g. s.add(x))
        if hasattr(func, '__self__') and isinstance(func.__self__, C变量):  # type: ignore
            args = [self.获取值(arg) for arg in node.args]
            return func(*args)  # type: ignore

        if node.keywords:
            self.抛出错误("Keyword arguments not supported in C++ translation", node)

        args_str = self.构建参数字符串(node.args)

        # 4. 调用其他 JIT 编译的函数
        if isinstance(func, type(self.transpiler)):
            self.transpiler.依赖函数.append(func)

            # 确保依赖函数已被分析（用于获取列表参数映射等信息）
            # 使用 tell() 检查缓冲区是否有内容
            if func.代码缓冲区.tell() == 0 and not func.是否为类:
                func.分析()

            # 检查是否有列表参数需要特殊处理
            args_list = []
            for i, arg_node in enumerate(node.args):
                arg_val = self.获取值(arg_node)

                # 检查这个参数在目标函数中是否是列表参数
                param_name = None
                if i < len(func.参数名称):
                    param_name = func.参数名称[i]

                if param_name and param_name in func.列表参数映射:
                    # 如果是列表参数，需要转换为指针和长度
                    args_list.append(f"{arg_val}.data()")
                    args_list.append(f"static_cast<int64_t>({arg_val}.size())")
                else:
                    args_list.append(str(arg_val))

            return C函数调用(func.C函数名, ", ".join(args_list))
        # 5. C++ 对象方法调用
        elif isinstance(func, C获取属性):
            return C函数调用(func, args_str)
        # 7. 静态方法调用
        elif isinstance(func, C静态调用):
            # 查找对应的类并添加为依赖
            class_obj = self.transpiler.全局变量.get(func.class_name)
            if class_obj and inspect.isclass(class_obj):
                dep_name = func.class_name
                if dep_name not in 全局上下文.编译栈:
                    全局上下文.编译栈.add(dep_name)
                    try:
                        dep_compiler = type(self.transpiler)(
                            class_obj, self.transpiler.编译器)
                        dep_compiler.编译()
                        self.transpiler.依赖函数.append(dep_compiler)
                    finally:
                        全局上下文.编译栈.discard(dep_name)
            return C函数调用(func, args_str)
        # 6. super() method calls
        elif isinstance(func, SuperMethodCall):
            # SuperMethodCall returns a C++ code string when called
            return func(*[self.获取值(arg) for arg in node.args])
        else:
            # 7. 如果依赖是普通 Python 函数，尝试递归编译
            try:
                # 对于类构造函数调用，检查是否是当前正在编译的类
                if inspect.isclass(func):
                    class_name = func.__name__
                    # 使用全局编译栈来避免递归
                    if class_name in 全局上下文.编译栈:
                        # 如果已经在编译中，直接生成构造函数调用
                        return C函数调用(class_name, args_str, class_name)

                # 检查是否已经在编译这个函数/类（避免循环依赖）
                if hasattr(func, '__name__'):
                    dep_name = func.__name__
                elif hasattr(func, '__class__'):
                    dep_name = func.__class__.__name__
                else:
                    dep_name = str(func)

                # 检查是否在全局编译栈中
                if dep_name in 全局上下文.编译栈:
                    # 如果已经在编译中，直接使用名称而不重新编译
                    return C函数调用(dep_name, args_str)

                全局上下文.编译栈.add(dep_name)
                try:
                    dep_compiler = type(self.transpiler)(
                        func, self.transpiler.编译器)
                    dep_compiler.编译()
                    self.transpiler.依赖函数.append(dep_compiler)
                    return C函数调用(dep_compiler.C函数名, args_str)
                finally:
                    全局上下文.编译栈.discard(dep_name)
            except Exception as e:
                # 保留原始异常信息和堆栈跟踪
                error_msg = f"Failed to compile dependency {func.__name__}: {str(e)}"
                if traceback.format_exc():
                    error_msg += f"\nOriginal traceback:\n{traceback.format_exc()}"
                self.抛出错误(error_msg, node)


    def visit_ListComp_Expr(self, node: ast.ListComp):
        if len(node.generators) != 1:
            self.抛出错误(
                "Nested List comprehensions not supported yet", node)

        gen = node.generators[0]
        if not isinstance(gen.target, ast.Name):
            self.抛出错误(
                "List comprehension target must be a simple name", node)

        # 我们已经验证了gen.target是ast.Name类型，所以可以安全访问.id属性
        target_name = gen.target.id  # type: ignore[attr-defined]
        iter_val = self.获取值(gen.iter)

        # Enter scope to register loop variable for resolution (resolved as C++ lambda arg)
        self.transpiler.进入作用域()
        dummy_tgt = C变量('auto', target_name, False)
        dummy_tgt.C名称 = target_name  # Ensure C name matches lambda arg
        self.transpiler.添加C变量(dummy_tgt)

        elt_val = self.获取值(node.elt)

        # Filter
        filter_expr = 'true'
        if gen.ifs:
            conditions = [f'({self.获取值(cond)})' for cond in gen.ifs]
            filter_expr = ' && '.join(conditions)

        self.transpiler.退出作用域()

        # We need type traits headers
        self.transpiler.包含头文件.add('<type_traits>')
        self.transpiler.包含头文件.add('<vector>')

        code = f"""
        ([&](){{
            auto&& _iter = {iter_val};
            using _IterType = std::decay_t<decltype(_iter)>;
            using _InType = typename _IterType::value_type;

            auto _mapper = [&](_InType {target_name}) {{ return {elt_val}; }};
            auto _filter = [&](_InType {target_name}) {{ return {filter_expr}; }};

            using _OutType = std::invoke_result_t<decltype(_mapper), _InType>;
            std::vector<_OutType> _result;

            for (auto&& _item : _iter) {{
                if (_filter(_item)) {{
                    _result.push_back(_mapper(_item));
                 }}
            }}
            return _result;
        }}())
        """
        # Collapse whitespace for cleaner output?
        return code.replace('\n', ' ').strip()