# -*- coding: utf-8 -*-
"""
选择操作工具 - 选择、清除选择

重构: 复用 PySap2000.selection 模块
"""

from langchain.tools import tool

from .base import get_sap_model, to_json, success_response, error_response, safe_sap_call

# 导入 PySap2000 封装
from PySap2000.selection import (
    select_all as _select_all,
    clear_selection as _clear_selection,
    select_by_group,
    get_selected,
    get_selected_by_type,
    SelectObjectType,
)


@tool
@safe_sap_call
def select_all() -> str:
    """选择模型中的所有对象。"""
    model = get_sap_model()
    _select_all(model)
    return success_response("已选择所有对象")


@tool
@safe_sap_call
def clear_selection() -> str:
    """清除当前选择。"""
    model = get_sap_model()
    _clear_selection(model)
    return success_response("已清除选择")


@tool
@safe_sap_call
def select_group(group_name: str) -> str:
    """
    选中指定组中的所有对象。
    
    Args:
        group_name: 组名
    """
    model = get_sap_model()
    ret = select_by_group(model, group_name)
    
    if ret == 0:
        return success_response(f"已选中组 '{group_name}'")
    return error_response(f"组 '{group_name}' 不存在")


@tool
@safe_sap_call
def get_selected_objects() -> str:
    """获取当前选中的对象列表。"""
    model = get_sap_model()
    
    # 使用 PySap2000 封装获取选中对象
    selected = get_selected(model)
    
    if not selected:
        return to_json({"选中对象": "无"})
    
    # 按类型分类
    type_map = {
        SelectObjectType.POINT.value: "节点",
        SelectObjectType.FRAME.value: "杆件",
        SelectObjectType.CABLE.value: "索",
        SelectObjectType.TENDON.value: "预应力筋",
        SelectObjectType.AREA.value: "面单元",
        SelectObjectType.SOLID.value: "实体",
        SelectObjectType.LINK.value: "连接",
    }
    
    classified = {}
    for obj_type, obj_name in selected:
        type_name = type_map.get(obj_type, f"类型{obj_type}")
        if type_name not in classified:
            classified[type_name] = []
        classified[type_name].append(obj_name)
    
    summary = {k: len(v) for k, v in classified.items()}
    
    return to_json({
        "选中统计": summary,
        "详情": {k: v[:20] for k, v in classified.items()}
    })


# 导入按属性选择函数
from PySap2000.selection import (
    select_by_property_frame,
    select_by_property_area,
    select_by_property_material,
)


@tool
@safe_sap_call
def select_by_property(property_name: str, property_type: str = "section") -> str:
    """
    按属性选择对象。
    
    Args:
        property_name: 属性名称（截面名或材料名）
        property_type: 属性类型 ("section"=按截面, "material"=按材料, "area_section"=按面截面)
    """
    model = get_sap_model()
    
    if property_type == "material":
        ret = select_by_property_material(model, property_name)
        type_desc = "材料"
    elif property_type == "area_section":
        ret = select_by_property_area(model, property_name)
        type_desc = "面截面"
    else:
        ret = select_by_property_frame(model, property_name)
        type_desc = "杆件截面"
    
    if ret == 0:
        return success_response(
            f"已选中{type_desc} '{property_name}' 的所有对象"
        )
    return error_response(f"按属性选择失败: {property_name}")
