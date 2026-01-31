# -*- coding: utf-8 -*-
"""
frame_results.py - 框架单元结果函数

SAP2000 Results API 的框架单元结果函数封装

SAP2000 API:
- Results.FrameForce - 框架内力
- Results.FrameJointForce - 框架节点力
"""

from typing import List
from .enums import ItemTypeElm
from .data_classes import FrameForceResult, FrameJointForceResult


def get_frame_force(
    model,
    name: str,
    item_type: ItemTypeElm = ItemTypeElm.OBJECT_ELM
) -> List[FrameForceResult]:
    """
    获取框架单元内力结果
    
    Args:
        model: SapModel 对象
        name: 线对象名、线元素名或组名
        item_type: 元素类型
            - OBJECT_ELM: 指定对象对应的元素
            - ELEMENT: 指定元素
            - GROUP_ELM: 组内所有元素
            - SELECTION_ELM: 所有选中元素 (忽略name)
            
    Returns:
        FrameForceResult 列表
        
    Example:
        # 获取单个杆件的内力
        results = get_frame_force(model, "1", ItemTypeElm.OBJECT_ELM)
        for r in results:
            print(f"位置: {r.obj_sta}, P={r.p}, V2={r.v2}, M3={r.m3}")
        
        # 获取所有杆件的内力
        results = get_frame_force(model, "ALL", ItemTypeElm.GROUP_ELM)
    """
    result = model.Results.FrameForce(
        name, int(item_type),
        0, [], [], [], [], [], [], [],
        [], [], [], [], [], []
    )
    
    if isinstance(result, (list, tuple)) and len(result) >= 16:
        num = result[0]
        obj = result[1]
        obj_sta = result[2]
        elm = result[3]
        elm_sta = result[4]
        load_case = result[5]
        step_type = result[6]
        step_num = result[7]
        p = result[8]
        v2 = result[9]
        v3 = result[10]
        t = result[11]
        m2 = result[12]
        m3 = result[13]
        ret = result[-1]
        
        if ret == 0 and num > 0:
            return [
                FrameForceResult(
                    obj=obj[i] if obj else "",
                    obj_sta=obj_sta[i] if obj_sta else 0.0,
                    elm=elm[i] if elm else "",
                    elm_sta=elm_sta[i] if elm_sta else 0.0,
                    load_case=load_case[i] if load_case else "",
                    step_type=step_type[i] if step_type else "",
                    step_num=step_num[i] if step_num else 0.0,
                    p=p[i] if p else 0.0,
                    v2=v2[i] if v2 else 0.0,
                    v3=v3[i] if v3 else 0.0,
                    t=t[i] if t else 0.0,
                    m2=m2[i] if m2 else 0.0,
                    m3=m3[i] if m3 else 0.0,
                )
                for i in range(num)
            ]
    return []


def get_frame_joint_force(
    model,
    name: str,
    item_type: ItemTypeElm = ItemTypeElm.OBJECT_ELM
) -> List[FrameJointForceResult]:
    """
    获取框架单元节点力结果
    
    Args:
        model: SapModel 对象
        name: 线对象名、线元素名或组名
        item_type: 元素类型
            
    Returns:
        FrameJointForceResult 列表
    """
    result = model.Results.FrameJointForce(
        name, int(item_type),
        0, [], [], [], [], [], [],
        [], [], [], [], [], []
    )
    
    if isinstance(result, (list, tuple)) and len(result) >= 15:
        num = result[0]
        obj = result[1]
        elm = result[2]
        point_elm = result[3]
        load_case = result[4]
        step_type = result[5]
        step_num = result[6]
        f1 = result[7]
        f2 = result[8]
        f3 = result[9]
        m1 = result[10]
        m2 = result[11]
        m3 = result[12]
        ret = result[-1]
        
        if ret == 0 and num > 0:
            return [
                FrameJointForceResult(
                    obj=obj[i] if obj else "",
                    elm=elm[i] if elm else "",
                    point_elm=point_elm[i] if point_elm else "",
                    load_case=load_case[i] if load_case else "",
                    step_type=step_type[i] if step_type else "",
                    step_num=step_num[i] if step_num else 0.0,
                    f1=f1[i] if f1 else 0.0,
                    f2=f2[i] if f2 else 0.0,
                    f3=f3[i] if f3 else 0.0,
                    m1=m1[i] if m1 else 0.0,
                    m2=m2[i] if m2 else 0.0,
                    m3=m3[i] if m3 else 0.0,
                )
                for i in range(num)
            ]
    return []
