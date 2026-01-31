# -*- coding: utf-8 -*-
"""
modal_results.py - 模态分析结果函数

SAP2000 Results API 的模态分析结果函数封装

SAP2000 API:
- Results.ModalPeriod - 模态周期
- Results.ModeShape - 振型
- Results.ModalParticipatingMassRatios - 模态参与质量比
- Results.ModalLoadParticipationRatios - 模态荷载参与比
- Results.ModalParticipationFactors - 模态参与因子
"""

from typing import List
from .enums import ItemTypeElm
from .data_classes import (
    ModalPeriodResult, ModeShapeResult, ModalMassRatioResult,
    ModalLoadParticipationRatioResult, ModalParticipationFactorResult,
)


def get_modal_period(model) -> List[ModalPeriodResult]:
    """
    获取模态周期结果
    
    返回所有选中模态工况的周期、频率和特征值。
    
    Args:
        model: SapModel 对象
        
    Returns:
        ModalPeriodResult 列表
        
    Example:
        from results import deselect_all_cases_and_combos, set_case_selected_for_output
        
        deselect_all_cases_and_combos(model)
        set_case_selected_for_output(model, "MODAL")
        
        results = get_modal_period(model)
        for r in results:
            print(f"Mode {int(r.step_num)}: T={r.period:.3f}s, f={r.frequency:.3f}Hz")
    """
    result = model.Results.ModalPeriod(
        0, [], [], [],
        [], [], [], []
    )
    
    if isinstance(result, (list, tuple)) and len(result) >= 8:
        num = result[0]
        load_case = result[1]
        step_type = result[2]
        step_num = result[3]
        period = result[4]
        frequency = result[5]
        circ_freq = result[6]
        eigenvalue = result[7]
        ret = result[-1] if len(result) > 8 else 0
        
        if (ret == 0 or len(result) == 8) and num > 0:
            return [
                ModalPeriodResult(
                    load_case=load_case[i] if load_case else "",
                    step_type=step_type[i] if step_type else "",
                    step_num=step_num[i] if step_num else 0.0,
                    period=period[i] if period else 0.0,
                    frequency=frequency[i] if frequency else 0.0,
                    circ_freq=circ_freq[i] if circ_freq else 0.0,
                    eigenvalue=eigenvalue[i] if eigenvalue else 0.0,
                )
                for i in range(num)
            ]
    return []


def get_mode_shape(
    model,
    name: str,
    item_type: ItemTypeElm = ItemTypeElm.GROUP_ELM
) -> List[ModeShapeResult]:
    """
    获取振型结果
    
    Args:
        model: SapModel 对象
        name: 点对象名、点元素名或组名
        item_type: 元素类型
            
    Returns:
        ModeShapeResult 列表
        
    Example:
        from results import deselect_all_cases_and_combos, set_case_selected_for_output
        
        deselect_all_cases_and_combos(model)
        set_case_selected_for_output(model, "MODAL")
        
        # 获取所有点的振型
        results = get_mode_shape(model, "ALL", ItemTypeElm.GROUP_ELM)
    """
    result = model.Results.ModeShape(
        name, int(item_type),
        0, [], [], [], [], [],
        [], [], [], [], [], []
    )
    
    if isinstance(result, (list, tuple)) and len(result) >= 14:
        num = result[0]
        obj = result[1]
        elm = result[2]
        load_case = result[3]
        step_type = result[4]
        step_num = result[5]
        u1 = result[6]
        u2 = result[7]
        u3 = result[8]
        r1 = result[9]
        r2 = result[10]
        r3 = result[11]
        ret = result[-1]
        
        if ret == 0 and num > 0:
            return [
                ModeShapeResult(
                    obj=obj[i] if obj else "",
                    elm=elm[i] if elm else "",
                    load_case=load_case[i] if load_case else "",
                    step_type=step_type[i] if step_type else "",
                    step_num=step_num[i] if step_num else 0.0,
                    u1=u1[i] if u1 else 0.0,
                    u2=u2[i] if u2 else 0.0,
                    u3=u3[i] if u3 else 0.0,
                    r1=r1[i] if r1 else 0.0,
                    r2=r2[i] if r2 else 0.0,
                    r3=r3[i] if r3 else 0.0,
                )
                for i in range(num)
            ]
    return []


