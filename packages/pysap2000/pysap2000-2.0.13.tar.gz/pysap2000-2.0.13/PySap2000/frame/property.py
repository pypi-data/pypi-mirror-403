# -*- coding: utf-8 -*-
"""
property.py - 杆件属性分配函数
对应 SAP2000 的 FrameObj.SetSection / GetSection

本模块用于分配属性到杆件（怎么用），而非定义属性（是什么）。
属性定义请使用 properties 模块。

Usage:
    from frame import set_frame_section, get_frame_section
    
    # 分配截面到杆件
    set_frame_section(model, "1", "W14X22")
    
    # 获取杆件的截面
    section_name = get_frame_section(model, "1")
"""

from typing import Optional, Tuple
from .enums import ItemType


def set_frame_section(
    model,
    frame_name: str,
    section_name: str,
    item_type: ItemType = ItemType.OBJECT
) -> int:
    """
    设置杆件的截面属性
    
    Args:
        model: SapModel 对象
        frame_name: 杆件名称
        section_name: 截面名称 (必须已在 PropFrame 中定义)
        item_type: 项目类型
            - OBJECT (0): 单个对象
            - GROUP (1): 组内所有对象
            - SELECTED (2): 所有选中对象
    
    Returns:
        0 表示成功，非 0 表示失败
    
    Example:
        # 设置杆件 "1" 的截面为 "W14X22"
        set_frame_section(model, "1", "W14X22")
        
        # 设置组 "Beams" 内所有杆件的截面
        set_frame_section(model, "Beams", "W14X22", ItemType.GROUP)
        
        # 设置所有选中杆件的截面
        set_frame_section(model, "", "W14X22", ItemType.SELECTED)
    """
    return model.FrameObj.SetSection(
        str(frame_name),
        section_name,
        item_type.value
    )


def get_frame_section(model, frame_name: str) -> str:
    """
    获取杆件的截面属性名称
    
    Args:
        model: SapModel 对象
        frame_name: 杆件名称
    
    Returns:
        截面名称
    
    Example:
        section = get_frame_section(model, "1")
        print(f"杆件 1 的截面: {section}")
    """
    result = model.FrameObj.GetSection(str(frame_name))
    
    if isinstance(result, (list, tuple)) and len(result) >= 2:
        return result[0] or ""
    return ""


def get_frame_section_info(model, frame_name: str) -> Tuple[str, str]:
    """
    获取杆件的截面信息（包括自动选择截面）
    
    Args:
        model: SapModel 对象
        frame_name: 杆件名称
    
    Returns:
        (section_name, auto_select_list) 元组
        - section_name: 当前截面名称
        - auto_select_list: 自动选择列表名称（如果有）
    
    Example:
        section, auto_list = get_frame_section_info(model, "1")
        if auto_list:
            print(f"使用自动选择: {auto_list}")
    """
    result = model.FrameObj.GetSection(str(frame_name))
    
    if isinstance(result, (list, tuple)) and len(result) >= 3:
        return (result[0] or "", result[1] or "")
    return ("", "")


def set_frame_material_overwrite(
    model,
    frame_name: str,
    material_name: str,
    item_type: ItemType = ItemType.OBJECT
) -> int:
    """
    设置杆件的材料覆盖
    
    覆盖截面属性中定义的材料。
    
    Args:
        model: SapModel 对象
        frame_name: 杆件名称
        material_name: 材料名称，空字符串表示使用截面属性中的材料
        item_type: 项目类型
    
    Returns:
        0 表示成功，非 0 表示失败
    
    Example:
        # 覆盖杆件 "1" 的材料为 "A992Fy50"
        set_frame_material_overwrite(model, "1", "A992Fy50")
        
        # 清除材料覆盖，使用截面属性中的材料
        set_frame_material_overwrite(model, "1", "")
    """
    return model.FrameObj.SetMaterialOverwrite(
        str(frame_name),
        material_name,
        item_type.value
    )


def get_frame_material_overwrite(model, frame_name: str) -> str:
    """
    获取杆件的材料覆盖
    
    Args:
        model: SapModel 对象
        frame_name: 杆件名称
    
    Returns:
        材料名称，空字符串表示未覆盖
    
    Example:
        mat = get_frame_material_overwrite(model, "1")
        if mat:
            print(f"材料覆盖: {mat}")
        else:
            print("使用截面属性中的材料")
    """
    result = model.FrameObj.GetMaterialOverwrite(str(frame_name))
    
    if isinstance(result, (list, tuple)) and len(result) >= 2:
        material = result[0] or ""
        # 'None' 字符串表示无覆盖，返回空字符串
        if material == "None":
            return ""
        return material
    return ""


def set_frame_material_temperature(
    model,
    frame_name: str,
    temperature: float,
    pattern_name: str = "",
    item_type: ItemType = ItemType.OBJECT
) -> int:
    """
    设置杆件的材料温度
    
    Args:
        model: SapModel 对象
        frame_name: 杆件名称
        temperature: 温度值 [T]
        pattern_name: 荷载模式名称，空字符串表示无模式
        item_type: 项目类型
    
    Returns:
        0 表示成功，非 0 表示失败
    
    Example:
        # 设置杆件 "1" 的材料温度为 20°C
        set_frame_material_temperature(model, "1", 20.0)
    """
    return model.FrameObj.SetMatTemp(
        str(frame_name),
        temperature,
        pattern_name,
        item_type.value
    )


def get_frame_material_temperature(model, frame_name: str) -> Tuple[float, str]:
    """
    获取杆件的材料温度
    
    Args:
        model: SapModel 对象
        frame_name: 杆件名称
    
    Returns:
        (temperature, pattern_name) 元组
    
    Example:
        temp, pattern = get_frame_material_temperature(model, "1")
        print(f"温度: {temp}, 模式: {pattern}")
    """
    result = model.FrameObj.GetMatTemp(str(frame_name))
    
    if isinstance(result, (list, tuple)) and len(result) >= 3:
        return (result[0], result[1] or "")
    return (0.0, "")
