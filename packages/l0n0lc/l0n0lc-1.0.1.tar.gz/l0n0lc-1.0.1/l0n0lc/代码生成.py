import ast
import inspect
from typing import Union
from .工具 import 全局上下文
from .cpp类型 import C变量, Cpp类型, 字典初始化列表, 列表初始化列表, 集合初始化列表
from .std_vector import 标准列表
from .std_map import 标准无序映射
from .std_set import 标准集合
from .类型转换 import 类型转换器
from .基础混入 import 错误处理混入, 类型处理混入
from .表达式处理 import 表达式访问者


class 代码生成器(错误处理混入, 类型处理混入):
    """负责生成C++代码的类"""

    def __init__(self, transpiler):
        self.transpiler = transpiler

    def _assign(
        self, target_node, value, context_node, cast_type: Union[str, None] = None
    ):
        """处理赋值操作"""
        try:
            target_var = self.transpiler.获取值(target_node)
        except Exception:
            # 如果获取值失败，说明这是一个复杂的表达式赋值目标
            # 这种情况下我们让代码继续，target_var为None会在后续处理中被捕获
            target_var = None
        except KeyboardInterrupt:
            raise

        # 处理 Python 变量的直接赋值 (仅在 正在直接调用 模式下)
        if self.transpiler.正在直接调用:
            if isinstance(target_node, ast.Name):
                self.transpiler.本地变量[target_node.id] = value
            else:
                self.抛出错误("Direct assignment only supports simple names", context_node)
            self.transpiler.正在直接调用 = False
            return

        if target_var is None:
            # 新变量声明
            if isinstance(target_node, ast.Name):
                if isinstance(value, 字典初始化列表):
                    target_var = 标准无序映射(value, target_node.id, False)
                    self.transpiler.包含头文件.add("<unordered_map>")
                    # 如果键或值类型包含string，添加string头文件
                    if "std::string" in str(target_var.类型名):
                        self.transpiler.包含头文件.add("<string>")
                elif isinstance(value, 列表初始化列表):
                    target_var = 标准列表(value, target_node.id, False)
                    self.transpiler.包含头文件.add("<vector>")
                    if value.类型名 == Cpp类型.任意:
                        self.transpiler.包含头文件.add("<any>")
                elif isinstance(value, 集合初始化列表):
                    target_var = 标准集合(value, target_node.id, False)
                    self.transpiler.包含头文件.add("<unordered_set>")
                else:
                    target_var = C变量("auto", target_node.id, False)

                self.transpiler.添加代码(target_var.初始化代码(value, cast_type),
                                  getattr(context_node, 'lineno', None))
                self.transpiler.添加C变量(target_var)
            else:
                self.抛出错误("Assignment target must be a name", context_node)
        else:
            # 现有变量赋值
            target_name = (
                target_var.C名称 if hasattr(target_var, "C名称") else str(target_var)
            )
            if cast_type:
                self.transpiler.添加代码(f"{target_name} = ({cast_type})({value});",
                                         getattr(context_node, 'lineno', None))
            else:
                self.transpiler.添加代码(f"{target_name} = {value};",
                                         getattr(context_node, 'lineno', None))

    def 生成函数定义(self):
        """生成 C 函数定义/声明，或 C++ 类定义"""
        if self.transpiler.是否为类:
            return self.生成类定义()
        else:
            return self.生成函数声明()

    def 生成函数声明(self):
        """生成函数声明"""
        params = []
        for name, var in self.transpiler.参数变量.items():
            if name in self.transpiler.列表参数映射:
                ptr_var, len_var = self.transpiler.列表参数映射[name]
                params.append(f"{ptr_var.类型名} {ptr_var.C名称}")
                params.append(f"{len_var.类型名} {len_var.C名称}")
            elif isinstance(var, C变量):
                params.append(f"{var.类型名} {var.C名称}")

        param_str = ", ".join(params)
        return f'extern "C" {self.transpiler.返回类型} {self.transpiler.C函数名} ({param_str})'

    def 生成类定义(self):
        """生成类定义 struct Name { ... };"""
        # 处理继承
        inheritance = ""
        if self.transpiler.类基类列表:
            base_names = []
            for base in self.transpiler.类基类列表:
                base_names.append(f"public {base.__name__}")
            inheritance = " : " + ", ".join(base_names)

        # 静态成员声明
        static_fields = []
        for name, (type_, value) in self.transpiler.类静态成员.items():
            static_fields.append(f"    static {type_} {name};")

        # 实例成员变量
        fields = []
        for name, type_ in self.transpiler.类成员变量.items():
            fields.append(f"    {type_} {name};")

        # 方法声明
        method_decls = []

        # 如果有默认值但没有显式构造函数，声明默认构造函数
        has_explicit_init = any(m["is_init"] for m in self.transpiler.类方法列表)
        if self.transpiler.类成员默认值 and not has_explicit_init:
            method_decls.append(f"    {self.transpiler.C函数名}();")

        for m in self.transpiler.类方法列表:
            # 构建方法修饰符
            modifiers = []
            if m.get("is_static", False):
                modifiers.append("static")

            modifier_str = " ".join(modifiers) + " " if modifiers else ""

            if m["is_init"]:
                # 构造函数
                method_decls.append(f"    {modifier_str}{m['name']}({m['params']});")
            else:
                # 普通方法或运算符
                method_decls.append(
                    f"    {modifier_str}{m['ret_type']} {m['name']}({m['params']});"
                )

        # 组合所有部分
        all_members = static_fields + fields
        if all_members and method_decls:
            all_members.append("")  # 空行分隔成员和方法
        all_members.extend(method_decls)

        struct_body = "\n".join(all_members)
        return f"struct {self.transpiler.C函数名}{inheritance} {{\n{struct_body}\n}};"

    def 生成包含代码(self):
        """生成包含头文件的代码"""
        return "\n".join([f"#include {d}" for d in sorted(self.transpiler.包含头文件)])

    def 生成头文件代码(self):
        """生成头文件完整代码"""
        return f"#pragma once\n{self.生成包含代码()}\n{self.生成函数定义()};"

    def 生成cpp代码(self):
        """生成cpp文件完整代码"""
        if self.transpiler.是否为类:
            return self.生成类实现代码()
        else:
            return self.生成函数实现代码()

    def 生成类实现代码(self):
        """生成类的实现代码"""
        parts = []

        # 1. 包含头文件
        parts.append(f'#include "{self.transpiler.获取头文件名()}"')

        # 2. 静态成员定义
        if self.transpiler.类静态成员:
            parts.append("")  # 空行
            for name, (type_, value) in self.transpiler.类静态成员.items():
                # 生成静态成员定义
                if isinstance(value, str):
                    parts.append(
                        f'{type_} {self.transpiler.C函数名}::{name} = "{value}";'
                    )
                elif isinstance(value, bool):
                    parts.append(
                        f'{type_} {self.transpiler.C函数名}::{name} = {"true" if value else "false"};'
                    )
                else:
                    parts.append(
                        f"{type_} {self.transpiler.C函数名}::{name} = {value};"
                    )

        # 3. 默认构造函数（如果有默认值且没有显式定义构造函数）
        has_explicit_init = any(m["is_init"] for m in self.transpiler.类方法列表)
        if self.transpiler.类成员默认值 and not has_explicit_init:
            # 生成默认构造函数
            parts.append("")
            initializers = []
            for name, default_val in self.transpiler.类成员默认值.items():
                if isinstance(default_val, str):
                    initializers.append(f'{name}("{default_val}")')
                else:
                    initializers.append(f"{name}({default_val})")

            if initializers:
                init_list = ", ".join(initializers)
                parts.append(
                    f"{self.transpiler.C函数名}::{self.transpiler.C函数名}() : {init_list} {{}}"
                )
            else:
                parts.append(
                    f"{self.transpiler.C函数名}::{self.transpiler.C函数名}() {{}}"
                )

        # 4. 方法实现
        impls = []
        for m in self.transpiler.类方法列表:
            # 静态方法需要 static 修饰符
            modifier = "static " if m.get("is_static", False) else ""

            full_name = f"{self.transpiler.C函数名}::{m['name']}"
            if m["is_init"]:
                # 构造函数实现
                head = f"{full_name}({m['params']})"

                # 构建初始化列表
                initializers = []

                # 如果有基类，首先添加基类构造函数调用
                if self.transpiler.类基类列表:
                    base_class = self.transpiler.类基类列表[0]
                    base_name = base_class.__name__
                    # 对于构造函数参数，我们需要传递第一个参数给基类构造函数
                    # 这里假设第一个参数是name，与基类构造函数匹配
                    if m["params"]:
                        # 提取第一个参数名（去掉类型声明，只保留参数名）
                        first_param_full = m["params"].split(",")[0].strip()
                        # 参数格式可能是 "std::string name" 或 "int x" 等，我们只需要参数名部分
                        if " " in first_param_full:
                            first_param = first_param_full.split()[-1]
                        else:
                            first_param = first_param_full
                        initializers.append(f"{base_name}({first_param})")
                    else:
                        # 如果没有参数，调用基类默认构造函数
                        initializers.append(f"{base_name}()")

                # 如果有默认值，添加成员变量初始化
                if self.transpiler.类成员默认值:
                    for name, default_val in self.transpiler.类成员默认值.items():
                        if isinstance(default_val, str):
                            initializers.append(f'{name}("{default_val}")')
                        else:
                            initializers.append(f"{name}({default_val})")

                if initializers:
                    init_list = ", ".join(initializers)
                    head = f"{full_name}({m['params']}) : {init_list}"
            else:
                # 普通方法或运算符
                head = f"{m['ret_type']} {full_name}({m['params']})"

            body_lines = [str(line) for line in m["body"]]
            body_str = "\n".join(body_lines)
            impls.append(f"{head}\n{body_str}")

        if impls:
            parts.append("")
            parts.extend(impls)

        return "\n".join(parts)

    def 生成函数实现代码(self):
        """生成函数的实现代码"""
        # 获取Python源码行，用于生成注释
        source_lines = self.transpiler.源代码.split('\n')

        # 直接从 StringIO 获取生成的代码
        body_code = self.transpiler.代码缓冲区.getvalue()

        # 生成完整的C++代码
        parts = []
        parts.append(f'#include "{self.transpiler.获取头文件名()}"')
        parts.append("")  # 空行
        parts.append("// === Python 源码 ===")
        for i, line in enumerate(source_lines, 1):
            parts.append(f"// 第{i:2d}行: {line}")
        parts.append("")
        parts.append("// === C++ 实现 ===")
        parts.append(self.生成函数声明())
        parts.append("{")
        if body_code.strip():
            # 将 body_code 按行分割并添加到 parts
            for line in body_code.strip().split('\n'):
                parts.append(line)
        parts.append("}")

        return "\n".join(parts)

    def 保存代码到文件(self):
        """保存代码到文件"""
        # 清理旧文件
        self.transpiler.文件管理器.清理旧文件(self.transpiler.文件前缀)

        # 保存头文件
        self.transpiler.文件管理器.写入文件(
            self.transpiler.获取头文件名(),
            self.生成头文件代码()
        )

        # 保存 cpp 文件
        self.transpiler.文件管理器.写入文件(
            self.transpiler.获取cpp文件名(),
            self.生成cpp代码()
        )

    def 构建当前参数列表字符串(self):
        """构建当前方法的参数列表字符串（用于类方法）"""
        params = []
        # 使用 当前方法参数 而非 参数变量，确保参数隔离
        param_dict = (
            self.transpiler.当前方法参数
            if self.transpiler.当前方法参数
            else self.transpiler.参数变量
        )

        for name, var in param_dict.items():
            if name in ["self", "cls"]:
                continue  # Skip self/cls if present

            if name in self.transpiler.列表参数映射:
                ptr_var, len_var = self.transpiler.列表参数映射[name]
                params.append(f"{ptr_var.类型名} {ptr_var.C名称}")
                params.append(f"{len_var.类型名} {len_var.C名称}")
            elif isinstance(var, C变量):
                params.append(f"{var.类型名} {var.C名称}")
        return ", ".join(params)


