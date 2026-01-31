# -*- coding: utf-8 -*-
"""
PySap2000 可视化模块

用于将 SAP2000 模型导出为可视化格式（需要完整几何信息）
"""

# 延迟导入，避免在 Rhino 环境中导入失败
__all__ = [
    'WebExporter',
    'WebExporterSolid',
    'MeshGenerator',
    'RhinoBuilder',
]

def __getattr__(name):
    if name == 'WebExporter':
        from .web import WebExporter
        return WebExporter
    elif name == 'WebExporterSolid':
        from .web import WebExporterSolid
        return WebExporterSolid
    elif name == 'MeshGenerator':
        from .web import MeshGenerator
        return MeshGenerator
    elif name == 'RhinoBuilder':
        from .rhino import RhinoBuilder
        return RhinoBuilder
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
