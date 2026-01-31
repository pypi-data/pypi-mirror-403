# -*- coding: utf-8 -*-
"""
编辑操作工具 - 移动、复制、镜像、分割、合并

重构: 复用 PySap2000.edit 模块
"""

from langchain.tools import tool

from .base import get_sap_model, success_response, error_response, safe_sap_call

# 导入 PySap2000 封装
from PySap2000.edit import (
    move_selected,
    replicate_linear as _replicate_linear,
    replicate_mirror as _replicate_mirror,
    replicate_radial as _replicate_radial,
    divide_frame_by_ratio,
    merge_point,
)
from PySap2000.frame.selection import select_frame
from PySap2000.selection import clear_selection


@tool
@safe_sap_call
def move_selected_objects(dx: float = 0, dy: float = 0, dz: float = 0) -> str:
    """
    移动当前选中的对象。
    
    Args:
        dx: X 方向移动距离
        dy: Y 方向移动距离
        dz: Z 方向移动距离
    """
    model = get_sap_model()
    model.SetModelIsLocked(False)
    
    ret = move_selected(model, dx, dy, dz)
    
    if ret == 0:
        return success_response("移动成功", 移动量={"dX": dx, "dY": dy, "dZ": dz})
    return error_response("移动失败，请先选中对象")


@tool
@safe_sap_call
def replicate_linear(dx: float, dy: float, dz: float, num: int = 1) -> str:
    """
    线性复制当前选中的对象。
    
    Args:
        dx: X 方向间距
        dy: Y 方向间距
        dz: Z 方向间距
        num: 复制数量
    """
    model = get_sap_model()
    model.SetModelIsLocked(False)
    
    ret = _replicate_linear(model, dx, dy, dz, num)
    
    if ret == 0:
        return success_response("线性复制成功", 间距={"dX": dx, "dY": dy, "dZ": dz}, 数量=num)
    return error_response("复制失败，请先选中对象")


@tool
@safe_sap_call
def replicate_mirror(plane: str = "XY", x: float = 0, y: float = 0, z: float = 0) -> str:
    """
    镜像复制当前选中的对象。
    
    Args:
        plane: 镜像平面 (XY, XZ, YZ)
        x: 镜像平面经过的 X 坐标
        y: 镜像平面经过的 Y 坐标
        z: 镜像平面经过的 Z 坐标
    """
    model = get_sap_model()
    model.SetModelIsLocked(False)
    
    # 映射平面代码
    plane_map = {"XY": 3, "XZ": 2, "YZ": 1}
    plane_code = plane_map.get(plane.upper(), 3)
    
    ret = _replicate_mirror(model, plane_code, x, y, z)
    
    if ret == 0:
        return success_response("镜像复制成功", 镜像平面=plane, 平面位置={"X": x, "Y": y, "Z": z})
    return error_response("镜像失败，请先选中对象")


@tool
@safe_sap_call
def replicate_radial(cx: float, cy: float, cz: float, axis: str = "Z", angle: float = 30, num: int = 1) -> str:
    """
    环形复制当前选中的对象。
    
    Args:
        cx: 旋转中心 X 坐标
        cy: 旋转中心 Y 坐标
        cz: 旋转中心 Z 坐标
        axis: 旋转轴 (X, Y, Z)
        angle: 每次旋转角度（度）
        num: 复制数量
    """
    model = get_sap_model()
    model.SetModelIsLocked(False)
    
    # 映射轴代码
    axis_map = {"X": 1, "Y": 2, "Z": 3}
    axis_code = axis_map.get(axis.upper(), 3)
    
    ret = _replicate_radial(model, axis_code, cx, cy, cz, angle, num)
    
    if ret == 0:
        return success_response(
            "环形复制成功",
            旋转中心={"X": cx, "Y": cy, "Z": cz},
            旋转轴=axis,
            角度=angle,
            数量=num
        )
    return error_response("环形复制失败，请先选中对象")


@tool
@safe_sap_call
def divide_frame(frame_name: str, num_segments: int = 2) -> str:
    """
    将杆件等分为多段。
    
    Args:
        frame_name: 杆件名称
        num_segments: 分段数量
    """
    model = get_sap_model()
    model.SetModelIsLocked(False)
    
    # 先选中杆件
    clear_selection(model)
    select_frame(model, frame_name)
    
    # 使用 PySap2000 封装
    ret = divide_frame_by_ratio(model, num_segments)
    
    if ret == 0:
        return success_response(f"杆件 '{frame_name}' 已分为 {num_segments} 段")
    return error_response("分割杆件失败")


@tool
@safe_sap_call
def merge_points(tolerance: float = 0.001) -> str:
    """
    合并重合的节点。
    
    Args:
        tolerance: 合并容差（距离小于此值的节点将被合并）
    """
    model = get_sap_model()
    model.SetModelIsLocked(False)
    
    # 使用 PySap2000 封装
    ret = merge_point(model, tolerance)
    
    if ret == 0:
        return success_response(f"节点合并完成，容差: {tolerance}")
    return error_response("合并节点失败")
