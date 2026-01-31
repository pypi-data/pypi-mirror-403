# -*- coding: utf-8 -*-
"""
组操作工具 - 创建组、添加对象到组

重构: 复用 PySap2000.group 和各模块的组分配函数
"""

from langchain.tools import tool

from .base import get_sap_model, success_response, error_response, safe_sap_call

# 导入 PySap2000 封装
from PySap2000.group import Group
from PySap2000.selection import get_selected, SelectObjectType
from PySap2000.frame.group import set_frame_group
from PySap2000.point.constraint import set_point_constraint
from PySap2000.area.group import set_area_group
from PySap2000.cable.group import set_cable_group
from PySap2000.link.group import set_link_group


@tool
@safe_sap_call
def create_group(group_name: str) -> str:
    """
    创建一个新组。
    
    Args:
        group_name: 组名
    """
    model = get_sap_model()
    
    group = Group(name=group_name)
    ret = group._create(model)
    
    if ret == 0:
        return success_response(f"组 '{group_name}' 创建成功")
    return error_response("创建组失败")


@tool
@safe_sap_call
def add_frame_to_group(frame_name: str, group_name: str) -> str:
    """
    将杆件添加到组。
    
    Args:
        frame_name: 杆件名称
        group_name: 组名
    """
    model = get_sap_model()
    
    # 使用 PySap2000 frame.group 模块
    ret = set_frame_group(model, frame_name, group_name)
    
    if ret == 0:
        return success_response(f"杆件 '{frame_name}' 已添加到组 '{group_name}'")
    return error_response("添加失败")


@tool
@safe_sap_call
def add_selected_to_group(group_name: str) -> str:
    """
    将当前选中的对象添加到组。
    
    Args:
        group_name: 组名
    """
    model = get_sap_model()
    
    # 确保组存在
    group = Group(name=group_name)
    group._create(model)
    
    # 获取选中对象
    selected = get_selected(model)
    
    if not selected:
        return error_response("没有选中任何对象")
    
    added = 0
    for obj_type, obj_name in selected:
        try:
            if obj_type == SelectObjectType.POINT.value:
                # Point 使用 structure_core.Point 的方法
                from PySap2000.structure_core import Point
                point = Point(no=obj_name)
                point.set_group_assign(model, group_name)
            elif obj_type == SelectObjectType.FRAME.value:
                set_frame_group(model, obj_name, group_name)
            elif obj_type == SelectObjectType.AREA.value:
                set_area_group(model, obj_name, group_name)
            elif obj_type == SelectObjectType.CABLE.value:
                set_cable_group(model, obj_name, group_name)
            elif obj_type == SelectObjectType.LINK.value:
                set_link_group(model, obj_name, group_name)
            added += 1
        except:
            pass
    
    return success_response(f"已将 {added} 个对象添加到组 '{group_name}'")