class 参数处理器(错误处理混入, 类型处理混入):
    """处理函数参数的类"""

    def __init__(self, transpiler):
        self.transpiler = transpiler

    def 处理参数列表(self, node: ast.arguments):
        """处理参数列表"""
        self.transpiler.正在构建参数 = True

        args = list(node.args)
        if node.vararg:
            # C++ 变长参数处理复杂，暂不支持
            self.抛出错误("*args not supported", node)

        for idx, arg in enumerate(args):
            default_val = None
            if idx >= len(args) - len(node.defaults):
                default_val = node.defaults[idx - (len(args) - len(node.defaults))]
            self.处理参数(arg, default_val)

        self.transpiler.正在构建参数 = False

    def 处理参数(self, node: ast.arg, default_val=None):
        """处理单个参数"""
        name = node.arg

        # 记录参数名称
        self.transpiler.参数名称.append(name)

        if default_val is not None:
            # C++ 默认参数在声明中支持，此处简化处理，暂忽略
            pass

        # 处理self/cls参数
        if node.annotation is None:
            # 对于类方法的self/cls参数，不需要类型注解
            if self.transpiler.是否为类 and name in ["self", "cls"]:
                # self/cls参数不会被添加到参数列表中（已在visit_FunctionDef中处理）
                return
            else:
                self.抛出错误(f"Argument '{name}' must have type annotation", node)

        expr_visitor = 表达式访问者(self.transpiler)
        py_type = expr_visitor.获取值(node.annotation, is_type_annotation=True)

        # 处理字符串类型注解（如 'Vector2D'）
        if isinstance(py_type, str) and py_type not in [
            "int",
            "float",
            "str",
            "bool",
            "void",
            "bytes",
        ]:
            # 尝试从全局变量中查找对应的类
            if py_type in self.transpiler.全局变量:
                potential_class = self.transpiler.全局变量[py_type]
                if inspect.isclass(potential_class):
                    py_type = potential_class

        # 使用类型转换器处理

        # 处理自定义类类型
        if inspect.isclass(py_type):
            # 首先检查是否有类型映射
            mapped_type = 全局上下文.类型映射表.get(py_type)
            if mapped_type:
                # 使用映射的类型
                c_type = mapped_type.目标类型
                # 添加需要包含的头文件
                if mapped_type.包含目录:
                    self.transpiler.包含头文件.update(mapped_type.包含目录)
                # 添加需要链接的库
                if mapped_type.库:
                    self.transpiler.链接库.update(mapped_type.库)
                # 添加库搜索目录
                if mapped_type.库目录:
                    self.transpiler.库搜索目录.update(mapped_type.库目录)
            elif py_type.__module__ == "builtins":
                # 内置类型如str, int等，需要正常转换
                c_type = self.解析类型(py_type)
            else:
                # 用户自定义类，使用类名作为C++类型
                c_type = py_type.__name__
        else:
            c_type = self.解析类型(py_type)

        if c_type is None:
            self.抛出错误(f"Unsupported type {py_type}", node)

        # 检测是否为 std::vector 类型 (即 Python 的 List[T])
        # 如果是，则将其拆分为 指针 和 长度 两个参数传递，以兼容 ctypes
        if str(c_type).startswith("std::vector"):
            self.transpiler.包含头文件.add("<vector>")
            # 提取基础类型 T: std::vector<int> -> int
            base_type = str(c_type)[12:-1]

            ptr_name = f"{name}_ptr"
            len_name = f"{name}_len"

            ptr_var = C变量(f"{base_type}*", ptr_name, True)
            len_var = C变量("int64_t", len_name, True)

            self.transpiler.列表参数映射[name] = (ptr_var, len_var)

            # 逻辑上的参数变量 (在 C++ 函数内部作为局部变量使用)
            # 对于List类型，创建标准列表对象以支持方法调用
            from .std_vector import 标准列表
            from .cpp类型 import 列表初始化列表

            # 直接使用已提取的 base_type（第449行已定义）
            # 创建列表初始化列表和标准列表对象
            init_list = 列表初始化列表("", base_type, 0)  # 空初始化，后续会重建
            impl_var = 标准列表(init_list, name, False)

            self.transpiler.参数变量[name] = impl_var

            if not self.transpiler.可执行文件名:
                # 设置 ctypes 参数类型
                origin = getattr(py_type, "__origin__", None)
                args = getattr(py_type, "__args__", [])
                if origin is list and args:
                    elem_type = args[0]
                    ctypes_elem = 类型转换器.Python类型转ctypes(elem_type)
                    import ctypes

                    self.transpiler.ctypes参数类型.append(ctypes.POINTER(ctypes_elem))
                    self.transpiler.ctypes参数类型.append(ctypes.c_int64)
                else:
                    self.抛出错误(f"Complex list type {py_type} not supported for JIT args", node)

        else:
            # 为 Set 和 Map 类型添加相应的头文件
            if str(c_type).startswith("std::unordered_set"):
                self.transpiler.包含头文件.add("<unordered_set>")

                # 对于Set类型，创建标准集合对象以支持方法调用
                from .std_set import 标准集合
                from .cpp类型 import 集合初始化列表

                # 获取元素类型
                origin = getattr(py_type, "__origin__", None)
                args = getattr(py_type, "__args__", [])
                if origin is set and args:
                    elem_type = self.解析类型(args[0])
                    elem_type_str = str(elem_type)
                else:
                    # 从 c_type 中提取类型，例如 "std::unordered_set<int>" -> "int"
                    if str(c_type).startswith("std::unordered_set<") and str(c_type).endswith(">"):
                        elem_type_str = str(c_type)[20:-1]  # 去掉 "std::unordered_set<" 和 ">"
                    else:
                        elem_type_str = "int64_t"  # fallback

                # 创建集合初始化列表和标准集合对象
                init_list = 集合初始化列表("", elem_type_str)
                var = 标准集合(init_list, name, True)
                self.transpiler.参数变量[name] = var

            elif str(c_type).startswith("std::unordered_map"):
                self.transpiler.包含头文件.add("<unordered_map>")
                # 如果键或值类型包含string，添加string头文件
                if "std::string" in str(c_type) or "string" in str(c_type):
                    self.transpiler.包含头文件.add("<string>")

                # 对于Map类型，创建标准字典对象以支持方法调用
                from .std_map import 标准无序映射
                from .cpp类型 import 字典初始化列表

                # 获取键值类型
                origin = getattr(py_type, "__origin__", None)
                args = getattr(py_type, "__args__", [])
                if origin is dict and len(args) == 2:
                    key_type = self.解析类型(args[0])
                    val_type = self.解析类型(args[1])
                    key_type_str = str(key_type)
                    val_type_str = str(val_type)
                else:
                    # 从 c_type 中提取类型，例如 "std::unordered_map<int, std::string>" -> "int, std::string"
                    if str(c_type).startswith("std::unordered_map<") and str(c_type).endswith(">"):
                        type_part = str(c_type)[18:-1]  # 去掉 "std::unordered_map<" 和 ">"
                        if "," in type_part:
                            key_type_str, val_type_str = type_part.split(",", 1)
                            key_type_str = key_type_str.strip()
                            val_type_str = val_type_str.strip()
                        else:
                            key_type_str = "int64_t"
                            val_type_str = "int64_t"
                    else:
                        key_type_str = "int64_t"
                        val_type_str = "int64_t"

                # 创建字典初始化列表和标准字典对象
                init_list = 字典初始化列表("", key_type_str, val_type_str)
                var = 标准无序映射(init_list, name, True)
                self.transpiler.参数变量[name] = var

            else:
                # 其他类型，创建普通C变量
                var = C变量(str(c_type), name, True)
                self.transpiler.参数变量[name] = var

            if not self.transpiler.可执行文件名:
                self.transpiler.ctypes参数类型.append(
                    类型转换器.Python类型转ctypes(py_type)
                )
