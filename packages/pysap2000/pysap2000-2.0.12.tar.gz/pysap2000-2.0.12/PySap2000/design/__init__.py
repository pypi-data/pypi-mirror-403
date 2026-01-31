# -*- coding: utf-8 -*-
"""
design - 设计模块

SAP2000 的 Design API，用于结构设计。

SAP2000 API 结构:
- DesignSteel - 钢结构设计
  - GetCode / SetCode - 设计规范
  - StartDesign - 开始设计
  - DeleteResults - 删除设计结果
  - GetSummaryResults - 获取设计汇总结果
  - GetGroup / SetGroup - 设计组
  - GetDesignSection / SetDesignSection - 设计截面
  - GetComboStrength / SetComboStrength - 强度设计组合
  - GetComboDeflection / SetComboDeflection - 挠度设计组合
  - ResetOverwrites - 重置覆盖
  - VerifyPassed - 验证通过
  - VerifySections - 验证截面
  - GetResultsAvailable - 结果是否可用
  - Chinese_2010 - 中国规范 GB 50017-2010
    - GetPreference / SetPreference - 首选项
    - GetOverwrite / SetOverwrite - 覆盖项

Usage:
    from PySap2000.design import (
        # 钢结构设计
        get_steel_code,
        set_steel_code,
        start_steel_design,
        delete_steel_results,
        get_steel_summary_results,
        # 枚举
        SteelDesignCode,
        RatioType,
        ItemType,
        # 中国规范
        get_chinese_2010_preference,
        set_chinese_2010_preference,
        get_chinese_2010_overwrite,
        set_chinese_2010_overwrite,
        FramingType,
        SeismicDesignGrade,
        PreferenceItem,
        OverwriteItem,
    )
    
    # 典型工作流 - 中国规范
    set_steel_code(model, SteelDesignCode.CHINESE_2010)
    set_chinese_2010_gamma0(model, 1.0)
    set_chinese_2010_seismic_grade(model, SeismicDesignGrade.GRADE_II)
    start_steel_design(model)
    results = get_steel_summary_results(model, "ALL", ItemType.GROUP)
"""

from .enums import SteelDesignCode, RatioType, ItemType

from .data_classes import (
    SteelSummaryResult,
    VerifyPassedResult,
)

from .steel import (
    get_steel_code,
    set_steel_code,
    start_steel_design,
    delete_steel_results,
    get_steel_summary_results,
    get_steel_design_group,
    set_steel_design_group,
    get_steel_design_section,
    set_steel_design_section,
    get_steel_combo_strength,
    set_steel_combo_strength,
    get_steel_combo_deflection,
    set_steel_combo_deflection,
    reset_steel_overwrites,
    verify_steel_passed,
    verify_steel_sections,
    get_steel_results_available,
)

# 中国规范 GB 50017-2010
from .chinese_2010 import (
    # 枚举
    FramingType,
    ElementType,
    SeismicDesignGrade,
    MultiResponseDesign,
    DeflectionCheckType,
    OverwriteItem,
    PreferenceItem,
    # 数据类
    OverwriteResult,
    # 核心函数
    get_chinese_2010_preference,
    set_chinese_2010_preference,
    get_chinese_2010_overwrite,
    set_chinese_2010_overwrite,
    # 便捷函数 - 首选项
    set_chinese_2010_framing_type,
    set_chinese_2010_gamma0,
    set_chinese_2010_seismic_grade,
    set_chinese_2010_dc_ratio_limit,
    set_chinese_2010_tall_building,
    # 便捷函数 - 覆盖项
    set_chinese_2010_element_type,
    set_chinese_2010_mue_factors,
    set_chinese_2010_unbraced_ratios,
)

