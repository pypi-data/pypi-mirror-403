"""
核心模块初始化文件

该文件定义了核心模块的公共接口，包含容器管理和实例管理功能。
通过此模块可以实现依赖注入容器和实例的创建与管理。
"""

# 导入容器类 - 提供依赖注入容器功能
from .container import Container
# 导入实例类 - 提供实例管理功能
from .instance import Instance

# 定义公共接口 - 指定模块对外暴露的类
__all__ = [
    'lang',
    'request',
    'response',
    'Container',  # 依赖注入容器类
    'Instance'    # 实例管理类
]

# 模块作者信息
__author__ = "wl4837"
