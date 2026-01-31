# -*- coding: utf-8 -*-
"""
分析与设计工具 - 运行分析、钢结构设计

重构: 复用 PySap2000.analyze 和 PySap2000.design 模块
"""

from langchain.tools import tool

from .base import get_sap_model, to_json, success_response, error_response, safe_sap_call

# 导入 PySap2000 封装
from PySap2000.structure_core import Frame


@tool
@safe_sap_call
def run_analysis() -> str:
    """运行 SAP2000 结构分析。"""
    model = get_sap_model()
    ret = model.Analyze.RunAnalysis()
    
    if ret == 0:
        return success_response("分析完成")
    return error_response(f"分析失败，返回码 {ret}")


@tool
@safe_sap_call
def run_steel_design() -> str:
    """运行钢结构设计。需要先运行分析。"""
    model = get_sap_model()
    ret = model.DesignSteel.StartDesign()
    
    if ret == 0:
        return success_response("钢结构设计完成")
    return error_response(f"设计失败，返回码 {ret}")


@tool
@safe_sap_call
def get_stress_ratios(top_n: int = 20) -> str:
    """
    获取钢结构设计的应力比结果。需要先运行钢结构设计。
    
    Args:
        top_n: 返回应力比最大的前 N 个杆件，默认 20
    """
    model = get_sap_model()
    
    # 使用 PySap2000 封装
    try:
        from PySap2000.design.steel import get_steel_summary_results
        from PySap2000.design.enums import ItemType
    except ImportError:
        # 如果模块不存在，使用直接 API 调用
        return _get_stress_ratios_direct(model, top_n)
    
    frame_names = Frame.get_name_list(model)
    results = []
    
    for fname in frame_names:
        try:
            summary = get_steel_summary_results(model, fname, ItemType.OBJECT)
            if summary:
                sr = summary[0]
                results.append({
                    "杆件": sr.frame_name,
                    "应力比": round(sr.ratio, 3),
                    "控制组合": sr.combo_name
                })
        except:
            pass
    
    return _format_stress_ratio_results(results, top_n)


def _get_stress_ratios_direct(model, top_n: int) -> str:
    """直接使用 API 获取应力比（备用方法）"""
    frame_names = Frame.get_name_list(model)
    results = []
    
    for fname in frame_names:
        try:
            ret = model.DesignSteel.GetSummaryResults(fname, 0, [], [], [], [], [], [], [], [], [], [], 0)
            if isinstance(ret, (list, tuple)) and ret[0] > 0:
                ratio = ret[4][0] if ret[4] else 0
                combo = ret[6][0] if ret[6] else ""
                results.append({"杆件": fname, "应力比": round(ratio, 3), "控制组合": combo})
        except:
            pass
    
    return _format_stress_ratio_results(results, top_n)


def _format_stress_ratio_results(results: list, top_n: int) -> str:
    """格式化应力比结果"""
    results.sort(key=lambda x: x["应力比"], reverse=True)
    ratios = [r["应力比"] for r in results]
    
    if not ratios:
        return error_response("无应力比结果，请先运行钢结构设计")
    
    stats = {
        "总数": len(ratios),
        "最大": round(max(ratios), 3),
        "最小": round(min(ratios), 3),
        "平均": round(sum(ratios) / len(ratios), 3),
        "超过0.9": len([r for r in ratios if r > 0.9]),
        "超过1.0": len([r for r in ratios if r > 1.0]),
    }
    
    # 计算分布
    ranges = [
        (0.0, 0.2, "0-0.2"), (0.2, 0.4, "0.2-0.4"), (0.4, 0.6, "0.4-0.6"),
        (0.6, 0.8, "0.6-0.8"), (0.8, 0.9, "0.8-0.9"), (0.9, 1.0, "0.9-1.0"),
        (1.0, 999, ">1.0")
    ]
    distribution = [
        {"区间": r[2], "数量": len([x for x in ratios if r[0] <= x < r[1]])}
        for r in ranges
    ]
    
    return to_json({
        "统计": stats,
        "分布": distribution,
        f"前{top_n}名": results[:top_n],
    }, indent=2)


@tool
@safe_sap_call
def verify_steel_design() -> str:
    """
    验证钢结构设计是否通过。需要先运行钢结构设计。
    返回未通过设计检查的杆件列表。
    """
    model = get_sap_model()
    ret = model.DesignSteel.VerifyPassed(0, 0, 0, [])
    
    if not isinstance(ret, (list, tuple)) or len(ret) < 4:
        return error_response("无法获取设计验证结果，请先运行钢结构设计")
    
    total = ret[0]
    failed = ret[1]
    unchecked = ret[2]
    failed_names = list(ret[3]) if ret[3] else []
    
    passed = total - failed - unchecked
    
    return to_json({
        "总杆件数": total,
        "通过": passed,
        "未通过": failed,
        "未检查": unchecked,
        "通过率": f"{passed/total*100:.1f}%" if total > 0 else "0%",
        "未通过杆件": failed_names[:30]
    }, indent=2)
