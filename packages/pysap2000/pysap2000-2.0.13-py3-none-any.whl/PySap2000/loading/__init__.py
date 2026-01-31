# -*- coding: utf-8 -*-
"""
loading - 荷载模式、工况、组合和质量源

SAP2000 术语:
    LoadPattern - 荷载模式 (如 DEAD, LIVE)
    LoadCase - 荷载工况/分析工况 (如 线性静力、模态、反应谱)
    LoadCombination - 荷载组合
    MassSource - 质量源 (动力分析质量来源)
"""

from .load_pattern import LoadPattern, LoadPatternType
from .load_case import (
    LoadCase,
    LoadCaseType,
    LoadCaseLoad,
    ModalSubType,
    TimeHistorySubType,
    DesignTypeOption,
    # 创建函数
    create_static_linear_case,
    create_static_nonlinear_case,
    create_modal_eigen_case,
    create_modal_ritz_case,
    create_response_spectrum_case,
    create_buckling_case,
    create_direct_history_linear_case,
    create_direct_history_nonlinear_case,
    create_modal_history_linear_case,
    create_modal_history_nonlinear_case,
    create_steady_state_case,
    create_psd_case,
    create_moving_load_case,
    create_hyperstatic_case,
    create_static_linear_multistep_case,
    create_static_nonlinear_multistep_case,
    create_staged_construction_case,
    # 荷载设置函数
    get_static_linear_loads,
    set_static_linear_loads,
)
from .load_combination import (
    # 枚举
    ComboCaseType,
    ComboType,
    # 函数
    add_combo,
    add_design_default_combos,
    change_combo_name,
    get_combo_count,
    get_combo_case_count,
    delete_combo,
    delete_combo_case,
    get_combo_name_list,
    get_combo_case_list,
    set_combo_case_list,
    get_combo_note,
    set_combo_note,
    get_combo_type,
    set_combo_type,
)
from .mass_source import MassSource, MassSourceLoad

__all__ = [
    # 荷载模式
    "LoadPattern",
    "LoadPatternType",
    # 荷载工况
    "LoadCase",
    "LoadCaseType",
    "LoadCaseLoad",
    "ModalSubType",
    "TimeHistorySubType",
    "DesignTypeOption",
    # 工况创建函数
    "create_static_linear_case",
    "create_static_nonlinear_case",
    "create_modal_eigen_case",
    "create_modal_ritz_case",
    "create_response_spectrum_case",
    "create_buckling_case",
    "create_direct_history_linear_case",
    "create_direct_history_nonlinear_case",
    "create_modal_history_linear_case",
    "create_modal_history_nonlinear_case",
    "create_steady_state_case",
    "create_psd_case",
    "create_moving_load_case",
    "create_hyperstatic_case",
    "create_static_linear_multistep_case",
    "create_static_nonlinear_multistep_case",
    "create_staged_construction_case",
    # 荷载设置函数
    "get_static_linear_loads",
    "set_static_linear_loads",
    # 荷载组合
    "ComboCaseType",
    "ComboType",
    "add_combo",
    "add_design_default_combos",
    "change_combo_name",
    "get_combo_count",
    "get_combo_case_count",
    "delete_combo",
    "delete_combo_case",
    "get_combo_name_list",
    "get_combo_case_list",
    "set_combo_case_list",
    "get_combo_note",
    "set_combo_note",
    "get_combo_type",
    "set_combo_type",
    # 质量源
    "MassSource",
    "MassSourceLoad",
]

# AI Agent 友好的 API 分类
LOADING_API_CATEGORIES = {
    "load_pattern": {
        "description": "荷载模式 (DEAD, LIVE 等)",
        "classes": ["LoadPattern"],
        "enums": ["LoadPatternType"],
    },
    "load_case": {
        "description": "荷载工况/分析工况",
        "classes": ["LoadCase", "LoadCaseLoad"],
        "enums": ["LoadCaseType", "ModalSubType", "TimeHistorySubType", "DesignTypeOption"],
        "functions": {
            "create": [
                "create_static_linear_case",
                "create_static_nonlinear_case",
                "create_modal_eigen_case",
                "create_modal_ritz_case",
                "create_response_spectrum_case",
                "create_buckling_case",
                "create_direct_history_linear_case",
                "create_direct_history_nonlinear_case",
                "create_modal_history_linear_case",
                "create_modal_history_nonlinear_case",
                "create_steady_state_case",
                "create_psd_case",
                "create_moving_load_case",
                "create_hyperstatic_case",
                "create_static_linear_multistep_case",
                "create_static_nonlinear_multistep_case",
                "create_staged_construction_case",
            ],
            "static_linear_loads": [
                "get_static_linear_loads",
                "set_static_linear_loads",
            ],
        },
    },
    "load_combination": {
        "description": "荷载组合",
        "classes": ["LoadCombination"],
    },
    "mass_source": {
        "description": "质量源 (动力分析质量来源)",
        "classes": ["MassSource", "MassSourceLoad"],
    },
}
