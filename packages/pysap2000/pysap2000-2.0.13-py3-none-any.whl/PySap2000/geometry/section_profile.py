# -*- coding: utf-8 -*-
"""
section_profile.py - 截面轮廓生成器

根据截面类型和参数，生成截面轮廓的二维坐标点
用于后续生成三维实体（拉伸、扫掠等）

支持的截面类型：
- Circle: 圆形截面
- Rect: 矩形截面
- I: 工字钢截面
- Pipe: 圆管截面
- Box: 箱形截面
- Channel: 槽钢截面
- Tee: T型钢截面
- Angle: 角钢截面
"""

from dataclasses import dataclass
from typing import List, Tuple
import math


@dataclass
class SectionProfile:
    """截面轮廓基类"""
    
    def get_profile_points(self, num_segments: int = 16) -> List[Tuple[float, float]]:
        """
        获取截面轮廓点（二维坐标，局部坐标系）
        
        Args:
            num_segments: 圆弧分段数
            
        Returns:
            [(y, z), ...] 坐标点列表（x 为单元轴向）
        """
        raise NotImplementedError


@dataclass
class CircleProfile(SectionProfile):
    """圆形截面"""
    diameter: float  # 直径（米）
    
    def get_profile_points(self, num_segments: int = 16) -> List[Tuple[float, float]]:
        """生成圆形轮廓点"""
        radius = self.diameter / 2
        points = []
        for i in range(num_segments):
            angle = 2 * math.pi * i / num_segments
            y = radius * math.cos(angle)
            z = radius * math.sin(angle)
            points.append((y, z))
        return points


@dataclass
class RectProfile(SectionProfile):
    """矩形截面"""
    width: float   # 宽度（y 方向，米）
    height: float  # 高度（z 方向，米）
    
    def get_profile_points(self, num_segments: int = 4) -> List[Tuple[float, float]]:
        """生成矩形轮廓点"""
        w2 = self.width / 2
        h2 = self.height / 2
        return [
            (-w2, -h2),
            (w2, -h2),
            (w2, h2),
            (-w2, h2),
        ]


@dataclass
class IProfile(SectionProfile):
    """工字钢截面"""
    height: float       # 总高度（米）
    top_width: float    # 上翼缘宽度（米）
    bottom_width: float # 下翼缘宽度（米）
    web_thickness: float    # 腹板厚度（米）
    flange_thickness: float # 上翼缘厚度（米）
    bottom_flange_thickness: float = None  # 下翼缘厚度（米），None 则使用 flange_thickness
    
    def get_profile_points(self, num_segments: int = 12) -> List[Tuple[float, float]]:
        """生成工字钢轮廓点"""
        h = self.height
        tw = self.top_width
        bw = self.bottom_width
        wt = self.web_thickness
        tft = self.flange_thickness  # 上翼缘厚度
        bft = self.bottom_flange_thickness if self.bottom_flange_thickness else self.flange_thickness  # 下翼缘厚度
        
        # 从左下角开始，逆时针
        points = [
            # 下翼缘
            (-bw/2, -h/2),
            (bw/2, -h/2),
            (bw/2, -h/2 + bft),
            # 腹板右侧
            (wt/2, -h/2 + bft),
            (wt/2, h/2 - tft),
            # 上翼缘
            (tw/2, h/2 - tft),
            (tw/2, h/2),
            (-tw/2, h/2),
            (-tw/2, h/2 - tft),
            # 腹板左侧
            (-wt/2, h/2 - tft),
            (-wt/2, -h/2 + bft),
            (-bw/2, -h/2 + bft),
        ]
        return points


@dataclass
class PipeProfile(SectionProfile):
    """圆管截面（空心圆）"""
    outer_diameter: float  # 外径（米）
    wall_thickness: float  # 壁厚（米）
    
    def get_profile_points(self, num_segments: int = 16) -> List[Tuple[float, float]]:
        """
        生成圆管外圆轮廓点
        
        注意：Rhino 中空心截面需要分别创建外圆和内圆，然后做布尔运算
        这里返回的是外圆轮廓，内圆需要单独处理
        """
        outer_radius = self.outer_diameter / 2
        
        points = []
        
        # 只返回外圆轮廓（逆时针）
        for i in range(num_segments):
            angle = 2 * math.pi * i / num_segments
            y = outer_radius * math.cos(angle)
            z = outer_radius * math.sin(angle)
            points.append((y, z))
        
        return points
    
    def get_inner_profile_points(self, num_segments: int = 16) -> List[Tuple[float, float]]:
        """获取内圆轮廓点（用于布尔运算）"""
        inner_radius = self.outer_diameter / 2 - self.wall_thickness
        
        points = []
        
        # 内圆轮廓（逆时针）
        for i in range(num_segments):
            angle = 2 * math.pi * i / num_segments
            y = inner_radius * math.cos(angle)
            z = inner_radius * math.sin(angle)
            points.append((y, z))
        
        return points


