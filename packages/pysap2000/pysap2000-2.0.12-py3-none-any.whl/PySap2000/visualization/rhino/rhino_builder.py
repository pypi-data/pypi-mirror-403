# -*- coding: utf-8 -*-
"""
rhino_builder.py - Rhino 几何生成器

在 Rhino 中生成三维实体模型
需要在 Rhino Python 环境中运行

使用 rhinoscriptsyntax 实现，简单易用
"""

from typing import List, Optional, Tuple
import math

try:
    import rhinoscriptsyntax as rs
    RHINO_AVAILABLE = True
except ImportError:
    RHINO_AVAILABLE = False
    print("警告: 此模块需要在 Rhino Python 环境中运行")

from PySap2000.geometry.element_geometry import Model3D, FrameElement3D, CableElement3D
from PySap2000.geometry.section_profile import create_profile_from_sap_section


class RhinoBuilder:
    """Rhino 几何生成器（使用 rhinoscriptsyntax）"""
    
    def __init__(self):
        if not RHINO_AVAILABLE:
            raise ImportError("此模块需要在 Rhino Python 环境中运行")
        
        self.created_guids = []  # 记录创建的对象
        self.layer_structure = {}  # 图层结构
    
    def _print_progress(self, current: int, total: int, prefix: str = ""):
        """打印进度条（Rhino 控制台优化版）"""
        if total == 0:
            return
        
        percent = int(100 * current / total)
        
        # 使用实例变量跟踪上次打印的百分比
        if not hasattr(self, '_last_printed_percent'):
            self._last_printed_percent = -1
        
        # 只在百分比变化且是 10 的倍数时打印，或者是最后一个
        if (percent != self._last_printed_percent and percent % 10 == 0) or current == total:
            bar_length = 30
            filled = int(bar_length * current / total)
            bar = '█' * filled + '░' * (bar_length - filled)
            
            # 计算 total 的位数，用于固定宽度
            total_width = len(str(total))
            
            # 固定宽度格式化
            count_str = f"({current:>{total_width}}/{total})"
            progress_text = f"{prefix}[{bar}] {percent:3d}% {count_str}"
            
            print(progress_text)
            self._last_printed_percent = percent
    
    def build_model(
        self, 
        model_3d: Model3D, 
        layer_name: str = "SAP2000_Model",
        num_segments: int = 8,
        organize_by_group: bool = True,
        organize_by_type: bool = True,
        create_solid: bool = True,
        num_threads: int = 4
    ) -> dict:
        """
        在 Rhino 中生成三维模型
        
        Args:
            model_3d: Model3D 对象
            layer_name: 根图层名称
            num_segments: 圆形截面分段数
            organize_by_group: 是否按组创建子图层
            organize_by_type: 是否按类型创建子图层
            create_solid: 是否创建实体（False 则创建线框）
            num_threads: 线程数（默认4，仅实体模式有效）
            
        Returns:
            结果字典 {
                "guids": [生成的对象 GUID],
                "layers": [创建的图层],
                "stats": {统计信息}
            }
            
        Example:
            # 在 Rhino Python 中运行
            from PySap2000.geometry import ModelExtractor
            from PySap2000.visualization.rhino import RhinoBuilder
            
            extractor = ModelExtractor(sap_model)
            model_3d = extractor.extract_all_elements()
            
            builder = RhinoBuilder()
            result = builder.build_model(model_3d, num_threads=4)
            print(f"创建了 {len(result['guids'])} 个对象")
        """
        print("=" * 60)
        print(f"单元数量: {len(model_3d.elements)}")
        print(f"生成模式: {'实体' if create_solid else '线框'}")
        print("=" * 60)
        
        # 禁用视图刷新以提升性能
        rs.EnableRedraw(False)
        
        self.created_guids = []
        self.layer_structure = {}
        
        # 创建根图层
        self._ensure_layer(layer_name)
        
        # 统计信息
        stats = {
            "total": len(model_3d.elements),
            "frame": 0,
            "cable": 0,
            "other": 0,
            "success": 0,
            "failed": 0
        }
        
        # 进度跟踪
        total_elements = len(model_3d.elements)
        
        # 按单元类型和组分类
        for idx, elem in enumerate(model_3d.elements):
            # 更新进度条
            self._print_progress(idx + 1, total_elements, "Progress: ")
            
            try:
                # 确定图层路径
                layer_path = self._get_layer_path(
                    elem, 
                    layer_name, 
                    organize_by_group, 
                    organize_by_type
                )
                self._ensure_layer(layer_path)
                rs.CurrentLayer(layer_path)
                
                # 生成几何体
                if isinstance(elem, FrameElement3D):
                    stats["frame"] += 1
                    if create_solid:
                        guid = self._build_frame_solid(elem, num_segments)
                    else:
                        guid = self._build_frame_line(elem)
                        
                elif isinstance(elem, CableElement3D):
                    stats["cable"] += 1
                    if create_solid:
                        guid = self._build_cable_solid(elem, num_segments)
                    else:
                        guid = self._build_cable_line(elem)
                else:
                    stats["other"] += 1
                    guid = self._build_line(elem)
                
                if guid:
                    self.created_guids.append(guid)
                    # 设置对象名称
                    rs.ObjectName(guid, elem.name)
                    
                    # 设置颜色：框架单元=蓝色，索单元=绿色
                    if isinstance(elem, FrameElement3D):
                        rs.ObjectColor(guid, (0, 0, 255))  # 蓝色
                    elif isinstance(elem, CableElement3D):
                        rs.ObjectColor(guid, (0, 255, 0))  # 绿色
                    
                    stats["success"] += 1
                else:
                    stats["failed"] += 1
                    print(f"\n  ⚠ 单元 '{elem.name}' 生成失败")
                    
            except Exception as e:
                stats["failed"] += 1
                print(f"\n  ✗ 单元 '{elem.name}' 异常: {e}")
                continue
        
        # 输出统计
        print("\n" + "=" * 60)
        print("生成完成!")
        print(f"  总计: {stats['total']} 个单元")
        print(f"  框架: {stats['frame']} | 索: {stats['cable']} | 其他: {stats['other']}")
        print(f"  成功: {stats['success']} | 失败: {stats['failed']}")
        print(f"  图层: {len(self.layer_structure)} 个")
        print("=" * 60)
        
        # 重新启用视图刷新
        rs.EnableRedraw(True)
        
        # 缩放到全部可见
        rs.ZoomExtents()
        
        return {
            "guids": self.created_guids,
            "layers": list(self.layer_structure.keys()),
            "stats": stats
        }
    
    def _get_layer_path(
        self, 
        elem, 
        root_layer: str, 
        by_group: bool, 
        by_type: bool
    ) -> str:
        """获取单元的图层路径"""
        parts = [root_layer]
        
        # 按组分类
        if by_group and elem.group:
            parts.append(elem.group)
        
        # 按类型分类
        if by_type:
            if isinstance(elem, FrameElement3D):
                parts.append("框架单元")
            elif isinstance(elem, CableElement3D):
                parts.append("索单元")
            else:
                parts.append("其他")
        
        return "::".join(parts)
    
    def _ensure_layer(self, layer_path: str):
        """确保图层存在（支持嵌套图层）"""
        if layer_path in self.layer_structure:
            return
        
        if not rs.IsLayer(layer_path):
            rs.AddLayer(layer_path)
        
        self.layer_structure[layer_path] = True
    
    def _build_frame_solid(self, elem: FrameElement3D, num_segments: int):
        """生成框架单元实体（使用 rhinoscriptsyntax）"""
        # 创建截面轮廓
        profile = create_profile_from_sap_section(elem.section_type, elem.section_params)
        profile_points_2d = profile.get_profile_points(num_segments)
        
        # 单元起点和终点
        start_pt = [elem.point_i.x, elem.point_i.y, elem.point_i.z]
        end_pt = [elem.point_j.x, elem.point_j.y, elem.point_j.z]
        
        # 计算单元方向向量
        direction = rs.VectorCreate(end_pt, start_pt)
        length = rs.VectorLength(direction)
        direction = rs.VectorUnitize(direction)
        
        # 计算局部坐标系
        # 选择一个垂直于单元轴的向量作为局部 Y 轴
        if abs(direction[2]) < 0.9:  # 不是竖直的
            local_y = rs.VectorCrossProduct(direction, [0, 0, 1])
        else:  # 竖直的
            local_y = rs.VectorCrossProduct(direction, [1, 0, 0])
        local_y = rs.VectorUnitize(local_y)
        
        # 局部 Z 轴
        local_z = rs.VectorCrossProduct(direction, local_y)
        local_z = rs.VectorUnitize(local_z)
        
        # 将二维轮廓点转换为三维点（在起点处）
        profile_points_3d = []
        for y, z in profile_points_2d:
            # pt = start_pt + local_y * y + local_z * z
            pt = [
                start_pt[0] + local_y[0] * y + local_z[0] * z,
                start_pt[1] + local_y[1] * y + local_z[1] * z,
                start_pt[2] + local_y[2] * y + local_z[2] * z
            ]
            profile_points_3d.append(pt)
        
        # 闭合轮廓
        profile_points_3d.append(profile_points_3d[0])
        
        # 创建轮廓曲线
        profile_curve = rs.AddPolyline(profile_points_3d)
        if not profile_curve:
            return None
        
        # 创建拉伸路径（单元轴线）
        path = rs.AddLine(start_pt, end_pt)
        if not path:
            rs.DeleteObject(profile_curve)
            return None
        
        # 拉伸生成实体
        solid = rs.ExtrudeCurve(profile_curve, path)
        
        # 删除辅助曲线
        rs.DeleteObject(profile_curve)
        rs.DeleteObject(path)
        
        return solid
    
    def _build_frame_line(self, elem: FrameElement3D):
        """生成框架单元线框"""
        start_pt = [elem.point_i.x, elem.point_i.y, elem.point_i.z]
        end_pt = [elem.point_j.x, elem.point_j.y, elem.point_j.z]
        return rs.AddLine(start_pt, end_pt)
    
    def _build_cable_solid(self, elem: CableElement3D, num_segments: int):
        """生成索单元实体（圆柱体）"""
        # 使用截面轮廓生成器
        from PySap2000.geometry.section_profile import create_profile_from_sap_section
        
        # 创建截面轮廓
        profile = create_profile_from_sap_section(
            elem.section_type, 
            elem.section_params
        )
        profile_points_2d = profile.get_profile_points(num_segments)
        
        start_pt = [elem.point_i.x, elem.point_i.y, elem.point_i.z]
        end_pt = [elem.point_j.x, elem.point_j.y, elem.point_j.z]
        
        # 计算方向和长度
        direction = rs.VectorCreate(end_pt, start_pt)
        length = rs.VectorLength(direction)
        direction = rs.VectorUnitize(direction)
        
        # 计算局部坐标系
        if abs(direction[2]) < 0.9:
            local_y = rs.VectorCrossProduct(direction, [0, 0, 1])
        else:
            local_y = rs.VectorCrossProduct(direction, [1, 0, 0])
        local_y = rs.VectorUnitize(local_y)
        
        local_z = rs.VectorCrossProduct(direction, local_y)
        local_z = rs.VectorUnitize(local_z)
        
        # 将二维轮廓点转换为三维点
        profile_points_3d = []
        for y, z in profile_points_2d:
            pt = [
                start_pt[0] + local_y[0] * y + local_z[0] * z,
                start_pt[1] + local_y[1] * y + local_z[1] * z,
                start_pt[2] + local_y[2] * y + local_z[2] * z
            ]
            profile_points_3d.append(pt)
        
        # 闭合轮廓
        profile_points_3d.append(profile_points_3d[0])
        
        # 创建轮廓曲线
        circle = rs.AddPolyline(profile_points_3d)
        if not circle:
            return None
        
        # 创建拉伸路径
        path = rs.AddLine(start_pt, end_pt)
        if not path:
            rs.DeleteObject(circle)
            return None
        
        # 拉伸生成圆柱体
        cylinder = rs.ExtrudeCurve(circle, path)
        
        # 删除辅助曲线
        rs.DeleteObject(circle)
        rs.DeleteObject(path)
        
        return cylinder
    
    def _build_cable_line(self, elem: CableElement3D):
        """生成索单元线框"""
        start_pt = [elem.point_i.x, elem.point_i.y, elem.point_i.z]
        end_pt = [elem.point_j.x, elem.point_j.y, elem.point_j.z]
        return rs.AddLine(start_pt, end_pt)
    
    def _build_line(self, elem):
        """生成线（默认）"""
        start_pt = [elem.point_i.x, elem.point_i.y, elem.point_i.z]
        end_pt = [elem.point_j.x, elem.point_j.y, elem.point_j.z]
        return rs.AddLine(start_pt, end_pt)
    
    def select_created_objects(self):
        """选中所有创建的对象"""
        if self.created_guids:
            rs.SelectObjects(self.created_guids)
            print(f"已选中 {len(self.created_guids)} 个对象")
    
    def delete_created_objects(self):
        """删除所有创建的对象"""
        if self.created_guids:
            rs.DeleteObjects(self.created_guids)
            count = len(self.created_guids)
            self.created_guids = []
            print(f"已删除 {count} 个对象")
    
    def export_to_file(self, filepath: str, file_type: str = "3dm"):
        """
        导出创建的对象到文件
        
        Args:
            filepath: 输出文件路径
            file_type: 文件类型（3dm, obj, stl, step 等）
        """
        if not self.created_guids:
            print("没有对象可导出")
            return False
        
        # 选中要导出的对象
        rs.UnselectAllObjects()
        rs.SelectObjects(self.created_guids)
        
        # 导出
        try:
            if file_type.lower() == "3dm":
                rs.Command(f"_-Export {filepath} _Enter", False)
            elif file_type.lower() == "obj":
                rs.Command(f"_-Export {filepath} _Enter", False)
            elif file_type.lower() == "stl":
                rs.Command(f"_-Export {filepath} _Enter", False)
            else:
                print(f"不支持的文件类型: {file_type}")
                return False
            
            print(f"✓ 已导出到: {filepath}")
            return True
            
        except Exception as e:
            print(f"导出失败: {e}")
            return False
