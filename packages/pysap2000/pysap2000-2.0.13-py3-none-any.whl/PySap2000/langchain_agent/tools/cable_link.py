# -*- coding: utf-8 -*-
"""
索单元和连接单元操作工具

重构: 复用 PySap2000.structure_core 中的 Cable 和 Link
"""

from typing import Optional
from langchain.tools import tool

from .base import get_sap_model, to_json, success_response, error_response, format_result_list, safe_sap_call

# 导入 PySap2000 封装
from PySap2000.structure_core import Cable, Link
from PySap2000.group import Group, GroupObjectType


# =============================================================================
# 索单元操作
# =============================================================================

@tool
@safe_sap_call
def create_cable(start_point: str, end_point: str, section: str = "Default") -> str:
    """
    创建索单元。
    
    Args:
        start_point: 起始节点名称
        end_point: 结束节点名称
        section: 索截面属性名称，默认 "Default"
    """
    model = get_sap_model()
    model.SetModelIsLocked(False)
    
    cable = Cable(start_point=start_point, end_point=end_point, section=section)
    ret = cable._create(model)
    
    if ret == 0:
        return success_response(
            "索单元创建成功",
            索单元=cable.no,
            起点=start_point,
            终点=end_point,
            截面=section
        )
    return error_response(f"创建索单元失败，返回码 {ret}")


@tool
@safe_sap_call
def delete_cable(cable_name: str) -> str:
    """
    删除索单元。
    
    Args:
        cable_name: 索单元名称
    """
    model = get_sap_model()
    model.SetModelIsLocked(False)
    
    cable = Cable(no=cable_name)
    ret = cable._delete(model)
    
    if ret == 0:
        return success_response(f"索单元 '{cable_name}' 已删除")
    return error_response(f"删除索单元 '{cable_name}' 失败")


@tool
@safe_sap_call
def get_cable_info(cable_name: str) -> str:
    """
    获取索单元信息。
    
    Args:
        cable_name: 索单元名称
    """
    model = get_sap_model()
    
    try:
        cable = Cable.get_by_name(model, cable_name)
        return to_json({
            "索单元": cable_name,
            "起点": cable.start_point,
            "终点": cable.end_point,
            "属性": cable.section,
        })
    except Exception as e:
        return error_response(f"索单元 '{cable_name}' 不存在: {e}")


@tool
@safe_sap_call
def get_cables_in_group(group_name: str) -> str:
    """
    获取指定组中的所有索单元。
    
    Args:
        group_name: 组名
    """
    model = get_sap_model()
    
    try:
        group = Group.get_by_name(model, group_name)
        assignments = group.get_assignments(model)
        
        # 筛选索单元 (type == 3)
        cables = [
            name for obj_type, name in assignments
            if obj_type == GroupObjectType.CABLE.value
        ]
        
        return to_json({
            "组": group_name,
            "索单元数": len(cables),
            "索单元列表": cables[:50]
        })
    except Exception as e:
        return error_response(f"组 '{group_name}' 不存在: {e}")


@tool
@safe_sap_call
def get_cable_list() -> str:
    """获取模型中所有索单元的名称列表。"""
    model = get_sap_model()
    cables = Cable.get_name_list(model)
    return format_result_list(cables, "索单元", max_items=100)


# =============================================================================
# 连接单元操作
# =============================================================================

@tool
@safe_sap_call
def create_link(start_point: str, end_point: str, section: str = "Default") -> str:
    """
    创建连接单元（弹簧/阻尼器）。
    
    Args:
        start_point: 起始节点名称
        end_point: 结束节点名称
        section: 连接属性名称，默认 "Default"
    """
    model = get_sap_model()
    model.SetModelIsLocked(False)
    
    link = Link(start_point=start_point, end_point=end_point, section=section)
    ret = link._create(model)
    
    if ret == 0:
        return success_response(
            "连接单元创建成功",
            连接单元=link.no,
            起点=start_point,
            终点=end_point,
            属性=section
        )
    return error_response(f"创建连接单元失败，返回码 {ret}")


@tool
@safe_sap_call
def delete_link(link_name: str) -> str:
    """
    删除连接单元。
    
    Args:
        link_name: 连接单元名称
    """
    model = get_sap_model()
    model.SetModelIsLocked(False)
    
    link = Link(no=link_name)
    ret = link._delete(model)
    
    if ret == 0:
        return success_response(f"连接单元 '{link_name}' 已删除")
    return error_response(f"删除连接单元 '{link_name}' 失败")


@tool
@safe_sap_call
def get_link_info(link_name: str) -> str:
    """
    获取连接单元信息。
    
    Args:
        link_name: 连接单元名称
    """
    model = get_sap_model()
    
    try:
        link = Link.get_by_name(model, link_name)
        return to_json({
            "连接单元": link_name,
            "起点": link.start_point,
            "终点": link.end_point,
            "属性": link.section,
        })
    except Exception as e:
        return error_response(f"连接单元 '{link_name}' 不存在: {e}")


@tool
@safe_sap_call
def get_link_list() -> str:
    """获取模型中所有连接单元的名称列表。"""
    model = get_sap_model()
    links = Link.get_name_list(model)
    return format_result_list(links, "连接单元", max_items=100)


@tool
@safe_sap_call
def get_links_in_group(group_name: str) -> str:
    """
    获取指定组中的所有连接单元。
    
    Args:
        group_name: 组名
    """
    model = get_sap_model()
    
    try:
        group = Group.get_by_name(model, group_name)
        assignments = group.get_assignments(model)
        
        # 筛选连接单元 (type == 7)
        links = [
            name for obj_type, name in assignments
            if obj_type == GroupObjectType.LINK.value
        ]
        
        return to_json({
            "组": group_name,
            "连接单元数": len(links),
            "连接单元列表": links[:50]
        })
    except Exception as e:
        return error_response(f"组 '{group_name}' 不存在: {e}")
