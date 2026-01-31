# -*- coding: utf-8 -*-
"""
design/enums.py - 设计模块枚举

钢结构设计相关枚举类型。
"""

from enum import IntEnum


class SteelDesignCode(IntEnum):
    """钢结构设计规范
    
    SAP2000 支持的钢结构设计规范代码。
    注意：API 使用字符串名称，此枚举用于类型安全和代码提示。
    """
    AASHTO_LRFD_2007 = 1
    AISC_ASD89 = 2
    AISC_360_10 = 3
    AISC_360_05_IBC2006 = 4
    AISC_LRFD93 = 5
    API_RP2A_LRFD_97 = 6
    API_RP2A_WSD2000 = 7
    API_RP2A_WSD2014 = 8
    AS_4100_1998 = 9
    ASCE_10_97 = 10
    BS5950_2000 = 11
    CHINESE_2010 = 12
    CSA_S16_19 = 13
    CSA_S16_14 = 14
    CSA_S16_09 = 15
    EN1993_1_1_2005 = 16  # formerly EUROCODE 3-2005
    INDIAN_IS_800_2007 = 17
    ITALIAN_NTC_2008 = 18
    ITALIAN_UNI_10011 = 19
    KBC_2009 = 20
    NORSOK_N_004_2013 = 21
    NZS_3404_1997 = 22
    SP_16_13330_2011 = 23


# 规范代码名称映射（API 使用字符串）
STEEL_CODE_NAMES = {
    SteelDesignCode.AASHTO_LRFD_2007: "AASHTO LRFD 2007",
    SteelDesignCode.AISC_ASD89: "AISC-ASD89",
    SteelDesignCode.AISC_360_10: "AISC 360-10",
    SteelDesignCode.AISC_360_05_IBC2006: "AISC360-05/IBC2006",
    SteelDesignCode.AISC_LRFD93: "AISC-LRFD93",
    SteelDesignCode.API_RP2A_LRFD_97: "API RP2A-LRFD 97",
    SteelDesignCode.API_RP2A_WSD2000: "API RP2A-WSD2000",
    SteelDesignCode.API_RP2A_WSD2014: "API RP2A-WSD2014",
    SteelDesignCode.AS_4100_1998: "AS 4100-1998",
    SteelDesignCode.ASCE_10_97: "ASCE 10-97",
    SteelDesignCode.BS5950_2000: "BS5950 2000",
    SteelDesignCode.CHINESE_2010: "Chinese 2010",
    SteelDesignCode.CSA_S16_19: "CSA S16-19",
    SteelDesignCode.CSA_S16_14: "CSA S16-14",
    SteelDesignCode.CSA_S16_09: "CSA-S16-09",
    SteelDesignCode.EN1993_1_1_2005: "EN1993-1-1:2005(formerlyEUROCODE3-2005)",
    SteelDesignCode.INDIAN_IS_800_2007: "Indian IS 800-2007",
    SteelDesignCode.ITALIAN_NTC_2008: "Italian NTC 2008",
    SteelDesignCode.ITALIAN_UNI_10011: "Italian UNI 10011",
    SteelDesignCode.KBC_2009: "KBC 2009",
    SteelDesignCode.NORSOK_N_004_2013: "Norsok N-004 2013",
    SteelDesignCode.NZS_3404_1997: "NZS 3404-1997",
    SteelDesignCode.SP_16_13330_2011: "SP 16.13330.2011",
}

# 反向映射：字符串名称 -> 枚举
STEEL_CODE_FROM_NAME = {v: k for k, v in STEEL_CODE_NAMES.items()}


class RatioType(IntEnum):
    """设计应力比类型
    
    控制应力比或承载力比的类型。
    """
    NONE = 0                    # 无/未知
    PMM = 1                     # 轴力-弯矩组合
    MAJOR_SHEAR = 2             # 主剪力
    MINOR_SHEAR = 3             # 次剪力
    MAJOR_BEAM_COLUMN = 4       # 主轴梁柱承载力比
    MINOR_BEAM_COLUMN = 5       # 次轴梁柱承载力比
    OTHER = 6                   # 其他


class ItemType(IntEnum):
    """对象选择类型
    
    用于指定设计结果的对象范围。
    """
    OBJECT = 0          # 单个对象
    GROUP = 1           # 组
    SELECTED_OBJECTS = 2  # 选中的对象
