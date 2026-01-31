# -*- coding: utf-8 -*-
"""
steel_design_tools.py - 钢结构设计工具

功能:
    - 按应力比分组杆件
    - 将分析截面替换为设计截面
    - 统计钢材用量
    - 统计索材用量

Usage:
    from PySap2000.application import Application
    from PySap2000.utils.steel_design_tools import (
        classify_frame_by_stress_ratio,
        replace_with_design_section,
        print_steel_usage,
        print_cable_usage
    )
    
    app = Application()
    model = app.model
    
    # 按应力比分组
    classify_frame_by_stress_ratio(model, ["BeamGroup", "ColumnGroup"])
    
    # 替换为设计截面
    replace_with_design_section(model, ["BeamGroup"])
    
    # 统计钢材用量
    print_steel_usage(model)
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import json
import os
from datetime import datetime


@dataclass
class StressRatioConfig:
    """应力比分组配置"""
    ranges: List[Tuple[float, float, str]] = None
    
    def __post_init__(self):
        if self.ranges is None:
            self.ranges = [
                (0.0, 0.2, "应力比0-0.2"),
                (0.2, 0.4, "应力比0.2-0.4"),
                (0.4, 0.6, "应力比0.4-0.6"),
                (0.6, 0.7, "应力比0.6-0.7"),
                (0.7, 0.8, "应力比0.7-0.8"),
                (0.8, 0.9, "应力比0.8-0.9"),
                (0.9, 1.0, "应力比0.9-1.0"),
            ]
    
    @property
    def group_names(self) -> List[str]:
        """获取所有组名"""
        names = [r[2] for r in self.ranges]
        names.append("应力比大于1")
        return names


def get_frames_from_groups(model, group_names: List[str]) -> List[str]:
    """从多个组中获取所有杆件名称"""
    from PySap2000.group import Group
    
    frame_set = set()
    for group_name in group_names:
        try:
            group = Group.get_by_name(model, group_name)
            frames = group.get_frames(model)
            frame_set.update(frames)
        except Exception:
            pass
    return list(frame_set)


def classify_frame_by_stress_ratio(
    model,
    group_names: List[str],
    config: StressRatioConfig = None,
    clear_groups: bool = True
) -> Dict[str, List[str]]:
    """按应力比将杆件分组，需要先运行钢结构设计才能获取应力比。"""
    from PySap2000.design.steel import get_steel_summary_results
    from PySap2000.design.enums import ItemType
    
    if config is None:
        config = StressRatioConfig()
    
    for group_name in config.group_names:
        model.GroupDef.SetGroup(group_name)
        if clear_groups:
            model.GroupDef.Clear(group_name)
    
    frames = get_frames_from_groups(model, group_names)
    result = {name: [] for name in config.group_names}

    
    for frame in frames:
        summary = get_steel_summary_results(model, frame, ItemType.OBJECT)
        if not summary:
            continue
        
        ratio = summary[0].ratio
        assigned = False
        for low, high, group_name in config.ranges:
            if low <= ratio < high:
                model.FrameObj.SetGroupAssign(frame, group_name, False, 0)
                result[group_name].append(frame)
                assigned = True
                break
        
        if not assigned:
            model.FrameObj.SetGroupAssign(frame, "应力比大于1", False, 0)
            result["应力比大于1"].append(frame)
    
    print("\n应力比分组结果:")
    print("-" * 40)
    for group_name in config.group_names:
        count = len(result[group_name])
        if count > 0:
            print(f"{group_name}: {count} 个杆件")
    print("-" * 40)
    
    return result


def replace_with_design_section(
    model,
    group_names: List[str],
    only_if_different: bool = True,
    run_analysis: bool = False,
    run_design: bool = False
) -> Dict[str, str]:
    """将分析截面替换为设计截面，需要先运行钢结构设计才能获取设计截面。"""
    from PySap2000.design.steel import get_steel_design_section
    from PySap2000.frame.property import get_frame_section
    
    model.SetModelIsLocked(False)
    frames = get_frames_from_groups(model, group_names)
    replaced = {}
    
    for frame in frames:
        design_section = get_steel_design_section(model, frame)
        if not design_section:
            continue
        
        if only_if_different:
            analysis_section = get_frame_section(model, frame)
            if analysis_section == design_section:
                continue

        
        ret = model.FrameObj.SetSection(frame, design_section, 0)
        if ret == 0:
            replaced[frame] = design_section
    
    print(f"\n替换截面完成: {len(replaced)} 个杆件")
    
    if run_analysis and replaced:
        print("正在运行分析...")
        model.Analyze.RunAnalysis()
        print("分析完成")
        
        if run_design:
            print("正在运行钢结构设计...")
            model.SelectObj.ClearSelection()
            for group_name in group_names:
                model.SelectObj.Group(group_name)
            model.DesignSteel.StartDesign()
            print("钢结构设计完成")
    
    return replaced


def _get_history_file(model) -> str:
    """获取历史记录文件路径"""
    filepath = model.GetModelFilepath()
    filename = model.GetModelFilename(False)
    if filepath and filename:
        return os.path.join(filepath, f"{filename}_usage_history.json")
    return "usage_history.json"


def _load_history(history_file: str) -> dict:
    """加载历史记录"""
    if os.path.exists(history_file):
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def _save_history(history_file: str, history: dict):
    """保存历史记录"""
    try:
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except IOError:
        pass


def print_steel_usage(
    model,
    group_name: str = None,
    group_by: str = None,
    save_history: bool = True
):
    """打印钢材用量统计，并与上次记录对比"""
    from statistics import SteelUsage
    
    frame_names = None
    if group_name:
        frame_names = get_frames_from_groups(model, [group_name])
    
    usage = SteelUsage.calculate(model, group_by=group_by, frame_names=frame_names)
    
    history_file = _get_history_file(model)
    history = _load_history(history_file)
    history_key = group_name or "ALL"
    prev_weight = history.get("steel", {}).get(history_key, {}).get("total", 0)
    
    title = f"Steel Usage ({group_name})" if group_name else "Steel Usage"
    print(f"\n{title}")
    print("=" * 40)
    
    if group_by == "section" and usage.by_section:
        print(f"{'Section':<25} {'Weight(t)':>12}")
        print("-" * 40)
        for section, weight in sorted(usage.by_section.items(), key=lambda x: -x[1]):
            print(f"{section:<25} {weight/1000:>12.2f}")
        print("-" * 40)
        
    elif group_by == "material" and usage.by_material:
        print(f"{'Material':<25} {'Weight(t)':>12}")
        print("-" * 40)
        for material, weight in sorted(usage.by_material.items(), key=lambda x: -x[1]):
            print(f"{material:<25} {weight/1000:>12.2f}")
        print("-" * 40)
    
    print(f"Total: {usage.total/1000:.2f} t")
    
    if prev_weight > 0:
        change_t = (usage.total - prev_weight) / 1000
        change_pct = ((usage.total - prev_weight) / prev_weight) * 100
        sign = "+" if change_t >= 0 else ""
        print(f"Change: {sign}{change_t:.2f} t ({sign}{change_pct:.2f}%)")
    
    print("=" * 40)
    
    if save_history:
        if "steel" not in history:
            history["steel"] = {}
        history["steel"][history_key] = {
            "total": usage.total,
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        _save_history(history_file, history)


def print_cable_usage(
    model,
    group_name: str = None,
    group_by: str = None,
    save_history: bool = True
):
    """打印索材用量统计，并与上次记录对比"""
    from statistics import CableUsage
    
    cable_names = None
    if group_name:
        from PySap2000.group import Group
        try:
            group = Group.get_by_name(model, group_name)
            cable_names = group.get_cables(model)
        except Exception:
            cable_names = []
    
    usage = CableUsage.calculate(model, group_by=group_by, cable_names=cable_names)
    
    history_file = _get_history_file(model)
    history = _load_history(history_file)
    history_key = group_name or "ALL"
    prev_weight = history.get("cable", {}).get(history_key, {}).get("total", 0)
    
    title = f"Cable Usage ({group_name})" if group_name else "Cable Usage"
    print(f"\n{title}")
    print("=" * 40)
    
    if group_by == "section" and usage.by_section:
        print(f"{'Section':<25} {'Weight(t)':>12}")
        print("-" * 40)
        for section, weight in sorted(usage.by_section.items(), key=lambda x: -x[1]):
            print(f"{section:<25} {weight/1000:>12.2f}")
        print("-" * 40)
        
    elif group_by == "material" and usage.by_material:
        print(f"{'Material':<25} {'Weight(t)':>12}")
        print("-" * 40)
        for material, weight in sorted(usage.by_material.items(), key=lambda x: -x[1]):
            print(f"{material:<25} {weight/1000:>12.2f}")
        print("-" * 40)
    
    print(f"Total: {usage.total/1000:.2f} t")
    
    if prev_weight > 0:
        change_t = (usage.total - prev_weight) / 1000
        change_pct = ((usage.total - prev_weight) / prev_weight) * 100
        sign = "+" if change_t >= 0 else ""
        print(f"Change: {sign}{change_t:.2f} t ({sign}{change_pct:.2f}%)")
    
    print("=" * 40)
    
    if save_history:
        if "cable" not in history:
            history["cable"] = {}
        history["cable"][history_key] = {
            "total": usage.total,
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        _save_history(history_file, history)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from application import Application
    
    app = Application()
    model = app.model
    
    print_steel_usage(model, group_name="S2_STR")
    print("完成")
