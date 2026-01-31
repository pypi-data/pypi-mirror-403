# -*- coding: utf-8 -*-
"""
model_extractor.py - 从 SAP2000 提取几何数据

从 SAP2000 模型中提取单元几何信息，转换为标准的 Model3D 对象

优化版本：使用 database_tables 批量读取数据，大幅减少 API 调用次数
"""

from typing import List, Optional, Callable, Dict, Any
import math
import sys
import time
from .element_geometry import Model3D, FrameElement3D, CableElement3D, Point3D
from ..section.cable_section import CableSection
from ..section.frame_section import FrameSection
from ..frame.property import get_frame_material_overwrite
from ..frame.group import get_frame_groups
from ..cable.group import get_cable_groups
from ..database_tables import DatabaseTables


def _print_progress(current: int, total: int, bar_width: int = 30):
    """
    打印对齐的进度条（使用美观的方块符号）
    
    Args:
        current: 当前进度
        total: 总数
        bar_width: 进度条宽度（方块数量）
    """
    if total == 0:
        return
    
    progress = current / total
    filled = int(bar_width * progress)
    
    # 构建进度条：█ 表示已完成，░ 表示未完成
    bar = "█" * filled + "░" * (bar_width - filled)
    percent = int(progress * 100)
    
    # 计算 total 的位数，用于固定宽度对齐
    total_width = len(str(total))
    
    # 固定宽度格式化，确保对齐
    print(f"  [{bar}] {percent:3d}% ({current:>{total_width}}/{total})")


