# -*- coding: utf-8 -*-
"""
表格操作工具 - DatabaseTables 相关操作

重构: 复用 PySap2000.database_tables 模块
"""

import json
from langchain.tools import tool

from .base import get_sap_model, to_json, success_response, error_response, safe_sap_call
from .history import add_to_history


@tool
@safe_sap_call
def get_joint_coordinates_table() -> str:
    """
    获取所有节点坐标表格数据。
    返回节点名称和 X、Y、Z 坐标。
    """
    model = get_sap_model()
    
    ret = model.DatabaseTables.GetTableForDisplayArray(
        "Joint Coordinates", ["Joint", "GlobalX", "GlobalY", "GlobalZ"], "", 0, [], 0, []
    )
    
    if not isinstance(ret, (list, tuple)) or len(ret) < 5 or ret[-1] != 0:
        return error_response("无法获取节点坐标表")
    
    fields = list(ret[1]) if ret[1] else []
    num_records = ret[2]
    data = list(ret[3]) if ret[3] else []
    num_fields = len(fields)
    
    joints = []
    for i in range(min(num_records, 100)):
        base = i * num_fields
        row = {fields[j]: data[base + j] if base + j < len(data) else "" for j in range(num_fields)}
        joints.append(row)
    
    return to_json({"节点数": num_records, "节点列表": joints}, indent=2)


@tool
@safe_sap_call
def modify_joint_coordinate(joint_name: str, x: float = None, y: float = None, z: float = None) -> str:
    """
    通过表格修改节点坐标。支持撤回操作。
    
    Args:
        joint_name: 节点名称
        x: 新的 X 坐标（可选，不填则不修改）
        y: 新的 Y 坐标（可选，不填则不修改）
        z: 新的 Z 坐标（可选，不填则不修改）
    """
    model = get_sap_model()
    model.SetModelIsLocked(False)
    
    try:
        from PySap2000.database_tables import DatabaseTables
        
        data = DatabaseTables.get_table_for_editing(model, "Joint Coordinates")
        if not data:
            return error_response("无法获取节点坐标表")
        
        rows = data.find_rows("Joint", str(joint_name))
        if not rows:
            return error_response(f"节点 '{joint_name}' 不存在")
        
        row_idx = rows[0]
        old_x = data.get_value(row_idx, "GlobalX") or data.get_value(row_idx, "XorR")
        old_y = data.get_value(row_idx, "GlobalY") or data.get_value(row_idx, "Y")
        old_z = data.get_value(row_idx, "GlobalZ") or data.get_value(row_idx, "Z")
        
        try:
            old_x_float = float(old_x) if old_x else 0.0
            old_y_float = float(old_y) if old_y else 0.0
            old_z_float = float(old_z) if old_z else 0.0
        except:
            old_x_float, old_y_float, old_z_float = 0.0, 0.0, 0.0
        
        if x is not None:
            data.set_value(row_idx, "GlobalX", str(x)) or data.set_value(row_idx, "XorR", str(x))
        if y is not None:
            data.set_value(row_idx, "GlobalY", str(y)) or data.set_value(row_idx, "Y", str(y))
        if z is not None:
            data.set_value(row_idx, "GlobalZ", str(z)) or data.set_value(row_idx, "Z", str(z))
        
        ret = DatabaseTables.set_table_for_editing(model, data)
        if ret != 0:
            return error_response("设置表格数据失败")
        
        result = DatabaseTables.apply_edited_tables(model)
        if not result.success:
            return error_response(result.import_log or "应用修改失败")
        
        add_to_history(
            tool_name="modify_joint_coordinate",
            undo_action="modify_joint_coordinate",
            undo_args={"joint_name": joint_name, "x": old_x_float, "y": old_y_float, "z": old_z_float},
            description=f"修改节点 {joint_name} 坐标"
        )
        
        return success_response(
            "修改成功",
            节点=joint_name,
            原坐标={"X": old_x, "Y": old_y, "Z": old_z},
            新坐标={"X": x if x is not None else old_x, "Y": y if y is not None else old_y, "Z": z if z is not None else old_z}
        )
        
    except ImportError:
        return error_response("database_tables 模块不可用")


