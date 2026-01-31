# -*- coding: utf-8 -*-
"""
SAP2000 LangChain Tools 模块

重构说明:
- 所有工具复用 PySap2000 已有封装，避免重复实现
- 工具只负责 @tool 装饰和 JSON 序列化
- 统一使用 base.py 中的响应函数

工具分类：
1. 模型信息 - 获取模型基本信息、组、截面等
2. 节点操作 - 创建、查询、删除节点
3. 杆件操作 - 创建、查询、修改杆件
4. 面单元操作 - 查询面单元信息
5. 荷载操作 - 添加、查询荷载
6. 分析设计 - 运行分析、钢结构设计
7. 结果查询 - 位移、内力、反力
8. 选择操作 - 选择、清除选择
9. 视图操作 - 刷新视图、缩放
10. 统计功能 - 用钢量、用索量
11. 批量操作 - 批量修改截面、荷载、约束
12. 绑图工具 - 通用图表绑制

Human-in-the-loop:
- QUERY_TOOLS: 查询类工具，自动执行
- MODIFY_TOOLS: 修改类工具，需要用户确认
"""

from .base import (
    QUERY_TOOLS,
    MODIFY_TOOLS,
    get_sap_model,
    safe_sap_call,
    SapConnectionError,
    SapModelError,
    to_json,
    success_response,
    error_response,
)

from .model_info import (
    check_connection,
    get_model_info,
    get_group_list,
    get_section_list,
    get_material_list,
    get_load_pattern_list,
    get_load_case_list,
    get_combo_list,
    get_section_info,
)

from .point import (
    get_point_coordinates,
    create_point,
    delete_point,
    get_point_restraint,
    set_point_restraint,
    get_point_list,
    get_points_in_group,
)

from .frame import (
    get_frame_info,
    create_frame,
    set_frame_section,
    delete_frame,
    get_frames_in_group,
    get_frame_list,
    set_frame_release,
    get_frame_release,
)

from .area import (
    create_area,
    delete_area,
    set_area_section,
    add_area_to_group_tool,
    get_area_info,
    get_areas_in_group,
    get_area_list,
)

from .cable_link import (
    create_cable,
    delete_cable,
    get_cable_info,
    get_cables_in_group,
    get_cable_list,
    create_link,
    delete_link,
    get_link_info,
    get_link_list,
    get_links_in_group,
)

from .load import (
    add_point_load,
    delete_point_load,
    add_frame_distributed_load,
    add_frame_point_load,
    delete_frame_load,
    get_frame_loads,
    add_area_load,
    delete_area_load,
    create_load_pattern,
    delete_load_pattern,
)

from .analysis import (
    run_analysis,
    run_steel_design,
    get_stress_ratios,
    verify_steel_design,
)

from .results import (
    get_point_displacement,
    get_point_reactions,
    get_base_reactions,
    get_frame_forces,
    get_max_frame_forces,
    get_modal_periods,
    get_modal_mass_ratios,
)

from .selection import (
    select_all,
    clear_selection,
    select_group,
    get_selected_objects,
    select_by_property,
)

from .view import (
    refresh_view,
    zoom_all,
)

from .statistics import (
    get_steel_usage,
    get_cable_usage,
)

from .group import (
    create_group,
    add_frame_to_group,
    add_selected_to_group,
)

from .file_ops import (
    save_model,
    unlock_model,
    new_model,
    open_model,
)

from .constraint import (
    get_constraint_list,
    create_diaphragm_constraint,
    assign_point_constraint,
)

from .edit import (
    move_selected_objects,
    replicate_linear,
    replicate_mirror,
    replicate_radial,
    divide_frame,
    merge_points,
)

from .table import (
    get_joint_coordinates_table,
    modify_joint_coordinate,
    batch_modify_joints,
    get_frame_section_assignments_table,
    get_available_tables,
)

from .history import (
    undo_last_operation,
    get_operation_history,
    clear_operation_history,
    add_to_history,
)

from .batch import (
    batch_set_section,
    batch_add_distributed_load,
    batch_set_restraint,
)

from .combo import (
    full_design_check,
    steel_usage_report,
    model_overview,
    COMBO_TOOLS,
)

# 可选模块（可能不存在）
try:
    from .rag_search import search_sap_docs
except ImportError:
    search_sap_docs = None

try:
    from .chart import draw_chart
except ImportError:
    draw_chart = None


def get_sap_tools():
    """返回所有 SAP2000 工具列表"""
    tools = [
        # 0. 连接检查
        check_connection,
        # 1. 模型信息
        get_model_info,
        get_group_list,
        get_section_list,
        get_material_list,
        get_load_pattern_list,
        get_load_case_list,
        get_combo_list,
        get_section_info,
        # 2. 节点操作
        get_point_coordinates,
        create_point,
        delete_point,
        get_point_restraint,
        set_point_restraint,
        get_point_list,
        get_points_in_group,
        # 3. 杆件操作
        get_frame_info,
        create_frame,
        set_frame_section,
        delete_frame,
        get_frames_in_group,
        get_frame_list,
        set_frame_release,
        get_frame_release,
        # 4. 面单元操作
        create_area,
        delete_area,
        set_area_section,
        add_area_to_group_tool,
        get_area_info,
        get_areas_in_group,
        get_area_list,
        # 5. 索/连接单元
        create_cable,
        delete_cable,
        get_cable_info,
        get_cables_in_group,
        get_cable_list,
        create_link,
        delete_link,
        get_link_info,
        get_link_list,
        get_links_in_group,
        # 6. 荷载操作
        add_point_load,
        delete_point_load,
        add_frame_distributed_load,
        add_frame_point_load,
        delete_frame_load,
        get_frame_loads,
        add_area_load,
        delete_area_load,
        create_load_pattern,
        delete_load_pattern,
        # 7. 分析设计
        run_analysis,
        run_steel_design,
        get_stress_ratios,
        verify_steel_design,
        # 8. 结果查询
        get_point_displacement,
        get_point_reactions,
        get_base_reactions,
        get_frame_forces,
        get_max_frame_forces,
        get_modal_periods,
        get_modal_mass_ratios,
        # 9. 选择操作
        select_all,
        clear_selection,
        select_group,
        select_by_property,
        get_selected_objects,
        # 10. 视图操作
        refresh_view,
        zoom_all,
        # 11. 统计功能
        get_steel_usage,
        get_cable_usage,
        # 12. 组操作
        create_group,
        add_frame_to_group,
        add_selected_to_group,
        # 13. 文件操作
        save_model,
        unlock_model,
        new_model,
        open_model,
        # 14. 约束操作
        get_constraint_list,
        create_diaphragm_constraint,
        assign_point_constraint,
        # 15. 编辑操作
        move_selected_objects,
        replicate_linear,
        replicate_mirror,
        replicate_radial,
        divide_frame,
        merge_points,
        # 16. 表格操作
        get_joint_coordinates_table,
        modify_joint_coordinate,
        batch_modify_joints,
        get_frame_section_assignments_table,
        get_available_tables,
        # 17. 撤回操作
        undo_last_operation,
        get_operation_history,
        clear_operation_history,
        # 18. 批量操作
        batch_set_section,
        batch_add_distributed_load,
        batch_set_restraint,
        # 19. 组合工具
        full_design_check,
        steel_usage_report,
        model_overview,
    ]
    
    # 添加可选工具
    if search_sap_docs:
        tools.append(search_sap_docs)
    if draw_chart:
        tools.append(draw_chart)
    
    return tools
