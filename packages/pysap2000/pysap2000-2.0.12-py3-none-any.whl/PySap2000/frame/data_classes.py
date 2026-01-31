# -*- coding: utf-8 -*-
"""
data_classes.py - 杆件相关数据类

用于封装 SAP2000 FrameObj API 的输入输出数据

注意: 荷载相关数据类已移至 loads/frame_load.py
"""

from dataclasses import dataclass
from typing import Tuple, Optional


@dataclass
class FrameReleaseData:
    """
    杆件端部释放数据
    
    Attributes:
        frame_name: 杆件名称
        release_i: I端释放 (U1, U2, U3, R1, R2, R3)
        release_j: J端释放 (U1, U2, U3, R1, R2, R3)
        start_value: I端部分固定刚度值
        end_value: J端部分固定刚度值
    """
    frame_name: str
    release_i: Tuple[bool, bool, bool, bool, bool, bool] = (False,) * 6
    release_j: Tuple[bool, bool, bool, bool, bool, bool] = (False,) * 6
    start_value: Tuple[float, ...] = (0.0,) * 6
    end_value: Tuple[float, ...] = (0.0,) * 6


@dataclass
class FrameModifierData:
    """
    杆件截面修改器数据
    
    8个修改器值 (默认值都是1.0):
        [0] = 截面面积修改器 (A)
        [1] = 局部2方向剪切面积修改器 (As2)
        [2] = 局部3方向剪切面积修改器 (As3)
        [3] = 扭转常数修改器 (J)
        [4] = 局部2轴惯性矩修改器 (I22)
        [5] = 局部3轴惯性矩修改器 (I33)
        [6] = 质量修改器
        [7] = 重量修改器
    """
    frame_name: str
    area: float = 1.0       # A
    shear_2: float = 1.0    # As2
    shear_3: float = 1.0    # As3
    torsion: float = 1.0    # J
    inertia_22: float = 1.0 # I22
    inertia_33: float = 1.0 # I33
    mass: float = 1.0       # Mass
    weight: float = 1.0     # Weight
    
    def to_tuple(self) -> Tuple[float, ...]:
        """转换为元组格式"""
        return (
            self.area, self.shear_2, self.shear_3, self.torsion,
            self.inertia_22, self.inertia_33, self.mass, self.weight
        )
    
    @classmethod
    def from_tuple(cls, frame_name: str, values: Tuple[float, ...]) -> 'FrameModifierData':
        """从元组创建"""
        return cls(
            frame_name=frame_name,
            area=values[0] if len(values) > 0 else 1.0,
            shear_2=values[1] if len(values) > 1 else 1.0,
            shear_3=values[2] if len(values) > 2 else 1.0,
            torsion=values[3] if len(values) > 3 else 1.0,
            inertia_22=values[4] if len(values) > 4 else 1.0,
            inertia_33=values[5] if len(values) > 5 else 1.0,
            mass=values[6] if len(values) > 6 else 1.0,
            weight=values[7] if len(values) > 7 else 1.0,
        )


@dataclass
class FrameLocalAxesData:
    """
    杆件局部坐标轴数据
    
    Attributes:
        frame_name: 杆件名称
        angle: 局部2和3轴绕正局部1轴旋转的角度 [deg]
        advanced: 是否使用高级局部轴参数
    """
    frame_name: str
    angle: float = 0.0
    advanced: bool = False


@dataclass
class FrameMassData:
    """
    杆件质量数据
    
    Attributes:
        frame_name: 杆件名称
        mass_per_length: 单位长度质量 [M/L]
    """
    frame_name: str
    mass_per_length: float = 0.0
