# -*- coding: utf-8 -*-
"""
组合工具模块 - 常用多步骤操作的封装

将常见的多步骤操作封装为单个工具，减少对话轮数，提高执行效率。

包含：
- full_design_check: 一键设计验算（分析 + 设计 + 应力比）
- steel_usage_report: 用钢量报告（统计 + 绘图）
- model_overview: 模型概览（模型信息 + 截面 + 材料 + 组）
"""

from langchain_core.tools import tool
from typing import Optional
from .base import get_sap_model, safe_sap_call, success_response, error_response, to_json


@tool
def full_design_check(group_name: str = "ALL", design_code: str = "auto") -> str:
    """
    一键钢结构设计验算：运行分析 → 运行设计 → 获取应力比
    
    Args:
        group_name: 要检查的组名，默认 "ALL" 表示全部
        design_code: 设计规范，"auto" 自动检测，或指定如 "Chinese"
        
    Returns:
        设计验算结果，包含应力比汇总
    """
    try:
        sap = get_sap_model()
        results = []
        
        # 步骤1：运行分析
        results.append("📊 **步骤1: 运行结构分析**")
        ret = sap.analyze.run_analysis()
        if ret != 0:
            return error_response(f"分析运行失败，错误码: {ret}")
        results.append("✓ 分析完成")
        
        # 步骤2：运行钢结构设计
        results.append("\n🔧 **步骤2: 运行钢结构设计**")
        ret = sap.design.steel.start_design()
        if ret != 0:
            return error_response(f"钢结构设计运行失败，错误码: {ret}")
        results.append("✓ 设计完成")
        
        # 步骤3：获取应力比
        results.append("\n📈 **步骤3: 应力比结果**")
        
        # 获取杆件列表
        if group_name == "ALL":
            frame_names = sap.frame.get_name_list()
        else:
            frame_names = sap.group.get_assigned_frames(group_name)
        
        if not frame_names:
            return error_response("未找到杆件")
        
        # 获取应力比
        stress_data = []
        max_ratio = 0
        max_frame = ""
        over_limit_count = 0
        
        for name in frame_names[:100]:  # 限制数量避免过长
            try:
                ratio_data = sap.design.steel.get_summary_results(name)
                if ratio_data and len(ratio_data) > 0:
                    ratio = ratio_data[0].get('Ratio', 0) if isinstance(ratio_data[0], dict) else 0
                    if ratio > 0:
                        stress_data.append({
                            "杆件": name,
                            "应力比": round(ratio, 3)
                        })
                        if ratio > max_ratio:
                            max_ratio = ratio
                            max_frame = name
                        if ratio > 1.0:
                            over_limit_count += 1
            except:
                pass
        
        # 汇总结果
        results.append(f"\n**汇总统计:**")
        results.append(f"- 检查杆件数: {len(stress_data)}")
        results.append(f"- 最大应力比: {max_ratio:.3f} (杆件 {max_frame})")
        results.append(f"- 超限杆件数: {over_limit_count}")
        
        if max_ratio <= 1.0:
            results.append(f"\n✅ **验算通过** - 所有杆件应力比均小于 1.0")
        else:
            results.append(f"\n⚠️ **验算不通过** - 有 {over_limit_count} 根杆件超限，需要加强截面")
        
        # 显示前10个最大应力比
        if stress_data:
            stress_data.sort(key=lambda x: x['应力比'], reverse=True)
            results.append(f"\n**应力比最大的10根杆件:**")
            for item in stress_data[:10]:
                status = "⚠️" if item['应力比'] > 1.0 else "✓"
                results.append(f"  {status} {item['杆件']}: {item['应力比']}")
        
        return "\n".join(results)
        
    except Exception as e:
        return error_response(f"设计验算失败: {str(e)}")


