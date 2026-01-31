# -*- coding: utf-8 -*-
"""
面单元操作工具 - 创建、查询、删除面单元

重构: 复用 PySap2000.structure_core.Area 和 PySap2000.area 模块
"""

from typing import List
from langchain.tools import tool

from .base import get_sap_model, to_json, success_response, error_response, format_result_list, safe_sap_call

# 导入 PySap2000 封装
from PySap2000.structure_core import Area
from PySap2000.group import Group, GroupObjectType
from PySap2000.area import set_area_property, add_area_to_group


@tool
@safe_sap_call
def create_area(points: List[str], section: str = "Default") -> str:
    """
    通过节点创建面单元。
    
    Args:
        points: 节点名称列表（至少3个节点，按顺序连接）
        section: 截面属性名称，默认 "Default"
    """
    model = get_sap_model()
    model.SetModelIsLocked(False)
    
    if len(points) < 3:
        return error_response("面单元至少需要3个节点")
    
    area = Area(points=points, section=section)
    ret = area._create(model)
    
    if ret == 0:
        return success_response(
            "面单元创建成功",
            面单元=area.no,
            节点=points,
            截面=section
        )
    return error_response(f"创建面单元失败，返回码 {ret}")


@tool
@safe_sap_call
def delete_area(area_name: str) -> str:
    """
    删除面单元。
    
    Args:
        area_name: 面单元名称
    """
    model = get_sap_model()
    model.SetModelIsLocked(False)
    
    area = Area(no=area_name)
    ret = area._delete(model)
    
    if ret == 0:
        return success_response(f"面单元 '{area_name}' 已删除")
    return error_response(f"删除面单元 '{area_name}' 失败")


@tool
@safe_sap_call
def set_area_section(area_name: str, section: str) -> str:
    """
    设置面单元的截面属性。
    
    Args:
        area_name: 面单元名称
        section: 截面属性名称
    """
    model = get_sap_model()
    model.SetModelIsLocked(False)
    
    ret = set_area_property(model, area_name, section)
    
    if ret == 0:
        return success_response(
            "截面设置成功",
            面单元=area_name,
            截面=section
        )
    return error_response(f"设置截面失败")


@tool
@safe_sap_call
def add_area_to_group_tool(area_name: str, group_name: str) -> str:
    """
    将面单元添加到组。
    
    Args:
        area_name: 面单元名称
        group_name: 组名
    """
    model = get_sap_model()
    
    ret = add_area_to_group(model, area_name, group_name)
    
    if ret == 0:
        return success_response(
            "添加成功",
            面单元=area_name,
            组=group_name
        )
    return error_response(f"添加面单元到组失败")


@tool
@safe_sap_call
def get_area_info(area_name: str) -> str:
    """
    获取指定面单元的信息。
    
    Args:
        area_name: 面单元名称/编号
    """
    model = get_sap_model()
    
    try:
        area = Area.get_by_name(model, area_name)
        return to_json({
            "面单元": area_name,
            "节点数": area.num_points,
            "节点列表": area.points,
            "属性": area.section,
        })
    except Exception as e:
        return error_response(f"面单元 '{area_name}' 不存在: {e}")


@tool
@safe_sap_call
def get_areas_in_group(group_name: str) -> str:
    """
    获取指定组中的所有面单元。
    
    Args:
        group_name: 组名
    """
    model = get_sap_model()
    
    try:
        group = Group.get_by_name(model, group_name)
        assignments = group.get_assignments(model)
        
        # 筛选面单元 (type == 5)
        areas = [
            name for obj_type, name in assignments
            if obj_type == GroupObjectType.AREA.value
        ]
        
        return to_json({
            "组": group_name,
            "面单元数": len(areas),
            "面单元列表": areas[:50]
        })
    except Exception as e:
        return error_response(f"组 '{group_name}' 不存在: {e}")


@tool
@safe_sap_call
def get_area_list() -> str:
    """获取模型中所有面单元的名称列表。"""
    model = get_sap_model()
    areas = Area.get_name_list(model)
    return format_result_list(areas, "面单元")