@dataclass
class BoxProfile(SectionProfile):
    """箱形截面（空心矩形）"""
    height: float          # 高度（米）
    width: float           # 宽度（米）
    flange_thickness: float  # 上下板厚度（米）
    web_thickness: float     # 左右板厚度（米）
    
    def get_profile_points(self, num_segments: int = 4) -> List[Tuple[float, float]]:
        """
        生成箱形外轮廓点
        
        注意：Rhino 中空心截面需要分别创建外矩形和内矩形，然后做布尔运算
        这里返回的是外矩形轮廓，内矩形需要单独处理
        """
        h = self.height
        w = self.width
        
        # 外矩形（逆时针）
        points = [
            (-w/2, -h/2),
            (w/2, -h/2),
            (w/2, h/2),
            (-w/2, h/2),
        ]
        
        return points
    
    def get_inner_profile_points(self, num_segments: int = 4) -> List[Tuple[float, float]]:
        """获取内矩形轮廓点（用于布尔运算）"""
        h = self.height
        w = self.width
        ft = self.flange_thickness
        wt = self.web_thickness
        
        # 内矩形（逆时针）
        points = [
            (-w/2 + wt, -h/2 + ft),
            (w/2 - wt, -h/2 + ft),
            (w/2 - wt, h/2 - ft),
            (-w/2 + wt, h/2 - ft),
        ]
        
        return points


@dataclass
class ChannelProfile(SectionProfile):
    """槽钢截面（C型）"""
    height: float          # 高度（米）
    width: float           # 翼缘宽度（米）
    flange_thickness: float  # 翼缘厚度（米）
    web_thickness: float     # 腹板厚度（米）
    mirror: bool = False     # 是否镜像
    
    def get_profile_points(self, num_segments: int = 8) -> List[Tuple[float, float]]:
        """生成槽钢轮廓点"""
        h = self.height
        w = self.width
        ft = self.flange_thickness
        wt = self.web_thickness
        
        if not self.mirror:
            # 标准方向（开口向右）
            points = [
                # 从左下角开始，逆时针
                (-wt/2, -h/2),
                (w - wt/2, -h/2),
                (w - wt/2, -h/2 + ft),
                (wt/2, -h/2 + ft),
                (wt/2, h/2 - ft),
                (w - wt/2, h/2 - ft),
                (w - wt/2, h/2),
                (-wt/2, h/2),
            ]
        else:
            # 镜像方向（开口向左）
            points = [
                (-w + wt/2, -h/2),
                (wt/2, -h/2),
                (wt/2, -h/2 + ft),
                (-w + wt/2, -h/2 + ft),
                (-w + wt/2, h/2 - ft),
                (wt/2, h/2 - ft),
                (wt/2, h/2),
                (-w + wt/2, h/2),
            ]
        
        return points


@dataclass
class TeeProfile(SectionProfile):
    """T型钢截面"""
    height: float          # 总高度（米）
    width: float           # 翼缘宽度（米）
    flange_thickness: float  # 翼缘厚度（米）
    web_thickness: float     # 腹板厚度（米）
    mirror: bool = False     # 是否镜像（上下翻转）
    
    def get_profile_points(self, num_segments: int = 6) -> List[Tuple[float, float]]:
        """生成T型钢轮廓点"""
        h = self.height
        w = self.width
        ft = self.flange_thickness
        wt = self.web_thickness
        
        if not self.mirror:
            # 标准方向（T字正立）
            points = [
                # 从左下角开始，逆时针
                (-wt/2, -h/2),
                (wt/2, -h/2),
                (wt/2, h/2 - ft),
                (w/2, h/2 - ft),
                (w/2, h/2),
                (-w/2, h/2),
                (-w/2, h/2 - ft),
                (-wt/2, h/2 - ft),
            ]
        else:
            # 镜像方向（T字倒立）
            points = [
                (-w/2, -h/2),
                (w/2, -h/2),
                (w/2, -h/2 + ft),
                (wt/2, -h/2 + ft),
                (wt/2, h/2),
                (-wt/2, h/2),
                (-wt/2, -h/2 + ft),
                (-w/2, -h/2 + ft),
            ]
        
        return points


