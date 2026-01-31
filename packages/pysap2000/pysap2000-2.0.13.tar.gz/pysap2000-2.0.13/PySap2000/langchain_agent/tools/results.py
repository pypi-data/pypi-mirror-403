# -*- coding: utf-8 -*-
"""
结果查询工具 - 位移、内力、反力、模态

重构: 复用 PySap2000.results 模块
"""

from langchain.tools import tool

from .base import get_sap_model, to_json, error_response, safe_sap_call

# 导入 PySap2000 封装
from PySap2000.results import (
    deselect_all_cases_and_combos,
    set_case_selected_for_output,
    get_joint_displ,
    get_joint_react,
    get_base_react,
    get_frame_force,
    get_modal_period,
    get_modal_participating_mass_ratios,
    ItemTypeElm,
)
from PySap2000.structure_core import Frame


def _setup_output_cases(model, load_case: str = ""):
    """设置输出工况"""
    deselect_all_cases_and_combos(model)
    
    if load_case:
        set_case_selected_for_output(model, load_case)
    else:
        ret = model.LoadCases.GetNameList(0, [])
        if isinstance(ret, (list, tuple)) and len(ret) >= 2 and ret[1]:
            for case in ret[1][:3]:
                set_case_selected_for_output(model, case)


@tool
@safe_sap_call
def get_point_displacement(point_name: str, load_case: str = "") -> str:
    """
    获取节点位移结果。需要先运行分析。
    
    Args:
        point_name: 节点名称
        load_case: 荷载工况名称（可选）
    """
    model = get_sap_model()
    _setup_output_cases(model, load_case)
    
    results = get_joint_displ(model, point_name, ItemTypeElm.OBJECT_ELM)
    
    if not results:
        return error_response("无位移结果，请先运行分析")
    
    displacements = []
    for r in results[:10]:
        displacements.append({
            "工况": r.load_case,
            "U1": round(r.u1, 6),
            "U2": round(r.u2, 6),
            "U3": round(r.u3, 6),
        })
    
    return to_json({"节点": point_name, "位移结果": displacements}, indent=2)


@tool
@safe_sap_call
def get_point_reactions(point_name: str, load_case: str = "") -> str:
    """
    获取节点反力结果。需要先运行分析。
    
    Args:
        point_name: 节点名称
        load_case: 荷载工况名称（可选）
    """
    model = get_sap_model()
    _setup_output_cases(model, load_case)
    
    results = get_joint_react(model, point_name, ItemTypeElm.OBJECT_ELM)
    
    if not results:
        return error_response("无反力结果，请先运行分析")
    
    reactions = []
    for r in results[:10]:
        reactions.append({
            "工况": r.load_case,
            "F1": round(r.f1, 2),
            "F2": round(r.f2, 2),
            "F3": round(r.f3, 2),
        })
    
    return to_json({"节点": point_name, "反力结果": reactions}, indent=2)


@tool
@safe_sap_call
def get_base_reactions(load_case: str = "") -> str:
    """
    获取基底总反力。需要先运行分析。
    
    Args:
        load_case: 荷载工况名称（可选）
    """
    model = get_sap_model()
    _setup_output_cases(model, load_case)
    
    results = get_base_react(model)
    
    if not results:
        return error_response("无基底反力结果，请先运行分析")
    
    reactions = []
    for r in results[:10]:
        reactions.append({
            "工况": r.load_case,
            "F1": round(r.f1, 2),
            "F2": round(r.f2, 2),
            "F3": round(r.f3, 2),
        })
    
    return to_json({"反力结果数": len(results), "反力列表": reactions}, indent=2)


@tool
@safe_sap_call
def get_frame_forces(frame_name: str, load_case: str = "") -> str:
    """
    获取杆件内力结果。需要先运行分析。
    
    Args:
        frame_name: 杆件名称
        load_case: 荷载工况名称（可选）
    """
    model = get_sap_model()
    _setup_output_cases(model, load_case)
    
    results = get_frame_force(model, frame_name, ItemTypeElm.OBJECT_ELM)
    
    if not results:
        return error_response("无内力结果，请先运行分析")
    
    forces = []
    for r in results[:20]:
        forces.append({
            "工况": r.load_case,
            "位置": round(r.obj_sta, 3),
            "轴力P": round(r.p, 2),
            "剪力V2": round(r.v2, 2),
            "弯矩M3": round(r.m3, 2),
        })
    
    return to_json({"杆件": frame_name, "内力列表": forces}, indent=2)


