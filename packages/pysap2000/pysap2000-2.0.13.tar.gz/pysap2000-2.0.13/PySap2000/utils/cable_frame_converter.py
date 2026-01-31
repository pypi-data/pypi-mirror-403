# -*- coding: utf-8 -*-
"""
cable_frame_converter.py - 索单元与框架单元互转工具

功能:
    - 将索单元转换为框架单元 (Cable -> Frame)
    - 将框架单元转换为索单元 (Frame -> Cable)
    - 自动创建对应的截面

Usage:
    from PySap2000.application import Application
    from PySap2000.utils.cable_frame_converter import (
        convert_cables_to_frames,
        convert_frames_to_cables
    )
    
    app = Application()
    model = app.model
    
    # 索转框架
    convert_cables_to_frames(model)
    
    # 框架转索
    convert_frames_to_cables(model, section_filter="索")
"""

import math
from typing import List, Optional


def convert_cables_to_frames(
    model,
    cable_names: List[str] = None,
    section_suffix: str = "_Frame"
) -> dict:
    """
    将索单元转换为框架单元
    
    Args:
        model: SapModel 对象
        cable_names: 要转换的索单元名称列表，None 表示全部
        section_suffix: 新框架截面名称后缀
        
    Returns:
        转换结果 {"converted": 数量, "sections_created": [截面名列表]}
        
    Example:
        # 转换所有索单元
        result = convert_cables_to_frames(model)
        print(f"转换了 {result['converted']} 根索单元")
        
        # 转换指定索单元
        result = convert_cables_to_frames(model, cable_names=["1", "2"])
    """
    result = {"converted": 0, "sections_created": []}
    
    # 获取索单元列表
    if cable_names is None:
        ret = model.CableObj.GetNameList(0, [])
        if isinstance(ret, (list, tuple)) and len(ret) >= 2 and ret[-1] == 0:
            cable_names = list(ret[1]) if ret[1] else []
        else:
            cable_names = []
    
    if not cable_names:
        print("没有索单元需要转换")
        return result
    
    # 缓存已创建的截面
    created_sections = set()
    
    for cable_name in cable_names:
        # 获取索单元端点
        ret = model.CableObj.GetPoints(str(cable_name), "", "")
        if not isinstance(ret, (list, tuple)) or len(ret) < 2:
            continue
        point_i = ret[0]
        point_j = ret[1]
        
        # 获取索单元截面
        ret = model.CableObj.GetProperty(str(cable_name), "")
        if not isinstance(ret, (list, tuple)) or len(ret) < 1:
            continue
        cable_section = ret[0]
        
        # 创建对应的框架截面（如果不存在）
        frame_section = cable_section + section_suffix
        if frame_section not in created_sections:
            # 获取索截面属性
            ret = model.PropCable.GetProp(cable_section, "", 0, 0)
            if isinstance(ret, (list, tuple)) and len(ret) >= 2:
                mat_prop = ret[0] or "A992Fy50"
                area_mm2 = float(ret[1]) if ret[1] else 0
                
                # 计算直径 (mm -> m)
                diameter = math.sqrt(4 * area_mm2 / math.pi) / 1000
                
                # 创建圆形截面
                model.PropFrame.SetCircle(frame_section, mat_prop, diameter)
                created_sections.add(frame_section)
                result["sections_created"].append(frame_section)
        
        # 删除索单元
        model.CableObj.Delete(str(cable_name))
        
        # 创建框架单元
        model.FrameObj.AddByPoint(point_i, point_j, "", frame_section, cable_name)
        result["converted"] += 1
    
    print(f"转换完成: {result['converted']} 根索单元 -> 框架单元")
    if result["sections_created"]:
        print(f"创建截面: {result['sections_created']}")
    
    return result


