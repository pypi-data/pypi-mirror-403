# -*- coding: utf-8 -*-
"""
荷载操作工具 - 添加、查询、删除荷载

重构: 复用 PySap2000.loads 模块
"""

from langchain.tools import tool

from .base import get_sap_model, to_json, success_response, error_response, safe_sap_call

# 导入 PySap2000 封装
from PySap2000.loads import (
    set_point_load_force,
    delete_point_load_force,
    set_frame_load_distributed,
    get_frame_load_distributed,
    delete_frame_load_distributed,
    set_frame_load_point,
    delete_frame_load_point,
    FrameLoadDirection,
    # 面荷载
    set_area_load_uniform,
    delete_area_load_uniform,
    AreaLoadDir,
)


@tool
@safe_sap_call
def add_point_load(
    point_name: str, load_pattern: str,
    fx: float = 0, fy: float = 0, fz: float = 0,
    mx: float = 0, my: float = 0, mz: float = 0
) -> str:
    """
    在节点上添加集中荷载。
    
    Args:
        point_name: 节点名称
        load_pattern: 荷载模式名称
        fx, fy, fz: X、Y、Z 方向的力
        mx, my, mz: 绕 X、Y、Z 轴的力矩
    """
    model = get_sap_model()
    model.SetModelIsLocked(False)
    
    forces = (fx, fy, fz, mx, my, mz)
    ret = set_point_load_force(model, point_name, load_pattern, forces)
    
    if ret == 0:
        return success_response(
            "荷载添加成功",
            节点=point_name,
            荷载模式=load_pattern,
            力={"Fx": fx, "Fy": fy, "Fz": fz}
        )
    return error_response("添加荷载失败")


@tool
@safe_sap_call
def delete_point_load(point_name: str, load_pattern: str) -> str:
    """
    删除节点上的荷载。
    
    Args:
        point_name: 节点名称
        load_pattern: 荷载模式名称
    """
    model = get_sap_model()
    model.SetModelIsLocked(False)
    
    ret = delete_point_load_force(model, point_name, load_pattern)
    
    if ret == 0:
        return success_response(
            "节点荷载已删除",
            节点=point_name,
            荷载模式=load_pattern
        )
    return error_response("删除节点荷载失败")


@tool
@safe_sap_call
def add_frame_distributed_load(
    frame_name: str, load_pattern: str, direction: int = 6, value: float = 0
) -> str:
    """
    在杆件上添加均布荷载。
    
    Args:
        frame_name: 杆件名称
        load_pattern: 荷载模式名称
        direction: 荷载方向 (1=局部1, 2=局部2, 3=局部3, 4=X, 5=Y, 6=Z/重力)
        value: 荷载值（负值向下）
    """
    model = get_sap_model()
    model.SetModelIsLocked(False)
    
    # 映射方向枚举
    dir_map = {
        1: FrameLoadDirection.LOCAL_1,
        2: FrameLoadDirection.LOCAL_2,
        3: FrameLoadDirection.LOCAL_3,
        4: FrameLoadDirection.GLOBAL_X,
        5: FrameLoadDirection.GLOBAL_Y,
        6: FrameLoadDirection.GLOBAL_Z,
    }
    load_dir = dir_map.get(direction, FrameLoadDirection.GLOBAL_Z)
    
    ret = set_frame_load_distributed(
        model, frame_name, load_pattern,
        load_type=1,  # 力荷载
        direction=load_dir,
        dist1=0.0, dist2=1.0,
        val1=value, val2=value
    )
    
    if ret == 0:
        return success_response(
            "均布荷载添加成功",
            杆件=frame_name,
            荷载模式=load_pattern,
            荷载值=value
        )
    return error_response("添加荷载失败")


@tool
@safe_sap_call
def add_frame_point_load(
    frame_name: str, load_pattern: str, value: float,
    direction: int = 6, dist: float = 0.5
) -> str:
    """
    在杆件上添加集中荷载。
    
    Args:
        frame_name: 杆件名称
        load_pattern: 荷载模式名称
        value: 荷载值（负值向下）
        direction: 荷载方向 (1=局部1, 2=局部2, 3=局部3, 4=X, 5=Y, 6=Z/重力)
        dist: 荷载位置（0-1之间的相对位置，0.5表示跨中）
    """
    model = get_sap_model()
    model.SetModelIsLocked(False)
    
    dir_map = {
        1: FrameLoadDirection.LOCAL_1,
        2: FrameLoadDirection.LOCAL_2,
        3: FrameLoadDirection.LOCAL_3,
        4: FrameLoadDirection.GLOBAL_X,
        5: FrameLoadDirection.GLOBAL_Y,
        6: FrameLoadDirection.GLOBAL_Z,
    }
    load_dir = dir_map.get(direction, FrameLoadDirection.GLOBAL_Z)
    
    ret = set_frame_load_point(
        model, frame_name, load_pattern,
        load_type=1,
        direction=load_dir,
        dist=dist,
        val=value,
        relative_dist=True
    )
    
    if ret == 0:
        return success_response(
            "集中荷载添加成功",
            杆件=frame_name,
            荷载模式=load_pattern,
            荷载值=value,
            位置=dist
        )
    return error_response("添加荷载失败")


