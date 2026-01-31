# -*- coding: utf-8 -*-
"""
local_axes.py - 杆件局部坐标轴相关函数

用于设置杆件的局部坐标轴方向

SAP2000 API:
- FrameObj.SetLocalAxes(Name, Ang, ItemType)
- FrameObj.GetLocalAxes(Name, Ang, Advanced)
- FrameObj.GetTransformationMatrix(Name, Value[], IsGlobal)
"""

from typing import Tuple, Optional, List
from .enums import ItemType
from .data_classes import FrameLocalAxesData


def set_frame_local_axes(
    model,
    frame_name: str,
    angle: float,
    item_type: ItemType = ItemType.OBJECT
) -> int:
    """
    设置杆件局部轴角度
    
    局部2和3轴绕正局部1轴旋转的角度。
    正角度从局部+1轴方向看为逆时针。
    
    Args:
        model: SapModel 对象
        frame_name: 杆件名称
        angle: 旋转角度 [deg]
        item_type: 操作范围
    
    Returns:
        0 表示成功
    
    Example:
        # 旋转局部轴 30 度
        set_frame_local_axes(model, "1", 30)
        
        # 旋转局部轴 90 度 (常用于斜撑)
        set_frame_local_axes(model, "B1", 90)
    """
    return model.FrameObj.SetLocalAxes(str(frame_name), angle, int(item_type))


def get_frame_local_axes(
    model,
    frame_name: str
) -> Optional[FrameLocalAxesData]:
    """
    获取杆件局部轴角度
    
    Args:
        model: SapModel 对象
        frame_name: 杆件名称
    
    Returns:
        FrameLocalAxesData 对象，失败返回 None
    
    Example:
        axes = get_frame_local_axes(model, "1")
        if axes:
            print(f"局部轴角度: {axes.angle}°")
    """
    try:
        result = model.FrameObj.GetLocalAxes(str(frame_name))
        if isinstance(result, (list, tuple)) and len(result) >= 3:
            return FrameLocalAxesData(
                frame_name=str(frame_name),
                angle=result[0],
                advanced=result[1]
            )
    except Exception:
        pass
    return None


def get_frame_transformation_matrix(
    model,
    frame_name: str,
    is_global: bool = True
) -> Optional[List[float]]:
    """
    获取杆件变换矩阵
    
    返回 3x3 变换矩阵（9个值），用于局部坐标和全局坐标转换。
    
    Args:
        model: SapModel 对象
        frame_name: 杆件名称
        is_global: True=全局坐标系, False=当前坐标系
    
    Returns:
        9个浮点数的列表 (3x3矩阵按行排列)，失败返回 None
    
    Example:
        matrix = get_frame_transformation_matrix(model, "1")
        if matrix:
            # matrix[0:3] = 局部1轴在全局坐标系中的方向
            # matrix[3:6] = 局部2轴在全局坐标系中的方向
            # matrix[6:9] = 局部3轴在全局坐标系中的方向
            print(f"局部1轴方向: {matrix[0:3]}")
    """
    try:
        result = model.FrameObj.GetTransformationMatrix(
            str(frame_name), [0.0] * 12, is_global
        )
        if isinstance(result, (list, tuple)) and len(result) >= 2:
            values = result[0]
            if values and len(values) >= 9:
                return list(values[:9])
    except Exception:
        pass
    return None
