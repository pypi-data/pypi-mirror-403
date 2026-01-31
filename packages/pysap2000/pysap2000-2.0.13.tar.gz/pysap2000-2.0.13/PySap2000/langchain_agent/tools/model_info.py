# -*- coding: utf-8 -*-
"""
模型信息工具 - 获取模型基本信息、组、截面、材料等

重构: 复用 PySap2000 各模块
"""

from langchain.tools import tool

from .base import (
    get_sap_model, to_json, error_response, safe_sap_call,
    SapConnectionError, SapModelError
)

# 导入 PySap2000 封装
from PySap2000.structure_core import Point, Frame, Area, Cable, Link
from PySap2000.group import Group


@tool
def check_connection() -> str:
    """
    检查 SAP2000 连接状态。
    返回连接是否正常、模型是否打开、模型是否锁定等信息。
    """
    try:
        model = get_sap_model()
        filename = model.GetModelFilename(False)
        is_locked = model.GetModelIsLocked()
        
        return to_json({
            "连接状态": "正常",
            "模型文件": filename or "未保存",
            "模型锁定": "是" if is_locked else "否",
            "节点数": Point.get_count(model),
            "杆件数": Frame.get_count(model),
        }, indent=2)
    except SapConnectionError as e:
        return to_json({
            "连接状态": "失败",
            "错误": str(e),
            "建议": "请启动 SAP2000 并打开模型文件"
        }, indent=2)
    except SapModelError as e:
        return to_json({
            "连接状态": "部分正常",
            "错误": str(e),
            "建议": "SAP2000 已启动，请打开或新建模型"
        }, indent=2)
    except Exception as e:
        return to_json({
            "连接状态": "未知错误",
            "错误": str(e)
        }, indent=2)


@tool
@safe_sap_call
def get_model_info() -> str:
    """
    获取当前 SAP2000 模型的基本信息。
    返回模型文件名、单位、节点数、杆件数、面单元数、组数等。
    """
    model = get_sap_model()
    
    filename = model.GetModelFilename(False) or "未保存"
    units_code = model.GetPresentUnits()
    units_map = {5: "kN-mm-C", 6: "kN-m-C", 9: "N-mm-C", 10: "N-m-C"}
    
    return to_json({
        "文件名": filename,
        "单位": units_map.get(units_code, f"代码 {units_code}"),
        "节点数": Point.get_count(model),
        "杆件数": Frame.get_count(model),
        "面单元数": Area.get_count(model),
        "索单元数": Cable.get_count(model),
        "连接单元数": Link.get_count(model),
        "组数": Group.get_count(model),
    }, indent=2)


@tool
@safe_sap_call
def get_group_list() -> str:
    """获取模型中所有组的名称列表。"""
    model = get_sap_model()
    groups = Group.get_name_list(model)
    return to_json({"组列表": groups})


@tool
@safe_sap_call
def get_section_list() -> str:
    """获取模型中所有杆件截面的名称列表。"""
    model = get_sap_model()
    sections = Frame.get_section_name_list(model)
    return to_json({"截面列表": sections})


@tool
@safe_sap_call
def get_material_list() -> str:
    """获取模型中所有材料的名称列表。"""
    model = get_sap_model()
    ret = model.PropMaterial.GetNameList(0, [])
    materials = list(ret[1]) if isinstance(ret, (list, tuple)) and len(ret) >= 2 and ret[1] else []
    return to_json({"材料列表": materials})


@tool
@safe_sap_call
def get_load_pattern_list() -> str:
    """获取模型中所有荷载模式的名称列表。"""
    model = get_sap_model()
    ret = model.LoadPatterns.GetNameList(0, [])
    patterns = list(ret[1]) if isinstance(ret, (list, tuple)) and len(ret) >= 2 and ret[1] else []
    return to_json({"荷载模式列表": patterns})


@tool
@safe_sap_call
def get_load_case_list() -> str:
    """获取模型中所有荷载工况的名称列表。"""
    model = get_sap_model()
    ret = model.LoadCases.GetNameList(0, [])
    cases = list(ret[1]) if isinstance(ret, (list, tuple)) and len(ret) >= 2 and ret[1] else []
    return to_json({"荷载工况列表": cases})


@tool
@safe_sap_call
def get_combo_list() -> str:
    """获取模型中所有荷载组合的名称列表。"""
    model = get_sap_model()
    ret = model.RespCombo.GetNameList(0, [])
    combos = list(ret[1]) if isinstance(ret, (list, tuple)) and len(ret) >= 2 and ret[1] else []
    return to_json({"荷载组合列表": combos})


@tool
@safe_sap_call
def get_section_info(section_name: str) -> str:
    """
    获取截面的详细信息。
    
    Args:
        section_name: 截面名称
    """
    model = get_sap_model()
    
    # 获取截面类型
    type_ret = model.PropFrame.GetTypeOAPI(section_name, 0)
    type_code = type_ret[0] if isinstance(type_ret, (list, tuple)) else 0
    
    type_map = {
        1: "I/Wide Flange", 2: "Channel", 3: "T", 4: "Angle",
        5: "Double Angle", 6: "Box/Tube", 7: "Pipe", 8: "Rectangular",
        9: "Circle", 10: "General", 11: "SD Section"
    }
    
    return to_json({
        "截面名": section_name,
        "类型": type_map.get(type_code, f"类型代码 {type_code}")
    })
