# -*- coding: utf-8 -*-
"""
基础模块 - SAP2000 连接、工具分类、JSON 序列化辅助

重构说明:
- 连接管理复用 PySap2000.application 模块
- 工具分类用于 Human-in-the-loop 确认机制
- 提供统一的 JSON 序列化辅助函数
"""

import json
import functools
from typing import Any, Dict, List, Optional
from dataclasses import asdict, is_dataclass

# =============================================================================
# 工具分类 - 用于 Human-in-the-loop 确认机制
# =============================================================================

# 查询类工具 - 不修改模型，自动执行
QUERY_TOOLS = {
    # 连接检查
    "check_connection",
    # 模型信息
    "get_model_info",
    "get_group_list",
    "get_section_list",
    "get_material_list",
    "get_load_pattern_list",
    "get_load_case_list",
    "get_combo_list",
    "get_section_info",
    # RAG 知识库搜索
    "search_sap_docs",
    # 节点查询
    "get_point_coordinates",
    "get_point_restraint",
    "get_point_list",
    "get_points_in_group",
    # 杆件查询
    "get_frame_info",
    "get_frames_in_group",
    "get_frame_list",
    "get_frame_loads",
    "get_frame_release",
    # 面单元查询
    "get_area_info",
    "get_areas_in_group",
    "get_area_list",
    # 索/连接单元查询
    "get_cable_info",
    "get_cables_in_group",
    "get_cable_list",
    "get_link_info",
    "get_link_list",
    "get_links_in_group",
    # 截面/约束查询
    "get_constraint_list",
    # 结果查询
    "get_point_displacement",
    "get_point_reactions",
    "get_base_reactions",
    "get_frame_forces",
    "get_max_frame_forces",
    "get_stress_ratios",
    "get_modal_periods",
    "get_modal_mass_ratios",
    "verify_steel_design",
    # 统计
    "get_steel_usage",
    "get_cable_usage",
    # 通用绑图
    "draw_chart",
    # 选择查询
    "get_selected_objects",
    # 表格查询
    "get_joint_coordinates_table",
    "get_frame_section_assignments_table",
    "get_available_tables",
    # 视图
    "refresh_view",
    "zoom_all",
    # 撤回操作（查看历史不需要确认）
    "get_operation_history",
}

# 修改类工具 - 会修改模型，需要用户确认
MODIFY_TOOLS = {
    # 节点操作
    "create_point",
    "delete_point",
    "set_point_restraint",
    "modify_joint_coordinate",
    "batch_modify_joints",
    "merge_points",
    # 杆件操作
    "create_frame",
    "delete_frame",
    "set_frame_section",
    "set_frame_release",
    "divide_frame",
    # 面单元操作
    "create_area",
    "delete_area",
    "set_area_section",
    # 索/连接单元操作
    "create_cable",
    "delete_cable",
    "create_link",
    "delete_link",
    # 批量操作
    "batch_set_section",
    "batch_add_distributed_load",
    "batch_set_restraint",
    # 荷载操作
    "add_point_load",
    "add_frame_distributed_load",
    "add_frame_point_load",
    "add_area_load",
    "delete_point_load",
    "delete_frame_load",
    "create_load_pattern",
    "delete_load_pattern",
    # 组操作
    "create_group",
    "delete_group",
    "add_frame_to_group",
    "add_point_to_group",
    "add_area_to_group",
    "add_selected_to_group",
    "remove_from_group",
    # 约束操作
    "create_diaphragm_constraint",
    "assign_point_constraint",
    "delete_constraint",
    # 编辑操作
    "move_selected_objects",
    "replicate_linear",
    "replicate_mirror",
    "replicate_radial",
    # 分析设计
    "run_analysis",
    "run_steel_design",
    "run_concrete_design",
    # 文件操作
    "save_model",
    "unlock_model",
    "new_model",
    "open_model",
    # 选择操作（修改选择状态）
    "select_all",
    "clear_selection",
    "select_group",
    "select_by_property",
    # 撤回操作（会修改模型，需要确认）
    "undo_last_operation",
    "clear_operation_history",
    # 截面/材料操作
    "create_section",
    "delete_section",
    "create_material",
    "delete_material",
}


# =============================================================================
# 异常类
# =============================================================================

class SapConnectionError(Exception):
    """SAP2000 连接错误"""
    pass


class SapModelError(Exception):
    """SAP2000 模型错误"""
    pass


# =============================================================================
# SAP2000 连接 - 复用 PySap2000.application
# =============================================================================

_sap_model = None