__all__ = [
    # 通用枚举
    "SteelDesignCode",
    "RatioType",
    "ItemType",
    # 通用数据类
    "SteelSummaryResult",
    "VerifyPassedResult",
    # 钢结构设计函数
    "get_steel_code",
    "set_steel_code",
    "start_steel_design",
    "delete_steel_results",
    "get_steel_summary_results",
    "get_steel_design_group",
    "set_steel_design_group",
    "get_steel_design_section",
    "set_steel_design_section",
    "get_steel_combo_strength",
    "set_steel_combo_strength",
    "get_steel_combo_deflection",
    "set_steel_combo_deflection",
    "reset_steel_overwrites",
    "verify_steel_passed",
    "verify_steel_sections",
    "get_steel_results_available",
    # 中国规范枚举
    "FramingType",
    "ElementType",
    "SeismicDesignGrade",
    "MultiResponseDesign",
    "DeflectionCheckType",
    "OverwriteItem",
    "PreferenceItem",
    # 中国规范数据类
    "OverwriteResult",
    # 中国规范核心函数
    "get_chinese_2010_preference",
    "set_chinese_2010_preference",
    "get_chinese_2010_overwrite",
    "set_chinese_2010_overwrite",
    # 中国规范便捷函数
    "set_chinese_2010_framing_type",
    "set_chinese_2010_gamma0",
    "set_chinese_2010_seismic_grade",
    "set_chinese_2010_dc_ratio_limit",
    "set_chinese_2010_tall_building",
    "set_chinese_2010_element_type",
    "set_chinese_2010_mue_factors",
    "set_chinese_2010_unbraced_ratios",
]

# AI Agent 友好的 API 分类
DESIGN_API_CATEGORIES = {
    "steel_code": {
        "description": "钢结构设计规范",
        "functions": ["get_steel_code", "set_steel_code"],
        "enums": ["SteelDesignCode"],
        "api_path": "DesignSteel.GetCode/SetCode",
    },
    "steel_design": {
        "description": "钢结构设计执行",
        "functions": ["start_steel_design", "delete_steel_results", "get_steel_results_available"],
        "api_path": "DesignSteel.StartDesign/DeleteResults/GetResultsAvailable",
    },
    "steel_results": {
        "description": "钢结构设计结果",
        "functions": ["get_steel_summary_results", "verify_steel_passed", "verify_steel_sections"],
        "classes": ["SteelSummaryResult", "VerifyPassedResult"],
        "enums": ["RatioType", "ItemType"],
        "api_path": "DesignSteel.GetSummaryResults/VerifyPassed/VerifySections",
    },
    "steel_group": {
        "description": "钢结构设计组",
        "functions": ["get_steel_design_group", "set_steel_design_group"],
        "api_path": "DesignSteel.GetGroup/SetGroup",
    },
    "steel_section": {
        "description": "钢结构设计截面",
        "functions": ["get_steel_design_section", "set_steel_design_section"],
        "api_path": "DesignSteel.GetDesignSection/SetDesignSection",
    },
    "steel_combo": {
        "description": "钢结构设计组合",
        "functions": [
            "get_steel_combo_strength",
            "set_steel_combo_strength",
            "get_steel_combo_deflection",
            "set_steel_combo_deflection",
        ],
        "api_path": "DesignSteel.GetComboStrength/SetComboStrength/GetComboDeflection/SetComboDeflection",
    },
    "steel_overwrites": {
        "description": "钢结构设计覆盖",
        "functions": ["reset_steel_overwrites"],
        "api_path": "DesignSteel.ResetOverwrites",
    },
    "chinese_2010_preference": {
        "description": "中国规范 GB 50017-2010 首选项",
        "functions": [
            "get_chinese_2010_preference",
            "set_chinese_2010_preference",
            "set_chinese_2010_framing_type",
            "set_chinese_2010_gamma0",
            "set_chinese_2010_seismic_grade",
            "set_chinese_2010_dc_ratio_limit",
            "set_chinese_2010_tall_building",
        ],
        "enums": ["PreferenceItem", "FramingType", "SeismicDesignGrade", "MultiResponseDesign"],
        "api_path": "DesignSteel.Chinese_2010.GetPreference/SetPreference",
    },
    "chinese_2010_overwrite": {
        "description": "中国规范 GB 50017-2010 覆盖项",
        "functions": [
            "get_chinese_2010_overwrite",
            "set_chinese_2010_overwrite",
            "set_chinese_2010_element_type",
            "set_chinese_2010_mue_factors",
            "set_chinese_2010_unbraced_ratios",
        ],
        "classes": ["OverwriteResult"],
        "enums": ["OverwriteItem", "ElementType", "DeflectionCheckType"],
        "api_path": "DesignSteel.Chinese_2010.GetOverwrite/SetOverwrite",
    },
}
