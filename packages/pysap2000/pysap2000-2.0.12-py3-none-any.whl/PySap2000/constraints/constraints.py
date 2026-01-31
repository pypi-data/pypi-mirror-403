# -*- coding: utf-8 -*-
"""
constraints.py - 约束定义函数

API 路径: SapModel.ConstraintDef
"""

from typing import List, Optional, Tuple
from .enums import ConstraintType, ConstraintAxis


# =============================================================================
# 通用函数
# =============================================================================

def get_constraint_count(model) -> int:
    """
    获取约束数量
    
    Returns:
        约束数量
    """
    result = model.ConstraintDef.Count()
    if isinstance(result, (list, tuple)):
        return result[0] if result else 0
    return result


def get_constraint_name_list(model) -> List[str]:
    """
    获取所有约束名称列表
    
    Returns:
        约束名称列表
    """
    result = model.ConstraintDef.GetNameList(0, [])
    if isinstance(result, (list, tuple)) and len(result) >= 3:
        ret = result[-1]
        if ret == 0:
            names = result[1]
            if names:
                return list(names)
    return []


def get_constraint_type(model, name: str) -> Optional[ConstraintType]:
    """
    获取约束类型
    
    Args:
        name: 约束名称
        
    Returns:
        ConstraintType 枚举，失败返回 None
    """
    result = model.ConstraintDef.GetConstraintType(name, 0)
    if isinstance(result, (list, tuple)) and len(result) >= 2:
        ret = result[-1]
        if ret == 0:
            return ConstraintType(result[0])
    return None


def change_constraint_name(model, old_name: str, new_name: str) -> bool:
    """
    修改约束名称
    
    Returns:
        成功返回 True
    """
    result = model.ConstraintDef.ChangeName(old_name, new_name)
    if isinstance(result, (list, tuple)):
        return result[-1] == 0
    return result == 0


def delete_constraint(model, name: str) -> bool:
    """
    删除约束
    
    Returns:
        成功返回 True
    """
    result = model.ConstraintDef.Delete(name)
    if isinstance(result, (list, tuple)):
        return result[-1] == 0
    return result == 0


# =============================================================================
# Diaphragm 刚性隔板
# =============================================================================

def get_diaphragm(
    model,
    name: str
) -> Optional[Tuple[ConstraintAxis, str]]:
    """
    获取刚性隔板约束定义
    
    Args:
        name: 约束名称
        
    Returns:
        (axis, csys) 元组，失败返回 None
        - axis: 垂直于隔板平面的轴
        - csys: 坐标系名称
    """
    result = model.ConstraintDef.GetDiaphragm(name, 0, "")
    if isinstance(result, (list, tuple)) and len(result) >= 3:
        ret = result[-1]
        if ret == 0:
            return (ConstraintAxis(result[0]), result[1])
    return None


def set_diaphragm(
    model,
    name: str,
    axis: ConstraintAxis = ConstraintAxis.AUTO,
    csys: str = "Global"
) -> bool:
    """
    设置刚性隔板约束
    
    Args:
        name: 约束名称
        axis: 垂直于隔板平面的轴 (默认自动)
        csys: 坐标系名称
        
    Returns:
        成功返回 True
    """
    result = model.ConstraintDef.SetDiaphragm(name, int(axis), csys)
    if isinstance(result, (list, tuple)):
        return result[-1] == 0
    return result == 0


# =============================================================================
# Body 刚体约束
# =============================================================================

def get_body(
    model,
    name: str
) -> Optional[Tuple[List[bool], str]]:
    """
    获取刚体约束定义
    
    Args:
        name: 约束名称
        
    Returns:
        (dof_values, csys) 元组，失败返回 None
        - dof_values: [UX, UY, UZ, RX, RY, RZ] 布尔列表
        - csys: 坐标系名称
    """
    result = model.ConstraintDef.GetBody(name, [], "")
    if isinstance(result, (list, tuple)) and len(result) >= 3:
        ret = result[-1]
        if ret == 0:
            values = list(result[0]) if result[0] else [False] * 6
            return (values, result[1])
    return None


def set_body(
    model,
    name: str,
    dof: List[bool] = None,
    csys: str = "Global"
) -> bool:
    """
    设置刚体约束
    
    Args:
        name: 约束名称
        dof: [UX, UY, UZ, RX, RY, RZ] 布尔列表，默认全 True
        csys: 坐标系名称
        
    Returns:
        成功返回 True
    """
    if dof is None:
        dof = [True] * 6
    result = model.ConstraintDef.SetBody(name, dof, csys)
    if isinstance(result, (list, tuple)):
        return result[-1] == 0
    return result == 0