@tool
def steel_usage_report(group_name: str = "ALL", group_by: str = "section", include_chart: bool = True) -> str:
    """
    用钢量统计报告：统计用钢量并可选生成图表
    
    Args:
        group_name: 统计的组名，默认 "ALL" 表示全部
        group_by: 分组方式，"section"(按截面) 或 "group"(按组)
        include_chart: 是否生成饼图，默认 True
        
    Returns:
        用钢量统计报告
    """
    try:
        sap = get_sap_model()
        results = []
        
        results.append("📊 **用钢量统计报告**\n")
        
        # 获取杆件列表
        if group_name == "ALL":
            frame_names = sap.frame.get_name_list()
        else:
            frame_names = sap.group.get_assigned_frames(group_name)
        
        if not frame_names:
            return error_response("未找到杆件")
        
        # 按截面或组统计
        usage_dict = {}
        total_weight = 0
        
        for name in frame_names:
            try:
                # 获取杆件信息
                info = sap.frame.get_obj_info(name)
                length = info.get('length', 0) if info else 0
                section_name = sap.frame.get_section(name)
                
                # 获取截面属性（线重量）
                sec_props = sap.section.get_property(section_name)
                unit_weight = sec_props.get('weight_per_length', 0) if sec_props else 0
                
                weight = length * unit_weight / 1000  # 转换为吨
                total_weight += weight
                
                if group_by == "section":
                    key = section_name
                else:
                    # 按组分
                    groups = sap.frame.get_group_assign(name)
                    key = groups[0] if groups else "未分组"
                
                if key not in usage_dict:
                    usage_dict[key] = {"weight": 0, "count": 0, "length": 0}
                usage_dict[key]["weight"] += weight
                usage_dict[key]["count"] += 1
                usage_dict[key]["length"] += length
                
            except:
                pass
        
        # 排序并输出
        sorted_items = sorted(usage_dict.items(), key=lambda x: x[1]["weight"], reverse=True)
        
        results.append(f"**总用钢量: {total_weight:.2f} 吨**\n")
        results.append(f"| {'截面' if group_by == 'section' else '组'} | 数量 | 长度(m) | 重量(t) | 占比 |")
        results.append("|---|---|---|---|---|")
        
        chart_data = {}
        for name, data in sorted_items[:15]:  # 最多显示15项
            percent = (data["weight"] / total_weight * 100) if total_weight > 0 else 0
            results.append(f"| {name} | {data['count']} | {data['length']:.1f} | {data['weight']:.2f} | {percent:.1f}% |")
            chart_data[name] = round(data["weight"], 2)
        
        # 生成图表数据（如果需要）
        if include_chart and chart_data:
            results.append(f"\n💡 **提示**: 可以使用 draw_chart 工具绑制饼图可视化，数据: {to_json(chart_data)}")
        
        return "\n".join(results)
        
    except Exception as e:
        return error_response(f"用钢量统计失败: {str(e)}")


@tool  
def model_overview() -> str:
    """
    模型概览：一次性获取模型基本信息、截面列表、材料列表、组列表
    
    Returns:
        模型概览信息
    """
    try:
        sap = get_sap_model()
        results = []
        
        results.append("📋 **模型概览**\n")
        
        # 1. 基本信息
        results.append("### 1. 基本信息")
        try:
            filename = sap.file.get_file_name()
            results.append(f"- 文件名: {filename}")
        except:
            results.append("- 文件名: (未保存)")
        
        # 对象数量统计
        try:
            point_count = len(sap.point.get_name_list() or [])
            frame_count = len(sap.frame.get_name_list() or [])
            area_count = len(sap.area.get_name_list() or [])
            results.append(f"- 节点数: {point_count}")
            results.append(f"- 杆件数: {frame_count}")
            results.append(f"- 面单元数: {area_count}")
        except:
            pass
        
        # 2. 截面列表
        results.append("\n### 2. 截面列表")
        try:
            sections = sap.section.get_name_list()
            if sections:
                results.append(f"共 {len(sections)} 个截面:")
                for sec in sections[:20]:  # 最多显示20个
                    results.append(f"  - {sec}")
                if len(sections) > 20:
                    results.append(f"  - ... (还有 {len(sections) - 20} 个)")
            else:
                results.append("  (无截面)")
        except:
            results.append("  (获取失败)")
        
        # 3. 材料列表
        results.append("\n### 3. 材料列表")
        try:
            materials = sap.material.get_name_list()
            if materials:
                results.append(f"共 {len(materials)} 种材料:")
                for mat in materials[:15]:
                    results.append(f"  - {mat}")
            else:
                results.append("  (无材料)")
        except:
            results.append("  (获取失败)")
        
        # 4. 组列表
        results.append("\n### 4. 组列表")
        try:
            groups = sap.group.get_name_list()
            # 过滤系统组
            user_groups = [g for g in groups if not g.startswith("~")]
            if user_groups:
                results.append(f"共 {len(user_groups)} 个用户组:")
                for grp in user_groups[:20]:
                    results.append(f"  - {grp}")
            else:
                results.append("  (无用户组)")
        except:
            results.append("  (获取失败)")
        
        # 5. 荷载模式
        results.append("\n### 5. 荷载模式")
        try:
            patterns = sap.load.pattern.get_name_list()
            if patterns:
                results.append(f"共 {len(patterns)} 个荷载模式:")
                for pat in patterns[:10]:
                    results.append(f"  - {pat}")
            else:
                results.append("  (无荷载模式)")
        except:
            results.append("  (获取失败)")
        
        return "\n".join(results)
        
    except Exception as e:
        return error_response(f"获取模型概览失败: {str(e)}")


# 导出工具列表
COMBO_TOOLS = [
    full_design_check,
    steel_usage_report,
    model_overview,
]
