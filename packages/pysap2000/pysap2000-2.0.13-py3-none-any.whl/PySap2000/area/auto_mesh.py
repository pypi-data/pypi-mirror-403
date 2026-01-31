# -*- coding: utf-8 -*-
"""
auto_mesh.py - 面单元自动网格划分函数
对应 SAP2000 的 AreaObj 自动网格划分相关 API
"""

from typing import Optional

from .enums import AreaMeshType, ItemType
from .data_classes import AreaAutoMeshData


def set_area_auto_mesh(
    model,
    area_name: str,
    mesh_type: AreaMeshType,
    n1: int = 2,
    n2: int = 2,
    max_size1: float = 0.0,
    max_size2: float = 0.0,
    point_on_edge_from_line: bool = False,
    point_on_edge_from_point: bool = False,
    extend_cookie_cut_lines: bool = False,
    rotation: float = 0.0,
    max_size_general: float = 0.0,
    local_axes_on_edge: bool = False,
    local_axes_on_face: bool = False,
    restraints_on_edge: bool = False,
    restraints_on_face: bool = False,
    group: str = "ALL",
    sub_mesh: bool = False,
    sub_mesh_size: float = 0.0,
    item_type: ItemType = ItemType.OBJECT
) -> int:
    """
    设置面单元自动网格划分
    
    Args:
        model: SapModel 对象
        area_name: 面单元名称
        mesh_type: 网格划分类型
            - NO_MESH: 不划分
            - MESH_BY_NUMBER: 按数量划分
            - MESH_BY_MAX_SIZE: 按最大尺寸划分
            - MESH_BY_POINTS_ON_EDGE: 按边上点划分
            - COOKIE_CUT_BY_LINES: 按线切割
            - COOKIE_CUT_BY_POINTS: 按点切割
            - GENERAL_DIVIDE: 通用划分
        n1, n2: 划分数量 (用于 MESH_BY_NUMBER)
        max_size1, max_size2: 最大尺寸 (用于 MESH_BY_MAX_SIZE)
        point_on_edge_from_line: 从线获取边上点
        point_on_edge_from_point: 从点获取边上点
        extend_cookie_cut_lines: 延伸切割线
        rotation: 旋转角度
        max_size_general: 通用最大尺寸
        local_axes_on_edge: 边上局部轴
        local_axes_on_face: 面上局部轴
        restraints_on_edge: 边上约束
        restraints_on_face: 面上约束
        group: 组名称
        sub_mesh: 是否子网格
        sub_mesh_size: 子网格尺寸
        item_type: 项目类型
        
    Returns:
        0 表示成功，非 0 表示失败
        
    Example:
        # 按数量划分 (4x4)
        set_area_auto_mesh(model, "1", AreaMeshType.MESH_BY_NUMBER, n1=4, n2=4)
        
        # 按最大尺寸划分
        set_area_auto_mesh(model, "1", AreaMeshType.MESH_BY_MAX_SIZE, max_size1=0.5, max_size2=0.5)
    """
    return model.AreaObj.SetAutoMesh(
        str(area_name), int(mesh_type), n1, n2, max_size1, max_size2,
        point_on_edge_from_line, point_on_edge_from_point,
        extend_cookie_cut_lines, rotation, max_size_general,
        local_axes_on_edge, local_axes_on_face,
        restraints_on_edge, restraints_on_face,
        group, sub_mesh, sub_mesh_size, int(item_type)
    )


def set_area_auto_mesh_data(
    model,
    area_name: str,
    data: AreaAutoMeshData,
    item_type: ItemType = ItemType.OBJECT
) -> int:
    """
    使用数据对象设置面单元自动网格划分
    
    Args:
        model: SapModel 对象
        area_name: 面单元名称
        data: AreaAutoMeshData 对象
        item_type: 项目类型
        
    Returns:
        0 表示成功，非 0 表示失败
        
    Example:
        data = AreaAutoMeshData(mesh_type=AreaMeshType.MESH_BY_NUMBER, n1=4, n2=4)
        set_area_auto_mesh_data(model, "1", data)
    """
    return model.AreaObj.SetAutoMesh(
        str(area_name), int(data.mesh_type), data.n1, data.n2,
        data.max_size1, data.max_size2,
        data.point_on_edge_from_line, data.point_on_edge_from_point,
        data.extend_cookie_cut_lines, data.rotation, data.max_size_general,
        data.local_axes_on_edge, data.local_axes_on_face,
        data.restraints_on_edge, data.restraints_on_face,
        data.group, data.sub_mesh, data.sub_mesh_size, int(item_type)
    )


def get_area_auto_mesh(
    model,
    area_name: str
) -> Optional[AreaAutoMeshData]:
    """
    获取面单元自动网格划分设置
    
    Args:
        model: SapModel 对象
        area_name: 面单元名称
        
    Returns:
        AreaAutoMeshData 对象，失败返回 None
        
    Example:
        data = get_area_auto_mesh(model, "1")
        if data:
            print(f"网格类型: {data.mesh_type}")
            print(f"划分数量: {data.n1} x {data.n2}")
    """
    try:
        result = model.AreaObj.GetAutoMesh(
            str(area_name), 0, 0, 0, 0.0, 0.0, False, False, False, 0.0, 0.0,
            False, False, False, False, "", False, 0.0
        )
        if isinstance(result, (list, tuple)) and len(result) >= 18:
            return AreaAutoMeshData(
                mesh_type=AreaMeshType(result[0]) if result[0] is not None else AreaMeshType.NO_MESH,
                n1=result[1] or 2,
                n2=result[2] or 2,
                max_size1=result[3] or 0.0,
                max_size2=result[4] or 0.0,
                point_on_edge_from_line=result[5] or False,
                point_on_edge_from_point=result[6] or False,
                extend_cookie_cut_lines=result[7] or False,
                rotation=result[8] or 0.0,
                max_size_general=result[9] or 0.0,
                local_axes_on_edge=result[10] or False,
                local_axes_on_face=result[11] or False,
                restraints_on_edge=result[12] or False,
                restraints_on_face=result[13] or False,
                group=result[14] or "ALL",
                sub_mesh=result[15] or False,
                sub_mesh_size=result[16] or 0.0
            )
    except Exception:
        pass
    return None


def is_area_meshed(
    model,
    area_name: str
) -> bool:
    """
    检查面单元是否设置了自动网格划分
    
    Args:
        model: SapModel 对象
        area_name: 面单元名称
        
    Returns:
        True 表示有网格划分，False 表示无
    """
    data = get_area_auto_mesh(model, area_name)
    if data:
        return data.mesh_type != AreaMeshType.NO_MESH
    return False
