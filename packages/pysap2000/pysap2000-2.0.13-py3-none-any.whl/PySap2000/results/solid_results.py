# -*- coding: utf-8 -*-
"""
solid_results.py - 实体单元结果函数

SAP2000 Results API 的实体单元结果函数封装

SAP2000 API:
- Results.SolidJointForce - 实体单元节点力
- Results.SolidStrain - 实体单元应变
- Results.SolidStress - 实体单元应力
"""

from typing import List
from .enums import ItemTypeElm
from .data_classes import SolidJointForceResult, SolidStrainResult, SolidStressResult


def get_solid_joint_force(
    model,
    name: str,
    item_type: ItemTypeElm = ItemTypeElm.OBJECT_ELM
) -> List[SolidJointForceResult]:
    """
    获取实体单元节点力结果
    
    Args:
        model: SapModel 对象
        name: 实体对象名、实体元素名或组名
        item_type: 元素类型
            
    Returns:
        SolidJointForceResult 列表
    """
    result = model.Results.SolidJointForce(
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
                SolidJointForceResult(
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


def get_solid_strain(
    model,
    name: str,
    item_type: ItemTypeElm = ItemTypeElm.OBJECT_ELM
) -> List[SolidStrainResult]:
    """
    获取实体单元应变结果
    
    Args:
        model: SapModel 对象
        name: 实体对象名、实体元素名或组名
        item_type: 元素类型
            
    Returns:
        SolidStrainResult 列表
    """
    result = model.Results.SolidStrain(
        name, int(item_type),
        0, [], [], [], [], [], [],
        [], [], [], [], [], [],
        [], [], [], [],
        [], [], [], [], [], [], [], [], []
    )
    
    if isinstance(result, (list, tuple)) and len(result) >= 27:
        num = result[0]
        obj = result[1]
        elm = result[2]
        point_elm = result[3]
        load_case = result[4]
        step_type = result[5]
        step_num = result[6]
        e11 = result[7]
        e22 = result[8]
        e33 = result[9]
        g12 = result[10]
        g13 = result[11]
        g23 = result[12]
        e_max = result[13]
        e_mid = result[14]
        e_min = result[15]
        e_vm = result[16]
        dir_cos_max1 = result[17]
        dir_cos_max2 = result[18]
        dir_cos_max3 = result[19]
        dir_cos_mid1 = result[20]
        dir_cos_mid2 = result[21]
        dir_cos_mid3 = result[22]
        dir_cos_min1 = result[23]
        dir_cos_min2 = result[24]
        dir_cos_min3 = result[25]
        ret = result[-1]
        
        if ret == 0 and num > 0:
            return [
                SolidStrainResult(
                    obj=obj[i] if obj else "",
                    elm=elm[i] if elm else "",
                    point_elm=point_elm[i] if point_elm else "",
                    load_case=load_case[i] if load_case else "",
                    step_type=step_type[i] if step_type else "",
                    step_num=step_num[i] if step_num else 0.0,
                    e11=e11[i] if e11 else 0.0,
                    e22=e22[i] if e22 else 0.0,
                    e33=e33[i] if e33 else 0.0,
                    g12=g12[i] if g12 else 0.0,
                    g13=g13[i] if g13 else 0.0,
                    g23=g23[i] if g23 else 0.0,
                    e_max=e_max[i] if e_max else 0.0,
                    e_mid=e_mid[i] if e_mid else 0.0,
                    e_min=e_min[i] if e_min else 0.0,
                    e_vm=e_vm[i] if e_vm else 0.0,
                    dir_cos_max1=dir_cos_max1[i] if dir_cos_max1 else 0.0,
                    dir_cos_max2=dir_cos_max2[i] if dir_cos_max2 else 0.0,
                    dir_cos_max3=dir_cos_max3[i] if dir_cos_max3 else 0.0,
                    dir_cos_mid1=dir_cos_mid1[i] if dir_cos_mid1 else 0.0,
                    dir_cos_mid2=dir_cos_mid2[i] if dir_cos_mid2 else 0.0,
                    dir_cos_mid3=dir_cos_mid3[i] if dir_cos_mid3 else 0.0,
                    dir_cos_min1=dir_cos_min1[i] if dir_cos_min1 else 0.0,
                    dir_cos_min2=dir_cos_min2[i] if dir_cos_min2 else 0.0,
                    dir_cos_min3=dir_cos_min3[i] if dir_cos_min3 else 0.0,
                )
                for i in range(num)
            ]
    return []


def get_solid_stress(
    model,
    name: str,
    item_type: ItemTypeElm = ItemTypeElm.OBJECT_ELM
) -> List[SolidStressResult]:
    """
    获取实体单元应力结果
    
    Args:
        model: SapModel 对象
        name: 实体对象名、实体元素名或组名
        item_type: 元素类型
            
    Returns:
        SolidStressResult 列表
    """
    result = model.Results.SolidStress(
        name, int(item_type),
        0, [], [], [], [], [], [],
        [], [], [], [], [], [],
        [], [], [], [],
        [], [], [], [], [], [], [], [], []
    )
    
    if isinstance(result, (list, tuple)) and len(result) >= 27:
        num = result[0]
        obj = result[1]
        elm = result[2]
        point_elm = result[3]
        load_case = result[4]
        step_type = result[5]
        step_num = result[6]
        s11 = result[7]
        s22 = result[8]
        s33 = result[9]
        s12 = result[10]
        s13 = result[11]
        s23 = result[12]
        s_max = result[13]
        s_mid = result[14]
        s_min = result[15]
        s_vm = result[16]
        dir_cos_max1 = result[17]
        dir_cos_max2 = result[18]
        dir_cos_max3 = result[19]
        dir_cos_mid1 = result[20]
        dir_cos_mid2 = result[21]
        dir_cos_mid3 = result[22]
        dir_cos_min1 = result[23]
        dir_cos_min2 = result[24]
        dir_cos_min3 = result[25]
        ret = result[-1]
        
        if ret == 0 and num > 0:
            return [
                SolidStressResult(
                    obj=obj[i] if obj else "",
                    elm=elm[i] if elm else "",
                    point_elm=point_elm[i] if point_elm else "",
                    load_case=load_case[i] if load_case else "",
                    step_type=step_type[i] if step_type else "",
                    step_num=step_num[i] if step_num else 0.0,
                    s11=s11[i] if s11 else 0.0,
                    s22=s22[i] if s22 else 0.0,
                    s33=s33[i] if s33 else 0.0,
                    s12=s12[i] if s12 else 0.0,
                    s13=s13[i] if s13 else 0.0,
                    s23=s23[i] if s23 else 0.0,
                    s_max=s_max[i] if s_max else 0.0,
                    s_mid=s_mid[i] if s_mid else 0.0,
                    s_min=s_min[i] if s_min else 0.0,
                    s_vm=s_vm[i] if s_vm else 0.0,
                    dir_cos_max1=dir_cos_max1[i] if dir_cos_max1 else 0.0,
                    dir_cos_max2=dir_cos_max2[i] if dir_cos_max2 else 0.0,
                    dir_cos_max3=dir_cos_max3[i] if dir_cos_max3 else 0.0,
                    dir_cos_mid1=dir_cos_mid1[i] if dir_cos_mid1 else 0.0,
                    dir_cos_mid2=dir_cos_mid2[i] if dir_cos_mid2 else 0.0,
                    dir_cos_mid3=dir_cos_mid3[i] if dir_cos_mid3 else 0.0,
                    dir_cos_min1=dir_cos_min1[i] if dir_cos_min1 else 0.0,
                    dir_cos_min2=dir_cos_min2[i] if dir_cos_min2 else 0.0,
                    dir_cos_min3=dir_cos_min3[i] if dir_cos_min3 else 0.0,
                )
                for i in range(num)
            ]
    return []
