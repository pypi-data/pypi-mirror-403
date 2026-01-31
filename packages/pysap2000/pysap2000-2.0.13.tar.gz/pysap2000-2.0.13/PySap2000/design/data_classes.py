# -*- coding: utf-8 -*-
"""
design/data_classes.py - 设计模块数据类

钢结构设计相关数据类。
"""

from dataclasses import dataclass, field
from typing import List, Optional

from .enums import RatioType


@dataclass
class SteelSummaryResult:
    """钢结构设计汇总结果
    
    单个框架对象的设计结果。
    
    Attributes:
        frame_name: 框架对象名称
        ratio: 控制应力比或承载力比
        ratio_type: 应力比类型 (1-6)
        location: 控制位置距 I 端的距离
        combo_name: 控制组合名称
        error_summary: 错误信息
        warning_summary: 警告信息
    """
    frame_name: str
    ratio: float
    ratio_type: RatioType
    location: float
    combo_name: str
    error_summary: str = ""
    warning_summary: str = ""
    
    @property
    def passed(self) -> bool:
        """是否通过设计检查（应力比 <= 1.0）"""
        return self.ratio <= 1.0
    
    @property
    def ratio_type_name(self) -> str:
        """应力比类型名称"""
        names = {
            RatioType.PMM: "PMM",
            RatioType.MAJOR_SHEAR: "Major Shear",
            RatioType.MINOR_SHEAR: "Minor Shear",
            RatioType.MAJOR_BEAM_COLUMN: "Major Beam-Column",
            RatioType.MINOR_BEAM_COLUMN: "Minor Beam-Column",
            RatioType.OTHER: "Other",
        }
        return names.get(self.ratio_type, "Unknown")


@dataclass
class VerifyPassedResult:
    """设计验证结果
    
    Attributes:
        total_count: 未通过或未检查的对象总数
        failed_count: 未通过设计检查的对象数
        unchecked_count: 尚未检查的对象数
        frame_names: 未通过或未检查的对象名称列表
    """
    total_count: int
    failed_count: int
    unchecked_count: int
    frame_names: List[str] = field(default_factory=list)
    
    @property
    def all_passed(self) -> bool:
        """是否全部通过"""
        return self.total_count == 0
