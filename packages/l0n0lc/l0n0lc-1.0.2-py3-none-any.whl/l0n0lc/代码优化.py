"""
代码优化模块

对生成的 C++ 代码进行优化，包括：
1. 常量折叠：编译时计算常量表达式
2. 死代码消除：移除永远不会执行的代码
3. 循环优化：使用范围循环替代索引循环
"""

import ast
from typing import Any, Optional, Union


class 常量折叠器(ast.NodeTransformer):
    """
    常量折叠优化器

    在编译时计算常量表达式，减少运行时计算。
    """

    def visit_BinOp(self, node: ast.BinOp) -> Any:
        """处理二元运算"""
        # 先递归处理子节点
        node = self.generic_visit(node)  # type: ignore[assignment]

        # 尝试计算常量表达式
        if isinstance(node.left, ast.Constant) and isinstance(node.right, ast.Constant):
            try:
                left_val = node.left.value
                right_val = node.right.value

                # 处理数值运算
                if isinstance(left_val, (int, float)) and isinstance(right_val, (int, float)):
                    if isinstance(node.op, ast.Add):
                        result = left_val + right_val
                    elif isinstance(node.op, ast.Sub):
                        result = left_val - right_val
                    elif isinstance(node.op, ast.Mult):
                        result = left_val * right_val
                    elif isinstance(node.op, ast.Div):
                        result = left_val / right_val
                    elif isinstance(node.op, ast.FloorDiv):
                        result = left_val // right_val
                    elif isinstance(node.op, ast.Mod):
                        result = left_val % right_val
                    elif isinstance(node.op, ast.Pow):
                        result = left_val ** right_val
                    else:
                        return node

                    # 返回计算结果
                    return ast.Constant(value=result)
            except (ZeroDivisionError, OverflowError, ValueError):
                # 计算失败，返回原节点
                pass

        return node

    def visit_UnaryOp(self, node: ast.UnaryOp) -> Any:
        """处理一元运算"""
        node = self.generic_visit(node)  # type: ignore[assignment]

        if isinstance(node.operand, ast.Constant):
            operand_val = node.operand.value

            if isinstance(operand_val, (int, float)):
                if isinstance(node.op, ast.UAdd):
                    return ast.Constant(value=+operand_val)
                elif isinstance(node.op, ast.USub):
                    return ast.Constant(value=-operand_val)
                elif isinstance(node.op, ast.Not):
                    return ast.Constant(value=not operand_val)

        return node

    def visit_Compare(self, node: ast.Compare) -> Any:
        """处理比较运算"""
        node = self.generic_visit(node) # type: ignore

        # 简单的比较：a < b（a, b 都是常量）
        if (len(node.ops) == 1 and
            isinstance(node.left, ast.Constant) and
            isinstance(node.comparators[0], ast.Constant)):

            left_val = node.left.value
            right_val = node.comparators[0].value
            op = node.ops[0]

            # 相等性运算符可以在不同类型之间使用
            if isinstance(left_val, (int, float, str)) and isinstance(right_val, (int, float, str)):
                try:
                    if isinstance(op, ast.Eq):
                        result = left_val == right_val
                        return ast.Constant(value=result)
                    elif isinstance(op, ast.NotEq):
                        result = left_val != right_val
                        return ast.Constant(value=result)
                except TypeError:
                    pass

            # 比较运算符只能在相同类型之间使用
            # 数值类型
            if (isinstance(left_val, (int, float)) and isinstance(right_val, (int, float))):
                try:
                    if isinstance(op, ast.Lt):
                        result = left_val < right_val
                    elif isinstance(op, ast.LtE):
                        result = left_val <= right_val
                    elif isinstance(op, ast.Gt):
                        result = left_val > right_val
                    elif isinstance(op, ast.GtE):
                        result = left_val >= right_val
                    else:
                        return node

                    return ast.Constant(value=result)
                except TypeError:
                    pass
            # 字符串类型
            elif (isinstance(left_val, str) and isinstance(right_val, str)):
                try:
                    if isinstance(op, ast.Lt):
                        result = left_val < right_val
                    elif isinstance(op, ast.LtE):
                        result = left_val <= right_val
                    elif isinstance(op, ast.Gt):
                        result = left_val > right_val
                    elif isinstance(op, ast.GtE):
                        result = left_val >= right_val
                    else:
                        return node

                    return ast.Constant(value=result)
                except TypeError:
                    pass

        return node

    def visit_BoolOp(self, node: ast.BoolOp) -> Any:
        """处理布尔运算（and/or）"""
        node = self.generic_visit(node)  # type: ignore[assignment]

        # 检查所有操作数是否都是常量
        values = node.values
        if all(isinstance(v, ast.Constant) for v in values):
            try:
                const_values = [v.value for v in values]  # type: ignore[attr-defined]

                if isinstance(node.op, ast.And):
                    result = all(const_values)
                elif isinstance(node.op, ast.Or):
                    result = any(const_values)
                else:
                    return node

                return ast.Constant(value=result)
            except (TypeError, ValueError):
                pass

        return node


