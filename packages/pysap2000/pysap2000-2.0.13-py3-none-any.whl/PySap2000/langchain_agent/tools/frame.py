# -*- coding: utf-8 -*-
"""
杆件操作工具 - 创建、查询、修改杆件

重构: 复用 PySap2000 已有封装
- structure_core.Frame: 杆件数据类
- frame: 杆件属性函数 (release, property, group 等)
"""

from langchain.tools import tool

from .base import (
    get_sap_model, to_json, success_response, error_response, 
    format_result_list, safe_sap_call
)
from .history import add_to_history

# 导入 PySap2000 封装
from PySap2000.structure_core import Frame
from PySap2000.frame import (
    set_frame_release, get_frame_release, FrameReleaseType,
    set_frame_section as _set_frame_section, get_frame_section,
    add_frame_to_group as _add_frame_to_group,
)
from PySap2000.group import Group, GroupObjectType


@tool
@safe_sap_call
def get_frame_info(frame_name: str) -> str:
    """
    获取指定杆件的详细信息，包括端点、截面、长度、材料等。
    
    Args:
        frame_name: 杆件名称/编号
    """
    model = get_sap_model()
    
    try:
        frame = Frame.get_by_name(model, frame_name)
        return to_json({
            "杆件": frame_name,
            "起点": frame.start_point,
            "终点": frame.end_point,
            "截面": frame.section,
            "截面类型": frame.section_type_name,
            "长度": frame.length,
            "局部轴角度": frame.local_axis_angle,
        }, indent=2)
    except Exception as e:
        return error_response(f"杆件 '{frame_name}' 不存在或获取失败: {e}")


@tool
@safe_sap_call
def create_frame(point_i: str, point_j: str, section: str = "", name: str = "") -> str:
    """
    创建杆件，连接两个已存在的节点。
    
    Args:
        point_i: 起点节点名称
        point_j: 终点节点名称
        section: 截面名称（可选）
        name: 杆件名称（可选，不填则自动编号）
    """
    model = get_sap_model()
    model.SetModelIsLocked(False)
    
    frame = Frame(
        no=name if name else None,
        start_point=point_i,
        end_point=point_j,
        section=section or "Default"
    )
    ret = frame._create(model)
    
    if ret == 0:
        return success_response(
            "创建成功",
            杆件名=frame.no,
            起点=point_i,
            终点=point_j,
            截面=section or "默认"
        )
    return error_response("创建杆件失败")


@tool
@safe_sap_call
def set_frame_section(frame_name: str, section_name: str) -> str:
    """
    修改杆件的截面。支持撤回操作。
    
    Args:
        frame_name: 杆件名称/编号
        section_name: 新截面名称
    """
    model = get_sap_model()
    model.SetModelIsLocked(False)
    
    # 获取旧截面用于撤回
    old_section = get_frame_section(model, frame_name)
    
    # 使用 PySap2000 封装设置截面
    ret = _set_frame_section(model, frame_name, section_name)
    
    if ret == 0:
        # 记录到操作历史（用于撤回）
        add_to_history(
            tool_name="set_frame_section",
            undo_action="set_frame_section",
            undo_args={"frame_name": frame_name, "section_name": old_section},
            description=f"修改杆件 {frame_name} 截面: {old_section} → {section_name}"
        )
        return success_response(
            "修改成功",
            杆件=frame_name,
            原截面=old_section,
            新截面=section_name
        )
    return error_response(f"修改失败，截面 '{section_name}' 可能不存在")


@tool
@safe_sap_call
def delete_frame(frame_name: str) -> str:
    """
    删除指定杆件。
    
    Args:
        frame_name: 杆件名称/编号
    """
    model = get_sap_model()
    model.SetModelIsLocked(False)
    
    frame = Frame(no=frame_name)
    ret = frame._delete(model)
    
    if ret == 0:
        return success_response(f"杆件 '{frame_name}' 已删除")
    return error_response(f"删除杆件 '{frame_name}' 失败")


@tool
@safe_sap_call
def get_frames_in_group(group_name: str) -> str:
    """
    获取指定组中的所有杆件。
    
    Args:
        group_name: 组名
    """
    model = get_sap_model()
    
    try:
        group = Group.get_by_name(model, group_name)
        assignments = group.get_assignments(model)
        
        # 筛选杆件 (type == 2)
        frames = [
            name for obj_type, name in assignments 
            if obj_type == GroupObjectType.FRAME.value
        ]
        
        return to_json({
            "组": group_name,
            "杆件数": len(frames),
            "杆件列表": frames[:50]
        })
    except Exception as e:
        return error_response(f"组 '{group_name}' 不存在: {e}")


@tool
@safe_sap_call
def get_frame_list() -> str:
    """获取模型中所有杆件的名称列表。"""
    model = get_sap_model()
    frames = Frame.get_name_list(model)
    return format_result_list(frames, "杆件")


@tool
@safe_sap_call
def set_frame_release(frame_name: str, i_end: str = "", j_end: str = "") -> str:
    """
    设置杆件端部释放（铰接）。
    
    Args:
        frame_name: 杆件名称
        i_end: I端释放 ("pin"=铰接, "moment"=释放弯矩, ""=固接)
        j_end: J端释放 ("pin"=铰接, "moment"=释放弯矩, ""=固接)
    """
    model = get_sap_model()
    model.SetModelIsLocked(False)
    
    # 映射释放类型
    release_map = {
        "pin": FrameReleaseType.BOTH_HINGED,
        "moment": FrameReleaseType.BOTH_HINGED,  # 简化处理
        "": FrameReleaseType.BOTH_FIXED,
    }
    
    # 根据两端设置确定释放类型
    if i_end.lower() == "pin" and j_end.lower() == "pin":
        release_type = FrameReleaseType.BOTH_HINGED
    elif i_end.lower() == "pin":
        release_type = FrameReleaseType.I_END_HINGED
    elif j_end.lower() == "pin":
        release_type = FrameReleaseType.J_END_HINGED
    else:
        release_type = FrameReleaseType.BOTH_FIXED
    
    # 使用 PySap2000 封装
    from PySap2000.frame.release import set_frame_release as _set_release
    ret = _set_release(model, frame_name, release_type)
    
    if ret == 0:
        return success_response(
            f"杆件 '{frame_name}' 端部释放设置成功",
            I端=i_end or "固接",
            J端=j_end or "固接"
        )
    return error_response("设置端部释放失败")


@tool
@safe_sap_call
def get_frame_release(frame_name: str) -> str:
    """
    获取杆件端部释放状态。
    
    Args:
        frame_name: 杆件名称
    """
    model = get_sap_model()
    
    # 使用 PySap2000 封装
    from PySap2000.frame.release import get_frame_release as _get_release
    release = _get_release(model, frame_name)
    
    if release is None:
        return error_response(f"获取杆件 '{frame_name}' 端部释放失败")
    
    dof_names = ["轴力P", "剪力V2", "剪力V3", "扭矩T", "弯矩M2", "弯矩M3"]
    
    i_released = [dof_names[i] for i in range(6) if release.release_i[i]]
    j_released = [dof_names[i] for i in range(6) if release.release_j[i]]
    
    return to_json({
        "杆件": frame_name,
        "I端释放": i_released if i_released else "无",
        "J端释放": j_released if j_released else "无"
    })
