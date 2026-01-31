# -*- coding: utf-8 -*-
"""
frame_section.py - 杆件截面属性定义
对应 SAP2000 的 PropFrame

本模块用于定义截面属性（是什么），而非分配截面到杆件（怎么用）。
截面分配功能请使用 types_for_frames 模块。

Usage:
    from section import FrameSection, FrameSectionType
    
    # 获取截面
    section = FrameSection.get_by_name(model, "W14X22")
    print(f"类型: {section.type_name}, 材料: {section.material}")
    
    # 创建矩形截面
    rect = FrameSection(
        name="R1",
        property_type=FrameSectionType.RECTANGULAR,
        material="4000Psi",
        height=0.5,
        width=0.3
    )
    rect._create(model)
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, ClassVar
from enum import IntEnum


class FrameSectionType(IntEnum):
    """杆件截面类型 - 对应 SAP2000 eFramePropType"""
    I_SECTION = 1
    CHANNEL = 2
    T_SECTION = 3
    ANGLE = 4
    DOUBLE_ANGLE = 5
    BOX = 6
    PIPE = 7
    RECTANGULAR = 8
    CIRCLE = 9
    GENERAL = 10
    DOUBLE_CHANNEL = 11
    SD = 13
    VARIABLE = 14
    COLD_C = 17
    COLD_Z = 19
    COLD_L = 20
    COLD_HAT = 22
    BUILTUP_I_COVERPLATE = 23
    PRECAST_I = 24
    PRECAST_U = 25


SECTION_TYPE_NAMES: Dict[FrameSectionType, str] = {
    FrameSectionType.I_SECTION: "I形截面",
    FrameSectionType.CHANNEL: "槽钢",
    FrameSectionType.T_SECTION: "T形截面",
    FrameSectionType.ANGLE: "角钢",
    FrameSectionType.DOUBLE_ANGLE: "双角钢",
    FrameSectionType.BOX: "箱形截面",
    FrameSectionType.PIPE: "圆管",
    FrameSectionType.RECTANGULAR: "矩形截面",
    FrameSectionType.CIRCLE: "圆形截面",
    FrameSectionType.GENERAL: "一般截面",
    FrameSectionType.DOUBLE_CHANNEL: "双槽钢",
    FrameSectionType.SD: "截面设计器",
    FrameSectionType.VARIABLE: "变截面",
    FrameSectionType.COLD_C: "冷弯C型钢",
    FrameSectionType.COLD_Z: "冷弯Z型钢",
    FrameSectionType.COLD_L: "冷弯L型钢",
    FrameSectionType.COLD_HAT: "冷弯帽型钢",
    FrameSectionType.BUILTUP_I_COVERPLATE: "组合I形盖板",
    FrameSectionType.PRECAST_I: "预制I形梁",
    FrameSectionType.PRECAST_U: "预制U形梁",
}


@dataclass
class FrameSection:
    """杆件截面属性 - 对应 SAP2000 PropFrame"""
    
    name: str = ""
    property_type: Optional[FrameSectionType] = None
    type_name: str = ""
    material: str = ""
    height: float = 0.0
    width: float = 0.0
    flange_thickness: float = 0.0
    web_thickness: float = 0.0
    bottom_flange_width: float = 0.0
    bottom_flange_thickness: float = 0.0
    fillet_radius: float = 0.0
    outer_diameter: float = 0.0
    wall_thickness: float = 0.0
    back_to_back_distance: float = 0.0
    mirror_about_2: bool = False
    mirror_about_3: bool = False
    color: int = -1
    notes: str = ""
    guid: Optional[str] = None
    file_name: str = ""
    
    # 截面力学属性 (from GetSectProps API)
    area: float = 0.0           # 截面面积 [L²]
    as2: float = 0.0            # 2轴剪切面积 [L²]
    as3: float = 0.0            # 3轴剪切面积 [L²]
    torsion: float = 0.0        # 扭转常数 [L⁴]
    i22: float = 0.0            # 2轴惯性矩 [L⁴]
    i33: float = 0.0            # 3轴惯性矩 [L⁴]
    s22: float = 0.0            # 2轴截面模量 [L³]
    s33: float = 0.0            # 3轴截面模量 [L³]
    z22: float = 0.0            # 2轴塑性模量 [L³]
    z33: float = 0.0            # 3轴塑性模量 [L³]
    r22: float = 0.0            # 2轴回转半径 [L]
    r33: float = 0.0            # 3轴回转半径 [L]
    
    # 单位长度重量 (计算值)
    _weight_per_meter: float = 0.0
    
    _object_type: ClassVar[str] = "PropFrame"
    
    @property
    def weight_per_meter(self) -> float:
        """单位长度重量 (kg/m)"""
        return self._weight_per_meter

    @classmethod
    def get_by_name(cls, model, name: str) -> 'FrameSection':
        """获取指定名称的截面"""
        prop = cls(name=name)
        prop._get(model)
        return prop

    @classmethod
    def get_all(cls, model) -> List['FrameSection']:
        """获取所有截面"""
        names = cls.get_name_list(model)
        props = []
        for name in names:
            try:
                prop = cls.get_by_name(model, name)
                props.append(prop)
            except Exception:
                pass
        return props
    
    @staticmethod
    def get_count(model) -> int:
        """获取截面总数"""
        return model.PropFrame.Count()
    
    @staticmethod
    def get_name_list(model, property_type: FrameSectionType = None) -> List[str]:
        """获取截面名称列表"""
        if property_type is not None:
            result = model.PropFrame.GetNameList(property_type.value)
        else:
            result = model.PropFrame.GetNameList()
        if isinstance(result, (list, tuple)) and len(result) >= 2:
            return list(result[1]) if result[1] else []
        return []

    def _get(self, model) -> 'FrameSection':
        """从 SAP2000 获取截面数据"""
        result = model.PropFrame.GetTypeOAPI(self.name)
        if isinstance(result, (list, tuple)) and len(result) >= 2:
            type_val = result[0]
            ret = result[-1]
        else:
            from exceptions import SectionError
            raise SectionError(f"获取截面 {self.name} 类型失败")
        if ret != 0:
            from exceptions import SectionError
            raise SectionError(f"截面 {self.name} 不存在")
        try:
            self.property_type = FrameSectionType(type_val)
            self.type_name = SECTION_TYPE_NAMES.get(self.property_type, f"未知类型({type_val})")
        except ValueError:
            self.property_type = None
            self.type_name = f"未知类型({type_val})"
        self._get_properties_by_type(model)
        # 如果材料为空，尝试通用方法获取
        if not self.material:
            self._get_material_fallback(model)
        # 获取截面力学属性
        self._get_sect_props(model)
        # 计算单位长度重量
        self._calculate_weight_per_meter(model)
        return self
    
    def _get_properties_by_type(self, model):
        """根据截面类型获取属性"""
        if self.property_type == FrameSectionType.RECTANGULAR:
            self._get_rectangle(model)
        elif self.property_type == FrameSectionType.CIRCLE:
            self._get_circle(model)
        elif self.property_type == FrameSectionType.PIPE:
            self._get_pipe(model)
        elif self.property_type == FrameSectionType.BOX:
            self._get_box(model)
        elif self.property_type == FrameSectionType.I_SECTION:
            self._get_isection(model)
        elif self.property_type == FrameSectionType.ANGLE:
            self._get_angle(model)
        elif self.property_type == FrameSectionType.CHANNEL:
            self._get_channel(model)
        elif self.property_type == FrameSectionType.T_SECTION:
            self._get_tee(model)
        elif self.property_type == FrameSectionType.DOUBLE_ANGLE:
            self._get_dbl_angle(model)
        elif self.property_type == FrameSectionType.DOUBLE_CHANNEL:
            self._get_dbl_channel(model)
        elif self.property_type == FrameSectionType.GENERAL:
            self._get_general(model)
        elif self.property_type == FrameSectionType.SD:
            self._get_sd_section(model)

    def _get_sect_props(self, model) -> None:
        """
        从 SAP2000 获取截面力学属性
        
        调用 PropFrame.GetSectProps API 获取截面面积、惯性矩等属性
        """
        try:
            result = model.PropFrame.GetSectProps(
                self.name, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0
            )
            if isinstance(result, (list, tuple)) and len(result) >= 13:
                self.area = result[0]
                self.as2 = result[1]
                self.as3 = result[2]
                self.torsion = result[3]
                self.i22 = result[4]
                self.i33 = result[5]
                self.s22 = result[6]
                self.s33 = result[7]
                self.z22 = result[8]
                self.z33 = result[9]
                self.r22 = result[10]
                self.r33 = result[11]
        except Exception:
            # 如果获取失败，保持默认值 0.0
            pass

    def _calculate_weight_per_meter(self, model) -> float:
        """
        计算单位长度重量 (kg/m)
        
        weight_per_meter = area × density
        
        如果当前不是 N-m-C 单位，会临时切换获取数据
        
        Args:
            model: SapModel 对象
            
        Returns:
            单位长度重量 (kg/m)，如果材料不存在则返回 0.0
        """
        if not self.material:
            self._weight_per_meter = 0.0
            return 0.0
        
        try:
            from global_parameters.units import Units, UnitSystem
            
            current_units = Units.get_present_units(model)
            need_switch = current_units != UnitSystem.N_M_C
            
            if need_switch:
                Units.set_present_units(model, UnitSystem.N_M_C)
            
            try:
                # 获取截面面积 (m²)
                result = model.PropFrame.GetSectProps(
                    self.name, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                    0.0, 0.0, 0.0, 0.0, 0.0, 0.0
                )
                area_m2 = result[0] if isinstance(result, (list, tuple)) and len(result) >= 1 else 0.0
                
                # 获取材料密度 (kg/m³)
                result = model.PropMaterial.GetWeightAndMass(self.material)
                density_kg_m3 = result[1] if isinstance(result, (list, tuple)) and len(result) >= 2 else 0.0
                
                if area_m2 > 0 and density_kg_m3 > 0:
                    self._weight_per_meter = area_m2 * density_kg_m3
                else:
                    self._weight_per_meter = 0.0
            finally:
                if need_switch:
                    Units.set_present_units(model, current_units)
            
        except Exception:
            self._weight_per_meter = 0.0
        
        return self._weight_per_meter

    def _get_rectangle(self, model):
        result = model.PropFrame.GetRectangle(self.name)
        if isinstance(result, (list, tuple)) and len(result) >= 8:
            self.file_name = result[0] or ""
            self.material = result[1] or ""
            self.height = result[2]
            self.width = result[3]
            self.color = result[4]
            self.notes = result[5] or ""
            self.guid = result[6] or None
    
    def _get_circle(self, model):
        result = model.PropFrame.GetCircle(self.name)
        if isinstance(result, (list, tuple)) and len(result) >= 7:
            self.file_name = result[0] or ""
            self.material = result[1] or ""
            self.outer_diameter = result[2]
            self.color = result[3]
            self.notes = result[4] or ""
            self.guid = result[5] or None
    
    def _get_pipe(self, model):
        result = model.PropFrame.GetPipe(self.name)
        if isinstance(result, (list, tuple)) and len(result) >= 8:
            self.file_name = result[0] or ""
            self.material = result[1] or ""
            self.outer_diameter = result[2]
            self.wall_thickness = result[3]
            self.color = result[4]
            self.notes = result[5] or ""
            self.guid = result[6] or None

    def _get_box(self, model):
        result = model.PropFrame.GetTube_1(self.name)
        if isinstance(result, (list, tuple)) and len(result) >= 11:
            self.file_name = result[0] or ""
            self.material = result[1] or ""
            self.height = result[2]
            self.width = result[3]
            self.flange_thickness = result[4]
            self.web_thickness = result[5]
            self.bottom_flange_thickness = result[6]
            self.color = result[7]
            self.notes = result[8] or ""
            self.guid = result[9] or None
    
    def _get_isection(self, model):
        result = model.PropFrame.GetISection_1(self.name)
        if isinstance(result, (list, tuple)) and len(result) >= 13:
            self.file_name = result[0] or ""
            self.material = result[1] or ""
            self.height = result[2]
            self.width = result[3]
            self.flange_thickness = result[4]
            self.web_thickness = result[5]
            self.bottom_flange_width = result[6]
            self.bottom_flange_thickness = result[7]
            self.fillet_radius = result[8]
            self.color = result[9]
            self.notes = result[10] or ""
            self.guid = result[11] or None

    def _get_angle(self, model):
        result = model.PropFrame.GetAngle_1(self.name)
        if isinstance(result, (list, tuple)) and len(result) >= 11:
            self.file_name = result[0] or ""
            self.material = result[1] or ""
            self.height = result[2]
            self.width = result[3]
            self.flange_thickness = result[4]
            self.web_thickness = result[5]
            self.fillet_radius = result[6]
            self.color = result[7]
            self.notes = result[8] or ""
            self.guid = result[9] or None

    def _get_channel(self, model):
        result = model.PropFrame.GetChannel_2(self.name)
        if isinstance(result, (list, tuple)) and len(result) >= 12:
            self.file_name = result[0] or ""
            self.material = result[1] or ""
            self.height = result[2]
            self.width = result[3]
            self.flange_thickness = result[4]
            self.web_thickness = result[5]
            self.fillet_radius = result[6]
            self.mirror_about_2 = result[7]
            self.color = result[8]
            self.notes = result[9] or ""
            self.guid = result[10] or None

    def _get_tee(self, model):
        result = model.PropFrame.GetTee_1(self.name)
        if isinstance(result, (list, tuple)) and len(result) >= 12:
            self.file_name = result[0] or ""
            self.material = result[1] or ""
            self.height = result[2]
            self.width = result[3]
            self.flange_thickness = result[4]
            self.web_thickness = result[5]
            self.fillet_radius = result[6]
            self.mirror_about_3 = result[7]
            self.color = result[8]
            self.notes = result[9] or ""
            self.guid = result[10] or None

    def _get_dbl_angle(self, model):
        result = model.PropFrame.GetDblAngle_2(self.name)
        if isinstance(result, (list, tuple)) and len(result) >= 13:
            self.file_name = result[0] or ""
            self.material = result[1] or ""
            self.height = result[2]
            self.width = result[3]
            self.flange_thickness = result[4]
            self.web_thickness = result[5]
            self.back_to_back_distance = result[6]
            self.fillet_radius = result[7]
            self.mirror_about_3 = result[8]
            self.color = result[9]
            self.notes = result[10] or ""
            self.guid = result[11] or None

    def _get_dbl_channel(self, model):
        result = model.PropFrame.GetDblChannel_1(self.name)
        if isinstance(result, (list, tuple)) and len(result) >= 12:
            self.file_name = result[0] or ""
            self.material = result[1] or ""
            self.height = result[2]
            self.width = result[3]
            self.flange_thickness = result[4]
            self.web_thickness = result[5]
            self.back_to_back_distance = result[6]
            self.fillet_radius = result[7]
            self.color = result[8]
            self.notes = result[9] or ""
            self.guid = result[10] or None

    def _get_general(self, model):
        """获取 GENERAL 类型截面属性"""
        try:
            result = model.PropFrame.GetGeneral(
                self.name, "", "", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "", ""
            )
            if isinstance(result, (list, tuple)) and len(result) >= 4:
                self.file_name = result[0] or ""
                self.material = result[1] or ""
                self.height = result[2]
                self.width = result[3]
        except Exception:
            pass

    def _get_sd_section(self, model):
        """获取 SD (Section Designer) 类型截面属性"""
        try:
            # SD 截面使用 GetSDSection 获取基本信息
            # GetSDSection(Name, MatProp, NumberItems, ShapeName[], MyType[], DesignType, Color, Notes, GUID)
            result = model.PropFrame.GetSDSection(
                self.name, "", 0, [], [], 0, 0, "", ""
            )
            if isinstance(result, (list, tuple)) and len(result) >= 2:
                self.material = result[0] or ""  # MatProp 在 index 0
                # NumberItems 在 index 1，其他属性在后续索引
        except Exception:
            # 如果失败，尝试通用方法
            self._get_material_fallback(model)

    def _get_material_fallback(self, model):
        """通用方法获取材料（最后的备用方案）"""
        # 尝试多种方法获取材料
        methods = [
            # 方法1: GetGeneral (适用于 GENERAL 类型)
            lambda: model.PropFrame.GetGeneral(
                self.name, "", "", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "", ""
            ),
            # 方法2: GetSDSection (适用于 SD 类型)
            lambda: model.PropFrame.GetSDSection(
                self.name, "", 0, [], [], 0, 0, "", ""
            ),
        ]
        
        for method in methods:
            try:
                result = method()
                if isinstance(result, (list, tuple)) and len(result) >= 2:
                    mat = result[1] if result[1] else (result[0] if result[0] else "")
                    if mat and isinstance(mat, str) and mat.strip():
                        self.material = mat
                        return
            except Exception:
                continue

    def _create(self, model) -> int:
        """在 SAP2000 中创建截面"""
        if self.property_type is None:
            from exceptions import SectionError
            raise SectionError("必须指定截面类型")
        if self.property_type == FrameSectionType.RECTANGULAR:
            return self._create_rectangle(model)
        elif self.property_type == FrameSectionType.CIRCLE:
            return self._create_circle(model)
        elif self.property_type == FrameSectionType.PIPE:
            return self._create_pipe(model)
        elif self.property_type == FrameSectionType.BOX:
            return self._create_box(model)
        elif self.property_type == FrameSectionType.I_SECTION:
            return self._create_isection(model)
        elif self.property_type == FrameSectionType.ANGLE:
            return self._create_angle(model)
        elif self.property_type == FrameSectionType.CHANNEL:
            return self._create_channel(model)
        elif self.property_type == FrameSectionType.T_SECTION:
            return self._create_tee(model)
        elif self.property_type == FrameSectionType.DOUBLE_ANGLE:
            return self._create_dbl_angle(model)
        elif self.property_type == FrameSectionType.DOUBLE_CHANNEL:
            return self._create_dbl_channel(model)
        else:
            from exceptions import SectionError
            raise SectionError(f"不支持创建截面类型: {self.property_type.name}")
    
    def _create_rectangle(self, model) -> int:
        return model.PropFrame.SetRectangle(
            self.name, self.material, self.height, self.width,
            self.color, self.notes, self.guid or "")
    
    def _create_circle(self, model) -> int:
        return model.PropFrame.SetCircle(
            self.name, self.material, self.outer_diameter,
            self.color, self.notes, self.guid or "")
    
    def _create_pipe(self, model) -> int:
        return model.PropFrame.SetPipe(
            self.name, self.material, self.outer_diameter, self.wall_thickness,
            self.color, self.notes, self.guid or "")

    def _create_box(self, model) -> int:
        return model.PropFrame.SetTube_1(
            self.name, self.material, self.height, self.width,
            self.flange_thickness, self.web_thickness, self.flange_thickness,
            self.color, self.notes, self.guid or "")
    
    def _create_isection(self, model) -> int:
        t2b = self.bottom_flange_width or self.width
        tfb = self.bottom_flange_thickness or self.flange_thickness
        return model.PropFrame.SetISection_1(
            self.name, self.material, self.height, self.width,
            self.flange_thickness, self.web_thickness, t2b, tfb, self.fillet_radius,
            self.color, self.notes, self.guid or "")

    def _create_angle(self, model) -> int:
        return model.PropFrame.SetAngle_1(
            self.name, self.material, self.height, self.width,
            self.flange_thickness, self.web_thickness, self.fillet_radius,
            self.color, self.notes, self.guid or "")

    def _create_channel(self, model) -> int:
        return model.PropFrame.SetChannel_2(
            self.name, self.material, self.height, self.width,
            self.flange_thickness, self.web_thickness, self.fillet_radius, self.mirror_about_2,
            self.color, self.notes, self.guid or "")

    def _create_tee(self, model) -> int:
        return model.PropFrame.SetTee_1(
            self.name, self.material, self.height, self.width,
            self.flange_thickness, self.web_thickness, self.fillet_radius, self.mirror_about_3,
            self.color, self.notes, self.guid or "")

    def _create_dbl_angle(self, model) -> int:
        return model.PropFrame.SetDblAngle_2(
            self.name, self.material, self.height, self.width,
            self.flange_thickness, self.web_thickness, self.back_to_back_distance, self.fillet_radius,
            self.mirror_about_3, self.color, self.notes, self.guid or "")

    def _create_dbl_channel(self, model) -> int:
        return model.PropFrame.SetDblChannel_1(
            self.name, self.material, self.height, self.width,
            self.flange_thickness, self.web_thickness, self.back_to_back_distance, self.fillet_radius,
            self.color, self.notes, self.guid or "")
    
    def _delete(self, model) -> int:
        """删除截面"""
        return model.PropFrame.Delete(self.name)
    
    def _update(self, model) -> int:
        """更新截面"""
        return self._create(model)

    @property
    def standard_name(self) -> str:
        """
        获取标准化截面名称
        
        根据截面类型和尺寸生成标准名称:
        - H - I形截面 (高x宽x腹板厚x翼缘厚)
        - C - 槽钢 (高x宽x腹板厚x翼缘厚)
        - T - T形截面 (高x宽x腹板厚x翼缘厚)
        - L - 角钢 (高x宽x厚)
        - 2L - 双角钢 (高x宽x厚x间距)
        - B - 箱形截面 (高x宽x腹板厚x翼缘厚)
        - P - 圆管 (直径x壁厚)
        - R - 矩形截面 (高x宽)
        - D - 圆形截面 (直径)
        - 2C - 双槽钢 (高x宽x厚x间距)
        
        Returns:
            标准化的截面名称，无法标准化时返回原名称
            
        Example:
            section = FrameSection.get_by_name(model, "FSEC1")
            print(section.standard_name)  # "H400x200x8x13"
        """
        if self.property_type == FrameSectionType.I_SECTION:
            return f"H{self.height:.0f}x{self.width:.0f}x{self.web_thickness:.0f}x{self.flange_thickness:.0f}"
        
        elif self.property_type == FrameSectionType.CHANNEL:
            return f"C{self.height:.0f}x{self.width:.0f}x{self.web_thickness:.0f}x{self.flange_thickness:.0f}"
        
        elif self.property_type == FrameSectionType.T_SECTION:
            return f"T{self.height:.0f}x{self.width:.0f}x{self.web_thickness:.0f}x{self.flange_thickness:.0f}"
        
        elif self.property_type == FrameSectionType.ANGLE:
            # 角钢厚度用 flange_thickness
            return f"L{self.height:.0f}x{self.width:.0f}x{self.flange_thickness:.0f}"
        
        elif self.property_type == FrameSectionType.DOUBLE_ANGLE:
            return f"2L{self.height:.0f}x{self.width:.0f}x{self.flange_thickness:.0f}x{self.back_to_back_distance:.0f}"
        
        elif self.property_type == FrameSectionType.BOX:
            return f"B{self.height:.0f}x{self.width:.0f}x{self.web_thickness:.0f}x{self.flange_thickness:.0f}"
        
        elif self.property_type == FrameSectionType.PIPE:
            return f"P{self.outer_diameter:.0f}x{self.wall_thickness:.0f}"
        
        elif self.property_type == FrameSectionType.RECTANGULAR:
            return f"R{self.height:.0f}x{self.width:.0f}"
        
        elif self.property_type == FrameSectionType.CIRCLE:
            return f"D{self.outer_diameter:.0f}"
        
        elif self.property_type == FrameSectionType.DOUBLE_CHANNEL:
            return f"2C{self.height:.0f}x{self.width:.0f}x{self.flange_thickness:.0f}x{self.back_to_back_distance:.0f}"
        
        # 无法标准化，返回原名称
        return self.name