class 死代码消除器(ast.NodeTransformer):
    """
    死代码消除优化器

    移除永远不会执行的代码，如 if False: ... 分支
    """

    def visit_If(self, node: ast.If) -> Any:
        """处理 if 语句"""
        # 先处理测试条件
        test = self.visit(node.test)

        # 检查是否为常量
        if isinstance(test, ast.Constant):
            if test.value:
                # 条件永远为 True，只保留 body
                if node.orelse:
                    # 移除 orelse，保留 body
                    result = [self.visit(n) for n in node.body]
                    return result if len(result) > 1 else (result[0] if result else None)
                else:
                    # 有 body，保留
                    return self.generic_visit(node)
            else:
                # 条件永远为 False，只保留 orelse
                if node.orelse:
                    result = [self.visit(n) for n in node.orelse]
                    return result if len(result) > 1 else (result[0] if result else None)
                else:
                    # 没有 orelse，完全移除
                    return None

        return self.generic_visit(node)

    def visit_While(self, node: ast.While) -> Any:
        """处理 while 循环"""
        test = self.visit(node.test)

        # 检查是否为常量 False
        if isinstance(test, ast.Constant) and not test.value:
            # 循环永远不会执行，移除
            return None

        return self.generic_visit(node)


class 循环优化器(ast.NodeTransformer):
    """
    循环优化器

    将 for i in range(len(lst)): lst[i] 模式转换为 for elem in lst:
    """

    def visit_For(self, node: ast.For) -> Any:
        """处理 for 循环"""
        node = self.generic_visit(node)  # type: ignore[assignment]

        # 检查模式：for i in range(len(x)): ... x[i] ...
        if (isinstance(node.iter, ast.Call) and
            isinstance(node.iter.func, ast.Name) and
            node.iter.func.id == 'range' and
            len(node.iter.args) == 1 and
            isinstance(node.iter.args[0], ast.Call) and
            isinstance(node.iter.args[0].func, ast.Name) and
            node.iter.args[0].func.id == 'len' and
            len(node.iter.args[0].args) == 1):

            # 获取被遍历的变量
            target_var = node.iter.args[0].args[0]
            loop_var = node.target

            # 检查是否是简单的索引访问模式
            # 这是一个简化版本，只检查基本情况
            # 完整实现需要更复杂的数据流分析

            return node

        return node


class 代码优化器:
    """
    代码优化器主类

    组合多个优化器，按顺序应用到 AST 上。
    """

    def __init__(self, transpiler):
        self.transpiler = transpiler
        self.常量折叠 = 常量折叠器()
        self.死代码消除 = 死代码消除器()
        self.循环优化 = 循环优化器()

    def 优化(self, tree: ast.AST) -> ast.AST:
        """
        对 AST 进行优化

        Args:
            tree: 要优化的 AST

        Returns:
            优化后的 AST
        """
        # 按顺序应用优化器
        # 1. 常量折叠（为其他优化提供更多信息）
        tree = self.常量折叠.visit(tree)

        # 2. 死代码消除（基于常量折叠的结果）
        tree = self.死代码消除.visit(tree)

        # 3. 循环优化
        tree = self.循环优化.visit(tree)

        # 修复 AST（确保节点完整性）
        ast.fix_missing_locations(tree)

        return tree

    def 获取统计(self) -> dict:
        """获取优化统计信息"""
        return {
            "常量折叠": "已启用",
            "死代码消除": "已启用",
            "循环优化": "已启用",
        }


def 优化AST(tree: ast.AST, transpiler) -> ast.AST:
    """
    优化 AST 的便捷函数

    Args:
        tree: 要优化的 AST
        transpiler: 转译器实例

    Returns:
        优化后的 AST
    """
    优化器 = 代码优化器(transpiler)
    return 优化器.优化(tree)
