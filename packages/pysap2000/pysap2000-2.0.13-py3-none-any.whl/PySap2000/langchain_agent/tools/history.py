# -*- coding: utf-8 -*-
"""
操作历史模块 - 用于撤回功能
"""

from langchain.tools import tool
from typing import Optional, List

from .base import get_sap_model, to_json, success_response, error_response, safe_sap_call


# =============================================================================
# 操作历史栈
# =============================================================================

_operation_history: List[dict] = []
MAX_HISTORY_SIZE = 50


def add_to_history(tool_name: str, undo_action: str, undo_args: dict, description: str):
    """添加操作到历史栈"""
    global _operation_history
    _operation_history.append({
        "tool": tool_name,
        "undo_action": undo_action,
        "undo_args": undo_args,
        "description": description
    })
    if len(_operation_history) > MAX_HISTORY_SIZE:
        _operation_history = _operation_history[-MAX_HISTORY_SIZE:]


def pop_from_history() -> Optional[dict]:
    """从历史栈弹出最近一条操作"""
    global _operation_history
    if _operation_history:
        return _operation_history.pop()
    return None


def get_history_count() -> int:
    """获取历史记录数量"""
    return len(_operation_history)


def clear_history_stack():
    """清空历史记录"""
    global _operation_history
    _operation_history = []


# =============================================================================
# 撤回操作工具
# =============================================================================

@tool
@safe_sap_call
def undo_last_operation() -> str:
    """
    撤回上一步修改操作，恢复到修改前的状态。
    支持撤回的操作包括：修改节点坐标、修改杆件截面等。
    """
    last_op = pop_from_history()
    
    if not last_op:
        return success_response("没有可撤回的操作")
    
    undo_action = last_op.get("undo_action")
    undo_args = last_op.get("undo_args", {})
    description = last_op.get("description", "")
    
    if undo_action == "modify_joint_coordinate":
        return _undo_joint_coordinate(undo_args, description)
    elif undo_action == "set_frame_section":
        return _undo_frame_section(undo_args, description)
    else:
        return error_response(f"不支持撤回的操作类型: {undo_action}")


def _undo_joint_coordinate(undo_args: dict, description: str) -> str:
    """撤回节点坐标修改"""
    try:
        from PySap2000.database_tables import DatabaseTables
        
        model = get_sap_model()
        model.SetModelIsLocked(False)
        
        joint_name = undo_args.get("joint_name")
        x = undo_args.get("x")
        y = undo_args.get("y")
        z = undo_args.get("z")
        
        data = DatabaseTables.get_table_for_editing(model, "Joint Coordinates")
        if not data:
            return error_response("无法获取节点坐标表")
        
        rows = data.find_rows("Joint", str(joint_name))
        if not rows:
            return error_response(f"节点 '{joint_name}' 不存在")
        
        row_idx = rows[0]
        data.set_value(row_idx, "GlobalX", str(x)) or data.set_value(row_idx, "XorR", str(x))
        data.set_value(row_idx, "GlobalY", str(y)) or data.set_value(row_idx, "Y", str(y))
        data.set_value(row_idx, "GlobalZ", str(z)) or data.set_value(row_idx, "Z", str(z))
        
        DatabaseTables.set_table_for_editing(model, data)
        result = DatabaseTables.apply_edited_tables(model)
        
        if result.success:
            return success_response("撤回成功", 撤回操作=description, 恢复坐标={"X": x, "Y": y, "Z": z})
        return error_response("撤回失败: " + (result.import_log or "未知错误"))
        
    except ImportError:
        return error_response("database_tables 模块不可用")


def _undo_frame_section(undo_args: dict, description: str) -> str:
    """撤回杆件截面修改"""
    from PySap2000.frame import set_frame_section
    
    model = get_sap_model()
    model.SetModelIsLocked(False)
    
    frame_name = undo_args.get("frame_name")
    section_name = undo_args.get("section_name")
    
    ret = set_frame_section(model, frame_name, section_name)
    
    if ret == 0:
        return success_response("撤回成功", 撤回操作=description, 恢复截面=section_name)
    return error_response(f"撤回失败: 无法设置截面 '{section_name}'")


@tool
def get_operation_history(count: int = 10) -> str:
    """
    查看最近的操作历史记录。
    
    Args:
        count: 返回的记录数量，默认 10 条
    """
    history_count = get_history_count()
    
    if history_count == 0:
        return success_response("暂无操作历史")
    
    recent = _operation_history[-count:] if count < history_count else _operation_history[:]
    recent = list(reversed(recent))
    
    history_list = [
        {"序号": i + 1, "操作": op.get("description", op.get("tool", "未知"))}
        for i, op in enumerate(recent)
    ]
    
    return to_json({"总记录数": history_count, "最近操作": history_list}, indent=2)


@tool
def clear_operation_history() -> str:
    """清空所有操作历史记录。"""
    clear_history_stack()
    return success_response("操作历史已清空")
