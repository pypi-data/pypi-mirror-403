# -*- coding: utf-8 -*-
"""
约束操作工具 - 刚性隔板、节点约束

重构: 复用 PySap2000.constraints 和 PySap2000.point 模块
"""

from langchain.tools import tool

from .base import get_sap_model, to_json, success_response, error_response, safe_sap_call

# 导入 PySap2000 封装
from PySap2000.point import set_point_constraint


@tool
@safe_sap_call
def get_constraint_list() -> str:
    """获取模型中所有约束的名称列表。"""
    model = get_sap_model()
    ret = model.ConstraintDef.GetNameList(0, [])
    
    if isinstance(ret, (list, tuple)) and len(ret) >= 2:
        constraints = list(ret[1]) if ret[1] else []
        return to_json({"约束数": len(constraints), "约束列表": constraints})
    return to_json({"约束列表": []})


@tool
@safe_sap_call
def create_diaphragm_constraint(name: str, axis: str = "Z") -> str:
    """
    创建刚性隔板约束。
    
    Args:
        name: 约束名称
        axis: 约束轴向 (X, Y, Z)，默认 Z
    """
    model = get_sap_model()
    model.SetModelIsLocked(False)
    
    axis_map = {"X": 1, "Y": 2, "Z": 3}
    axis_code = axis_map.get(axis.upper(), 3)
    
    ret = model.ConstraintDef.SetDiaphragm(name, axis_code)
    
    if ret == 0:
        return success_response(f"刚性隔板约束 '{name}' 创建成功", 轴向=axis)
    return error_response("创建约束失败")


@tool
@safe_sap_call
def assign_point_constraint(point_name: str, constraint_name: str) -> str:
    """
    将约束分配给节点。
    
    Args:
        point_name: 节点名称
        constraint_name: 约束名称
    """
    model = get_sap_model()
    model.SetModelIsLocked(False)
    
    # 使用 PySap2000 封装
    ret = set_point_constraint(model, point_name, constraint_name)
    
    if ret == 0:
        return success_response(f"节点 '{point_name}' 已分配约束 '{constraint_name}'")
    return error_response("分配约束失败")
