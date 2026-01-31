# -*- coding: utf-8 -*-
"""
分析软件互操作基类

所有分析软件导出器的共同特点：
- 只需要结构数据（节点、单元、截面属性）
- 不需要截面轮廓和3D网格
- 用于结构分析计算
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class AnalysisExporter(ABC):
    """分析软件导出器基类"""
    
    def __init__(self):
        """初始化分析软件导出器"""
        pass
    
    @abstractmethod
    def export(self, model_3d: Any, output_path: str) -> None:
        """
        导出模型为目标软件格式
        
        Args:
            model_3d: 3D模型数据
            output_path: 输出文件路径
        """
        pass
    
    def export_nodes(self, model_3d: Any) -> List[Dict]:
        """
        导出节点数据
        
        Args:
            model_3d: 3D模型数据
            
        Returns:
            节点列表 [{"id": 1, "x": 0, "y": 0, "z": 0}, ...]
        """
        nodes = []
        for point in model_3d.points:
            nodes.append({
                "id": point.name,
                "x": point.x,
                "y": point.y,
                "z": point.z
            })
        return nodes
    
    def export_elements(self, model_3d: Any) -> List[Dict]:
        """
        导出单元数据
        
        Args:
            model_3d: 3D模型数据
            
        Returns:
            单元列表 [{"id": 1, "nodes": [1, 2], "section": "W12X26"}, ...]
        """
        elements = []
        for elem in model_3d.elements:
            elements.append({
                "id": elem.name,
                "nodes": [elem.point_i, elem.point_j],
                "section": elem.section_name,
                "material": elem.material
            })
        return elements
    
    def export_section_properties(self, model_3d: Any) -> List[Dict]:
        """
        导出截面属性（不含轮廓）
        
        Args:
            model_3d: 3D模型数据
            
        Returns:
            截面属性列表 [{"name": "W12X26", "area": 0.01, "Ixx": 0.001, ...}, ...]
        """
        sections = []
        # 从 section_params 提取数值属性
        for elem in model_3d.elements:
            if elem.section_name not in [s["name"] for s in sections]:
                sections.append({
                    "name": elem.section_name,
                    "type": elem.section_type,
                    "params": elem.section_params  # 只有数值，不含轮廓
                })
        return sections
    
    def export_materials(self, model_3d: Any) -> List[Dict]:
        """
        导出材料数据
        
        Args:
            model_3d: 3D模型数据
            
        Returns:
            材料列表 [{"name": "STEEL", "E": 2e11, "nu": 0.3, ...}, ...]
        """
        materials = []
        # 提取唯一材料
        unique_materials = set(elem.material for elem in model_3d.elements)
        for mat in unique_materials:
            materials.append({
                "name": mat,
                # 材料属性需要从 SAP2000 API 获取
            })
        return materials
    
    def export_loads(self, model_3d: Any) -> List[Dict]:
        """
        导出荷载数据
        
        Args:
            model_3d: 3D模型数据
            
        Returns:
            荷载列表
        """
        # 待实现
        return []
