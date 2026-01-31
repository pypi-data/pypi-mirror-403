# -*- coding: utf-8 -*-
"""
time_history.py - 时程函数

SAP2000 Func.FuncTH API 封装

SAP2000 API:
- Func.FuncTH.GetCosine / SetCosine - 余弦函数
- Func.FuncTH.GetFromFile_1 / SetFromFile_1 - 从文件读取
- Func.FuncTH.GetRamp / SetRamp - 斜坡函数
- Func.FuncTH.GetSawtooth / SetSawtooth - 锯齿波函数
- Func.FuncTH.GetSine / SetSine - 正弦函数
- Func.FuncTH.GetTriangular / SetTriangular - 三角波函数
- Func.FuncTH.GetUser / SetUser - 用户定义函数
- Func.FuncTH.GetUserPeriodic / SetUserPeriodic - 用户周期函数
"""

from typing import List, Tuple
from dataclasses import dataclass


# =============================================================================
# 数据类
# =============================================================================

@dataclass
class CosineParams:
    """余弦函数参数"""
    period: float = 0.0         # 周期 [s]
    steps: int = 0              # 每周期步数
    cycles: int = 0             # 周期数
    amplitude: float = 0.0      # 幅值


@dataclass
class RampParams:
    """斜坡函数参数"""
    time: float = 0.0           # 斜坡时间 [s]
    amplitude: float = 0.0      # 幅值
    max_time: float = 0.0       # 最大时间 [s]


@dataclass
class SawtoothParams:
    """锯齿波函数参数"""
    period: float = 0.0         # 周期 [s]
    time: float = 0.0           # 上升时间 [s]
    cycles: int = 0             # 周期数
    amplitude: float = 0.0      # 幅值


@dataclass
class SineParams:
    """正弦函数参数"""
    period: float = 0.0         # 周期 [s]
    steps: int = 0              # 每周期步数
    cycles: int = 0             # 周期数
    amplitude: float = 0.0      # 幅值


@dataclass
class TriangularParams:
    """三角波函数参数"""
    period: float = 0.0         # 周期 [s]
    cycles: int = 0             # 周期数
    amplitude: float = 0.0      # 幅值


@dataclass
class FromFileParams:
    """从文件读取参数"""
    file_name: str = ""         # 文件名
    header_lines: int = 0       # 头部行数
    prefix_chars: int = 0       # 前缀字符数


# =============================================================================
# 余弦函数
# =============================================================================

def get_func_th_cosine(model, name: str) -> CosineParams:
    """
    获取余弦时程函数参数
    
    Args:
        model: SapModel 对象
        name: 函数名称
        
    Returns:
        CosineParams 参数对象
    """
    result = model.Func.FuncTH.GetCosine(name, 0.0, 0, 0, 0.0)
    if isinstance(result, (list, tuple)) and len(result) >= 5:
        return CosineParams(
            period=result[0],
            steps=result[1],
            cycles=result[2],
            amplitude=result[3],
        )
    return CosineParams()


def set_func_th_cosine(
    model,
    name: str,
    period: float,
    steps: int,
    cycles: int,
    amplitude: float
) -> int:
    """
    设置余弦时程函数
    
    Args:
        model: SapModel 对象
        name: 函数名称
        period: 周期 [s]
        steps: 每周期步数
        cycles: 周期数
        amplitude: 幅值
        
    Returns:
        0 表示成功
    """
    return model.Func.FuncTH.SetCosine(name, period, steps, cycles, amplitude)


# =============================================================================
# 从文件读取
# =============================================================================

def get_func_th_from_file(model, name: str) -> FromFileParams:
    """
    获取从文件读取的时程函数参数
    
    Args:
        model: SapModel 对象
        name: 函数名称
        
    Returns:
        FromFileParams 参数对象
    """
    result = model.Func.FuncTH.GetFromFile_1(name, "", 0, 0)
    if isinstance(result, (list, tuple)) and len(result) >= 4:
        return FromFileParams(
            file_name=result[0] if result[0] else "",
            header_lines=result[1],
            prefix_chars=result[2],
        )
    return FromFileParams()


def set_func_th_from_file(
    model,
    name: str,
    file_name: str,
    header_lines: int = 0,
    prefix_chars: int = 0
) -> int:
    """
    从文件设置时程函数
    
    Args:
        model: SapModel 对象
        name: 函数名称
        file_name: 文件路径
        header_lines: 头部跳过行数
        prefix_chars: 每行前缀跳过字符数
        
    Returns:
        0 表示成功
    """
    return model.Func.FuncTH.SetFromFile_1(name, file_name, header_lines, prefix_chars)


# =============================================================================
# 斜坡函数
# =============================================================================

def get_func_th_ramp(model, name: str) -> RampParams:
    """
    获取斜坡时程函数参数
    
    Args:
        model: SapModel 对象
        name: 函数名称
        
    Returns:
        RampParams 参数对象
    """
    result = model.Func.FuncTH.GetRamp(name, 0.0, 0.0, 0.0)
    if isinstance(result, (list, tuple)) and len(result) >= 4:
        return RampParams(
            time=result[0],
            amplitude=result[1],
            max_time=result[2],
        )
    return RampParams()


def set_func_th_ramp(
    model,
    name: str,
    time: float,
    amplitude: float,
    max_time: float
) -> int:
    """
    设置斜坡时程函数
    
    Args:
        model: SapModel 对象
        name: 函数名称
        time: 斜坡时间 [s]
        amplitude: 幅值
        max_time: 最大时间 [s]
        
    Returns:
        0 表示成功
    """
    return model.Func.FuncTH.SetRamp(name, time, amplitude, max_time)


