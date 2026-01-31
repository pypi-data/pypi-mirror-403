# -*- coding: utf-8 -*-
"""
视图操作工具 - 刷新视图、缩放

重构: 复用 PySap2000.view 模块（如果存在）
"""

from langchain.tools import tool

from .base import get_sap_model, success_response, error_response, safe_sap_call


@tool
@safe_sap_call
def refresh_view() -> str:
    """刷新 SAP2000 视图。"""
    model = get_sap_model()
    model.View.RefreshView(0, False)
    return success_response("视图已刷新")


@tool
@safe_sap_call
def zoom_all() -> str:
    """缩放视图以显示所有对象。"""
    model = get_sap_model()
    ret = model.View.RefreshView(0, True)
    
    if ret == 0:
        return success_response("已缩放至全部")
    return error_response("缩放失败")
