"""
响应模块初始化文件

该文件定义了响应处理相关的公共接口，包含各种结果类型和控制器路径类型。
用于统一处理和返回不同类型的响应数据。
"""

# 导入控制器路径类型枚举
from .controller_path_type import ControllerPathType
# 导入基础结果类 - 响应结果的基础实现
from .result import Result
# 导入分页结果类 - 用于返回分页数据的响应
from .page_result import PageResult
# 导入JSON结果类 - 用于返回JSON格式的响应
from .json_result import JsonResult
# 导入通用响应类 - 提供统一的响应格式
from .r import R

# 定义公共接口 - 指定模块对外暴露的类
__all__ = [
    'ControllerPathType',  # 控制器路径类型枚举
    'Result',              # 基础结果类
    'PageResult',          # 分页结果类
    'JsonResult',          # JSON结果类
    'R',                   # 通用响应类
]

# 模块作者信息
__author__ = "wl4837"
