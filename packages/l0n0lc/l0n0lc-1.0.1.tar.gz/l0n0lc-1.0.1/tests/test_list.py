import sys
import pathlib
sys.path.append(str(pathlib.Path(__file__).parent.parent))

from typing import List
from l0n0lc.即时编译 import 即时编译
import unittest

class TestList(unittest.TestCase):
    """测试列表功能，包括基础操作和方法操作"""

    # ========== 基础操作测试 ==========

    def test_indexing(self):
        @即时编译(总是重编=True)
        def get_elem(arr: List[int], idx: int) -> int:
            return arr[idx]

        self.assertEqual(get_elem([10, 20, 30], 0), 10)
        self.assertEqual(get_elem([10, 20, 30], 2), 30)

    def test_length(self):
        @即时编译(总是重编=True)
        def get_len(arr: List[int]) -> int:
            return len(arr)

        self.assertEqual(get_len([1, 2, 3]), 3)
        self.assertEqual(get_len([]), 0)

    def test_length_manual(self):
        @即时编译(总是重编=True)
        def get_len_manual(arr: List[int]) -> int:
            count = 0
            for x in arr:
                count = count + 1
            return count

        self.assertEqual(get_len_manual([1, 2, 3]), 3)
        self.assertEqual(get_len_manual([]), 0)

    def test_float_list(self):
        @即时编译(总是重编=True)
        def sum_floats(arr: List[float]) -> float:
            s = 0.0
            for x in arr:
                s = s + x
            return s

        self.assertAlmostEqual(sum_floats([1.1, 2.2, 3.3]), 6.6, places=5)

    def test_list_arg_func(self):
        @即时编译(总是重编=True)
        def 获取列表长度(arr: List[int]) -> int:
            return len(arr)

        @即时编译(总是重编=True)
        def 测试列表参数() -> int:
            a:List[int] = []
            b:List[int] = [1,2,3]
            return 获取列表长度(a) + 获取列表长度(b)

        self.assertAlmostEqual(测试列表参数(), 3, places=5)

    # ========== 方法相关测试 ==========

    def test_append(self):
        @即时编译(总是重编=True)
        def test_append_func(arr: List[int]) -> int:
            arr.append(42)
            return len(arr)

        result = test_append_func([1, 2, 3])
        self.assertEqual(result, 4)

    def test_extend(self):
        @即时编译(总是重编=True)
        def test_extend_func(arr: List[int]) -> int:
            arr.extend([4, 5, 6])
            return len(arr)

        result = test_extend_func([1, 2, 3])
        self.assertEqual(result, 6)

    def test_insert(self):
        @即时编译(总是重编=True)
        def test_insert_func(arr: List[int]) -> int:
            arr.insert(1, 99)
            return arr[1]

        result = test_insert_func([1, 2, 3])
        self.assertEqual(result, 99)

    def test_pop_last(self):
        @即时编译(总是重编=True)
        def test_pop_last_func(arr: List[int]) -> int:
            return arr.pop()  # 默认移除最后一个

        result = test_pop_last_func([1, 2, 3])
        self.assertEqual(result, 3)

    def test_pop_index(self):
        @即时编译(总是重编=True)
        def test_pop_index_func(arr: List[int]) -> int:
            return arr.pop(0)  # 移除第一个元素

        result = test_pop_index_func([1, 2, 3])
        self.assertEqual(result, 1)

    def test_remove(self):
        @即时编译(总是重编=True)
        def test_remove_func(arr: List[int]) -> int:
            arr.remove(3)  # 移除值为3的元素
            return len(arr)

        result = test_remove_func([1, 2, 3, 4])
        self.assertEqual(result, 3)

    def test_clear(self):
        @即时编译(总是重编=True)
        def test_clear_func(arr: List[int]) -> int:
            arr.clear()
            return len(arr)

        result = test_clear_func([1, 2, 3])
        self.assertEqual(result, 0)

    # ========== 复合操作测试 ==========

    def test_complex_operations(self):
        @即时编译(总是重编=True)
        def test_complex_func(arr: List[int]) -> int:
            # 测试复合操作
            arr.append(100)
            arr.insert(0, 200)
            arr.pop()
            arr.extend([1, 2, 3])
            return len(arr)

        result = test_complex_func([1, 2, 3])
        self.assertEqual(result, 7)

    def test_chained_operations(self):
        @即时编译(总是重编=True)
        def test_chained_func(arr: List[int]) -> int:
            # 测试链式操作的效果
            original_size = len(arr)
            arr.append(10)
            arr.append(20)
            arr.insert(0, 30)
            removed = arr.pop()
            arr.extend([1, 2])
            return len(arr) - original_size  # 返回净增长的数量

        result = test_chained_func([1, 2, 3])
        # 原始大小3，+10, +20, +30(插入), -20(pop), +1, +2 = +4
        self.assertEqual(result, 4)

    # ========== 在表达式中的使用测试 ==========

    def test_len_in_expression(self):
        """测试 len() 在表达式中的使用"""
        @即时编译(总是重编=True)
        def is_empty(arr: List[int]) -> bool:
            return len(arr) == 0

        self.assertTrue(is_empty([]))
        self.assertFalse(is_empty([1, 2, 3]))

    def test_len_in_comparison(self):
        """测试 len() 在比较运算中的使用"""
        @即时编译(总是重编=True)
        def has_elements(arr: List[int]) -> bool:
            return len(arr) > 0

        self.assertFalse(has_elements([]))
        self.assertTrue(has_elements([1]))
        self.assertTrue(has_elements([1, 2, 3]))

    def test_len_in_loop(self):
        """测试 len() 在循环中的使用"""
        @即时编译(总是重编=True)
        def sum_by_index(arr: List[int]) -> int:
            total = 0
            for i in range(len(arr)):
                total = total + arr[i]
            return total

        self.assertEqual(sum_by_index([1, 2, 3, 4, 5]), 15)
        self.assertEqual(sum_by_index([]), 0)
        self.assertEqual(sum_by_index([10]), 10)

    def test_len_arithmetic(self):
        """测试 len() 在算术运算中的使用"""
        @即时编译(总是重编=True)
        def double_length(arr: List[int]) -> int:
            return len(arr) * 2

        self.assertEqual(double_length([1, 2, 3]), 6)
        self.assertEqual(double_length([]), 0)

    # ========== 遗漏的方法测试 ==========

    def test_setitem(self):
        """测试列表元素赋值"""
        @即时编译(总是重编=True)
        def test_setitem_func(arr: List[int]) -> int:
            arr[1] = 99
            return arr[1]

        result = test_setitem_func([1, 2, 3])
        self.assertEqual(result, 99)

    def test_empty_check(self):
        """测试列表空检查"""
        @即时编译(总是重编=True)
        def test_empty_non_empty(arr: List[int]) -> int:
            result = 0
            if arr.empty(): # type: ignore
                result = 1
            else:
                result = 2
            return result

        self.assertEqual(test_empty_non_empty([]), 1)  # 空列表
        self.assertEqual(test_empty_non_empty([1, 2, 3]), 2)  # 非空列表

    def test_first_last_access(self):
        """测试访问首尾元素（使用Python标准方式）"""
        @即时编译(总是重编=True)
        def test_first_last_func(arr: List[int]) -> int:
            if len(arr) >= 2:
                return arr[0] + arr[len(arr) - 1]
            return 0

        result = test_first_last_func([10, 20, 30, 40])
        self.assertEqual(result, 50)  # 10 + 40

        result = test_first_last_func([5])
        self.assertEqual(result, 0)  # 长度不够

    def test_list_slicing_bounds(self):
        """测试列表边界访问"""
        @即时编译(总是重编=True)
        def test_bounds_access() -> int:
            arr: List[int] = [1, 2, 3, 4, 5]
            first = arr[0]
            last = arr[len(arr) - 1]
            middle = arr[2]
            return first + last + middle

        result = test_bounds_access()
        self.assertEqual(result, 1 + 5 + 3)  # 9

if __name__ == '__main__':
    unittest.main()