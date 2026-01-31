# -*- coding: utf-8 -*-
"""
steel_design.py - 钢结构设计
对应 SAP2000 的 DesignSteel 接口

API Reference:
    - DesignSteel.GetCode(CodeName) -> Long
    - DesignSteel.SetCode(CodeName) -> Long
    - DesignSteel.GetGroup(NumberItems, MyName[]) -> Long
    - DesignSteel.SetGroup(Name, Selected) -> Long
    - DesignSteel.StartDesign() -> Long
    - DesignSteel.DeleteResults() -> Long
    - DesignSteel.GetSummaryResults(...) -> Long
    - DesignSteel.VerifyPassed(...) -> Long
    - DesignSteel.GetComboStrength / SetComboStrength
    - DesignSteel.GetDesignSection / SetDesignSection

Usage:
    from steel_design import SteelDesign, SteelDesignCode
    
    # 设置设计规范
    SteelDesign.set_code(model, SteelDesignCode.AISC_360_16)
    
    # 设置设计组
    SteelDesign.set_group(model, "ALL", True)
    
    # 运行设计
    SteelDesign.start_design(model)
    
    # 获取设计结果
    results = SteelDesign.get_summary_results(model, "1")
"""

from enum import Enum, IntEnum
from dataclasses import dataclass
from typing import List, Tuple, Optional


class SteelDesignCode(str, Enum):
    """
    钢结构设计规范枚举
    
    对应 SAP2000 支持的钢结构设计规范
    """
    # 美国规范
    AASHTO_LRFD_2007 = "AASHTO LRFD 2007"
    AISC_ASD89 = "AISC-ASD89"
    AISC_LRFD93 = "AISC-LRFD93"
    AISC_360_05_IBC2006 = "AISC360-05/IBC2006"
    AISC_360_10 = "AISC 360-10"
    AISC_360_16 = "AISC 360-16"
    
    # API 规范 (海洋平台)
    API_RP2A_LRFD_97 = "API RP2A-LRFD 97"
    API_RP2A_WSD2000 = "API RP2A-WSD2000"
    API_RP2A_WSD2014 = "API RP2A-WSD2014"
    API_4F_2020 = "API 4F 2020"
    
    # 澳大利亚规范
    AS_4100_1998 = "AS 4100-1998"
    AS_4100_2020 = "AS 4100-2020"
    
    # ASCE 规范
    ASCE_10_97 = "ASCE 10-97"
    
    # 英国规范
    BS5950_90 = "BS5950 90"
    BS5950_2000 = "BS5950 2000"
    
    # 加拿大规范
    CSA_S16_09 = "CSA-S16-09"
    CSA_S16_14 = "CSA S16-14"
    CSA_S16_19 = "CSA S16-19"
    CISC_95 = "CISC 95"
    
    # 中国规范
    CHINESE_2010 = "Chinese 2010"
    
    # 欧洲规范
    EN_1993_1_1_2005 = "EN1993-1-1:2005(formerlyEUROCODE3-2005)"
    EN_1993_1_1_2022 = "EN 1993-1-1:2022"
    EUROCODE_3_1993 = "Eurocode 3-1993"
    
    # 印度规范
    INDIAN_IS_800_1998 = "Indian IS 800-1998"
    INDIAN_IS_800_2007 = "Indian IS 800-2007"
    
    # 意大利规范
    ITALIAN_NTC_2008 = "Italian NTC 2008"
    ITALIAN_NTC_2018 = "Italian NTC 2018"
    ITALIAN_UNI_10011 = "Italian UNI 10011"
    
    # 韩国规范
    KBC_2009 = "KBC 2009"
    
    # 挪威规范
    NORSOK_N_004 = "Norsok N-004"
    NORSOK_N_004_2013 = "Norsok N-004 2013"
    
    # 新西兰规范
    NZS_3404_1997 = "NZS 3404-1997"
    
    # 俄罗斯规范
    SP_16_13330_2011 = "SP 16.13330.2011"



class RatioType(IntEnum):
    """
    控制应力/承载力比类型
    """
    PMM = 1                    # 轴力-弯矩组合
    MAJOR_SHEAR = 2            # 主剪力
    MINOR_SHEAR = 3            # 次剪力
    MAJOR_BEAM_COLUMN = 4      # 主轴梁柱承载力比
    MINOR_BEAM_COLUMN = 5      # 次轴梁柱承载力比
    OTHER = 6                  # 其他


class ItemType(IntEnum):
    """
    对象类型枚举
    用于指定操作对象的范围
    """
    OBJECT = 0           # 单个对象
    GROUP = 1            # 组
    SELECTED_OBJECTS = 2 # 选中的对象


@dataclass
class SteelDesignResult:
    """
    钢结构设计结果
    
    Attributes:
        frame_name: 框架对象名称
        ratio: 控制应力/承载力比
        ratio_type: 比值类型
        location: 控制位置距I端距离 [L]
        combo_name: 控制荷载组合名称
        error_summary: 错误信息
        warning_summary: 警告信息
    """
    frame_name: str
    ratio: float
    ratio_type: RatioType
    location: float
    combo_name: str
    error_summary: str = ""
    warning_summary: str = ""


@dataclass
class SteelVerifyResult:
    """
    钢结构设计验证结果
    
    Attributes:
        total_not_passed: 未通过或未检查的对象总数
        not_passed_count: 未通过设计检查的对象数
        not_checked_count: 尚未检查的对象数
        frame_names: 未通过或未检查的框架对象名称列表
    """
    total_not_passed: int
    not_passed_count: int
    not_checked_count: int
    frame_names: List[str]