# =============================================================================
# Equal 等位移约束
# =============================================================================

def get_equal(
    model,
    name: str
) -> Optional[Tuple[List[bool], str]]:
    """
    获取等位移约束定义
    
    Args:
        name: 约束名称
        
    Returns:
        (dof_values, csys) 元组，失败返回 None
        - dof_values: [UX, UY, UZ, RX, RY, RZ] 布尔列表
        - csys: 坐标系名称
    """
    result = model.ConstraintDef.GetEqual(name, [], "")
    if isinstance(result, (list, tuple)) and len(result) >= 3:
        ret = result[-1]
        if ret == 0:
            values = list(result[0]) if result[0] else [False] * 6
            return (values, result[1])
    return None


def set_equal(
    model,
    name: str,
    dof: List[bool] = None,
    csys: str = "Global"
) -> bool:
    """
    设置等位移约束
    
    Args:
        name: 约束名称
        dof: [UX, UY, UZ, RX, RY, RZ] 布尔列表，默认全 True
        csys: 坐标系名称
        
    Returns:
        成功返回 True
    """
    if dof is None:
        dof = [True] * 6
    result = model.ConstraintDef.SetEqual(name, dof, csys)
    if isinstance(result, (list, tuple)):
        return result[-1] == 0
    return result == 0


# =============================================================================
# Local 局部约束
# =============================================================================

def get_local(
    model,
    name: str
) -> Optional[List[bool]]:
    """
    获取局部约束定义
    
    Args:
        name: 约束名称
        
    Returns:
        [U1, U2, U3, R1, R2, R3] 布尔列表，失败返回 None
        
    Note:
        Local 约束使用节点局部坐标系，无需指定坐标系
    """
    result = model.ConstraintDef.GetLocal(name, [])
    if isinstance(result, (list, tuple)) and len(result) >= 2:
        ret = result[-1]
        if ret == 0:
            return list(result[0]) if result[0] else [False] * 6
    return None


def set_local(
    model,
    name: str,
    dof: List[bool] = None
) -> bool:
    """
    设置局部约束
    
    Args:
        name: 约束名称
        dof: [U1, U2, U3, R1, R2, R3] 布尔列表，默认全 True
        
    Returns:
        成功返回 True
        
    Note:
        Local 约束使用节点局部坐标系
    """
    if dof is None:
        dof = [True] * 6
    result = model.ConstraintDef.SetLocal(name, dof)
    if isinstance(result, (list, tuple)):
        return result[-1] == 0
    return result == 0


# =============================================================================
# Beam 梁约束
# =============================================================================

def get_beam(
    model,
    name: str
) -> Optional[Tuple[ConstraintAxis, str]]:
    """
    获取梁约束定义
    
    Args:
        name: 约束名称
        
    Returns:
        (axis, csys) 元组，失败返回 None
        - axis: 平行于梁轴的方向
        - csys: 坐标系名称
    """
    result = model.ConstraintDef.GetBeam(name, 0, "")
    if isinstance(result, (list, tuple)) and len(result) >= 3:
        ret = result[-1]
        if ret == 0:
            return (ConstraintAxis(result[0]), result[1])
    return None


def set_beam(
    model,
    name: str,
    axis: ConstraintAxis = ConstraintAxis.AUTO,
    csys: str = "Global"
) -> bool:
    """
    设置梁约束
    
    Args:
        name: 约束名称
        axis: 平行于梁轴的方向 (默认自动)
        csys: 坐标系名称
        
    Returns:
        成功返回 True
    """
    result = model.ConstraintDef.SetBeam(name, int(axis), csys)
    if isinstance(result, (list, tuple)):
        return result[-1] == 0
    return result == 0


# =============================================================================
# Plate 板约束
# =============================================================================

def get_plate(
    model,
    name: str
) -> Optional[Tuple[ConstraintAxis, str]]:
    """
    获取板约束定义
    
    Args:
        name: 约束名称
        
    Returns:
        (axis, csys) 元组，失败返回 None
        - axis: 垂直于板平面的轴
        - csys: 坐标系名称
    """
    result = model.ConstraintDef.GetPlate(name, 0, "")
    if isinstance(result, (list, tuple)) and len(result) >= 3:
        ret = result[-1]
        if ret == 0:
            return (ConstraintAxis(result[0]), result[1])
    return None


def set_plate(
    model,
    name: str,
    axis: ConstraintAxis = ConstraintAxis.AUTO,
    csys: str = "Global"
) -> bool:
    """
    设置板约束
    
    Args:
        name: 约束名称
        axis: 垂直于板平面的轴 (默认自动)
        csys: 坐标系名称
        
    Returns:
        成功返回 True
    """
    result = model.ConstraintDef.SetPlate(name, int(axis), csys)
    if isinstance(result, (list, tuple)):
        return result[-1] == 0
    return result == 0


