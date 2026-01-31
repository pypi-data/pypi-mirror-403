# -*- coding: utf-8 -*-
"""
批量操作工具 - 批量修改截面、荷载、约束

重构: 复用 PySap2000 各模块
"""

import json
from langchain.tools import tool

from .base import get_sap_model, to_json, success_response, error_response, safe_sap_call

# 导入 PySap2000 封装
from PySap2000.structure_core import Frame, Point
from PySap2000.frame import set_frame_section, get_frame_section
from PySap2000.group import Group, GroupObjectType
from PySap2000.loads import set_frame_load_distributed, FrameLoadDirection
from PySap2000.point import set_point_restraint


@tool
@safe_sap_call
def batch_set_section(
    new_section: str,
    old_section: str = "",
    group_name: str = "",
    frame_names: str = ""
) -> str:
    """
    批量修改杆件截面。可以按原截面、组名或杆件列表筛选。
    
    Args:
        new_section: 新截面名称
        old_section: 原截面名称（可选，只修改该截面的杆件）
        group_name: 组名（可选，只修改该组内的杆件）
        frame_names: 杆件名称列表，逗号分隔（可选，如 "1,2,3"）
    """
    model = get_sap_model()
    model.SetModelIsLocked(False)
    
    # 获取要修改的杆件列表
    target_frames = []
    
    if frame_names:
        target_frames = [f.strip() for f in frame_names.split(",") if f.strip()]
    elif group_name:
        try:
            group = Group.get_by_name(model, group_name)
            assignments = group.get_assignments(model)
            target_frames = [n for t, n in assignments if t == GroupObjectType.FRAME.value]
        except:
            return error_response(f"组 '{group_name}' 不存在")
    elif old_section:
        all_frames = Frame.get_name_list(model)
        for fname in all_frames:
            sec = get_frame_section(model, fname)
            if sec == old_section:
                target_frames.append(fname)
    else:
        return error_response("请指定筛选条件：old_section、group_name 或 frame_names")
    
    if not target_frames:
        return error_response("未找到符合条件的杆件")
    
    # 批量修改
    success_count = 0
    for fname in target_frames:
        ret = set_frame_section(model, fname, new_section)
        if ret == 0:
            success_count += 1
    
    return success_response(
        "批量修改完成",
        新截面=new_section,
        成功=success_count,
        总数=len(target_frames)
    )


@tool
@safe_sap_call
def batch_add_distributed_load(
    load_pattern: str,
    value: float,
    direction: int = 6,
    group_name: str = "",
    section_name: str = "",
    frame_names: str = ""
) -> str:
    """
    批量添加杆件均布荷载。可以按组名、截面或杆件列表筛选。
    
    Args:
        load_pattern: 荷载模式名称
        value: 荷载值（负值向下）
        direction: 荷载方向 (1=局部1, 2=局部2, 3=局部3, 4=X, 5=Y, 6=Z/重力)
        group_name: 组名（可选）
        section_name: 截面名称（可选）
        frame_names: 杆件名称列表，逗号分隔（可选）
    """
    model = get_sap_model()
    model.SetModelIsLocked(False)
    
    # 获取目标杆件
    target_frames = []
    
    if frame_names:
        target_frames = [f.strip() for f in frame_names.split(",") if f.strip()]
    elif group_name:
        try:
            group = Group.get_by_name(model, group_name)
            assignments = group.get_assignments(model)
            target_frames = [n for t, n in assignments if t == GroupObjectType.FRAME.value]
        except:
            return error_response(f"组 '{group_name}' 不存在")
    elif section_name:
        all_frames = Frame.get_name_list(model)
        for fname in all_frames:
            sec = get_frame_section(model, fname)
            if sec == section_name:
                target_frames.append(fname)
    else:
        return error_response("请指定筛选条件：group_name、section_name 或 frame_names")
    
    if not target_frames:
        return error_response("未找到符合条件的杆件")
    
    # 映射方向
    dir_map = {
        1: FrameLoadDirection.LOCAL_1,
        2: FrameLoadDirection.LOCAL_2,
        3: FrameLoadDirection.LOCAL_3,
        4: FrameLoadDirection.GLOBAL_X,
        5: FrameLoadDirection.GLOBAL_Y,
        6: FrameLoadDirection.GLOBAL_Z,
    }
    load_dir = dir_map.get(direction, FrameLoadDirection.GLOBAL_Z)
    
    # 批量添加荷载
    success_count = 0
    for fname in target_frames:
        ret = set_frame_load_distributed(
            model, fname, load_pattern,
            load_type=1, direction=load_dir,
            dist1=0.0, dist2=1.0, val1=value, val2=value
        )
        if ret == 0:
            success_count += 1
    
    return success_response(
        "批量添加荷载完成",
        荷载模式=load_pattern,
        荷载值=value,
        成功=success_count,
        总数=len(target_frames)
    )


@tool
@safe_sap_call
def batch_set_restraint(
    point_names: str = "",
    group_name: str = "",
    z_level: float = None,
    u1: bool = False, u2: bool = False, u3: bool = False,
    r1: bool = False, r2: bool = False, r3: bool = False
) -> str:
    """
    批量设置节点约束（支座）。可以按节点列表、组名或 Z 坐标筛选。
    
    Args:
        point_names: 节点名称列表，逗号分隔（可选）
        group_name: 组名（可选）
        z_level: Z 坐标值（可选，选择该高度的所有节点）
        u1, u2, u3: 是否约束 X、Y、Z 方向平动
        r1, r2, r3: 是否约束绕 X、Y、Z 轴转动
    """
    model = get_sap_model()
    model.SetModelIsLocked(False)
    
    # 获取目标节点
    target_points = []
    
    if point_names:
        target_points = [p.strip() for p in point_names.split(",") if p.strip()]
    elif group_name:
        try:
            group = Group.get_by_name(model, group_name)
            assignments = group.get_assignments(model)
            target_points = [n for t, n in assignments if t == GroupObjectType.POINT.value]
        except:
            return error_response(f"组 '{group_name}' 不存在")
    elif z_level is not None:
        all_points = Point.get_name_list(model)
        tolerance = 0.001
        for pname in all_points:
            point = Point.get_by_name(model, pname)
            if abs(point.z - z_level) < tolerance:
                target_points.append(pname)
    else:
        return error_response("请指定筛选条件：point_names、group_name 或 z_level")
    
    if not target_points:
        return error_response("未找到符合条件的节点")
    
    # 批量设置约束
    restraints = (u1, u2, u3, r1, r2, r3)
    success_count = 0
    for pname in target_points:
        ret = set_point_restraint(model, pname, restraints)
        if ret == 0:
            success_count += 1
    
    dof_names = ["U1", "U2", "U3", "R1", "R2", "R3"]
    active_dofs = [dof_names[i] for i in range(6) if restraints[i]]
    
    return success_response(
        "批量设置约束完成",
        约束自由度=active_dofs if active_dofs else "无",
        成功=success_count,
        总数=len(target_points)
    )
