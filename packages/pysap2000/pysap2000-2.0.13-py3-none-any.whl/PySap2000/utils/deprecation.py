# -*- coding: utf-8 -*-
"""
deprecation.py - 弃用警告工具

提供 @deprecated 装饰器，用于标记弃用的类和函数。

Usage:
    from PySap2000.utils.deprecation import deprecated
    
    @deprecated("Use PointError instead")
    class NodeError(ObjectError):
        pass
"""

import warnings
import functools
from typing import Optional, Callable, Type, TypeVar

T = TypeVar('T')


def deprecated(reason: str = "", replacement: Optional[str] = None):
    """
    标记函数或类为弃用状态的装饰器
    
    Args:
        reason: 弃用原因
        replacement: 建议使用的替代项
        
    Returns:
        装饰后的函数或类
        
    Example:
        @deprecated("This function is outdated", replacement="new_function")
        def old_function():
            pass
    """
    def decorator(obj: T) -> T:
        message = f"{obj.__name__} is deprecated."
        if reason:
            message += f" {reason}"
        if replacement:
            message += f" Use {replacement} instead."
        
        if isinstance(obj, type):
            # 装饰类
            original_init = obj.__init__
            
            @functools.wraps(original_init)
            def new_init(self, *args, **kwargs):
                warnings.warn(message, DeprecationWarning, stacklevel=2)
                original_init(self, *args, **kwargs)
            
            obj.__init__ = new_init
            obj.__doc__ = f"[DEPRECATED] {obj.__doc__ or ''}\n\n{message}"
            return obj
        else:
            # 装饰函数
            @functools.wraps(obj)
            def wrapper(*args, **kwargs):
                warnings.warn(message, DeprecationWarning, stacklevel=2)
                return obj(*args, **kwargs)
            
            wrapper.__doc__ = f"[DEPRECATED] {obj.__doc__ or ''}\n\n{message}"
            return wrapper
    
    return decorator
