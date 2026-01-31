# -*- coding: utf-8 -*-
"""
view - 视图刷新模块

SAP2000 的 View API，用于刷新显示窗口。

SAP2000 API 结构:
- View.RefreshView - 刷新视图（重建显示数组后更新）
- View.RefreshWindow - 刷新窗口（仅更新显示）

区别：
- RefreshView: 添加、删除或移动对象后调用，会重建所有显示数组
- RefreshWindow: 修改属性（如约束、荷载）后调用，仅更新显示，速度更快

Usage:
    from PySap2000.view import refresh_view, refresh_window
    
    # 添加对象后刷新视图
    model.FrameObj.AddByPoint("1", "2", name)
    refresh_view(model)
    
    # 修改属性后刷新窗口
    model.PointObj.SetRestraint("1", [True]*6)
    refresh_window(model)
"""


def refresh_view(model, window: int = 0, zoom: bool = True) -> int:
    """刷新视图
    
    重建所有显示数组后更新显示。添加、删除或移动对象后应调用此函数。
    
    Args:
        model: SapModel 对象
        window: 窗口编号，0 表示所有窗口
        zoom: True 保持当前缩放，False 恢复默认缩放
        
    Returns:
        0 表示成功，非 0 表示失败
    """
    ret = model.View.RefreshView(window, zoom)
    if isinstance(ret, (list, tuple)):
        return ret[-1]
    return ret


def refresh_window(model, window: int = 0) -> int:
    """刷新窗口
    
    仅更新显示，不重建显示数组。修改属性（约束、荷载等）后调用此函数。
    比 refresh_view 更快。
    
    Args:
        model: SapModel 对象
        window: 窗口编号，0 表示所有窗口
        
    Returns:
        0 表示成功，非 0 表示失败
    """
    ret = model.View.RefreshWindow(window)
    if isinstance(ret, (list, tuple)):
        return ret[-1]
    return ret


__all__ = [
    "refresh_view",
    "refresh_window",
]

# AI Agent 友好的 API 分类
VIEW_API_CATEGORIES = {
    "refresh": {
        "description": "视图刷新",
        "functions": ["refresh_view", "refresh_window"],
        "api_path": "View.RefreshView/RefreshWindow",
        "notes": "RefreshView 用于添加/删除/移动对象后，RefreshWindow 用于修改属性后",
    },
}
