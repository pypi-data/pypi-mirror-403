# -*- coding: utf-8 -*-
"""
model_viewer.py - SAP2000 模型 3D 查看器（简化版）

直接使用 PySap2000 现有功能，无需重复造轮子

Usage:
    from PySap2000.application import Application
    from PySap2000.visualization.web.model_viewer import ModelViewer
    
    app = Application()
    viewer = ModelViewer(app.model)
    viewer.export_solid_html("model.html")
"""

from typing import List, Dict, Any
from PySap2000.structure_core.frame import Frame
from PySap2000.structure_core.cable import Cable
from PySap2000.section.frame_section import FrameSection
from PySap2000.section.cable_section import CableSection
from .web_exporter_solid import WebExporterSolid
from .mesh_generator import MeshGenerator


class ModelViewer:
    """SAP2000 模型 3D 查看器"""
    
    def __init__(self, model):
        """
        Args:
            model: SAP2000 的 SapModel 对象
        """
        self.model = model
        self.mesh_generator = MeshGenerator()
    
    def export_solid_html(
        self, 
        output_file: str,
        frame_names: List[str] = None,
        cable_names: List[str] = None,
        num_segments: int = 16
    ):
        """
        导出实体模型为 HTML 文件
        
        Args:
            output_file: 输出文件路径
            frame_names: 要导出的框架单元列表（None=全部）
            cable_names: 要导出的索单元列表（None=全部）
            num_segments: 圆形截面的分段数
        """
        print(f"\n导出 3D 模型: {output_file}")
        
        # 1. 获取框架单元
        print("  提取框架单元...")
        frames = Frame.get_all(self.model, names=frame_names)
        print(f"    ✓ {len(frames)} 个框架单元")
        
        # 2. 获取索单元
        print("  提取索单元...")
        cables = Cable.get_all(self.model, names=cable_names)
        print(f"    ✓ {len(cables)} 个索单元")
        
        # 3. 生成网格数据
        print("  生成 3D 网格...")
        geometry_data = self._generate_geometry(frames, cables, num_segments)
        
        # 4. 导出 HTML
        print("  导出 HTML...")
        exporter = WebExporterSolid(num_segments=num_segments)
        
        # 构造简单的 model_3d 对象
        class SimpleModel:
            def __init__(self, name):
                self.model_name = name
                self.elements = []
        
        model_3d = SimpleModel(self.model.GetModelFilename() or "SAP2000_Model")
        exporter._export_html(output_file, model_3d, geometry_data)
        
        print(f"  ✓ 完成: {output_file}")
    
    def _generate_geometry(
        self, 
        frames: List[Frame], 
        cables: List[Cable],
        num_segments: int
    ) -> Dict[str, Any]:
        """生成几何数据"""
        
        vertices = []
        normals = []
        colors = []
        indices = []
        
        vertex_offset = 0
        
        # 处理框架单元
        for frame in frames:
            if not frame.start_point or not frame.end_point:
                continue
            
            # 获取端点坐标
            try:
                ret_i = self.model.PointObj.GetCoordCartesian(str(frame.start_point), 0, 0, 0)
                ret_j = self.model.PointObj.GetCoordCartesian(str(frame.end_point), 0, 0, 0)
                
                point_i = (ret_i[0], ret_i[1], ret_i[2])
                point_j = (ret_j[0], ret_j[1], ret_j[2])
            except:
                continue
            
            # 获取截面信息
            section_type, section_params = self._get_section_info(frame.section)
            
            if section_type == "Unknown":
                continue
            
            # 生成网格
            mesh = self.mesh_generator.generate_mesh(
                point_i, point_j,
                section_type, section_params,
                num_segments
            )
            
            if mesh:
                # 添加顶点
                vertices.extend(mesh['vertices'])
                normals.extend(mesh['normals'])
                
                # 框架单元用蓝色
                color = [0.2, 0.5, 0.9] * (len(mesh['vertices']) // 3)
                colors.extend(color)
                
                # 添加索引（需要偏移）
                for idx in mesh['indices']:
                    indices.append(idx + vertex_offset)
                
                vertex_offset += len(mesh['vertices']) // 3
        
        # 处理索单元
        for cable in cables:
            if not cable.start_point or not cable.end_point:
                continue
            
            # 获取端点坐标
            try:
                ret_i = self.model.PointObj.GetCoordCartesian(str(cable.start_point), 0, 0, 0)
                ret_j = self.model.PointObj.GetCoordCartesian(str(cable.end_point), 0, 0, 0)
                
                point_i = (ret_i[0], ret_i[1], ret_i[2])
                point_j = (ret_j[0], ret_j[1], ret_j[2])
            except:
                continue
            
            # 索用圆形截面
            diameter = getattr(cable, 'diameter', 0.01)
            
            mesh = self.mesh_generator.generate_mesh(
                point_i, point_j,
                "Circle", {"diameter": diameter},
                num_segments
            )
            
            if mesh:
                vertices.extend(mesh['vertices'])
                normals.extend(mesh['normals'])
                
                # 索单元用红色
                color = [0.9, 0.2, 0.2] * (len(mesh['vertices']) // 3)
                colors.extend(color)
                
                for idx in mesh['indices']:
                    indices.append(idx + vertex_offset)
                
                vertex_offset += len(mesh['vertices']) // 3
        
        return {
            'vertices': vertices,
            'normals': normals,
            'colors': colors,
            'indices': indices
        }
    
    def _get_section_info(self, section_name: str) -> tuple:
        """获取截面类型和参数"""
        try:
            section = FrameSection.get_by_name(self.model, section_name)
            
            if section.property_type:
                type_val = section.property_type
                
                # 根据类型返回参数
                if type_val == 9:  # Circle
                    return ("Circle", {"diameter": section.outer_diameter or section.height})
                elif type_val == 8:  # Rectangular
                    return ("Rect", {"height": section.height, "width": section.width})
                elif type_val == 7:  # Pipe
                    return ("Pipe", {
                        "outer_diameter": section.outer_diameter,
                        "wall_thickness": section.wall_thickness
                    })
                elif type_val == 6:  # Box
                    return ("Box", {
                        "height": section.height,
                        "width": section.width,
                        "flange_thickness": section.flange_thickness,
                        "web_thickness": section.web_thickness
                    })
                elif type_val == 1:  # I-Section
                    return ("I", {
                        "height": section.height,
                        "top_width": section.width,
                        "flange_thickness": section.flange_thickness,
                        "web_thickness": section.web_thickness,
                        "bottom_width": section.bottom_flange_width or section.width,
                        "bottom_flange_thickness": section.bottom_flange_thickness or section.flange_thickness
                    })
        except:
            pass
        
        return ("Unknown", {})
