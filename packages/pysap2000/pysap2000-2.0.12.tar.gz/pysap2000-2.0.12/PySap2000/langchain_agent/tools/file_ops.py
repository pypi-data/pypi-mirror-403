# -*- coding: utf-8 -*-
"""
文件操作工具 - 保存、解锁、新建、打开模型

重构: 复用 PySap2000.file 模块（如果存在）
"""

from langchain.tools import tool

from .base import get_sap_model, success_response, error_response, safe_sap_call


@tool
@safe_sap_call
def save_model() -> str:
    """保存当前模型。"""
    model = get_sap_model()
    ret = model.File.Save()
    
    if ret == 0:
        filename = model.GetModelFilename(False) or "未命名"
        return success_response("保存成功", 文件名=filename)
    return error_response("保存失败")


@tool
@safe_sap_call
def unlock_model() -> str:
    """解锁模型，允许修改。"""
    model = get_sap_model()
    model.SetModelIsLocked(False)
    return success_response("模型已解锁")


@tool
@safe_sap_call
def new_model(units: int = 6) -> str:
    """
    新建空白模型。
    
    Args:
        units: 单位制 (1=lb_in_F, 2=lb_ft_F, 3=kip_in_F, 4=kip_ft_F, 
               5=kN_mm_C, 6=kN_m_C, 7=kgf_mm_C, 8=kgf_m_C, 9=N_mm_C, 10=N_m_C)
    """
    model = get_sap_model()
    
    # 初始化新模型
    ret = model.InitializeNewModel(units)
    if ret != 0:
        return error_response("初始化新模型失败")
    
    # 创建空白模型
    ret = model.File.NewBlank()
    
    if ret == 0:
        unit_names = {
            1: "lb_in_F", 2: "lb_ft_F", 3: "kip_in_F", 4: "kip_ft_F",
            5: "kN_mm_C", 6: "kN_m_C", 7: "kgf_mm_C", 8: "kgf_m_C",
            9: "N_mm_C", 10: "N_m_C"
        }
        return success_response(
            "新模型已创建",
            单位制=unit_names.get(units, f"类型{units}")
        )
    return error_response("创建新模型失败")


@tool
@safe_sap_call
def open_model(file_path: str) -> str:
    """
    打开模型文件。
    
    Args:
        file_path: 模型文件完整路径 (.sdb 文件)
    """
    model = get_sap_model()
    ret = model.File.OpenFile(file_path)
    
    if ret == 0:
        return success_response("模型已打开", 文件=file_path)
    return error_response(f"打开模型失败: {file_path}")
