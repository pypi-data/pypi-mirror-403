# -*- coding: utf-8 -*-
"""
offset.py - 面单元偏移函数
对应 SAP2000 的 AreaObj 偏移相关 API
"""

from typing import Optional, List

from .enums import AreaOffsetType, ItemType
from .data_classes import AreaOffsetData


def set_area_offset(
    model,
    area_name: str,
    offset_type: AreaOffsetType,
    offset_pattern: str,
    offset_pattern_sf: float,
    offsets: List[float],
    item_type: ItemType = ItemType.OBJECT
) -> int:
    """
    设置面单元偏移
    
    Args:
        model: SapModel 对象
        area_name: 面单元名称
        offset_type: 偏移类型
            - NO_OFFSET: 无偏移
            - BY_JOINT_PATTERN: 按节点模式
            - BY_POINT: 按节点
        offset_pattern: 偏移模式名称 (用于 BY_JOINT_PATTERN)
        offset_pattern_sf: 偏移模式比例因子
        offsets: 偏移值列表 (每个节点一个值，用于 BY_POINT)
        item_type: 项目类型
        
    Returns:
        0 表示成功，非 0 表示失败
        
    Example:
        # 按节点设置偏移
        set_area_offset(model, "1", AreaOffsetType.BY_POINT, "", 1.0, [0.1, 0.1, 0.1, 0.1])
    """
    result = model.AreaObj.SetOffsets(
        str(area_name), int(offset_type), offset_pattern,
        offset_pattern_sf, offsets, int(item_type)
    )
    # 解析返回值
    if isinstance(result, (list, tuple)) and len(result) >= 2:
        return result[-1]
    return result


def set_area_offset_data(
    model,
    area_name: str,
    data: AreaOffsetData,
    item_type: ItemType = ItemType.OBJECT
) -> int:
    """
    使用数据对象设置面单元偏移
    
    Args:
        model: SapModel 对象
        area_name: 面单元名称
        data: AreaOffsetData 对象
        item_type: 项目类型
        
    Returns:
        0 表示成功，非 0 表示失败
        
    Example:
        data = AreaOffsetData(
            offset_type=AreaOffsetType.BY_POINT,
            offsets=[0.1, 0.1, 0.1, 0.1]
        )
        set_area_offset_data(model, "1", data)
    """
    return model.AreaObj.SetOffsets(
        str(area_name), int(data.offset_type), data.offset_pattern,
        data.offset_pattern_sf, data.offsets or [], int(item_type)
    )


def get_area_offset(
    model,
    area_name: str
) -> Optional[AreaOffsetData]:
    """
    获取面单元偏移
    
    Args:
        model: SapModel 对象
        area_name: 面单元名称
        
    Returns:
        AreaOffsetData 对象，失败返回 None
        
    Example:
        data = get_area_offset(model, "1")
        if data:
            print(f"偏移类型: {data.offset_type}")
            print(f"偏移值: {data.offsets}")
    """
    try:
        result = model.AreaObj.GetOffsets(str(area_name), 0, "", 0.0, [])
        if isinstance(result, (list, tuple)) and len(result) >= 5:
            offset_type = AreaOffsetType(result[0]) if result[0] is not None else AreaOffsetType.NO_OFFSET
            offset_pattern = result[1] or ""
            offset_pattern_sf = result[2] or 1.0
            offsets = list(result[3]) if result[3] else None
            ret = result[4]
            
            if ret == 0:
                return AreaOffsetData(
                    offset_type=offset_type,
                    offset_pattern=offset_pattern,
                    offset_pattern_sf=offset_pattern_sf,
                    offsets=offsets
                )
    except Exception:
        pass
    return None


def has_area_offset(
    model,
    area_name: str
) -> bool:
    """
    检查面单元是否有偏移
    
    Args:
        model: SapModel 对象
        area_name: 面单元名称
        
    Returns:
        True 表示有偏移，False 表示无
    """
    data = get_area_offset(model, area_name)
    if data:
        return data.offset_type != AreaOffsetType.NO_OFFSET
    return False
