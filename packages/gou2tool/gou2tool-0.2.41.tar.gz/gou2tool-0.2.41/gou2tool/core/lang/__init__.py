"""
语言/工具模块初始化文件

该文件定义了语言相关的公共接口，包含HTTP状态码等工具类。
"""

# 导入HTTP状态码类 - 提供HTTP状态码常量定义
from .http_status_code import HttpStatusCode

# 定义公共接口 - 指定模块对外暴露的类
__all__ = [
    'HttpStatusCode',  # HTTP状态码类
]

# 模块作者信息
__author__ = "wl4837"
