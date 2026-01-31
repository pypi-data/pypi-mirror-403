# -*- coding: utf-8 -*-
"""
PySap2000 - SAP2000 Python API 封装库
参考 dlubal.api 设计模式

Usage:
    from PySap2000 import Application
    from PySap2000.structure_core import Point, Frame, Material, Section
    from PySap2000.types_for_points import PointSupport, PointSupportType
    from PySap2000.loads import PointLoad, FrameDistributedLoad
    from PySap2000.loading import LoadPattern, LoadCombination
    from PySap2000.results import PointResults, FrameResults
    from PySap2000.global_parameters import Units, UnitSystem, ModelSettings
    from PySap2000.types_for_steel_design import SteelDesign, SteelDesignCode
    
    # 连接 SAP2000
    with Application() as app:
        # 设置单位
        Units.set_present_units(app.model, UnitSystem.KN_M_C)
        
        # 创建节点
        app.create_object(Point(no=1, x=0, y=0, z=0))
        app.create_object(Point(no=2, x=10, y=0, z=0))
        
        # 创建框架
        app.create_object(Frame(no=1, start_point=1, end_point=2, section="W14X30"))
        
        # 添加支座
        app.create_object(PointSupport(points=[1], type=PointSupportType.FIXED))
        
        # 添加荷载
        app.create_object(PointLoad(load_pattern="DEAD", points=[2], fz=-10))
        
        # 运行分析
        app.calculate()
        
        # 钢结构设计
        SteelDesign.set_code(app.model, SteelDesignCode.AISC_360_16)
        SteelDesign.start_design(app.model)
        
        # 获取结果
        results = PointResults(app.model)
        disp = results.get_displacement("2", load_case="DEAD")
        print(f"位移: {disp.uz}")

Author: JIANGYAO-AISA
Version: 2.0.0
"""

__version__ = "2.0.12"
__author__ = "JIANGYAO-AISA"

# 核心类
from .application import Application

# 异常
from .exceptions import (
    PySap2000Error,
    ConnectionError,
    ObjectError,
    PointError,
    FrameError,
    AreaError,
    CableError,
    LinkError,
    SurfaceError,
    MaterialError,
    SectionError,
    LoadError,
    AnalysisError,
    ResultError,
    # 弃用的异常（保留向后兼容）
    NodeError,
    MemberError,
)

# 配置和日志
from .config import config
from .logger import logger, setup_logger, get_logger

# 工具类
from .utils import Result, Ok, Err, BatchResult, deprecated

__all__ = [
    # 版本信息
    '__version__',
    '__author__',
    
    # 核心类
    'Application',
    
    # 配置和日志
    'config',
    'logger',
    'setup_logger',
    'get_logger',
    
    # 工具类
    'Result',
    'Ok',
    'Err',
    'BatchResult',
    'deprecated',
    
    # 异常（推荐使用）
    'PySap2000Error',
    'ConnectionError',
    'ObjectError',
    'PointError',
    'FrameError',
    'AreaError',
    'CableError',
    'LinkError',
    'SurfaceError',
    'MaterialError',
    'SectionError',
    'LoadError',
    'AnalysisError',
    'ResultError',
    
    # 异常（弃用，保留向后兼容）
    'NodeError',
    'MemberError',
]