# =============================================================================
# 锯齿波函数
# =============================================================================

def get_func_th_sawtooth(model, name: str) -> SawtoothParams:
    """
    获取锯齿波时程函数参数
    
    Args:
        model: SapModel 对象
        name: 函数名称
        
    Returns:
        SawtoothParams 参数对象
    """
    result = model.Func.FuncTH.GetSawtooth(name, 0.0, 0.0, 0, 0.0)
    if isinstance(result, (list, tuple)) and len(result) >= 5:
        return SawtoothParams(
            period=result[0],
            time=result[1],
            cycles=result[2],
            amplitude=result[3],
        )
    return SawtoothParams()


def set_func_th_sawtooth(
    model,
    name: str,
    period: float,
    time: float,
    cycles: int,
    amplitude: float
) -> int:
    """
    设置锯齿波时程函数
    
    Args:
        model: SapModel 对象
        name: 函数名称
        period: 周期 [s]
        time: 上升时间 [s]
        cycles: 周期数
        amplitude: 幅值
        
    Returns:
        0 表示成功
    """
    return model.Func.FuncTH.SetSawtooth(name, period, time, cycles, amplitude)


# =============================================================================
# 正弦函数
# =============================================================================

def get_func_th_sine(model, name: str) -> SineParams:
    """
    获取正弦时程函数参数
    
    Args:
        model: SapModel 对象
        name: 函数名称
        
    Returns:
        SineParams 参数对象
    """
    result = model.Func.FuncTH.GetSine(name, 0.0, 0, 0, 0.0)
    if isinstance(result, (list, tuple)) and len(result) >= 5:
        return SineParams(
            period=result[0],
            steps=result[1],
            cycles=result[2],
            amplitude=result[3],
        )
    return SineParams()


def set_func_th_sine(
    model,
    name: str,
    period: float,
    steps: int,
    cycles: int,
    amplitude: float
) -> int:
    """
    设置正弦时程函数
    
    Args:
        model: SapModel 对象
        name: 函数名称
        period: 周期 [s]
        steps: 每周期步数
        cycles: 周期数
        amplitude: 幅值
        
    Returns:
        0 表示成功
    """
    return model.Func.FuncTH.SetSine(name, period, steps, cycles, amplitude)


# =============================================================================
# 三角波函数
# =============================================================================

def get_func_th_triangular(model, name: str) -> TriangularParams:
    """
    获取三角波时程函数参数
    
    Args:
        model: SapModel 对象
        name: 函数名称
        
    Returns:
        TriangularParams 参数对象
    """
    result = model.Func.FuncTH.GetTriangular(name, 0.0, 0, 0.0)
    if isinstance(result, (list, tuple)) and len(result) >= 4:
        return TriangularParams(
            period=result[0],
            cycles=result[1],
            amplitude=result[2],
        )
    return TriangularParams()


def set_func_th_triangular(
    model,
    name: str,
    period: float,
    cycles: int,
    amplitude: float
) -> int:
    """
    设置三角波时程函数
    
    Args:
        model: SapModel 对象
        name: 函数名称
        period: 周期 [s]
        cycles: 周期数
        amplitude: 幅值
        
    Returns:
        0 表示成功
    """
    return model.Func.FuncTH.SetTriangular(name, period, cycles, amplitude)


# =============================================================================
# 用户定义函数
# =============================================================================

def get_func_th_user(model, name: str) -> Tuple[List[float], List[float]]:
    """
    获取用户定义时程函数数据
    
    Args:
        model: SapModel 对象
        name: 函数名称
        
    Returns:
        (times, values) 元组
        - times: 时间列表 [s]
        - values: 值列表
    """
    result = model.Func.FuncTH.GetUser(name, 0, [], [])
    if isinstance(result, (list, tuple)) and len(result) >= 4:
        num = result[0]
        times = result[1]
        values = result[2]
        ret = result[-1]
        
        if ret == 0 and num > 0:
            return (list(times) if times else [], list(values) if values else [])
    return ([], [])


def set_func_th_user(
    model,
    name: str,
    times: List[float],
    values: List[float]
) -> int:
    """
    设置用户定义时程函数
    
    Args:
        model: SapModel 对象
        name: 函数名称
        times: 时间列表 [s]
        values: 值列表
        
    Returns:
        0 表示成功
    """
    num = len(times)
    return model.Func.FuncTH.SetUser(name, num, times, values)


# =============================================================================
# 用户周期函数
# =============================================================================

def get_func_th_user_periodic(model, name: str) -> Tuple[List[float], List[float], int]:
    """
    获取用户周期时程函数数据
    
    Args:
        model: SapModel 对象
        name: 函数名称
        
    Returns:
        (times, values, cycles) 元组
        - times: 时间列表 [s]
        - values: 值列表
        - cycles: 周期数
    """
    result = model.Func.FuncTH.GetUserPeriodic(name, 0, [], [], 0)
    if isinstance(result, (list, tuple)) and len(result) >= 5:
        num = result[0]
        times = result[1]
        values = result[2]
        cycles = result[3]
        ret = result[-1]
        
        if ret == 0 and num > 0:
            return (
                list(times) if times else [],
                list(values) if values else [],
                cycles
            )
    return ([], [], 0)


def set_func_th_user_periodic(
    model,
    name: str,
    times: List[float],
    values: List[float],
    cycles: int
) -> int:
    """
    设置用户周期时程函数
    
    Args:
        model: SapModel 对象
        name: 函数名称
        times: 时间列表 [s]
        values: 值列表
        cycles: 周期数
        
    Returns:
        0 表示成功
    """
    num = len(times)
    return model.Func.FuncTH.SetUserPeriodic(name, num, times, values, cycles)