def convert_frames_to_cables(
    model,
    frame_names=None,
    cable_section: str = None,
    use_selected: bool = False,
    section_filter: str = None,
    group_name: str = None
) -> dict:
    """
    将框架单元转换为索单元
    
    Args:
        model: SapModel 对象
        frame_names: 要转换的框架单元名称
            - None: 根据 use_selected 决定
            - str: 单个框架单元名称
            - List[str]: 框架单元名称列表
        cable_section: 索截面名称（必须已存在，必填）
        use_selected: 是否使用选中的框架单元（当 frame_names=None 时生效）
        section_filter: 截面名称过滤（包含此字符串的才转换）
        group_name: 将转换后的索添加到此组
            - None: 默认添加到 "Cable-{截面名称}" 组
            - str: 自定义组名
        
    Returns:
        转换结果 {"converted": 数量, "frames": [转换的框架名], "group": 组名}
        
    Example:
        # 1. 转换选中的框架单元，使用指定索截面
        result = convert_frames_to_cables(
            model, 
            use_selected=True, 
            cable_section="索-Φ20"
        )
        
        # 2. 转换并添加到自定义组
        result = convert_frames_to_cables(
            model, 
            frame_names="1", 
            cable_section="索-Φ20",
            group_name="我的索组"
        )
        
        # 3. 转换多个框架单元
        result = convert_frames_to_cables(
            model, 
            frame_names=["1", "2", "3"], 
            cable_section="索-Φ20"
        )
        
        # 4. 转换截面名包含"索"的框架单元
        result = convert_frames_to_cables(
            model, 
            section_filter="索",
            cable_section="索-Φ20"
        )
    """
    result = {"converted": 0, "frames": [], "group": None}
    
    # 检查必填参数
    if not cable_section:
        print("错误: 必须指定 cable_section 参数")
        print("请先在 SAP2000 中创建索截面，然后传入截面名称")
        return result
    
    # 处理 frame_names 参数
    if frame_names is None:
        if use_selected:
            # 获取选中的框架单元
            ret = model.SelectObj.GetSelected()
            if isinstance(ret, (list, tuple)) and len(ret) >= 4:
                num_selected = ret[0]
                obj_types = list(ret[1]) if ret[1] else []
                obj_names = list(ret[2]) if ret[2] else []
                
                # 过滤出框架单元 (type=2)
                frame_names = [
                    obj_names[i] for i in range(num_selected) 
                    if i < len(obj_types) and obj_types[i] == 2
                ]
            else:
                frame_names = []
        else:
            # 获取所有框架单元
            ret = model.FrameObj.GetNameList(0, [])
            if isinstance(ret, (list, tuple)) and len(ret) >= 2 and ret[-1] == 0:
                frame_names = list(ret[1]) if ret[1] else []
            else:
                frame_names = []
    elif isinstance(frame_names, str):
        # 单个框架单元名称转为列表
        frame_names = [frame_names]
    
    if not frame_names:
        print("没有框架单元需要转换")
        return result
    
    print(f"准备转换 {len(frame_names)} 根框架单元")
    
    # 检查索截面是否存在
    print(f"\n检查索截面 '{cable_section}' ...")
    ret = model.PropCable.GetProp(cable_section, "", 0, 0)
    
    if not isinstance(ret, (list, tuple)):
        print(f"错误: 无法获取索截面 '{cable_section}' 的属性")
        print("请确认截面名称是否正确")
        return result
    
    if ret[-1] != 0:
        print(f"错误: 索截面 '{cable_section}' 不存在（返回码: {ret[-1]}）")
        print("\n请先在 SAP2000 中创建该索截面：")
        print("  1. Define → Section Properties → Cable Sections")
        print("  2. Add New Property")
        print(f"  3. 输入名称: {cable_section}")
        print("  4. 设置材料和面积")
        return result
    
    # 显示索截面信息
    if len(ret) >= 2:
        mat_prop = ret[0] or "未知"
        area_mm2 = float(ret[1]) if ret[1] else 0
        print(f"✓ 索截面存在: {cable_section}")
        print(f"  材料: {mat_prop}")
        print(f"  面积: {area_mm2:.2f} mm²")
    else:
        print(f"✓ 索截面存在: {cable_section}")
    
    print(f"\n开始转换...")
    print("-" * 50)
    
    # 确定组名
    if group_name is None:
        group_name = f"Cable-{cable_section}"
    
    # 创建或清空组
    model.GroupDef.SetGroup(group_name)
    print(f"将索单元添加到组: {group_name}")
    result["group"] = group_name
    
    converted_cables = []  # 记录成功转换的索单元名称
    
    for frame_name in frame_names:
        try:
            # 获取框架单元截面
            ret = model.FrameObj.GetSection(str(frame_name), "", "")
            if not isinstance(ret, (list, tuple)) or len(ret) < 1:
                print(f"警告: 无法获取框架 '{frame_name}' 的截面")
                continue
            frame_section = ret[0]
            
            # 截面过滤
            if section_filter and section_filter not in frame_section:
                continue
            
            # 获取框架单元端点
            ret = model.FrameObj.GetPoints(str(frame_name), "", "")
            if not isinstance(ret, (list, tuple)) or len(ret) < 2:
                print(f"警告: 无法获取框架 '{frame_name}' 的端点")
                continue
            point_i = ret[0]
            point_j = ret[1]
            
            # 先创建索单元（使用临时名称）
            temp_cable_name = f"TEMP_CABLE_{frame_name}"
            ret = model.CableObj.AddByPoint(point_i, point_j, "", cable_section, temp_cable_name)
            
            # 检查创建是否成功
            # AddByPoint 返回 [name, ret_code]，ret_code=0 表示成功
            if isinstance(ret, (list, tuple)):
                actual_name = ret[0] if len(ret) > 0 else None
                ret_code = ret[1] if len(ret) > 1 else -1
            else:
                ret_code = ret
                actual_name = None
            
            if ret_code != 0:
                print(f"错误: 无法创建索单元 '{frame_name}'，返回码: {ret_code}")
                print(f"  可能原因: 索截面 '{cable_section}' 不存在或无效")
                continue
            
            # 创建成功，使用实际创建的名称
            created_cable_name = actual_name if actual_name else temp_cable_name
            
            # 删除框架单元
            ret = model.FrameObj.Delete(str(frame_name))
            if ret != 0:
                print(f"警告: 删除框架 '{frame_name}' 失败，返回码: {ret}")
                # 删除刚创建的索单元
                model.CableObj.Delete(created_cable_name)
                continue
            
            # 如果创建的索名称不是目标名称，重命名
            if created_cable_name != frame_name:
                ret = model.CableObj.ChangeName(created_cable_name, frame_name)
                if ret != 0:
                    print(f"警告: 重命名索单元失败，保持名称为 '{created_cable_name}'")
                    final_cable_name = created_cable_name
                else:
                    final_cable_name = frame_name
            else:
                final_cable_name = frame_name
            
            # 添加到组
            ret = model.CableObj.SetGroupAssign(final_cable_name, group_name, False, 0)
            if ret != 0:
                print(f"警告: 无法将索 '{final_cable_name}' 添加到组 '{group_name}'")
            
            result["converted"] += 1
            result["frames"].append(frame_name)
            converted_cables.append(final_cable_name)
            print(f"✓ 转换成功: {frame_name} -> {final_cable_name}")
            
        except Exception as e:
            print(f"错误: 转换框架 '{frame_name}' 时发生异常: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print("-" * 50)
    print(f"\n转换完成!")
    print(f"  成功: {result['converted']} 根")
    print(f"  失败: {len(frame_names) - result['converted']} 根")
    print(f"  索截面: {cable_section}")
    print(f"  添加到组: {group_name}")
    
    if result["converted"] == 0:
        print("\n⚠️  没有成功转换任何框架单元")
        print("请检查:")
        print(f"  1. 索截面 '{cable_section}' 是否存在")
        print("  2. 框架单元是否被正确选中")
        print("  3. SAP2000 控制台是否有错误信息")
    else:
        print(f"\n✓ 已将 {len(converted_cables)} 根索单元添加到组 '{group_name}'")
    
    return result


# =============================================================================
# 使用示例
# =============================================================================

if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from application import Application
    
    app = Application()
    model = app.model
    
    # ========== 框架转索的多种用法 ==========
    
    # 注意: 必须先在 SAP2000 中创建索截面（如 "索-Φ20"）
    
    # 1. 转换选中的框架单元
    print("\n示例1: 转换选中的框架单元")
    result = convert_frames_to_cables(
        model, 
        use_selected=True, 
        cable_section="d15.2"  # 必须先在 SAP2000 中创建此截面
    )
    
