# -*- coding: utf-8 -*-
"""
PyInstaller hook for PySap2000 modules
"""
from PyInstaller.utils.hooks import collect_submodules, collect_data_files
import os
import sys

# 获取 PySap2000 根目录
pysap_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 添加到 sys.path
if pysap_root not in sys.path:
    sys.path.insert(0, pysap_root)

# 收集所有 PySap2000 子模块
hiddenimports = []

# 主要模块
modules = [
    'export',
    'export.cad_export',
    'statistics',
    'statistics.SteelUsage',
    'statistics.CableUsage', 
    'design',
    'design.steel',
    'design.enums',
    'frame',
    'frame.property',
    'group',
    'group.Group',
    'results',
    'results.frame_results',
    'area',
    'cable',
    'link',
    'loading',
    'loads',
    'selection',
    'file',
    'point',
    'section',
    'database_tables',
    'utils',
    'structure_core',
]

for module in modules:
    try:
        hiddenimports.extend(collect_submodules(module))
    except:
        pass

# 收集数据文件（如果有）
datas = []
try:
    datas.extend(collect_data_files('export'))
except:
    pass