class ModelExtractor:
    """SAP2000 模型几何提取器"""
    
    def __init__(self, sap_model, unit_scale: float = 0.001):
        """
        Args:
            sap_model: SAP2000 的 SapModel 对象
            unit_scale: 单位缩放系数（默认 0.001 = mm -> m）
        """
        self.model = sap_model
        self.unit_scale = unit_scale
    
    def extract_frame_elements(
        self, 
        frame_names: List[str] = None,
        group_name: str = None
    ) -> Model3D:
        """
        提取框架单元几何
        
        Args:
            frame_names: 要提取的框架单元名称列表，None 表示全部
            group_name: 按组过滤
            
        Returns:
            Model3D 对象
            
        Example:
            extractor = ModelExtractor(sap_model)
            model_3d = extractor.extract_frame_elements()
            model_3d.to_json("model.json")
        """
        model_3d = Model3D(model_name="SAP2000_Frame_Model")
        
        # 获取框架单元列表
        if frame_names is None:
            if group_name:
                ret = self.model.GroupDef.GetAssignments(group_name, 0, [], [])
                if isinstance(ret, (list, tuple)) and len(ret) >= 3:
                    obj_types = list(ret[1]) if ret[1] else []
                    obj_names = list(ret[2]) if ret[2] else []
                    # 过滤出框架单元 (type=2)
                    frame_names = [
                        obj_names[i] for i in range(len(obj_types))
                        if obj_types[i] == 2
                    ]
                else:
                    frame_names = []
            else:
                ret = self.model.FrameObj.GetNameList(0, [])
                if isinstance(ret, (list, tuple)) and len(ret) >= 2 and ret[-1] == 0:
                    frame_names = list(ret[1]) if ret[1] else []
                else:
                    frame_names = []
        
        total = len(frame_names)
        print(f"Extracting {total} frame elements...")
        
        # 计算进度更新间隔：显示约 10 次进度
        update_interval = max(1, total // 10)
        last_progress = -1
        
        for idx, frame_name in enumerate(frame_names):
            # 每 10% 显示一次进度
            current_progress = (idx + 1) * 10 // total if total > 0 else 0
            if current_progress > last_progress:
                _print_progress(idx + 1, total)
                last_progress = current_progress
            try:
                # 获取端点
                ret = self.model.FrameObj.GetPoints(str(frame_name), "", "")
                if not isinstance(ret, (list, tuple)) or len(ret) < 2:
                    continue
                point_i_name = ret[0]
                point_j_name = ret[1]
                
                # 获取端点坐标
                ret_i = self.model.PointObj.GetCoordCartesian(point_i_name, 0, 0, 0)
                ret_j = self.model.PointObj.GetCoordCartesian(point_j_name, 0, 0, 0)
                
                if not isinstance(ret_i, (list, tuple)) or not isinstance(ret_j, (list, tuple)):
                    continue
                
                # 应用单位缩放（mm -> m）
                point_i = Point3D(
                    x=ret_i[0] * self.unit_scale, 
                    y=ret_i[1] * self.unit_scale, 
                    z=ret_i[2] * self.unit_scale
                )
                point_j = Point3D(
                    x=ret_j[0] * self.unit_scale, 
                    y=ret_j[1] * self.unit_scale, 
                    z=ret_j[2] * self.unit_scale
                )
                
                # 获取截面
                ret = self.model.FrameObj.GetSection(str(frame_name))
                section_name = ret[0] if isinstance(ret, (list, tuple)) and len(ret) > 0 else ""
                
                # 获取截面类型和参数
                section_type, section_params, _ = self._get_section_info(section_name)
                # 缩放截面参数
                section_params = {k: v * self.unit_scale for k, v in section_params.items()}
                
                # 优先使用材料覆盖项
                material_overwrite = get_frame_material_overwrite(self.model, frame_name)
                if material_overwrite:
                    material = material_overwrite
                else:
                    # 使用 FrameSection 获取截面材料（最可靠）
                    material = ""
                    try:
                        section = FrameSection.get_by_name(self.model, section_name)
                        material = section.material or ""
                    except Exception:
                        pass
                
                # 获取组（使用 get_frame_groups 函数，过滤掉 'ALL' 和系统组）
                groups = get_frame_groups(self.model, frame_name) or []
                # 过滤掉 'ALL' 和以 '~' 开头的系统组
                user_groups = [g for g in groups if g and g != "ALL" and not g.startswith("~")]
                group = user_groups[0] if user_groups else ""
                
                # 创建框架单元对象
                frame_elem = FrameElement3D(
                    name=frame_name,
                    point_i=point_i,
                    point_j=point_j,
                    section_name=section_name,
                    section_type=section_type,
                    section_params=section_params,
                    material=material,
                    group=group,
                )
                
                model_3d.add_element(frame_elem)
                
            except Exception as e:
                # Silently skip failed frames
                continue
        
        print(f"✓ Extracted {len(model_3d.elements)} frame elements")
        return model_3d
    
    def extract_cable_elements(
        self,
        cable_names: List[str] = None,
        group_name: str = None
    ) -> Model3D:
        """
        提取索单元几何
        
        Args:
            cable_names: 要提取的索单元名称列表，None 表示全部
            group_name: 按组过滤
            
        Returns:
            Model3D 对象
        """
        model_3d = Model3D(model_name="SAP2000_Cable_Model")
        
        # 获取索单元列表
        if cable_names is None:
            if group_name:
                ret = self.model.GroupDef.GetAssignments(group_name, 0, [], [])
                if isinstance(ret, (list, tuple)) and len(ret) >= 3:
                    obj_types = list(ret[1]) if ret[1] else []
                    obj_names = list(ret[2]) if ret[2] else []
                    # 过滤出索单元 (type=3)
                    cable_names = [
                        obj_names[i] for i in range(len(obj_types))
                        if obj_types[i] == 3
                    ]
                else:
                    cable_names = []
            else:
                ret = self.model.CableObj.GetNameList(0, [])
                if isinstance(ret, (list, tuple)) and len(ret) >= 2 and ret[-1] == 0:
                    cable_names = list(ret[1]) if ret[1] else []
                else:
                    cable_names = []
        
        total = len(cable_names)
        print(f"Extracting {total} cable elements...")
        
        last_progress = -1
        
        for idx, cable_name in enumerate(cable_names):
            # 每 10% 显示一次进度
            current_progress = (idx + 1) * 10 // total if total > 0 else 0
            if current_progress > last_progress:
                _print_progress(idx + 1, total)
                last_progress = current_progress
            try:
                # 获取端点
                ret = self.model.CableObj.GetPoints(str(cable_name), "", "")
                if not isinstance(ret, (list, tuple)) or len(ret) < 2:
                    continue
                point_i_name = ret[0]
                point_j_name = ret[1]
                
                # 获取端点坐标
                ret_i = self.model.PointObj.GetCoordCartesian(point_i_name, 0, 0, 0)
                ret_j = self.model.PointObj.GetCoordCartesian(point_j_name, 0, 0, 0)
                
                if not isinstance(ret_i, (list, tuple)) or not isinstance(ret_j, (list, tuple)):
                    continue
                
                # 应用单位缩放（mm -> m）
                point_i = Point3D(
                    x=ret_i[0] * self.unit_scale, 
                    y=ret_i[1] * self.unit_scale, 
                    z=ret_i[2] * self.unit_scale
                )
                point_j = Point3D(
                    x=ret_j[0] * self.unit_scale, 
                    y=ret_j[1] * self.unit_scale, 
                    z=ret_j[2] * self.unit_scale
                )
                
                # 获取截面
                ret = self.model.CableObj.GetProperty(str(cable_name), "")
                section_name = ret[0] if isinstance(ret, (list, tuple)) and len(ret) > 0 else ""
                
                # 使用 CableSection 获取截面属性
                material = ""
                area = 0.0
                diameter = 0.0
                
                try:
                    if section_name:
                        cable_section = CableSection.get_by_name(self.model, section_name)
                        material = cable_section.material or ""
                        area = cable_section.area * (self.unit_scale ** 2)  # mm² -> m²
                except Exception:
                    pass
                
                # 根据面积计算等效直径（假设圆形）
                if area > 0:
                    diameter = 2 * (area / 3.14159265359) ** 0.5
                else:
                    diameter = 0.01 * self.unit_scale  # 默认 10mm，也要缩放
                
                # 获取组（使用 get_cable_groups 函数，过滤掉 'ALL' 和系统组）
                groups = get_cable_groups(self.model, cable_name) or []
                # 过滤掉 'ALL' 和以 '~' 开头的系统组
                user_groups = [g for g in groups if g and g != "ALL" and not g.startswith("~")]
                group = user_groups[0] if user_groups else ""
                
                # 创建索单元对象
                cable_elem = CableElement3D(
                    name=cable_name,
                    point_i=point_i,
                    point_j=point_j,
                    section_name=section_name,
                    material=material,
                    group=group,
                    diameter=diameter,
                    area=area,
                    section_type="Circle",  # 索截面默认为圆形
                    section_params={"diameter": diameter}  # 截面参数
                )
                
                model_3d.add_element(cable_elem)
                
            except Exception as e:
                # Silently skip failed cables
                continue
        
        print(f"✓ Extracted {len(model_3d.elements)} cable elements")
        return model_3d
    
    def extract_all_elements(self, group_name: str = None) -> Model3D:
        """
        提取所有单元（框架 + 索）
        
        Args:
            group_name: 按组过滤
            
        Returns:
            Model3D 对象
        """
        model_3d = Model3D(model_name="SAP2000_Complete_Model")
        
        # 提取框架单元
        frame_model = self.extract_frame_elements(group_name=group_name)
        model_3d.elements.extend(frame_model.elements)
        
        # 提取索单元
        cable_model = self.extract_cable_elements(group_name=group_name)
        model_3d.elements.extend(cable_model.elements)
        
        print(f"✓ Total extracted: {len(model_3d.elements)} elements")
        return model_3d
    
    # ==================== 批量提取方法（优化版） ====================
    
    def extract_frame_elements_batch(self, group_name: str = None) -> Model3D:
        """
        批量提取框架单元几何（优化版，使用 database_tables）
        
        使用 database_tables 一次性获取所有数据，大幅减少 API 调用次数。
        对于大模型（5000+ 单元），速度提升 10-50 倍。
        
        Args:
            group_name: 按组过滤（可选）
            
        Returns:
            Model3D 对象
        """
        model_3d = Model3D(model_name="SAP2000_Frame_Model")
        start_time = time.time()
        
        # 1. 批量获取节点坐标
        joints_data = DatabaseTables.get_table_for_display(
            self.model, "Joint Coordinates", group_name=group_name or ""
        )
        if not joints_data:
            return model_3d
        
        # 建立节点坐标索引 {节点名: (x, y, z)}
        joint_coords: Dict[str, tuple] = {}
        for row in joints_data.to_dict_list():
            joint_name = row.get("Joint", "")
            try:
                x = float(row.get("XorR", 0)) * self.unit_scale
                y = float(row.get("Y", 0)) * self.unit_scale
                z = float(row.get("Z", 0)) * self.unit_scale
                joint_coords[joint_name] = (x, y, z)
            except (ValueError, TypeError):
                continue
        
        # 2. 批量获取杆件连接关系
        conn_data = DatabaseTables.get_table_for_display(
            self.model, "Connectivity - Frame", group_name=group_name or ""
        )
        if not conn_data:
            return model_3d
        
        # 建立杆件连接索引 {杆件名: (节点I, 节点J)}
        frame_connectivity: Dict[str, tuple] = {}
        for row in conn_data.to_dict_list():
            frame_name = row.get("Frame", "")
            joint_i = row.get("JointI", "")
            joint_j = row.get("JointJ", "")
            if frame_name and joint_i and joint_j:
                frame_connectivity[frame_name] = (joint_i, joint_j)
        
        # 3. 批量获取截面分配
        section_data = DatabaseTables.get_table_for_display(
            self.model, "Frame Section Assignments", group_name=group_name or ""
        )
        
        # 建立截面分配索引 {杆件名: 截面名}
        frame_sections: Dict[str, str] = {}
        if section_data:
            for row in section_data.to_dict_list():
                frame_name = row.get("Frame", "")
                section_name = row.get("AnalSect", "") or row.get("Section", "")
                if frame_name:
                    frame_sections[frame_name] = section_name
        
        # 4. 预加载截面信息（减少重复调用）
        unique_sections = set(frame_sections.values())
        section_cache: Dict[str, tuple] = {}  # {截面名: (类型, 参数, 材料)}
        
        for section_name in unique_sections:
            if section_name and section_name not in section_cache:
                section_cache[section_name] = self._get_section_info(section_name)
        
        # 5. 批量获取组分配（这个仍需逐个获取，但可以优化）
        frame_groups: Dict[str, str] = {}
        
        for frame_name in frame_connectivity.keys():
            groups = get_frame_groups(self.model, frame_name) or []
            user_groups = [g for g in groups if g and g != "ALL" and not g.startswith("~")]
            frame_groups[frame_name] = user_groups[0] if user_groups else ""
        
        # 6. 组装 FrameElement3D 对象
        for frame_name, (joint_i, joint_j) in frame_connectivity.items():
            try:
                # 获取节点坐标
                if joint_i not in joint_coords or joint_j not in joint_coords:
                    continue
                
                xi, yi, zi = joint_coords[joint_i]
                xj, yj, zj = joint_coords[joint_j]
                
                point_i = Point3D(x=xi, y=yi, z=zi)
                point_j = Point3D(x=xj, y=yj, z=zj)
                
                # 获取截面信息
                section_name = frame_sections.get(frame_name, "")
                section_type, section_params, section_material = section_cache.get(
                    section_name, ("Unknown", {}, "")
                )
                
                # 缩放截面参数
                scaled_params = {k: v * self.unit_scale for k, v in section_params.items()}
                
                # 获取材料（优先使用材料覆盖项）
                material_overwrite = get_frame_material_overwrite(self.model, frame_name)
                material = material_overwrite if material_overwrite else section_material
                
                # 获取组
                group = frame_groups.get(frame_name, "")
                
                # 创建框架单元对象
                frame_elem = FrameElement3D(
                    name=frame_name,
                    point_i=point_i,
                    point_j=point_j,
                    section_name=section_name,
                    section_type=section_type,
                    section_params=scaled_params,
                    material=material,
                    group=group,
                )
                
                model_3d.add_element(frame_elem)
                
            except Exception as e:
                # Silently skip failed frames
                continue
        
        elapsed = time.time() - start_time
        print(f"✓ Extracted {len(model_3d.elements)} frame elements ({elapsed:.2f}s)")
        return model_3d
    
    def extract_cable_elements_batch(self, group_name: str = None) -> Model3D:
        """
        批量提取索单元几何（优化版，使用 database_tables）
        
        Args:
            group_name: 按组过滤（可选）
            
        Returns:
            Model3D 对象
        """
        model_3d = Model3D(model_name="SAP2000_Cable_Model")
        start_time = time.time()
        
        # 1. 获取节点坐标（可能已经有了，但这里独立获取）
        joints_data = DatabaseTables.get_table_for_display(
            self.model, "Joint Coordinates", group_name=group_name or ""
        )
        if not joints_data:
            return model_3d
        
        # 建立节点坐标索引
        joint_coords: Dict[str, tuple] = {}
        for row in joints_data.to_dict_list():
            joint_name = row.get("Joint", "")
            try:
                x = float(row.get("XorR", 0)) * self.unit_scale
                y = float(row.get("Y", 0)) * self.unit_scale
                z = float(row.get("Z", 0)) * self.unit_scale
                joint_coords[joint_name] = (x, y, z)
            except (ValueError, TypeError):
                continue
        
        # 2. 获取索连接关系
        conn_data = DatabaseTables.get_table_for_display(
            self.model, "Connectivity - Cable", group_name=group_name or ""
        )
        if not conn_data:
            return model_3d
        
        cable_connectivity: Dict[str, tuple] = {}
        for row in conn_data.to_dict_list():
            cable_name = row.get("Cable", "")
            joint_i = row.get("JointI", "")
            joint_j = row.get("JointJ", "")
            if cable_name and joint_i and joint_j:
                cable_connectivity[cable_name] = (joint_i, joint_j)
        
        # 3. 获取截面分配
        section_data = DatabaseTables.get_table_for_display(
            self.model, "Cable Section Assignments", group_name=group_name or ""
        )
        
        cable_sections: Dict[str, str] = {}
        if section_data:
            for row in section_data.to_dict_list():
                cable_name = row.get("Cable", "")
                # 字段名是 "CableSect" 而不是 "Section"
                section_name = row.get("CableSect", "") or row.get("Section", "")
                if cable_name:
                    cable_sections[cable_name] = section_name
        
        # 4. 预加载索截面属性
        unique_sections = set(cable_sections.values())
        section_cache: Dict[str, tuple] = {}  # {截面名: (material, area, diameter)}
        
        for section_name in unique_sections:
            if section_name and section_name not in section_cache:
                try:
                    cable_section = CableSection.get_by_name(self.model, section_name)
                    material = cable_section.material or ""
                    area = cable_section.area * (self.unit_scale ** 2)
                    diameter = 2 * (area / 3.14159265359) ** 0.5 if area > 0 else 0.01 * self.unit_scale
                    section_cache[section_name] = (material, area, diameter)
                except Exception as e:
                    # 调试：打印获取截面失败的原因
                    print(f"  Warning: Failed to get cable section '{section_name}': {e}")
                    section_cache[section_name] = ("", 0.0, 0.01 * self.unit_scale)
        
        # 5. 获取组分配
        cable_groups: Dict[str, str] = {}
        for cable_name in cable_connectivity.keys():
            groups = get_cable_groups(self.model, cable_name) or []
            user_groups = [g for g in groups if g and g != "ALL" and not g.startswith("~")]
            cable_groups[cable_name] = user_groups[0] if user_groups else ""
        
        # 6. 组装 CableElement3D 对象
        for cable_name, (joint_i, joint_j) in cable_connectivity.items():
            try:
                if joint_i not in joint_coords or joint_j not in joint_coords:
                    continue
                
                xi, yi, zi = joint_coords[joint_i]
                xj, yj, zj = joint_coords[joint_j]
                
                point_i = Point3D(x=xi, y=yi, z=zi)
                point_j = Point3D(x=xj, y=yj, z=zj)
                
                section_name = cable_sections.get(cable_name, "")
                material, area, diameter = section_cache.get(
                    section_name, ("", 0.0, 0.01 * self.unit_scale)
                )
                
                group = cable_groups.get(cable_name, "")
                
                cable_elem = CableElement3D(
                    name=cable_name,
                    point_i=point_i,
                    point_j=point_j,
                    section_name=section_name,
                    material=material,
                    group=group,
                    diameter=diameter,
                    area=area,
                    section_type="Circle",
                    section_params={"diameter": diameter}
                )
                
                model_3d.add_element(cable_elem)
                
            except Exception as e:
                continue
        
        elapsed = time.time() - start_time
        print(f"✓ Extracted {len(model_3d.elements)} cable elements ({elapsed:.2f}s)")
        return model_3d
    
    def extract_all_elements_batch(self, group_name: str = None) -> Model3D:
        """
        批量提取所有单元（优化版）
        
        使用 database_tables 批量读取，大幅提升性能。
        
        Args:
            group_name: 按组过滤（可选）
            
        Returns:
            Model3D 对象
        """
        model_3d = Model3D(model_name="SAP2000_Complete_Model")
        start_time = time.time()
        
        # 提取框架单元
        frame_model = self.extract_frame_elements_batch(group_name=group_name)
        model_3d.elements.extend(frame_model.elements)
        
        # 提取索单元
        cable_model = self.extract_cable_elements_batch(group_name=group_name)
        model_3d.elements.extend(cable_model.elements)
        
        elapsed = time.time() - start_time
        print(f"✓ Total extracted: {len(model_3d.elements)} elements ({elapsed:.2f}s)")
        return model_3d
    
    def _get_section_info(self, section_name: str) -> tuple:
        """
        获取截面类型、参数和材料
        
        Returns:
            (section_type, section_params, material)
        """
        try:
            # 确保 section_name 是字符串
            section_name = str(section_name)
            
            # 获取截面类型
            ret = self.model.PropFrame.GetTypeOAPI(section_name)
            if not isinstance(ret, (list, tuple)) or len(ret) < 2 or ret[-1] != 0:
                return ("Unknown", {}, "")
            
            type_val = ret[0]
            
            # 圆形截面 (9)
            if type_val == 9:
                ret = self.model.PropFrame.GetCircle(section_name)
                if isinstance(ret, (list, tuple)) and ret[-1] == 0 and len(ret) >= 3:
                    material = ret[1] or "" if len(ret) >= 2 else ""
                    return ("Circle", {"diameter": ret[2]}, material)
            
            # 矩形截面 (8)
            elif type_val == 8:
                ret = self.model.PropFrame.GetRectangle(section_name)
                if isinstance(ret, (list, tuple)) and ret[-1] == 0 and len(ret) >= 4:
                    material = ret[1] or "" if len(ret) >= 2 else ""
                    return ("Rect", {"height": ret[2], "width": ret[3]}, material)
            
            # 圆管截面 (7)
            elif type_val == 7:
                ret = self.model.PropFrame.GetPipe(section_name)
                if isinstance(ret, (list, tuple)) and ret[-1] == 0 and len(ret) >= 4:
                    material = ret[1] or "" if len(ret) >= 2 else ""
                    return ("Pipe", {
                        "outer_diameter": ret[2],
                        "wall_thickness": ret[3]
                    }, material)
            
            # 箱形截面 (6)
            elif type_val == 6:
                ret = self.model.PropFrame.GetTube_1(section_name)
                if isinstance(ret, (list, tuple)) and ret[-1] == 0 and len(ret) >= 6:
                    material = ret[1] or "" if len(ret) >= 2 else ""
                    return ("Box", {
                        "height": ret[2],
                        "width": ret[3],
                        "flange_thickness": ret[4],
                        "web_thickness": ret[5]
                    }, material)
            
            # 工字钢截面 (1)
            elif type_val == 1:
                ret = self.model.PropFrame.GetISection_1(section_name)
                if isinstance(ret, (list, tuple)) and ret[-1] == 0 and len(ret) >= 8:
                    material = ret[1] or "" if len(ret) >= 2 else ""
                    return ("I", {
                        "height": ret[2],
                        "top_width": ret[3],
                        "flange_thickness": ret[4],
                        "web_thickness": ret[5],
                        "bottom_width": ret[6],
                        "bottom_flange_thickness": ret[7]
                    }, material)
            
            # 槽钢截面 (2)
            elif type_val == 2:
                ret = self.model.PropFrame.GetChannel_2(section_name)
                if isinstance(ret, (list, tuple)) and ret[-1] == 0 and len(ret) >= 7:
                    material = ret[1] or "" if len(ret) >= 2 else ""
                    return ("Channel", {
                        "height": ret[2],
                        "width": ret[3],
                        "flange_thickness": ret[4],
                        "web_thickness": ret[5],
                        "mirror": ret[6]
                    }, material)
            
            # T型钢截面 (3)
            elif type_val == 3:
                ret = self.model.PropFrame.GetTee_1(section_name)
                if isinstance(ret, (list, tuple)) and ret[-1] == 0 and len(ret) >= 7:
                    material = ret[1] or "" if len(ret) >= 2 else ""
                    return ("Tee", {
                        "height": ret[2],
                        "width": ret[3],
                        "flange_thickness": ret[4],
                        "web_thickness": ret[5],
                        "mirror": ret[6]
                    }, material)
            
            # 角钢截面 (4)
            elif type_val == 4:
                ret = self.model.PropFrame.GetAngle_1(section_name)
                if isinstance(ret, (list, tuple)) and ret[-1] == 0 and len(ret) >= 6:
                    material = ret[1] or "" if len(ret) >= 2 else ""
                    return ("Angle", {
                        "height": ret[2],
                        "width": ret[3],
                        "flange_thickness": ret[4],
                        "web_thickness": ret[5]
                    }, material)
            
            # 未知类型或未匹配，使用 FrameSection 获取材料
            material = ""
            try:
                section = FrameSection.get_by_name(self.model, section_name)
                material = section.material or ""
            except Exception:
                pass
            return ("Unknown", {}, material)
            
        except Exception as e:
            print(f"警告: 获取截面 '{section_name}' 信息失败: {e}")
            return ("Unknown", {}, "")