def get_modal_participating_mass_ratios(model) -> List[ModalMassRatioResult]:
    """
    获取模态参与质量比
    
    返回各振型的参与质量比和累计参与质量比。
    
    Args:
        model: SapModel 对象
        
    Returns:
        ModalMassRatioResult 列表
        
    Example:
        results = get_modal_participating_mass_ratios(model)
        for r in results:
            print(f"Mode {int(r.step_num)}: "
                  f"Ux={r.ux:.2%}, Uy={r.uy:.2%}, Uz={r.uz:.2%}, "
                  f"SumUx={r.sum_ux:.2%}")
    """
    result = model.Results.ModalParticipatingMassRatios(
        0, [], [], [],
        [],
        [], [], [], [], [], [],
        [], [], [], [], [], []
    )
    
    if isinstance(result, (list, tuple)) and len(result) >= 17:
        num = result[0]
        load_case = result[1]
        step_type = result[2]
        step_num = result[3]
        period = result[4]
        ux = result[5]
        uy = result[6]
        uz = result[7]
        sum_ux = result[8]
        sum_uy = result[9]
        sum_uz = result[10]
        rx = result[11]
        ry = result[12]
        rz = result[13]
        sum_rx = result[14]
        sum_ry = result[15]
        sum_rz = result[16]
        ret = result[-1] if len(result) > 17 else 0
        
        if (ret == 0 or len(result) == 17) and num > 0:
            return [
                ModalMassRatioResult(
                    load_case=load_case[i] if load_case else "",
                    step_type=step_type[i] if step_type else "",
                    step_num=step_num[i] if step_num else 0.0,
                    period=period[i] if period else 0.0,
                    ux=ux[i] if ux else 0.0,
                    uy=uy[i] if uy else 0.0,
                    uz=uz[i] if uz else 0.0,
                    sum_ux=sum_ux[i] if sum_ux else 0.0,
                    sum_uy=sum_uy[i] if sum_uy else 0.0,
                    sum_uz=sum_uz[i] if sum_uz else 0.0,
                    rx=rx[i] if rx else 0.0,
                    ry=ry[i] if ry else 0.0,
                    rz=rz[i] if rz else 0.0,
                    sum_rx=sum_rx[i] if sum_rx else 0.0,
                    sum_ry=sum_ry[i] if sum_ry else 0.0,
                    sum_rz=sum_rz[i] if sum_rz else 0.0,
                )
                for i in range(num)
            ]
    return []


def get_modal_load_participation_ratios(model) -> List[ModalLoadParticipationRatioResult]:
    """
    获取模态荷载参与比
    
    返回各荷载模式的静态和动态参与比。
    
    Args:
        model: SapModel 对象
        
    Returns:
        ModalLoadParticipationRatioResult 列表
    """
    result = model.Results.ModalLoadParticipationRatios(
        0, [], [], [], [], []
    )
    
    if isinstance(result, (list, tuple)) and len(result) >= 6:
        num = result[0]
        load_case = result[1]
        item_type = result[2]
        item = result[3]
        stat = result[4]
        dyn = result[5]
        ret = result[-1] if len(result) > 6 else 0
        
        if (ret == 0 or len(result) == 6) and num > 0:
            return [
                ModalLoadParticipationRatioResult(
                    load_case=load_case[i] if load_case else "",
                    item_type=item_type[i] if item_type else "",
                    item=item[i] if item else "",
                    stat=stat[i] if stat else 0.0,
                    dyn=dyn[i] if dyn else 0.0,
                )
                for i in range(num)
            ]
    return []


def get_modal_participation_factors(model) -> List[ModalParticipationFactorResult]:
    """
    获取模态参与因子
    
    返回各振型的参与因子、模态质量和模态刚度。
    
    Args:
        model: SapModel 对象
        
    Returns:
        ModalParticipationFactorResult 列表
    """
    result = model.Results.ModalParticipationFactors(
        0, [], [], [],
        [],
        [], [], [], [], [], [],
        [], []
    )
    
    if isinstance(result, (list, tuple)) and len(result) >= 13:
        num = result[0]
        load_case = result[1]
        step_type = result[2]
        step_num = result[3]
        period = result[4]
        ux = result[5]
        uy = result[6]
        uz = result[7]
        rx = result[8]
        ry = result[9]
        rz = result[10]
        modal_mass = result[11]
        modal_stiff = result[12]
        ret = result[-1] if len(result) > 13 else 0
        
        if (ret == 0 or len(result) == 13) and num > 0:
            return [
                ModalParticipationFactorResult(
                    load_case=load_case[i] if load_case else "",
                    step_type=step_type[i] if step_type else "",
                    step_num=step_num[i] if step_num else 0.0,
                    period=period[i] if period else 0.0,
                    ux=ux[i] if ux else 0.0,
                    uy=uy[i] if uy else 0.0,
                    uz=uz[i] if uz else 0.0,
                    rx=rx[i] if rx else 0.0,
                    ry=ry[i] if ry else 0.0,
                    rz=rz[i] if rz else 0.0,
                    modal_mass=modal_mass[i] if modal_mass else 0.0,
                    modal_stiff=modal_stiff[i] if modal_stiff else 0.0,
                )
                for i in range(num)
            ]
    return []