# =============================================================================
# Rod 杆约束
# =============================================================================

def get_rod(
    model,
    name: str
) -> Optional[Tuple[ConstraintAxis, str]]:
    """
    获取杆约束定义
    
    Args:
        name: 约束名称
        
    Returns:
        (axis, csys) 元组，失败返回 None
        - axis: 平行于杆轴的方向
        - csys: 坐标系名称
    """
    result = model.ConstraintDef.GetRod(name, 0, "")
    if isinstance(result, (list, tuple)) and len(result) >= 3:
        ret = result[-1]
        if ret == 0:
            return (ConstraintAxis(result[0]), result[1])
    return None


def set_rod(
    model,
    name: str,
    axis: ConstraintAxis = ConstraintAxis.AUTO,
    csys: str = "Global"
) -> bool:
    """
    设置杆约束
    
    Args:
        name: 约束名称
        axis: 平行于杆轴的方向 (默认自动)
        csys: 坐标系名称
        
    Returns:
        成功返回 True
    """
    result = model.ConstraintDef.SetRod(name, int(axis), csys)
    if isinstance(result, (list, tuple)):
        return result[-1] == 0
    return result == 0


# =============================================================================
# Weld 焊接约束
# =============================================================================

def get_weld(
    model,
    name: str
) -> Optional[Tuple[List[bool], float, str]]:
    """
    获取焊接约束定义
    
    Args:
        name: 约束名称
        
    Returns:
        (dof_values, tolerance, csys) 元组，失败返回 None
        - dof_values: [UX, UY, UZ, RX, RY, RZ] 布尔列表
        - tolerance: 焊接容差
        - csys: 坐标系名称
    """
    result = model.ConstraintDef.GetWeld(name, [], 0.0, "")
    if isinstance(result, (list, tuple)) and len(result) >= 4:
        ret = result[-1]
        if ret == 0:
            values = list(result[0]) if result[0] else [False] * 6
            return (values, result[1], result[2])
    return None


def set_weld(
    model,
    name: str,
    dof: List[bool] = None,
    tolerance: float = 0.0,
    csys: str = "Global"
) -> bool:
    """
    设置焊接约束
    
    Args:
        name: 约束名称
        dof: [UX, UY, UZ, RX, RY, RZ] 布尔列表，默认全 True
        tolerance: 焊接容差
        csys: 坐标系名称
        
    Returns:
        成功返回 True
    """
    if dof is None:
        dof = [True] * 6
    result = model.ConstraintDef.SetWeld(name, dof, tolerance, csys)
    if isinstance(result, (list, tuple)):
        return result[-1] == 0
    return result == 0


# =============================================================================
# Line 线约束
# =============================================================================

def get_line(
    model,
    name: str
) -> Optional[Tuple[List[bool], str]]:
    """
    获取线约束定义
    
    Args:
        name: 约束名称
        
    Returns:
        (dof_values, csys) 元组，失败返回 None
        - dof_values: [UX, UY, UZ, RX, RY, RZ] 布尔列表
        - csys: 坐标系名称
    """
    result = model.ConstraintDef.GetLine(name, [], "")
    if isinstance(result, (list, tuple)) and len(result) >= 3:
        ret = result[-1]
        if ret == 0:
            values = list(result[0]) if result[0] else [False] * 6
            return (values, result[1])
    return None


def set_line(
    model,
    name: str,
    dof: List[bool] = None,
    csys: str = "Global"
) -> bool:
    """
    设置线约束
    
    Args:
        name: 约束名称
        dof: [UX, UY, UZ, RX, RY, RZ] 布尔列表，默认全 True
        csys: 坐标系名称
        
    Returns:
        成功返回 True
    """
    if dof is None:
        dof = [True] * 6
    result = model.ConstraintDef.SetLine(name, dof, csys)
    if isinstance(result, (list, tuple)):
        return result[-1] == 0
    return result == 0


# =============================================================================
# 特殊函数
# =============================================================================

def get_special_rigid_diaphragm_list(model) -> List[str]:
    """
    获取特殊刚性隔板列表
    
    Returns:
        刚性隔板约束名称列表
    """
    result = model.ConstraintDef.GetSpecialRigidDiaphragmList(0, [])
    if isinstance(result, (list, tuple)) and len(result) >= 3:
        ret = result[-1]
        if ret == 0:
            names = result[1]
            if names:
                return list(names)
    return []
