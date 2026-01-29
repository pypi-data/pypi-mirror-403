from __future__ import annotations
import sys
import pathlib
sys.path.append(str(pathlib.Path(__file__).parent.parent))

from l0n0lc import jit

# 测试1: 字符串类型支持
class Person:
    name: str
    age: int
    _legs: int = 2

    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age

# 测试2: 运算符重载
class Point:
    x: float
    y: float

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def __add__(self, other: Point) -> Point:
        return Point(self.x + other.x, self.y + other.y)

# 测试3: 静态方法
class Calculator:
    @staticmethod
    def add(a: int, b: int) -> int:
        return a + b


@jit(总是重编=True)
def test_operator_overloading() -> float:
    p1 = Point(1.0, 2.0)
    p2 = Point(3.0, 4.0)
    result = p1 + p2
    return result.x  # Should be 4.0

@jit(总是重编=True)
def test_static_method() -> int:
    return Calculator.add(10, 20)  # Should be 30

if __name__ == '__main__':
    print("=== 测试C++类支持改进 ===")

    # 测试运算符重载
    try:
        result2 = test_operator_overloading()
        print(f"✓ 运算符重载: {result2}")
    except Exception as e:
        print(f"✗ 运算符重载: {e}")

    # 测试静态方法
    try:
        result3 = test_static_method()
        print(f"✓ 静态方法: {result3}")
    except Exception as e:
        print(f"✗ 静态方法: {e}")