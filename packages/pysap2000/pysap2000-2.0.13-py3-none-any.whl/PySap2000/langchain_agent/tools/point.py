# -*- coding: utf-8 -*-
"""
节点操作工具 - 创建、查询、删除节点

重构: 复用 PySap2000 已有封装
- structure_core.Point: 节点数据类
- point: 节点属性函数 (support, spring, mass 等)
"""

from langchain.tools import tool

from .base import (
    get_sap_model, to_json, success_response, error_response,
    format_result_list, safe_sap_call
)

# 导入 PySap2000 封装
from PySap2000.structure_core import Point
from PySap2000.point import (
    set_point_restraint as _set_point_restraint,
    get_point_restraint as _get_point_restraint,
    PointSupportType,
    set_point_support,
)
from PySap2000.group import Group, GroupObjectType


@tool
@safe_sap_call
def get_point_coordinates(point_name: str) -> str:
    """
    获取指定节点的坐标。
    
    Args:
        point_name: 节点名称/编号
    """
    model = get_sap_model()
    
    try:
        point = Point.get_by_name(model, point_name)
        return to_json({
            "节点": point_name,
            "X": point.x,
            "Y": point.y,
            "Z": point.z
        })
    except Exception as e:
        return error_response(f"节点 '{point_name}' 不存在: {e}")


@tool
@safe_sap_call
def create_point(x: float, y: float, z: float, name: str = "") -> str:
    """
    创建一个新节点。
    
    Args:
        x: X 坐标
        y: Y 坐标
        z: Z 坐标
        name: 节点名称（可选，不填则自动编号）
    """
    model = get_sap_model()
    model.SetModelIsLocked(False)
    
    point = Point(no=name if name else None, x=x, y=y, z=z)
    ret = point._create(model)
    
    if ret == 0:
        return success_response(
            "创建成功",
            节点名=point.no,
            坐标={"X": x, "Y": y, "Z": z}
        )
    return error_response("创建节点失败")


@tool
@safe_sap_call
def delete_point(point_name: str) -> str:
    """
    删除指定节点。
    
    Args:
        point_name: 节点名称/编号
    """
    model = get_sap_model()
    model.SetModelIsLocked(False)
    
    point = Point(no=point_name)
    ret = point._delete(model)
    
    if ret == 0:
        return success_response(f"节点 '{point_name}' 已删除")
    return error_response(f"删除节点 '{point_name}' 失败")


@tool
@safe_sap_call
def get_point_restraint(point_name: str) -> str:
    """
    获取节点的约束（支座）信息。
    
    Args:
        point_name: 节点名称/编号
    """
    model = get_sap_model()
    
    # 使用 PySap2000 封装
    restraints = _get_point_restraint(model, point_name)
    
    if restraints is None:
        return error_response(f"获取节点 '{point_name}' 约束失败")
    
    dof_names = ["U1", "U2", "U3", "R1", "R2", "R3"]
    restrained = [dof_names[i] for i in range(6) if restraints[i]]
    
    return to_json({
        "节点": point_name,
        "约束自由度": restrained if restrained else "无约束"
    })


@tool
@safe_sap_call
def set_point_restraint(
    point_name: str, u1: bool = False, u2: bool = False, u3: bool = False,
    r1: bool = False, r2: bool = False, r3: bool = False
) -> str:
    """
    设置节点的约束（支座）。
    
    Args:
        point_name: 节点名称
        u1: 是否约束 X 方向平动
        u2: 是否约束 Y 方向平动
        u3: 是否约束 Z 方向平动
        r1: 是否约束绕 X 轴转动
        r2: 是否约束绕 Y 轴转动
        r3: 是否约束绕 Z 轴转动
    """
    model = get_sap_model()
    model.SetModelIsLocked(False)
    
    # 使用 PySap2000 封装
    restraints = (u1, u2, u3, r1, r2, r3)
    ret = _set_point_restraint(model, point_name, restraints)
    
    if ret == 0:
        return success_response(f"节点 '{point_name}' 约束设置成功")
    return error_response("设置约束失败")


@tool
@safe_sap_call
def get_point_list() -> str:
    """获取模型中所有节点的名称列表。"""
    model = get_sap_model()
    points = Point.get_name_list(model)
    return format_result_list(points, "节点")


@tool
@safe_sap_call
def get_points_in_group(group_name: str) -> str:
    """
    获取指定组中的所有节点。
    
    Args:
        group_name: 组名
    """
    model = get_sap_model()
    
    try:
        group = Group.get_by_name(model, group_name)
        assignments = group.get_assignments(model)
        
        # 筛选节点 (type == 1)
        points = [
            name for obj_type, name in assignments
            if obj_type == GroupObjectType.POINT.value
        ]
        
        return to_json({
            "组": group_name,
            "节点数": len(points),
            "节点列表": points[:100]
        })
    except Exception as e:
        return error_response(f"组 '{group_name}' 不存在: {e}")
