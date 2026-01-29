"""
编译上下文模块的单元测试
"""

import unittest
from l0n0lc.编译上下文 import 编译上下文


class Test编译上下文(unittest.TestCase):
    """测试编译上下文类"""

    def setUp(self):
        """每个测试前的设置"""
        self.上下文 = 编译上下文()

    def test_初始化(self):
        """测试编译上下文的初始化"""
        self.assertEqual(self.上下文.工作目录, "./l0n0lcoutput")
        self.assertEqual(self.上下文.最大变量ID, 0)
        self.assertEqual(len(self.上下文.编译栈), 0)
        self.assertEqual(len(self.上下文.包含头文件), 0)
        self.assertEqual(len(self.上下文.链接库), 0)
        self.assertEqual(len(self.上下文.库搜索目录), 0)

    def test_自定义工作目录(self):
        """测试自定义工作目录"""
        上下文 = 编译上下文("/custom/output")
        self.assertEqual(上下文.工作目录, "/custom/output")

    def test_生成变量ID(self):
        """测试变量ID生成"""
        id1 = self.上下文.生成变量ID()
        id2 = self.上下文.生成变量ID()
        id3 = self.上下文.生成变量ID()

        self.assertEqual(id1, 1)
        self.assertEqual(id2, 2)
        self.assertEqual(id3, 3)
        self.assertEqual(self.上下文.最大变量ID, 3)

    def test_添加包含头文件(self):
        """测试添加头文件"""
        self.上下文.添加包含头文件("<stdint.h>")
        self.上下文.添加包含头文件("<vector>")
        self.上下文.添加包含头文件('"myheader.h"')

        self.assertIn("<stdint.h>", self.上下文.包含头文件)
        self.assertIn("<vector>", self.上下文.包含头文件)
        self.assertIn('"myheader.h"', self.上下文.包含头文件)
        self.assertEqual(len(self.上下文.包含头文件), 3)

    def test_添加重复头文件(self):
        """测试添加重复的头文件"""
        self.上下文.添加包含头文件("<vector>")
        self.上下文.添加包含头文件("<vector>")  # 重复

        self.assertEqual(len(self.上下文.包含头文件), 1)

    def test_添加链接库(self):
        """测试添加链接库"""
        self.上下文.添加链接库("m")
        self.上下文.添加链接库("pthread")
        self.上下文.添加链接库("dl")

        self.assertIn("m", self.上下文.链接库)
        self.assertIn("pthread", self.上下文.链接库)
        self.assertIn("dl", self.上下文.链接库)
        self.assertEqual(len(self.上下文.链接库), 3)

    def test_添加重复链接库(self):
        """测试添加重复的链接库"""
        self.上下文.添加链接库("m")
        self.上下文.添加链接库("m")  # 重复

        self.assertEqual(len(self.上下文.链接库), 1)

    def test_添加库搜索目录(self):
        """测试添加库搜索目录"""
        self.上下文.添加库搜索目录("/usr/local/lib")
        self.上下文.添加库搜索目录("/opt/lib")

        self.assertIn("/usr/local/lib", self.上下文.库搜索目录)
        self.assertIn("/opt/lib", self.上下文.库搜索目录)
        self.assertEqual(len(self.上下文.库搜索目录), 2)

    def test_编译栈操作(self):
        """测试编译栈的入栈和出栈操作"""
        # 入栈
        self.上下文.入栈编译("func1")
        self.上下文.入栈编译("func2")
        self.上下文.入栈编译("func3")

        self.assertTrue(self.上下文.是否正在编译("func1"))
        self.assertTrue(self.上下文.是否正在编译("func2"))
        self.assertTrue(self.上下文.是否正在编译("func3"))
        self.assertEqual(len(self.上下文.编译栈), 3)

        # 出栈
        self.上下文.出栈编译("func2")
        self.assertFalse(self.上下文.是否正在编译("func2"))
        self.assertTrue(self.上下文.是否正在编译("func1"))
        self.assertTrue(self.上下文.是否正在编译("func3"))
        self.assertEqual(len(self.上下文.编译栈), 2)

    def test_循环编译检测(self):
        """测试循环编译的检测"""
        self.上下文.入栈编译("func1")
        self.上下文.入栈编译("func2")

        # 尝试再次入栈 func1 应该抛出异常
        with self.assertRaises(RuntimeError) as context:
            self.上下文.入栈编译("func1")

        self.assertIn("循环编译", str(context.exception))
        self.assertIn("func1", str(context.exception))

    def test_出栈不存在的函数(self):
        """测试出栈不存在的函数（应该不报错）"""
        # discard() 方法即使元素不存在也不会报错
        self.上下文.出栈编译("nonexistent")
        self.assertEqual(len(self.上下文.编译栈), 0)

    def test_重置(self):
        """测试重置编译上下文"""
        # 添加一些数据
        self.上下文.生成变量ID()
        self.上下文.生成变量ID()
        self.上下文.添加包含头文件("<vector>")
        self.上下文.添加链接库("m")
        self.上下文.添加库搜索目录("/usr/lib")
        self.上下文.入栈编译("func1")

        # 重置
        self.上下文.重置()

        # 验证所有状态都被重置
        self.assertEqual(self.上下文.最大变量ID, 0)
        self.assertEqual(len(self.上下文.包含头文件), 0)
        self.assertEqual(len(self.上下文.链接库), 0)
        self.assertEqual(len(self.上下文.库搜索目录), 0)
        self.assertEqual(len(self.上下文.编译栈), 0)
        # 工作目录不应该被重置
        self.assertEqual(self.上下文.工作目录, "./l0n0lcoutput")

    def test_获取状态摘要(self):
        """测试获取状态摘要"""
        self.上下文.生成变量ID()
        self.上下文.生成变量ID()
        self.上下文.添加包含头文件("<vector>")
        self.上下文.添加链接库("m")
        self.上下文.入栈编译("func1")

        摘要 = self.上下文.获取状态摘要()

        self.assertEqual(摘要["工作目录"], "./l0n0lcoutput")
        self.assertEqual(摘要["编译栈大小"], 1)
        self.assertEqual(摘要["最大变量ID"], 2)
        self.assertEqual(摘要["包含头文件数量"], 1)
        self.assertEqual(摘要["链接库数量"], 1)
        self.assertEqual(摘要["库搜索目录数量"], 0)

    def test_多个独立上下文(self):
        """测试多个独立的编译上下文"""
        上下文1 = 编译上下文()
        上下文2 = 编译上下文()

        上下文1.生成变量ID()
        上下文1.生成变量ID()
        上下文1.添加包含头文件("<vector>")

        上下文2.生成变量ID()
        上下文2.添加链接库("m")

        # 验证两个上下文是独立的
        self.assertEqual(上下文1.最大变量ID, 2)
        self.assertEqual(上下文2.最大变量ID, 1)
        self.assertIn("<vector>", 上下文1.包含头文件)
        self.assertNotIn("<vector>", 上下文2.包含头文件)
        self.assertIn("m", 上下文2.链接库)
        self.assertNotIn("m", 上下文1.链接库)


if __name__ == '__main__':
    unittest.main()
