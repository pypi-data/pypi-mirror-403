# -*- coding: utf-8 -*-
"""
统计功能工具 - 用钢量、用索量

重构: 复用 PySap2000.statistics 模块
"""

from langchain.tools import tool

from .base import get_sap_model, to_json, error_response, safe_sap_call


@tool
@safe_sap_call
def get_steel_usage(group_name: str = "", group_by: str = "section") -> str:
    """
    统计用钢量。返回总重量和按截面/材料分组的明细。
    
    Args:
        group_name: 组名（可选，不填则统计全部杆件）
        group_by: 分组方式，"section" 按截面分组，"material" 按材料分组
    """
    model = get_sap_model()
    
    try:
        from PySap2000.statistics import SteelUsage
        from PySap2000.group import Group
        
        frame_names = None
        if group_name:
            try:
                group = Group.get_by_name(model, group_name)
                frame_names = group.get_frames(model)
            except:
                return error_response(f"组 '{group_name}' 不存在")
        
        usage = SteelUsage.calculate(model, group_by=group_by, frame_names=frame_names)
        
        result = {
            "组名": group_name or "全部",
            "总重量(t)": round(usage.total / 1000, 3),
        }
        
        if group_by == "material" and usage.by_material:
            by_material = [
                {"材料": name, "重量(t)": round(weight / 1000, 3)}
                for name, weight in sorted(usage.by_material.items(), key=lambda x: -x[1])[:15]
            ]
            result["按材料分组"] = by_material
        elif usage.by_section:
            by_section = [
                {"截面": name, "重量(t)": round(weight / 1000, 3)}
                for name, weight in sorted(usage.by_section.items(), key=lambda x: -x[1])[:15]
            ]
            result["按截面分组"] = by_section
        
        return to_json(result, indent=2)
        
    except ImportError:
        # 如果 statistics 模块不存在，使用简化计算
        return _get_steel_usage_simple(model, group_name)


def _get_steel_usage_simple(model, group_name: str) -> str:
    """简化的用钢量计算（备用方法）"""
    from PySap2000.structure_core import Frame
    
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
    
    total_weight = 0
    by_section = {}
    
    for fname in frame_names:
        try:
            frame = Frame.get_by_name(model, fname)
            weight = frame.weight or 0
            total_weight += weight
            
            section = frame.section or "未知"
            by_section[section] = by_section.get(section, 0) + weight
        except:
            pass
    
    result = {
        "组名": group_name or "全部",
        "杆件数": len(frame_names),
        "总重量(t)": round(total_weight / 1000, 3),
        "按截面分组": [
            {"截面": name, "重量(t)": round(weight / 1000, 3)}
            for name, weight in sorted(by_section.items(), key=lambda x: -x[1])[:15]
        ]
    }
    
    return to_json(result, indent=2)


@tool
@safe_sap_call
def get_cable_usage() -> str:
    """统计索材用量。"""
    model = get_sap_model()
    
    try:
        from PySap2000.statistics import CableUsage
        
        usage = CableUsage.calculate(model, group_by="section")
        
        by_section = [
            {"截面": name, "重量(t)": round(weight / 1000, 3)}
            for name, weight in sorted(usage.by_section.items(), key=lambda x: -x[1])[:15]
        ] if usage.by_section else []
        
        return to_json({
            "总重量(t)": round(usage.total / 1000, 3),
            "按截面分组": by_section,
        }, indent=2)
        
    except ImportError:
        # 如果 statistics 模块不存在，返回简化信息
        from PySap2000.structure_core import Cable
        cables = Cable.get_name_list(model)
        return to_json({
            "索单元数": len(cables),
            "提示": "详细统计需要 statistics 模块"
        })
