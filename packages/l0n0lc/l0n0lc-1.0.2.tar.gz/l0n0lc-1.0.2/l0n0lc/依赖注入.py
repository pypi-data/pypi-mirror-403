"""
依赖注入模块 - 实现依赖注入模式，降低模块间的耦合度
"""

from typing import Dict, Any, Type, TypeVar, Callable, Optional, Union, cast
from abc import ABC, abstractmethod

T = TypeVar('T')


class 服务容器:
    """简单的依赖注入容器"""
    
    def __init__(self):
        self._服务: Dict[str, Any] = {}
        self._工厂: Dict[str, Union[Callable[[], Any], Type[Any], Any]] = {}
        self._单例: Dict[str, bool] = {}
    
    def 注册单例(self, 接口: Type[T], 实现: Type[T]) -> None:
        """注册单例服务"""
        接口名 = 接口.__name__
        self._工厂[接口名] = 实现
        self._单例[接口名] = True
    
    def 注册工厂(self, 接口: Type[T], 工厂: Callable[[], T]) -> None:
        """注册工厂方法"""
        接口名 = 接口.__name__
        self._工厂[接口名] = 工厂
        self._单例[接口名] = False
    
    def 注册实例(self, 接口: Type[T], 实例: T) -> None:
        """注册实例"""
        接口名 = 接口.__name__
        self._服务[接口名] = 实例
        self._单例[接口名] = True
    
    def 解析(self, 接口: Type[T]) -> T:
        """解析服务"""
        接口名 = 接口.__name__
        
        # 如果已有实例且为单例，直接返回
        if 接口名 in self._服务 and self._单例.get(接口名, False):
            return cast(T, self._服务[接口名])
        
        # 创建新实例
        if 接口名 in self._工厂:
            if callable(self._工厂[接口名]):
                实例 = self._工厂[接口名]()
            else:
                实例 = self._工厂[接口名]
            
            if self._单例.get(接口名, False):
                self._服务[接口名] = 实例
            
            return cast(T, 实例)
        
        raise ValueError(f"未注册的服务: {接口名}")
    
    def 清理(self) -> None:
        """清理容器"""
        self._服务.clear()
        self._工厂.clear()
        self._单例.clear()


# 全局服务容器
全局容器 = 服务容器()


class 转译器组件接口(ABC):
    """转译器组件的抽象基类"""
    
    @abstractmethod
    def 初始化(self, 转译器) -> None:
        """初始化组件"""
        pass
    
    @abstractmethod
    def 清理(self) -> None:
        """清理组件资源"""
        pass


class 代码生成接口(ABC):
    """代码生成接口"""
    
    @abstractmethod
    def 生成代码(self) -> str:
        """生成代码"""
        pass
    
    @abstractmethod
    def 保存代码(self, 文件路径: str) -> None:
        """保存代码到文件"""
        pass


class 类型推断接口(ABC):
    """类型推断接口"""
    
    @abstractmethod
    def 推断类型(self, 节点) -> str:
        """推断类型"""
        pass
    
    @abstractmethod
    def 验证类型(self, 类型1: str, 类型2: str) -> bool:
        """验证类型兼容性"""
        pass


class 编译管理接口(ABC):
    """编译管理接口"""
    
    @abstractmethod
    def 编译(self, 源文件: str, 输出文件: str) -> bool:
        """编译文件"""
        pass
    
    @abstractmethod
    def 清理临时文件(self) -> None:
        """清理临时文件"""
        pass


class 依赖解析接口(ABC):
    """依赖解析接口"""
    
    @abstractmethod
    def 解析依赖(self, 函数) -> list:
        """解析函数依赖"""
        pass
    
    @abstractmethod
    def 排序依赖(self, 依赖列表: list) -> list:
        """对依赖进行拓扑排序"""
        pass


def 注册服务(接口: Type[T], 实现: Type[T], 单例: bool = True) -> None:
    """便捷的服务注册函数"""
    if 单例:
        全局容器.注册单例(接口, 实现)
    else:
        全局容器.注册工厂(接口, 实现)


def 解析服务(接口: Type[T]) -> T:
    """便捷的服务解析函数"""
    return 全局容器.解析(接口)


def 清理容器() -> None:
    """清理全局容器"""
    全局容器.清理()
