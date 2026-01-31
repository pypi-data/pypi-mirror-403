# -*- coding: utf-8 -*-
"""
utils - 工具函数

包含:
- deprecation: 弃用装饰器
- result: 统一返回值类型
- format_trans: 格式转换
"""

from .format_trans import *
from .deprecation import deprecated
from .result import Result, Ok, Err, BatchResult

__all__ = [
    "deprecated",
    "Result",
    "Ok", 
    "Err",
    "BatchResult",
]
