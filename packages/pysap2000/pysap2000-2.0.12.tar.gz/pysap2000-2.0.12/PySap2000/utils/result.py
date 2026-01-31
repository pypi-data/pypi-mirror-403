# -*- coding: utf-8 -*-
"""
result.py - 统一返回值类型

提供 Result 泛型类，用于统一 API 返回值格式。

Usage:
    from PySap2000.utils.result import Result, Ok, Err
    
    # 成功返回
    def get_point(model, name: str) -> Result[Point]:
        try:
            point = Point.get_by_name(model, name)
            return Ok(point)
        except Exception as e:
            return Err(str(e))
    
    # 使用结果
    result = get_point(model, "1")
    if result.is_ok:
        print(result.data)
    else:
        print(result.error)
"""

from dataclasses import dataclass, field
from typing import Generic, TypeVar, Optional, Union, List, Any

T = TypeVar('T')


@dataclass
class Result(Generic[T]):
    """
    统一的操作结果类型
    
    Attributes:
        success: 操作是否成功
        data: 成功时的返回数据
        error: 失败时的错误信息
        error_code: 错误代码（可选）
        warnings: 警告信息列表
        
    Example:
        result = Result(success=True, data=point)
        result = Result(success=False, error="Point not found")
    """
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    error_code: Optional[int] = None
    warnings: List[str] = field(default_factory=list)
    
    @property
    def is_ok(self) -> bool:
        """是否成功"""
        return self.success
    
    @property
    def is_err(self) -> bool:
        """是否失败"""
        return not self.success
    
    def unwrap(self) -> T:
        """
        获取数据，如果失败则抛出异常
        
        Returns:
            成功时的数据
            
        Raises:
            ValueError: 如果操作失败
        """
        if self.success and self.data is not None:
            return self.data
        raise ValueError(self.error or "Operation failed")
    
    def unwrap_or(self, default: T) -> T:
        """
        获取数据，如果失败则返回默认值
        
        Args:
            default: 默认值
            
        Returns:
            成功时的数据或默认值
        """
        if self.success and self.data is not None:
            return self.data
        return default
    
    def map(self, func) -> 'Result':
        """
        对成功的数据应用函数
        
        Args:
            func: 转换函数
            
        Returns:
            新的 Result 对象
        """
        if self.success and self.data is not None:
            try:
                return Result(success=True, data=func(self.data))
            except Exception as e:
                return Result(success=False, error=str(e))
        return Result(success=False, error=self.error)
    
    def __bool__(self) -> bool:
        """允许直接用 if result: 判断"""
        return self.success


def Ok(data: T, warnings: Optional[List[str]] = None) -> Result[T]:
    """
    创建成功结果的快捷函数
    
    Args:
        data: 返回数据
        warnings: 警告信息（可选）
        
    Returns:
        成功的 Result 对象
        
    Example:
        return Ok(point)
        return Ok(frames, warnings=["Some frames were skipped"])
    """
    return Result(success=True, data=data, warnings=warnings or [])


def Err(error: str, error_code: Optional[int] = None) -> Result[Any]:
    """
    创建失败结果的快捷函数
    
    Args:
        error: 错误信息
        error_code: 错误代码（可选）
        
    Returns:
        失败的 Result 对象
        
    Example:
        return Err("Point not found")
        return Err("Connection failed", error_code=-1)
    """
    return Result(success=False, error=error, error_code=error_code)


@dataclass
class BatchResult(Generic[T]):
    """
    批量操作结果类型
    
    Attributes:
        succeeded: 成功的结果列表
        failed: 失败的结果列表（包含错误信息）
        total: 总数
        
    Example:
        result = BatchResult()
        result.add_success(point1)
        result.add_failure("Point2", "Invalid coordinates")
    """
    succeeded: List[T] = field(default_factory=list)
    failed: List[tuple] = field(default_factory=list)  # (item_id, error_message)
    
    @property
    def total(self) -> int:
        """总处理数量"""
        return len(self.succeeded) + len(self.failed)
    
    @property
    def success_count(self) -> int:
        """成功数量"""
        return len(self.succeeded)
    
    @property
    def failure_count(self) -> int:
        """失败数量"""
        return len(self.failed)
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        return self.success_count / self.total if self.total > 0 else 0.0
    
    @property
    def all_succeeded(self) -> bool:
        """是否全部成功"""
        return len(self.failed) == 0
    
    def add_success(self, item: T) -> None:
        """添加成功项"""
        self.succeeded.append(item)
    
    def add_failure(self, item_id: str, error: str) -> None:
        """添加失败项"""
        self.failed.append((item_id, error))
    
    def to_result(self) -> Result[List[T]]:
        """
        转换为 Result 类型
        
        Returns:
            如果全部成功返回 Ok，否则返回包含警告的 Result
        """
        if self.all_succeeded:
            return Ok(self.succeeded)
        else:
            warnings = [f"{item_id}: {error}" for item_id, error in self.failed]
            return Result(
                success=True,
                data=self.succeeded,
                warnings=warnings
            )