@dataclass
class AngleProfile(SectionProfile):
    """角钢截面（L型）"""
    height: float          # 竖边高度（米）
    width: float           # 横边宽度（米）
    flange_thickness: float  # 横边厚度（米）
    web_thickness: float     # 竖边厚度（米）
    
    def get_profile_points(self, num_segments: int = 6) -> List[Tuple[float, float]]:
        """生成角钢轮廓点"""
        h = self.height
        w = self.width
        ft = self.flange_thickness
        wt = self.web_thickness
        
        # L型，从左下角开始，逆时针
        points = [
            (0, 0),
            (w, 0),
            (w, ft),
            (wt, ft),
            (wt, h),
            (0, h),
        ]
        
        # 移动到中心（近似）
        center_y = (w + wt) / 4
        center_z = (h + ft) / 4
        points = [(y - center_y, z - center_z) for y, z in points]
        
        return points


def create_profile_from_sap_section(section_type: str, params: dict) -> SectionProfile:
    """
    根据 SAP2000 截面类型和参数创建截面轮廓
    
    Args:
        section_type: 截面类型（Circle, Rect, I, Pipe, Box, Channel, Tee, Angle）
        params: 截面参数字典
        
    Returns:
        SectionProfile 对象
        
    Example:
        profile = create_profile_from_sap_section("Circle", {"diameter": 0.5})
        points = profile.get_profile_points()
    """
    section_type = section_type.upper()
    
    if section_type in ("CIRCLE", "CIRCULAR"):
        return CircleProfile(
            diameter=params.get("diameter") or params.get("outer_diameter", 0.1)
        )
    
    elif section_type in ("RECT", "RECTANGULAR"):
        return RectProfile(
            width=params.get("width", 0.2),
            height=params.get("height", 0.3)
        )
    
    elif section_type in ("I", "I_SECTION", "ISECTION"):
        return IProfile(
            height=params.get("height", 0.5),
            top_width=params.get("top_width") or params.get("width", 0.2),
            bottom_width=params.get("bottom_width") or params.get("width", 0.2),
            web_thickness=params.get("web_thickness", 0.01),
            flange_thickness=params.get("flange_thickness", 0.02),
            bottom_flange_thickness=params.get("bottom_flange_thickness")
        )
    
    elif section_type in ("PIPE", "TUBE"):
        return PipeProfile(
            outer_diameter=params.get("outer_diameter", 0.2),
            wall_thickness=params.get("wall_thickness", 0.01)
        )
    
    elif section_type in ("BOX", "RECTANGULAR_TUBE"):
        return BoxProfile(
            height=params.get("height", 0.3),
            width=params.get("width", 0.2),
            flange_thickness=params.get("flange_thickness", 0.01),
            web_thickness=params.get("web_thickness", 0.01)
        )
    
    elif section_type in ("CHANNEL", "C"):
        return ChannelProfile(
            height=params.get("height", 0.3),
            width=params.get("width", 0.1),
            flange_thickness=params.get("flange_thickness", 0.01),
            web_thickness=params.get("web_thickness", 0.008),
            mirror=params.get("mirror", False)
        )
    
    elif section_type in ("TEE", "T", "T_SECTION"):
        return TeeProfile(
            height=params.get("height", 0.3),
            width=params.get("width", 0.2),
            flange_thickness=params.get("flange_thickness", 0.015),
            web_thickness=params.get("web_thickness", 0.01),
            mirror=params.get("mirror", False)
        )
    
    elif section_type in ("ANGLE", "L"):
        return AngleProfile(
            height=params.get("height", 0.1),
            width=params.get("width", 0.1),
            flange_thickness=params.get("flange_thickness", 0.01),
            web_thickness=params.get("web_thickness", 0.01)
        )
    
    else:
        # 默认返回圆形截面
        return CircleProfile(diameter=0.1)
