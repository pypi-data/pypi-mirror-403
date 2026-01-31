# -*- coding: utf-8 -*-
"""
mesh_generator.py - 3D 网格生成器

根据截面轮廓和单元轴线生成 3D 网格数据
用于 Web 查看器的实体模式
"""

import numpy as np
from typing import List, Tuple, Dict
from dataclasses import dataclass
from ..geometry.element_geometry import FrameElement3D, CableElement3D, Point3D
from ..geometry.section_profile import create_profile_from_sap_section


@dataclass
class MeshData:
    """网格数据"""
    vertices: List[float]  # 顶点坐标 [x1,y1,z1, x2,y2,z2, ...]
    normals: List[float]   # 法向量 [nx1,ny1,nz1, ...]
    indices: List[int]     # 三角形索引
    colors: List[float]    # 顶点颜色 [r1,g1,b1, ...]


class MeshGenerator:
    """3D 网格生成器"""
    
    def __init__(self, num_segments: int = 16):
        """
        初始化
        
        Args:
            num_segments: 圆形截面的分段数
        """
        self.num_segments = num_segments
    
    def generate_element_mesh(
        self,
        element,
        color: Tuple[float, float, float] = (0.2, 0.5, 0.9)
    ) -> MeshData:
        """
        为单个单元生成网格
        
        Args:
            element: FrameElement3D 或 CableElement3D
            color: RGB 颜色 (0-1)
            
        Returns:
            MeshData 对象
        """
        # 获取截面轮廓
        if hasattr(element, 'section_type') and element.section_type:
            profile = create_profile_from_sap_section(
                element.section_type,
                element.section_params
            )
            profile.num_segments = self.num_segments
            profile_points = profile.get_profile_points()
        else:
            # 默认圆形截面
            profile_points = self._get_default_circle_profile(0.1)
        
        # 生成拉伸网格
        return self._extrude_profile(
            profile_points,
            element.point_i,
            element.point_j,
            color
        )
    
    def _get_default_circle_profile(self, radius: float) -> List[Tuple[float, float]]:
        """生成默认圆形截面轮廓"""
        points = []
        for i in range(self.num_segments):
            angle = 2 * np.pi * i / self.num_segments
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)
            points.append((x, y))
        return points
    
    def _extrude_profile(
        self,
        profile_points: List[Tuple[float, float]],
        point_i: Point3D,
        point_j: Point3D,
        color: Tuple[float, float, float]
    ) -> MeshData:
        """
        沿轴线拉伸截面轮廓
        
        Args:
            profile_points: 截面轮廓点 [(x1,y1), (x2,y2), ...]
            point_i: 起点
            point_j: 终点
            color: 颜色
            
        Returns:
            MeshData
        """
        # 计算局部坐标系
        axis_x, axis_y, axis_z = self._compute_local_axes(point_i, point_j)
        
        # 转换截面点到 3D 空间
        n_profile = len(profile_points)
        vertices = []
        normals = []
        colors = []
        
        # 起点截面
        for px, py in profile_points:
            # 局部坐标转全局坐标
            point = (
                point_i.x + px * axis_x[0] + py * axis_y[0],
                point_i.y + px * axis_x[1] + py * axis_y[1],
                point_i.z + px * axis_x[2] + py * axis_y[2]
            )
            vertices.extend(point)
            
            # 法向量（径向）
            normal = self._normalize([px * axis_x[i] + py * axis_y[i] for i in range(3)])
            normals.extend(normal)
            
            colors.extend(color)
        
        # 终点截面
        for px, py in profile_points:
            point = (
                point_j.x + px * axis_x[0] + py * axis_y[0],
                point_j.y + px * axis_x[1] + py * axis_y[1],
                point_j.z + px * axis_x[2] + py * axis_y[2]
            )
            vertices.extend(point)
            
            normal = self._normalize([px * axis_x[i] + py * axis_y[i] for i in range(3)])
            normals.extend(normal)
            
            colors.extend(color)
        
        # 生成侧面三角形索引
        indices = []
        for i in range(n_profile):
            i_next = (i + 1) % n_profile
            
            # 第一个三角形
            indices.extend([
                i,                    # 起点当前
                i + n_profile,        # 终点当前
                i_next                # 起点下一个
            ])
            
            # 第二个三角形
            indices.extend([
                i_next,               # 起点下一个
                i + n_profile,        # 终点当前
                i_next + n_profile    # 终点下一个
            ])
        
        # 添加端盖（可选）
        # 起点端盖
        start_cap_indices = self._generate_cap_indices(0, n_profile, False)
        indices.extend(start_cap_indices)
        
        # 终点端盖
        end_cap_indices = self._generate_cap_indices(n_profile, n_profile, True)
        indices.extend(end_cap_indices)
        
        return MeshData(
            vertices=vertices,
            normals=normals,
            indices=indices,
            colors=colors
        )
    
    def _compute_local_axes(
        self,
        point_i: Point3D,
        point_j: Point3D
    ) -> Tuple[List[float], List[float], List[float]]:
        """
        计算局部坐标系
        
        Returns:
            (axis_x, axis_y, axis_z) - 三个轴的方向向量
        """
        # Z 轴：沿单元方向
        axis_z = [
            point_j.x - point_i.x,
            point_j.y - point_i.y,
            point_j.z - point_i.z
        ]
        axis_z = self._normalize(axis_z)
        
        # X 轴：垂直于 Z 轴
        # 选择一个不平行于 Z 轴的向量
        if abs(axis_z[2]) < 0.9:
            up = [0, 0, 1]
        else:
            up = [1, 0, 0]
        
        # X = up × Z
        axis_x = self._cross(up, axis_z)
        axis_x = self._normalize(axis_x)
        
        # Y = Z × X
        axis_y = self._cross(axis_z, axis_x)
        axis_y = self._normalize(axis_y)
        
        return axis_x, axis_y, axis_z
    
    def _generate_cap_indices(
        self,
        start_index: int,
        n_points: int,
        reverse: bool = False
    ) -> List[int]:
        """
        生成端盖的三角形索引（扇形三角化）
        
        Args:
            start_index: 起始顶点索引
            n_points: 轮廓点数
            reverse: 是否反向（法向量方向）
        """
        indices = []
        center_idx = start_index  # 使用第一个点作为中心
        
        for i in range(1, n_points - 1):
            if reverse:
                indices.extend([
                    center_idx,
                    start_index + i + 1,
                    start_index + i
                ])
            else:
                indices.extend([
                    center_idx,
                    start_index + i,
                    start_index + i + 1
                ])
        
        return indices
    
    @staticmethod
    def _normalize(v: List[float]) -> List[float]:
        """归一化向量"""
        length = np.sqrt(sum(x**2 for x in v))
        if length < 1e-10:
            return [0, 0, 1]
        return [x / length for x in v]
    
    @staticmethod
    def _cross(a: List[float], b: List[float]) -> List[float]:
        """向量叉乘"""
        return [
            a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]
        ]