def get_sap_model():
    """
    获取 SAP2000 模型对象（带缓存和错误处理）
    
    复用 PySap2000.application 模块的连接逻辑
    
    Raises:
        SapConnectionError: SAP2000 未启动或连接失败
        SapModelError: 模型未打开或已锁定
    """
    global _sap_model
    
    # 检查缓存的连接是否有效
    if _sap_model is not None:
        try:
            _sap_model.GetModelFilename(False)
            return _sap_model
        except:
            _sap_model = None
    
    # 尝试连接 SAP2000
    try:
        import comtypes
        comtypes.CoInitialize()
        import comtypes.client
        sap = comtypes.client.GetActiveObject("CSI.SAP2000.API.SapObject")
        _sap_model = sap.SapModel
    except Exception as e:
        error_msg = str(e).lower()
        if "没有注册类" in error_msg or "class not registered" in error_msg:
            raise SapConnectionError("SAP2000 未安装或未正确注册，请检查安装")
        elif "操作不可用" in error_msg or "operation unavailable" in error_msg:
            raise SapConnectionError("SAP2000 未启动，请先打开 SAP2000 软件")
        else:
            raise SapConnectionError(f"无法连接 SAP2000: {e}")
    
    # 检查是否有模型打开
    try:
        filename = _sap_model.GetModelFilename(False)
        if not filename:
            raise SapModelError("SAP2000 已启动但未打开模型，请先打开或新建一个模型")
    except SapModelError:
        raise
    except Exception as e:
        raise SapModelError(f"无法获取模型信息: {e}")
    
    return _sap_model


def reset_sap_connection():
    """重置 SAP2000 连接缓存"""
    global _sap_model
    _sap_model = None


def is_sap_connected() -> bool:
    """检查 SAP2000 连接是否有效"""
    global _sap_model
    if _sap_model is None:
        return False
    try:
        _sap_model.GetModelFilename(False)
        return True
    except:
        return False


# =============================================================================
# JSON 序列化辅助函数
# =============================================================================

def to_json(data: Any, indent: int = None) -> str:
    """
    将数据转换为 JSON 字符串
    
    支持:
    - dict, list, 基本类型
    - dataclass 对象
    - 带 to_dict() 方法的对象
    """
    if is_dataclass(data) and not isinstance(data, type):
        data = asdict(data)
    elif hasattr(data, 'to_dict'):
        data = data.to_dict()
    elif hasattr(data, '__dict__'):
        data = {k: v for k, v in data.__dict__.items() if not k.startswith('_')}
    
    return json.dumps(data, ensure_ascii=False, indent=indent)


def success_response(message: str, **kwargs) -> str:
    """返回成功响应的 JSON"""
    return to_json({"结果": message, **kwargs})


def error_response(message: str, suggestion: str = None) -> str:
    """返回错误响应的 JSON"""
    data = {"错误": message}
    if suggestion:
        data["建议"] = suggestion
    return to_json(data)


def format_result_list(
    items: List[Any],
    item_name: str,
    max_items: int = 200,
    extra_info: Dict = None
) -> str:
    """
    格式化结果列表为 JSON
    
    Args:
        items: 结果列表
        item_name: 项目名称（如 "杆件"、"节点"）
        max_items: 最大返回数量
        extra_info: 额外信息
    """
    data = {
        f"{item_name}数": len(items),
        f"{item_name}列表": items[:max_items]
    }
    if extra_info:
        data.update(extra_info)
    return to_json(data)


# =============================================================================
# 装饰器
# =============================================================================

def safe_sap_call(func):
    """
    装饰器：为 SAP2000 工具调用添加统一的错误处理
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SapConnectionError as e:
            reset_sap_connection()
            return error_response(str(e), "请确保 SAP2000 已启动并打开了模型文件")
        except SapModelError as e:
            return error_response(str(e), "请在 SAP2000 中打开或新建一个模型")
        except Exception as e:
            error_msg = str(e)
            if "disconnected" in error_msg.lower() or "rpc" in error_msg.lower():
                reset_sap_connection()
                return error_response("SAP2000 连接已断开", "请确保 SAP2000 正在运行，然后重试")
            elif "locked" in error_msg.lower() or "锁定" in error_msg:
                return error_response("模型已锁定，无法修改", "请先解锁模型")
            elif "not found" in error_msg.lower() or "不存在" in error_msg:
                return error_response(f"对象不存在: {error_msg}", "请检查对象名称是否正确")
            else:
                return error_response(f"操作失败: {error_msg}")
    return wrapper