class SteelDesign:
    """
    钢结构设计管理类
    
    提供钢结构设计相关的静态方法
    """
    
    # ==================== 设计规范 ====================
    
    @staticmethod
    def get_code(model) -> str:
        """获取当前钢结构设计规范"""
        result = model.DesignSteel.GetCode("")
        if isinstance(result, tuple) and len(result) >= 2:
            return result[1]
        return ""
    
    @staticmethod
    def set_code(model, code: SteelDesignCode) -> int:
        """设置钢结构设计规范"""
        code_name = code.value if isinstance(code, SteelDesignCode) else str(code)
        return model.DesignSteel.SetCode(code_name)
    
    # ==================== 设计组 ====================
    
    @staticmethod
    def get_group(model) -> List[str]:
        """获取选定用于钢结构设计的组"""
        result = model.DesignSteel.GetGroup()
        if isinstance(result, tuple) and len(result) >= 3:
            names = result[2]
            if names:
                return list(names)
        return []
    
    @staticmethod
    def set_group(model, name: str, selected: bool = True) -> int:
        """选择或取消选择用于钢结构设计的组"""
        return model.DesignSteel.SetGroup(name, selected)
    
    # ==================== 设计执行 ====================
    
    @staticmethod
    def start_design(model) -> int:
        """开始钢结构设计"""
        return model.DesignSteel.StartDesign()
    
    @staticmethod
    def delete_results(model) -> int:
        """删除所有钢结构设计结果"""
        return model.DesignSteel.DeleteResults()

    
    # ==================== 设计结果 ====================
    
    @staticmethod
    def get_summary_results(
        model, 
        name: str, 
        item_type: ItemType = ItemType.OBJECT
    ) -> List[SteelDesignResult]:
        """获取钢结构设计汇总结果"""
        result = model.DesignSteel.GetSummaryResults(name, item_type)
        
        results = []
        if isinstance(result, tuple) and len(result) >= 9:
            ret = result[0]
            if ret == 0:
                num_items = result[1]
                frame_names = result[2] or []
                ratios = result[3] or []
                ratio_types = result[4] or []
                locations = result[5] or []
                combo_names = result[6] or []
                errors = result[7] or []
                warnings = result[8] or []
                
                for i in range(num_items):
                    results.append(SteelDesignResult(
                        frame_name=frame_names[i] if i < len(frame_names) else "",
                        ratio=ratios[i] if i < len(ratios) else 0.0,
                        ratio_type=RatioType(ratio_types[i]) if i < len(ratio_types) else RatioType.OTHER,
                        location=locations[i] if i < len(locations) else 0.0,
                        combo_name=combo_names[i] if i < len(combo_names) else "",
                        error_summary=errors[i] if i < len(errors) else "",
                        warning_summary=warnings[i] if i < len(warnings) else "",
                    ))
        
        return results
    
    @staticmethod
    def verify_passed(model) -> SteelVerifyResult:
        """验证设计是否通过"""
        result = model.DesignSteel.VerifyPassed()
        
        if isinstance(result, tuple) and len(result) >= 5:
            return SteelVerifyResult(
                total_not_passed=result[1],
                not_passed_count=result[2],
                not_checked_count=result[3],
                frame_names=list(result[4]) if result[4] else []
            )
        
        return SteelVerifyResult(0, 0, 0, [])
    
    @staticmethod
    def get_results_available(model) -> bool:
        """检查设计结果是否可用"""
        return model.DesignSteel.GetResultsAvailable()
    
    # ==================== 荷载组合 ====================
    
    @staticmethod
    def get_combo_strength(model) -> List[str]:
        """获取用于强度设计的荷载组合"""
        result = model.DesignSteel.GetComboStrength()
        if isinstance(result, tuple) and len(result) >= 3:
            names = result[2]
            if names:
                return list(names)
        return []
    
    @staticmethod
    def set_combo_strength(model, name: str, selected: bool = True) -> int:
        """选择或取消选择用于强度设计的荷载组合"""
        return model.DesignSteel.SetComboStrength(name, selected)
    
    @staticmethod
    def get_combo_deflection(model) -> List[str]:
        """获取用于挠度设计的荷载组合"""
        result = model.DesignSteel.GetComboDeflection()
        if isinstance(result, tuple) and len(result) >= 3:
            names = result[2]
            if names:
                return list(names)
        return []
    
    @staticmethod
    def set_combo_deflection(model, name: str, selected: bool = True) -> int:
        """选择或取消选择用于挠度设计的荷载组合"""
        return model.DesignSteel.SetComboDeflection(name, selected)
    
    @staticmethod
    def set_combo_auto_generate(model, auto_generate: bool = True) -> int:
        """设置是否自动生成设计荷载组合"""
        return model.DesignSteel.SetComboAutoGenerate(auto_generate)
    
    # ==================== 设计截面 ====================
    
    @staticmethod
    def get_design_section(model, name: str) -> str:
        """获取框架对象的设计截面"""
        result = model.DesignSteel.GetDesignSection(name, "")
        if isinstance(result, tuple) and len(result) >= 2:
            return result[1]
        return ""
    
    @staticmethod
    def set_design_section(
        model, 
        name: str, 
        prop_name: str = "",
        last_analysis: bool = False,
        item_type: ItemType = ItemType.OBJECT
    ) -> int:
        """设置框架对象的设计截面"""
        return model.DesignSteel.SetDesignSection(name, prop_name, last_analysis, item_type)
    
    # ==================== 重置 ====================
    
    @staticmethod
    def reset_overwrites(model) -> int:
        """重置所有钢结构设计覆盖值为默认值"""
        return model.DesignSteel.ResetOverwrites()
    
    @staticmethod
    def set_auto_select_null(model, name: str, item_type: ItemType = ItemType.OBJECT) -> int:
        """将自动选择截面设置为空"""
        return model.DesignSteel.SetAutoSelectNull(name, item_type)
