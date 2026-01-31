# -*- coding: utf-8 -*-
"""
可视化导出器基类

所有可视化导出器的共同特点：
- 需要截面的二维轮廓信息
- 需要生成3D网格
- 用于渲染和显示
"""

from abc import ABC, abstractmethod
from typing import Any


class VisualizationExporter(ABC):
    """可视化导出器基类"""
    
    def __init__(self):
        """初始化可视化导出器"""
        pass
    
    @abstractmethod
    def export(self, model_3d: Any, output_path: str) -> None:
        """
        导出模型为可视化格式
        
        Args:
            model_3d: 3D模型数据（包含完整几何信息）
            output_path: 输出文件路径
        """
        pass
    
    def generate_geometry(self, element: Any) -> Any:
        """
        生成单元的3D几何
        
        Args:
            element: 单元对象
            
        Returns:
            3D几何数据（顶点、面等）
        """
        pass
    
    def generate_section_profile(self, section_params: dict) -> list:
        """
        生成截面轮廓
        
        Args:
            section_params: 截面参数
            
        Returns:
            截面轮廓点列表
        """
        pass