@tool
@safe_sap_call
def batch_modify_joints(modifications: str) -> str:
    """
    批量修改多个节点的坐标。
    
    Args:
        modifications: JSON 格式的修改列表，例如：
            '[{"joint": "1", "x": 100}, {"joint": "2", "y": 200, "z": 50}]'
    """
    model = get_sap_model()
    model.SetModelIsLocked(False)
    
    try:
        mods = json.loads(modifications)
    except:
        return error_response("JSON 格式错误")
    
    try:
        from PySap2000.database_tables import DatabaseTables
        
        data = DatabaseTables.get_table_for_editing(model, "Joint Coordinates")
        if not data:
            return error_response("无法获取节点坐标表")
        
        modified = []
        for mod in mods:
            joint_name = mod.get("joint")
            if not joint_name:
                continue
            rows = data.find_rows("Joint", str(joint_name))
            if not rows:
                continue
            row_idx = rows[0]
            if "x" in mod:
                data.set_value(row_idx, "GlobalX", str(mod["x"])) or data.set_value(row_idx, "XorR", str(mod["x"]))
            if "y" in mod:
                data.set_value(row_idx, "GlobalY", str(mod["y"])) or data.set_value(row_idx, "Y", str(mod["y"]))
            if "z" in mod:
                data.set_value(row_idx, "GlobalZ", str(mod["z"])) or data.set_value(row_idx, "Z", str(mod["z"]))
            modified.append(joint_name)
        
        ret = DatabaseTables.set_table_for_editing(model, data)
        if ret != 0:
            return error_response("设置表格数据失败")
        
        result = DatabaseTables.apply_edited_tables(model)
        if not result.success:
            return error_response(result.import_log or "应用修改失败")
        
        return success_response("批量修改成功", 修改节点数=len(modified), 节点列表=modified)
        
    except ImportError:
        return error_response("database_tables 模块不可用")


@tool
@safe_sap_call
def get_frame_section_assignments_table() -> str:
    """
    获取杆件截面分配表格数据。
    返回杆件名称和对应的截面。
    """
    model = get_sap_model()
    
    ret = model.DatabaseTables.GetTableForDisplayArray(
        "Frame Section Assignments", ["Frame", "AnalSect", "DesignSect"], "", 0, [], 0, []
    )
    
    if not isinstance(ret, (list, tuple)) or len(ret) < 5 or ret[-1] != 0:
        return error_response("无法获取杆件截面表")
    
    fields = list(ret[1]) if ret[1] else []
    num_records = ret[2]
    data = list(ret[3]) if ret[3] else []
    num_fields = len(fields)
    
    frames = []
    for i in range(min(num_records, 100)):
        base = i * num_fields
        row = {fields[j]: data[base + j] if base + j < len(data) else "" for j in range(num_fields)}
        frames.append(row)
    
    return to_json({"杆件数": num_records, "杆件列表": frames}, indent=2)


@tool
@safe_sap_call
def get_available_tables() -> str:
    """获取模型中所有可用的数据库表格列表。"""
    model = get_sap_model()
    
    ret = model.DatabaseTables.GetAvailableTables(0, [], [], [], [])
    
    if not isinstance(ret, (list, tuple)) or len(ret) < 5:
        return error_response("无法获取表格列表")
    
    num_tables = ret[0]
    table_keys = list(ret[1]) if ret[1] else []
    table_names = list(ret[2]) if ret[2] else []
    
    tables = [{"键名": table_keys[i], "名称": table_names[i]} for i in range(min(num_tables, 50))]
    
    return to_json({"表格数": num_tables, "表格列表": tables}, indent=2)
