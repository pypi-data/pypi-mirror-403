# -*- coding: utf-8 -*-
"""
steel_design - 钢结构设计模块
包含钢结构设计规范、设计组、设计结果等

API Reference:
    - DesignSteel.GetCode / SetCode
    - DesignSteel.GetGroup / SetGroup
    - DesignSteel.StartDesign
    - DesignSteel.GetSummaryResults
    - DesignSteel.DeleteResults
    - DesignSteel.VerifyPassed
"""

from .steel_design import (
    SteelDesign,
    SteelDesignCode,
    SteelDesignResult,
    SteelVerifyResult,
    RatioType,
    ItemType,
)

__all__ = [
    'SteelDesign',
    'SteelDesignCode',
    'SteelDesignResult',
    'SteelVerifyResult',
    'RatioType',
    'ItemType',
]