@tool
@safe_sap_call
def get_max_frame_forces(group_name: str = "", load_case: str = "") -> str:
    """
    获取杆件最大内力统计。需要先运行分析。
    
    Args:
        group_name: 组名（可选）
        load_case: 荷载工况名称（可选）
    """
    model = get_sap_model()
    _setup_output_cases(model, load_case)
    
    if group_name:
        from PySap2000.group import Group, GroupObjectType
        try:
            group = Group.get_by_name(model, group_name)
            assignments = group.get_assignments(model)
            frame_names = [n for t, n in assignments if t == GroupObjectType.FRAME.value]
        except:
            return error_response(f"组 '{group_name}' 不存在")
    else:
        frame_names = Frame.get_name_list(model)
    
    max_vals = {"P": (0, ""), "V2": (0, ""), "M3": (0, "")}
    
    for fname in frame_names[:100]:
        results = get_frame_force(model, fname, ItemTypeElm.OBJECT_ELM)
        if not results:
            continue
        for r in results:
            if abs(r.p) > abs(max_vals["P"][0]):
                max_vals["P"] = (r.p, fname)
            if abs(r.v2) > abs(max_vals["V2"][0]):
                max_vals["V2"] = (r.v2, fname)
            if abs(r.m3) > abs(max_vals["M3"][0]):
                max_vals["M3"] = (r.m3, fname)
    
    return to_json({
        "组名": group_name or "全部",
        "杆件数": len(frame_names),
        "最大轴力": {"值": round(max_vals["P"][0], 2), "杆件": max_vals["P"][1]},
        "最大剪力": {"值": round(max_vals["V2"][0], 2), "杆件": max_vals["V2"][1]},
        "最大弯矩": {"值": round(max_vals["M3"][0], 2), "杆件": max_vals["M3"][1]},
    }, indent=2)


@tool
@safe_sap_call
def get_modal_periods(num_modes: int = 12) -> str:
    """
    获取模态周期和频率。需要先运行分析。
    
    Args:
        num_modes: 返回的模态数量
    """
    model = get_sap_model()
    deselect_all_cases_and_combos(model)
    
    ret = model.LoadCases.GetNameList(0, [])
    modal_case = None
    if isinstance(ret, (list, tuple)) and len(ret) >= 2 and ret[1]:
        for case in ret[1]:
            case_type = model.LoadCases.GetTypeOAPI(case, 0)
            if isinstance(case_type, (list, tuple)) and case_type[0] == 1:
                modal_case = case
                break
    
    if not modal_case:
        return error_response("未找到模态分析工况")
    
    set_case_selected_for_output(model, modal_case)
    results = get_modal_period(model)
    
    if not results:
        return error_response("无模态结果，请先运行分析")
    
    modal_results = [
        {"模态": r.mode_number, "周期(s)": round(r.period, 4), "频率(Hz)": round(r.frequency, 4)}
        for r in results[:num_modes]
    ]
    
    return to_json({"模态工况": modal_case, "结果": modal_results}, indent=2)


@tool
@safe_sap_call
def get_modal_mass_ratios(num_modes: int = 12) -> str:
    """
    获取模态质量参与系数。需要先运行分析。
    
    Args:
        num_modes: 返回的模态数量
    """
    model = get_sap_model()
    deselect_all_cases_and_combos(model)
    
    ret = model.LoadCases.GetNameList(0, [])
    modal_case = None
    if isinstance(ret, (list, tuple)) and len(ret) >= 2 and ret[1]:
        for case in ret[1]:
            case_type = model.LoadCases.GetTypeOAPI(case, 0)
            if isinstance(case_type, (list, tuple)) and case_type[0] == 1:
                modal_case = case
                break
    
    if not modal_case:
        return error_response("未找到模态分析工况")
    
    set_case_selected_for_output(model, modal_case)
    results = get_modal_participating_mass_ratios(model)
    
    if not results:
        return error_response("无模态质量参与系数结果")
    
    modal_results = [
        {
            "模态": r.mode_number,
            "UX%": round(r.ux * 100, 2),
            "UY%": round(r.uy * 100, 2),
            "累计UX%": round(r.sum_ux * 100, 2),
            "累计UY%": round(r.sum_uy * 100, 2),
        }
        for r in results[:num_modes]
    ]
    
    return to_json({"模态质量参与系数": modal_results}, indent=2)