@tool
@safe_sap_call
def get_frame_loads(frame_name: str) -> str:
    """
    获取杆件上的所有荷载。
    
    Args:
        frame_name: 杆件名称
    """
    model = get_sap_model()
    
    # 使用 PySap2000 封装
    loads_data = get_frame_load_distributed(model, frame_name)
    
    if not loads_data:
        return to_json({"杆件": frame_name, "荷载": "无"})
    
    loads = []
    for load in loads_data:
        loads.append({
            "荷载模式": load.load_pattern,
            "荷载值": load.val1,
        })
    
    return to_json({
        "杆件": frame_name,
        "荷载数": len(loads),
        "荷载列表": loads
    })


@tool
@safe_sap_call
def create_load_pattern(name: str, pattern_type: int = 1, self_weight_multiplier: float = 0) -> str:
    """
    创建荷载模式。
    
    Args:
        name: 荷载模式名称
        pattern_type: 类型 (1=恒载, 2=活载, 3=风载, 4=地震, 5=温度, 6=其他)
        self_weight_multiplier: 自重系数（1表示包含自重）
    """
    model = get_sap_model()
    
    type_names = {1: "恒载", 2: "活载", 3: "风载", 4: "地震", 5: "温度", 6: "其他"}
    ret = model.LoadPatterns.Add(name, pattern_type, self_weight_multiplier, True)
    
    if ret == 0:
        return success_response(
            f"荷载模式 '{name}' 创建成功",
            类型=type_names.get(pattern_type, f"类型{pattern_type}"),
            自重系数=self_weight_multiplier
        )
    return error_response("创建荷载模式失败")


@tool
@safe_sap_call
def delete_load_pattern(name: str) -> str:
    """
    删除荷载模式。
    
    Args:
        name: 荷载模式名称
    """
    model = get_sap_model()
    ret = model.LoadPatterns.Delete(name)
    
    if ret == 0:
        return success_response(f"荷载模式 '{name}' 已删除")
    return error_response(f"删除荷载模式 '{name}' 失败")


@tool
@safe_sap_call
def delete_frame_load(frame_name: str, load_pattern: str, load_type: str = "distributed") -> str:
    """
    删除杆件上的荷载。
    
    Args:
        frame_name: 杆件名称
        load_pattern: 荷载模式名称
        load_type: 荷载类型 ("distributed"=均布荷载, "point"=集中荷载)
    """
    model = get_sap_model()
    model.SetModelIsLocked(False)
    
    if load_type == "point":
        ret = delete_frame_load_point(model, frame_name, load_pattern)
    else:
        ret = delete_frame_load_distributed(model, frame_name, load_pattern)
    
    if ret == 0:
        return success_response(
            "杆件荷载已删除",
            杆件=frame_name,
            荷载模式=load_pattern,
            类型=load_type
        )
    return error_response("删除杆件荷载失败")


@tool
@safe_sap_call
def add_area_load(
    area_name: str, load_pattern: str, value: float, direction: int = 10
) -> str:
    """
    在面单元上添加均布荷载。
    
    Args:
        area_name: 面单元名称
        load_pattern: 荷载模式名称
        value: 荷载值（负值向下）
        direction: 荷载方向 (6=Z/重力, 10=重力方向)
    """
    model = get_sap_model()
    model.SetModelIsLocked(False)
    
    # 映射方向枚举
    dir_map = {
        1: AreaLoadDir.LOCAL_1,
        2: AreaLoadDir.LOCAL_2,
        3: AreaLoadDir.LOCAL_3,
        4: AreaLoadDir.GLOBAL_X,
        5: AreaLoadDir.GLOBAL_Y,
        6: AreaLoadDir.GLOBAL_Z,
        10: AreaLoadDir.GRAVITY,
    }
    load_dir = dir_map.get(direction, AreaLoadDir.GRAVITY)
    
    ret = set_area_load_uniform(
        model, area_name, load_pattern,
        value=value,
        direction=load_dir
    )
    
    if ret == 0:
        return success_response(
            "面荷载添加成功",
            面单元=area_name,
            荷载模式=load_pattern,
            荷载值=value
        )
    return error_response("添加面荷载失败")


@tool
@safe_sap_call
def delete_area_load(area_name: str, load_pattern: str) -> str:
    """
    删除面单元上的均布荷载。
    
    Args:
        area_name: 面单元名称
        load_pattern: 荷载模式名称
    """
    model = get_sap_model()
    model.SetModelIsLocked(False)
    
    ret = delete_area_load_uniform(model, area_name, load_pattern)
    
    if ret == 0:
        return success_response(
            "面荷载已删除",
            面单元=area_name,
            荷载模式=load_pattern
        )
    return error_response("删除面荷载失败")
