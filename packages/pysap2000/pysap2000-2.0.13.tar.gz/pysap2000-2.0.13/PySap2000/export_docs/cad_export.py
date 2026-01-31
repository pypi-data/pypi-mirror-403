# -*- coding: utf-8 -*-
"""
cad_export.py - CAD 出图模块

功能:
    - 导出杆件表格 (单元号、节点1、节点2、长度、材料、截面)
    - 导出节点表格 (节点号、X、Y、Z)
    - 支持导出选中对象或全部对象
    - 输出 DXF 文件 (可用 CAD 打开)
    - 支持使用模板文件

Usage:
    from application import Application
    from export_docs.cad_export import export_frame_table, export_point_table
    
    app = Application()
    model = app.model
    
    # 导出选中的杆件
    export_frame_table(model, "frames.dxf", selected_only=True)
    
    # 导出所有节点
    export_point_table(model, "points.dxf")
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import math
import os


@dataclass
class FrameData:
    """杆件数据"""
    name: str
    point_i: str
    point_j: str
    length: float
    material: str
    section: str


@dataclass
class PointData:
    """节点数据"""
    name: str
    x: float
    y: float
    z: float


def get_selected_objects(model) -> Tuple[List[str], List[str]]:
    """
    获取选中的对象
    
    Returns:
        (frame_names, point_names)
    """
    ret = model.SelectObj.GetSelected(0, [], [])
    if not isinstance(ret, (list, tuple)) or len(ret) < 3:
        return [], []
    
    obj_types = ret[1] if ret[1] else []
    obj_names = ret[2] if ret[2] else []
    
    frames = []
    points = []
    for i, obj_type in enumerate(obj_types):
        if obj_type == 2:  # Frame
            frames.append(obj_names[i])
        elif obj_type == 1:  # Point
            points.append(obj_names[i])
    
    return frames, points


def get_frame_data(model, frame_names: List[str] = None) -> List[FrameData]:
    """
    获取杆件数据 (使用 DatabaseTables 批量获取，速度更快)
    
    Args:
        model: SapModel 对象
        frame_names: 杆件名称列表，None 表示全部
    """
    from global_parameters.units import Units, UnitSystem
    
    # 切换到 N-mm-C 单位
    original_units = Units.get_present_units(model)
    Units.set_present_units(model, UnitSystem.N_MM_C)
    
    try:
        # 1. 获取杆件连接信息 (Connectivity - Frame)
        conn_dict = {}  # frame -> (point_i, point_j, length)
        ret = model.DatabaseTables.GetTableForDisplayArray(
            "Connectivity - Frame", ["Frame", "JointI", "JointJ", "Length"], "", 0, [], 0, []
        )
        if isinstance(ret, (list, tuple)) and len(ret) >= 5 and ret[5] == 0:
            fields = list(ret[2])
            num_records = ret[3]
            data = ret[4]
            num_fields = len(fields)
            
            frame_idx = fields.index("Frame") if "Frame" in fields else -1
            ji_idx = fields.index("JointI") if "JointI" in fields else -1
            jj_idx = fields.index("JointJ") if "JointJ" in fields else -1
            len_idx = fields.index("Length") if "Length" in fields else -1
            
            for i in range(num_records):
                base = i * num_fields
                fname = data[base + frame_idx] if frame_idx >= 0 else ""
                if fname:
                    conn_dict[fname] = (
                        data[base + ji_idx] if ji_idx >= 0 else "",
                        data[base + jj_idx] if jj_idx >= 0 else "",
                        float(data[base + len_idx]) if len_idx >= 0 and data[base + len_idx] else 0.0
                    )
        
        if not conn_dict:
            return []
        
        # 2. 获取截面分配和材料覆盖 (Frame Section Assignments)
        section_dict = {}  # frame -> section
        mat_overwrite_dict = {}  # frame -> material (非Default时)
        ret = model.DatabaseTables.GetTableForDisplayArray(
            "Frame Section Assignments", ["Frame", "AnalSect", "MatProp"], "", 0, [], 0, []
        )
        if isinstance(ret, (list, tuple)) and len(ret) >= 5 and ret[5] == 0:
            fields = list(ret[2])
            num_records = ret[3]
            data = ret[4]
            num_fields = len(fields)
            
            frame_idx = fields.index("Frame") if "Frame" in fields else -1
            sect_idx = fields.index("AnalSect") if "AnalSect" in fields else -1
            mat_idx = fields.index("MatProp") if "MatProp" in fields else -1
            
            for i in range(num_records):
                base = i * num_fields
                fname = data[base + frame_idx] if frame_idx >= 0 else ""
                if fname:
                    section = data[base + sect_idx] if sect_idx >= 0 else ""
                    if section:
                        section_dict[fname] = section
                    # 获取材料覆盖 (非 Default 时有效)
                    if mat_idx >= 0:
                        mat = data[base + mat_idx]
                        if mat and mat != "Default":
                            mat_overwrite_dict[fname] = mat
        
        # 3. 缓存截面材料和标准名称
        section_material_cache = {}
        section_name_cache = {}  # 截面标准化名称缓存
        
        # 构建结果
        result = []
        frame_set = set(frame_names) if frame_names else None
        
        for fname, (point_i, point_j, length) in conn_dict.items():
            # 如果指定了杆件列表，只处理列表中的杆件
            if frame_set and fname not in frame_set:
                continue
            
            section = section_dict.get(fname, "")
            
            # 获取材料: 优先使用覆盖材料，否则从截面获取
            material = mat_overwrite_dict.get(fname, "")
            if not material and section:
                # 从截面获取材料 (带缓存)
                if section not in section_material_cache:
                    section_material_cache[section] = _get_section_material(model, section)
                material = section_material_cache[section]
            
            # 获取截面标准化名称 (带缓存)
            standard_section = section
            if section:
                if section not in section_name_cache:
                    section_name_cache[section] = get_standard_section_name(model, section)
                standard_section = section_name_cache[section]
            
            result.append(FrameData(
                name=fname,
                point_i=point_i,
                point_j=point_j,
                length=length,
                material=material,
                section=standard_section
            ))
        
        return result
    finally:
        Units.set_present_units(model, original_units)


def get_point_data(model, point_names: List[str] = None) -> List[PointData]:
    """
    获取节点数据
    
    Args:
        model: SapModel 对象
        point_names: 节点名称列表，None 表示全部
    """
    from global_parameters.units import Units, UnitSystem
    
    # 切换到 N-m-C 单位
    original_units = Units.get_present_units(model)
    Units.set_present_units(model, UnitSystem.N_M_C)
    
    try:
        # 获取节点列表
        if point_names is None:
            ret = model.PointObj.GetNameList(0, [])
            if isinstance(ret, (list, tuple)) and len(ret) >= 2:
                point_names = list(ret[1]) if ret[1] else []
            else:
                point_names = []
        
        result = []
        for pname in point_names:
            ret = model.PointObj.GetCoordCartesian(str(pname), 0.0, 0.0, 0.0)
            if isinstance(ret, (list, tuple)) and len(ret) >= 3:
                result.append(PointData(
                    name=pname,
                    x=ret[0],
                    y=ret[1],
                    z=ret[2]
                ))
        
        return result
    finally:
        Units.set_present_units(model, original_units)


def _get_frame_length(model, frame_name: str) -> float:
    """计算杆件长度 (mm)"""
    ret = model.FrameObj.GetPoints(str(frame_name), "", "")
    if not isinstance(ret, (list, tuple)) or len(ret) < 2:
        return 0.0
    
    point_i, point_j = ret[0], ret[1]
    
    ret1 = model.PointObj.GetCoordCartesian(point_i, 0.0, 0.0, 0.0)
    ret2 = model.PointObj.GetCoordCartesian(point_j, 0.0, 0.0, 0.0)
    
    if isinstance(ret1, (list, tuple)) and isinstance(ret2, (list, tuple)):
        dx = ret2[0] - ret1[0]
        dy = ret2[1] - ret1[1]
        dz = ret2[2] - ret1[2]
        return math.sqrt(dx*dx + dy*dy + dz*dz)
    return 0.0


def _get_section_material(model, section_name: str) -> str:
    """获取截面材料"""
    if not section_name:
        return ""
    
    try:
        # 先获取截面类型
        ret = model.PropFrame.GetTypeOAPI(section_name)
        if not isinstance(ret, (list, tuple)) or len(ret) < 1:
            return ""
        sec_type = ret[0]
        
        # 根据类型调用对应的获取方法
        if sec_type == 8:  # RECTANGULAR
            ret = model.PropFrame.GetRectangle(section_name)
        elif sec_type == 9:  # CIRCLE
            ret = model.PropFrame.GetCircle(section_name)
        elif sec_type == 7:  # PIPE
            ret = model.PropFrame.GetPipe(section_name)
        elif sec_type == 6:  # BOX
            ret = model.PropFrame.GetTube_1(section_name)
        elif sec_type == 1:  # I_SECTION
            ret = model.PropFrame.GetISection_1(section_name)
        elif sec_type == 4:  # ANGLE
            ret = model.PropFrame.GetAngle_1(section_name)
        elif sec_type == 2:  # CHANNEL
            ret = model.PropFrame.GetChannel_2(section_name)
        elif sec_type == 3:  # T_SECTION
            ret = model.PropFrame.GetTee_1(section_name)
        elif sec_type == 5:  # DOUBLE_ANGLE
            ret = model.PropFrame.GetDblAngle_2(section_name)
        elif sec_type == 11:  # DOUBLE_CHANNEL
            ret = model.PropFrame.GetDblChannel_1(section_name)
        else:
            return ""
        
        if isinstance(ret, (list, tuple)) and len(ret) >= 2:
            return ret[1] or ""
    except Exception:
        pass
    return ""


def get_standard_section_name(model, section_name: str) -> str:
    """
    获取截面的标准化命名
    
    使用 FrameSection.standard_name 属性获取标准化名称。
    
    Args:
        model: SapModel 对象
        section_name: 截面名称
    
    Returns:
        标准化的截面名称，失败返回原名称
    
    Note:
        调用前需确保单位为 N-mm-C，API 返回的尺寸单位为 mm
    """
    if not section_name:
        return ""
    
    try:
        from section.frame_section import FrameSection
        section = FrameSection.get_by_name(model, section_name)
        return section.standard_name
    except Exception:
        return section_name


# =============================================================================
# DXF 导出
# =============================================================================

# 模板文件路径
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
DXF_TEMPLATE = os.path.join(TEMPLATE_DIR, "template.dxf")

# 模板中的图层名
LAYER_TABLE = "jointtable"   # 表格外框图层
LAYER_TEXT = "jointtext"     # 文字图层

# 模板中的文字样式
TEXT_STYLE = "毫米(大)"


def _read_template(template_path: str) -> Tuple[bytes, bytes]:
    """
    读取 DXF 模板文件，分离 ENTITIES 段前后的内容 (二进制模式)
    
    模板 ENTITIES 段格式:
    SECTION
      2
    ENTITIES
      0        <-- 这里插入实体
    ENDSEC
    
    Returns:
        (before_entities, after_entities) - ENTITIES 段前后的内容 (bytes)
    """
    with open(template_path, "rb") as f:
        content = f.read()
    
    # 查找 "ENTITIES" 位置
    entities_pos = content.find(b"ENTITIES")
    if entities_pos == -1:
        raise ValueError("模板文件中未找到 ENTITIES 段")
    
    # 找 ENTITIES 后第一个换行
    newline_after_entities = content.find(b"\n", entities_pos)
    if newline_after_entities == -1:
        raise ValueError("模板文件格式错误")
    
    # before: 包含到 ENTITIES 后的换行
    before = content[:newline_after_entities + 1]
    
    # after: 从 ENTITIES 后的 "  0\r\nENDSEC" 或 "  0\nENDSEC" 开始
    after = content[newline_after_entities + 1:]
    
    return before, after


# 全局句柄计数器
_handle_counter = 0x2000


def _next_handle() -> str:
    """获取下一个句柄 (十六进制)"""
    global _handle_counter
    _handle_counter += 1
    return format(_handle_counter, 'X')


def _reset_handle():
    """重置句柄计数器"""
    global _handle_counter
    _handle_counter = 0x2000


def _generate_dxf_text(x: float, y: float, text: str, height: float = 350, 
                       layer: str = LAYER_TEXT, style: str = TEXT_STYLE,
                       use_ac1024: bool = True) -> str:
    """生成 DXF TEXT 实体"""
    if use_ac1024:
        # AC1024 格式 (AutoCAD 2010+)
        handle = _next_handle()
        return f"""  0
TEXT
  5
{handle}
330
6F
100
AcDbEntity
  8
{layer}
100
AcDbText
 10
{x:.6f}
 20
{y:.6f}
 30
0.0
 40
{height:.6f}
  1
{text}
  7
{style}
100
AcDbText
"""
    else:
        # R12 格式
        return f"""  0
TEXT
  8
{layer}
 10
{x:.6f}
 20
{y:.6f}
 30
0.0
 40
{height:.6f}
  1
{text}
  7
{style}
"""


def _generate_dxf_line(x1: float, y1: float, x2: float, y2: float, 
                       layer: str = LAYER_TABLE,
                       use_ac1024: bool = True) -> str:
    """生成 DXF LINE 实体"""
    if use_ac1024:
        # AC1024 格式 (AutoCAD 2010+)
        handle = _next_handle()
        return f"""  0
LINE
  5
{handle}
330
6F
100
AcDbEntity
  8
{layer}
100
AcDbLine
 10
{x1:.6f}
 20
{y1:.6f}
 30
0.0
 11
{x2:.6f}
 21
{y2:.6f}
 31
0.0
"""
    else:
        # R12 格式
        return f"""  0
LINE
  8
{layer}
 10
{x1:.6f}
 20
{y1:.6f}
 30
0.0
 11
{x2:.6f}
 21
{y2:.6f}
 31
0.0
"""


def _write_dxf_header(f):
    """写入 DXF 文件头 (无模板时使用)"""
    f.write("0\nSECTION\n2\nENTITIES\n")


def _write_dxf_footer(f):
    """写入 DXF 文件尾 (无模板时使用)"""
    f.write("0\nENDSEC\n0\nEOF\n")


def _write_dxf_text(f, x: float, y: float, text: str, height: float = 350, 
                    color: int = 3, layer: str = "text"):
    """写入 DXF 文本 (无模板时使用)"""
    f.write(f"0\nTEXT\n8\n{layer}\n62\n{color}\n10\n{x}\n20\n{y}\n30\n0\n40\n{height}\n1\n{text}\n")


def _write_dxf_line(f, x1: float, y1: float, x2: float, y2: float, 
                    color: int = 5, layer: str = "line"):
    """写入 DXF 线段 (无模板时使用)"""
    f.write(f"0\nLINE\n8\n{layer}\n62\n{color}\n10\n{x1}\n20\n{y1}\n30\n0\n11\n{x2}\n21\n{y2}\n31\n0\n")


def export_frame_table(
    model,
    output_file: str,
    selected_only: bool = False,
    rows_per_column: int = 90,
    row_height: float = 800,
    text_height: float = 350,
    column_gap: float = 2500,
    group_gap: float = 40000,
    tables_per_group: int = 5,
    use_template: bool = True
) -> int:
    """
    导出杆件表格到 DXF
    
    Args:
        model: SapModel 对象
        output_file: 输出文件路径 (.dxf)
        selected_only: 是否只导出选中的杆件
        rows_per_column: 每列行数 (默认90)
        row_height: 行高
        text_height: 文字高度
        column_gap: 组内列间距 (默认2500)
        group_gap: 组间间距 (默认40000)
        tables_per_group: 每组表格数 (默认5)
        use_template: 是否使用模板 (默认True)
        
    Returns:
        导出的杆件数量
    """
    # 获取杆件数据
    if selected_only:
        frame_names, _ = get_selected_objects(model)
        print(f"选中的杆件: {frame_names}")
    else:
        frame_names = None
    
    frames = get_frame_data(model, frame_names)
    if not frames:
        print("没有杆件数据")
        return 0
    
    # 按单元号排序 (尝试数字排序，失败则字符串排序)
    def sort_key(f):
        try:
            return (0, int(f.name))
        except ValueError:
            return (1, f.name)
    frames.sort(key=sort_key)
    
    # 重置句柄计数器
    _reset_handle()
    
    # 列宽定义 (单元号、节点1、节点2、长度、材料、截面)
    col_widths = [2400, 2400, 2400, 2400, 2400, 4800]
    headers = ["单元号", "节点1", "节点2", "长度(mm)", "材料", "截面"]
    table_width = sum(col_widths)
    
    # 计算需要多少个表格列
    num_tables = (len(frames) + rows_per_column - 1) // rows_per_column
    
    # 生成实体内容
    entities_content = []
    
    for table_idx in range(num_tables):
        # 计算当前表格的起始位置
        # 每 tables_per_group 列为一组，组内间距 column_gap，组间间距 group_gap
        group_idx = table_idx // tables_per_group  # 第几组
        idx_in_group = table_idx % tables_per_group  # 组内第几个
        
        # x_offset = 组偏移 + 组内偏移
        group_offset = group_idx * (tables_per_group * (table_width + column_gap) - column_gap + group_gap)
        in_group_offset = idx_in_group * (table_width + column_gap)
        x_offset = group_offset + in_group_offset
        
        # 当前表格的数据范围
        start_idx = table_idx * rows_per_column
        end_idx = min(start_idx + rows_per_column, len(frames))
        table_frames = frames[start_idx:end_idx]
        
        # 表格高度
        table_height = (len(table_frames) + 1) * row_height
        
        # 绘制水平线
        y = 0
        for i in range(len(table_frames) + 2):
            entities_content.append(_generate_dxf_line(x_offset, y, x_offset + table_width, y, use_ac1024=use_template))
            y -= row_height
        
        # 绘制垂直线
        x = x_offset
        for w in col_widths:
            entities_content.append(_generate_dxf_line(x, 0, x, -table_height, use_ac1024=use_template))
            x += w
        entities_content.append(_generate_dxf_line(x_offset + table_width, 0, x_offset + table_width, -table_height, use_ac1024=use_template))
        
        # 写入表头
        x = x_offset + 50
        for i, header in enumerate(headers):
            entities_content.append(_generate_dxf_text(x, -row_height + 200, header, text_height, use_ac1024=use_template))
            x += col_widths[i]
        
        # 写入数据
        y = -row_height
        for frame in table_frames:
            y -= row_height
            row_data = [
                frame.name,
                frame.point_i,
                frame.point_j,
                f"{frame.length:.0f}",
                frame.material,
                frame.section
            ]
            x = x_offset + 50
            for i, data in enumerate(row_data):
                entities_content.append(_generate_dxf_text(x, y + 200, str(data), text_height, use_ac1024=use_template))
                x += col_widths[i]
    
    # 添加截面说明 (在第一个表格下方，分2列)
    legend_y = -(rows_per_column + 3) * row_height
    legend_col1 = [
        "截面说明:",
        "H - I形截面 (高x宽x腹板厚x翼缘厚)",
        "B - 箱形截面 (高x宽x腹板厚x翼缘厚)",
        "P - 圆管 (直径x壁厚)",
        "R - 矩形截面 (高x宽)",
        "D - 圆形截面 (直径)",
        
       
    ]
    legend_col2 = [
        "",
        "T - T形截面 (高x宽x腹板厚x翼缘厚)",
        "C - 槽钢 (高x宽x腹板厚x翼缘厚)",
        "L - 角钢 (高x宽x厚)",
        "2C - 双槽钢 (高x宽x厚x间距)",
        "2L - 双角钢 (高x宽x厚x间距)",
    ]
    col2_x = 9000  # 第二列x偏移
    for i, line in enumerate(legend_col1):
        entities_content.append(_generate_dxf_text(0, legend_y - i * row_height, line, text_height, use_ac1024=use_template))
    for i, line in enumerate(legend_col2):
        if line:
            entities_content.append(_generate_dxf_text(col2_x, legend_y - i * row_height, line, text_height, use_ac1024=use_template))
    
    # 写入文件
    if use_template and os.path.exists(DXF_TEMPLATE):
        # 使用模板 (二进制模式，UTF-8 编码)
        before, after = _read_template(DXF_TEMPLATE)
        entities_bytes = "".join(entities_content).encode("utf-8")
        with open(output_file, "wb") as f:
            f.write(before)
            f.write(entities_bytes)
            f.write(after)
    else:
        # 不使用模板
        with open(output_file, "w", encoding="gbk") as f:
            _write_dxf_header(f)
            for entity in entities_content:
                f.write(entity)
            _write_dxf_footer(f)
    
    print(f"导出完成: {len(frames)} 根杆件 -> {output_file}")
    return len(frames)


def export_point_table(
    model,
    output_file: str,
    selected_only: bool = False,
    rows_per_column: int = 90,
    row_height: float = 800,
    text_height: float = 350,
    column_gap: float = 2500,
    group_gap: float = 40000,
    tables_per_group: int = 4,
    use_template: bool = True
) -> int:
    """
    导出节点表格到 DXF
    
    Args:
        model: SapModel 对象
        output_file: 输出文件路径 (.dxf)
        selected_only: 是否只导出选中的节点
        rows_per_column: 每列行数 (默认90)
        row_height: 行高
        text_height: 文字高度
        column_gap: 组内列间距 (默认2500)
        group_gap: 组间间距 (默认40000)
        tables_per_group: 每组表格数 (默认4)
        use_template: 是否使用模板 (默认True)
        
    Returns:
        导出的节点数量
    """
    # 获取节点数据
    if selected_only:
        _, point_names = get_selected_objects(model)
    else:
        point_names = None
    
    points = get_point_data(model, point_names)
    if not points:
        print("没有节点数据")
        return 0
    
    # 按节点号排序 (尝试数字排序，失败则字符串排序)
    def sort_key(p):
        try:
            return (0, int(p.name))
        except ValueError:
            return (1, p.name)
    points.sort(key=sort_key)
    
    # 重置句柄计数器
    _reset_handle()
    
    # 列宽定义 (节点号、X、Y、Z)
    col_widths = [1500, 2500, 2500, 2500]
    headers = ["节点号", "X(m)", "Y(m)", "Z(m)"]
    table_width = sum(col_widths)
    
    # 计算需要多少个表格列
    num_tables = (len(points) + rows_per_column - 1) // rows_per_column
    
    # 生成实体内容
    entities_content = []
    
    for table_idx in range(num_tables):
        # 计算当前表格的起始位置
        # 每 tables_per_group 列为一组，组内间距 column_gap，组间间距 group_gap
        group_idx = table_idx // tables_per_group
        idx_in_group = table_idx % tables_per_group
        
        group_offset = group_idx * (tables_per_group * (table_width + column_gap) - column_gap + group_gap)
        in_group_offset = idx_in_group * (table_width + column_gap)
        x_offset = group_offset + in_group_offset
        
        # 当前表格的数据范围
        start_idx = table_idx * rows_per_column
        end_idx = min(start_idx + rows_per_column, len(points))
        table_points = points[start_idx:end_idx]
        
        # 表格高度
        table_height = (len(table_points) + 1) * row_height
        
        # 绘制水平线
        y = 0
        for i in range(len(table_points) + 2):
            entities_content.append(_generate_dxf_line(x_offset, y, x_offset + table_width, y, use_ac1024=use_template))
            y -= row_height
        
        # 绘制垂直线
        x = x_offset
        for w in col_widths:
            entities_content.append(_generate_dxf_line(x, 0, x, -table_height, use_ac1024=use_template))
            x += w
        entities_content.append(_generate_dxf_line(x_offset + table_width, 0, x_offset + table_width, -table_height, use_ac1024=use_template))
        
        # 写入表头
        x = x_offset + 50
        for i, header in enumerate(headers):
            entities_content.append(_generate_dxf_text(x, -row_height + 200, header, text_height, use_ac1024=use_template))
            x += col_widths[i]
        
        # 写入数据
        y = -row_height
        for point in table_points:
            y -= row_height
            row_data = [
                point.name,
                f"{point.x:.3f}",
                f"{point.y:.3f}",
                f"{point.z:.3f}"
            ]
            x = x_offset + 50
            for i, data in enumerate(row_data):
                entities_content.append(_generate_dxf_text(x, y + 200, str(data), text_height, use_ac1024=use_template))
                x += col_widths[i]
    
    # 写入文件
    if use_template and os.path.exists(DXF_TEMPLATE):
        # 使用模板 (二进制模式，UTF-8 编码)
        before, after = _read_template(DXF_TEMPLATE)
        entities_bytes = "".join(entities_content).encode("utf-8")
        with open(output_file, "wb") as f:
            f.write(before)
            f.write(entities_bytes)
            f.write(after)
    else:
        # 不使用模板
        with open(output_file, "w", encoding="gbk") as f:
            _write_dxf_header(f)
            for entity in entities_content:
                f.write(entity)
            _write_dxf_footer(f)
    
    print(f"导出完成: {len(points)} 个节点 -> {output_file}")
    return len(points)


def export_to_csv(
    model,
    output_file: str,
    export_type: str = "frame",
    selected_only: bool = False
) -> int:
    """
    导出到 CSV 文件
    
    Args:
        model: SapModel 对象
        output_file: 输出文件路径 (.csv)
        export_type: "frame" 或 "point"
        selected_only: 是否只导出选中的对象
        
    Returns:
        导出的数量
    """
    if export_type == "frame":
        if selected_only:
            frame_names, _ = get_selected_objects(model)
        else:
            frame_names = None
        
        frames = get_frame_data(model, frame_names)
        if not frames:
            print("没有杆件数据")
            return 0
        
        with open(output_file, "w", encoding="utf-8-sig") as f:
            f.write("单元号,节点1,节点2,长度(mm),材料,截面\n")
            for frame in frames:
                f.write(f"{frame.name},{frame.point_i},{frame.point_j},"
                       f"{frame.length:.0f},{frame.material},{frame.section}\n")
        
        print(f"导出完成: {len(frames)} 根杆件 -> {output_file}")
        return len(frames)
    
    elif export_type == "point":
        if selected_only:
            _, point_names = get_selected_objects(model)
        else:
            point_names = None
        
        points = get_point_data(model, point_names)
        if not points:
            print("没有节点数据")
            return 0
        
        with open(output_file, "w", encoding="utf-8-sig") as f:
            f.write("节点号,X(m),Y(m),Z(m)\n")
            for point in points:
                f.write(f"{point.name},{point.x:.3f},{point.y:.3f},{point.z:.3f}\n")
        
        print(f"导出完成: {len(points)} 个节点 -> {output_file}")
        return len(points)
    
    return 0


def _generate_dxf_line_3d(x1: float, y1: float, z1: float, 
                          x2: float, y2: float, z2: float,
                          layer: str = "frame",
                          use_ac1024: bool = True) -> str:
    """生成 3D DXF LINE 实体"""
    if use_ac1024:
        handle = _next_handle()
        return f"""  0
LINE
  5
{handle}
330
6F
100
AcDbEntity
  8
{layer}
100
AcDbLine
 10
{x1:.6f}
 20
{y1:.6f}
 30
{z1:.6f}
 11
{x2:.6f}
 21
{y2:.6f}
 31
{z2:.6f}
"""
    else:
        return f"""  0
LINE
  8
{layer}
 10
{x1:.6f}
 20
{y1:.6f}
 30
{z1:.6f}
 11
{x2:.6f}
 21
{y2:.6f}
 31
{z2:.6f}
"""


def _generate_dxf_text_3d(x: float, y: float, z: float, text: str, 
                          height: float = 350, layer: str = "text",
                          color: int = None, style: str = TEXT_STYLE,
                          use_ac1024: bool = True) -> str:
    """生成 3D DXF TEXT 实体
    
    Args:
        color: ACI颜色索引 (1=红, 2=黄, 3=绿, 4=青, 5=蓝, 6=洋红, 7=白, 30=橙)
        style: 文字样式名称
    """
    color_line = f" 62\n{color}\n" if color else ""
    if use_ac1024:
        handle = _next_handle()
        return f"""  0
TEXT
  5
{handle}
330
6F
100
AcDbEntity
  8
{layer}
{color_line}100
AcDbText
 10
{x:.6f}
 20
{y:.6f}
 30
{z:.6f}
 40
{height:.6f}
  1
{text}
  7
{style}
100
AcDbText
"""
    else:
        return f"""  0
TEXT
  8
{layer}
{color_line} 10
{x:.6f}
 20
{y:.6f}
 30
{z:.6f}
 40
{height:.6f}
  1
{text}
  7
{style}
"""


def _project_point(x: float, y: float, z: float, projection) -> Tuple[float, float, float]:
    """
    将3D坐标投影到2D平面，与 ModelViewer 中的视角一致
    
    坐标系说明:
    - SAP2000: X右, Y前(屏幕内), Z上
    - Three.js/ModelViewer: X右, Y上, Z前(屏幕外)
    - ModelViewer 转换: three_x=sap_x, three_y=sap_z, three_z=-sap_y
    
    Args:
        x, y, z: 3D坐标 (SAP2000坐标系)
        projection: 投影类型
    
    Returns:
        (x2d, y2d, z2d) - 投影后的坐标
    """
    # 处理自定义角度（带视图矩阵）
    if isinstance(projection, dict):
        # 先将 SAP 坐标转换到 Three.js 坐标系
        # ModelViewer: three_x=sap_x, three_y=sap_z, three_z=-sap_y
        tx = x
        ty = z
        tz = -y
        
        # 优先使用视图矩阵
        vm = projection.get("viewMatrix")
        if vm and len(vm) >= 6:
            # vm = [right.x, right.y, right.z, orthoUp.x, orthoUp.y, orthoUp.z]
            # right 和 orthoUp 是 Three.js 坐标系中的向量
            # 投影: screen_x = right · point, screen_y = orthoUp · point
            px = vm[0] * tx + vm[1] * ty + vm[2] * tz
            py = vm[3] * tx + vm[4] * ty + vm[5] * tz
            return px, py, 0.0
        
        # 如果没有视图矩阵，使用角度计算
        angles = projection.get("angles")
        if angles:
            rx_deg = angles.get("x", 0)
            ry_deg = angles.get("y", 0)
            rx = math.radians(rx_deg)
            ry = math.radians(ry_deg)
            
            # 绕Y轴旋转 -ry
            c, s = math.cos(-ry), math.sin(-ry)
            tx1 = tx * c + tz * s
            ty1 = ty
            tz1 = -tx * s + tz * c
            
            # 绕X轴旋转 -rx
            c, s = math.cos(-rx), math.sin(-rx)
            tx2 = tx1
            ty2 = ty1 * c - tz1 * s
            
            return tx2, ty2, 0.0
    
    if projection == "3d":
        return x, y, z
    elif projection == "iso":
        # 等轴测投影: 先转到Three.js坐标，再应用等轴测
        tx, ty, tz = x, z, -y
        ry = math.radians(45)
        rx = math.radians(35.264)
        
        c, s = math.cos(-ry), math.sin(-ry)
        tx1 = tx * c + tz * s
        ty1 = ty
        tz1 = -tx * s + tz * c
        
        c, s = math.cos(-rx), math.sin(-rx)
        tx2 = tx1
        ty2 = ty1 * c - tz1 * s
        
        return tx2, ty2, 0.0
    elif projection == "top":
        # 俯视图: 从上往下看 (rx=90, ry=0)
        return x, -y, 0.0
    elif projection == "front":
        # 正视图: 从Y正方向看 (rx=0, ry=0)
        return x, z, 0.0
    elif projection == "right":
        # 右视图: 从X正方向看 (rx=0, ry=90)
        return -y, z, 0.0
    else:
        return x, y, z


def export_3d_model(
    model,
    output_file: str,
    selected_only: bool = False,
    group_names: List[str] = None,
    group_gap: float = 400000,
    show_point_labels: bool = False,
    show_frame_labels: bool = False,
    label_height: float = 350,
    projection = "3d",
    use_template: bool = True
) -> int:
    """
    导出结构三维线框模型到 DXF
    
    Args:
        model: SapModel 对象
        output_file: 输出文件路径 (.dxf)
        selected_only: 是否只导出选中的杆件
        group_names: 组名列表，按顺序在X方向排列，None表示导出全部
        group_gap: 组间间距 (默认400000mm)
        show_point_labels: 是否显示节点编号
        show_frame_labels: 是否显示单元编号
        label_height: 标签文字高度 (默认350mm)
        projection: 投影类型，可以是:
            - 字符串: 所有组使用相同投影 ("3d", "iso", "top", "front", "right")
            - 列表: 每个组使用不同投影，如 ["iso", "top", "front"]
        use_template: 是否使用模板 (默认True)
        
    Returns:
        导出的杆件数量
    """
    from global_parameters.units import Units, UnitSystem
    
    # 切换到 N-mm-C 单位
    original_units = Units.get_present_units(model)
    Units.set_present_units(model, UnitSystem.N_MM_C)
    
    try:
        # 获取所有节点坐标
        point_coords = {}  # point_name -> (x, y, z)
        ret = model.PointObj.GetNameList(0, [])
        if isinstance(ret, (list, tuple)) and len(ret) >= 2:
            point_names = list(ret[1]) if ret[1] else []
            for pname in point_names:
                ret = model.PointObj.GetCoordCartesian(str(pname), 0.0, 0.0, 0.0)
                if isinstance(ret, (list, tuple)) and len(ret) >= 3:
                    point_coords[pname] = (ret[0], ret[1], ret[2])
        
        # 重置句柄计数器
        _reset_handle()
        
        # 生成实体内容
        entities_content = []
        total_count = 0
        labeled_points = set()  # 已标注的节点
        
        if group_names:
            # 按组导出
            x_offset = 0.0
            for group_idx, group_name in enumerate(group_names):
                # 获取该组的投影类型
                if isinstance(projection, list):
                    group_projection = projection[group_idx] if group_idx < len(projection) else "3d"
                else:
                    group_projection = projection
                
                # 获取组内杆件
                ret = model.GroupDef.GetAssignments(group_name, 0, [], [])
                if not isinstance(ret, (list, tuple)) or len(ret) < 3:
                    print(f"警告: 无法获取组 '{group_name}' 的成员")
                    continue
                
                obj_types = ret[1] if ret[1] else []
                obj_names = ret[2] if ret[2] else []
                
                # 筛选杆件 (type=2)
                frame_names = [obj_names[i] for i, t in enumerate(obj_types) if t == 2]
                
                if not frame_names:
                    print(f"警告: 组 '{group_name}' 中没有杆件")
                    continue
                
                # 计算该组投影后的边界框
                min_px, max_px = float('inf'), float('-inf')
                min_py, max_py = float('inf'), float('-inf')
                for fname in frame_names:
                    ret = model.FrameObj.GetPoints(str(fname), "", "")
                    if isinstance(ret, (list, tuple)) and len(ret) >= 2:
                        for pname in [ret[0], ret[1]]:
                            if pname in point_coords:
                                x, y, z = point_coords[pname]
                                px, py, _ = _project_point(x, y, z, group_projection)
                            else:
                                continue
                            min_px = min(min_px, px)
                            max_px = max(max_px, px)
                            min_py = min(min_py, py)
                            max_py = max(max_py, py)
                
                group_width = max_px - min_px if max_px > min_px else 0
                
                # 绘制该组的杆件
                count = 0
                group_labeled_points = set()  # 该组已标注的节点
                for fname in frame_names:
                    ret = model.FrameObj.GetPoints(str(fname), "", "")
                    if not isinstance(ret, (list, tuple)) or len(ret) < 2:
                        continue
                    
                    point_i, point_j = ret[0], ret[1]
                    
                    # 获取投影坐标
                    if point_i not in point_coords or point_j not in point_coords:
                        continue
                    x1, y1, z1 = point_coords[point_i]
                    x2, y2, z2 = point_coords[point_j]
                    px1, py1, pz1 = _project_point(x1, y1, z1, group_projection)
                    px2, py2, pz2 = _project_point(x2, y2, z2, group_projection)
                    
                    # 应用偏移 (相对于投影后的边界框)
                    px1 = px1 - min_px + x_offset
                    px2 = px2 - min_px + x_offset
                    py1 = py1 - min_py
                    py2 = py2 - min_py
                    
                    entities_content.append(_generate_dxf_line_3d(
                        px1, py1, pz1, px2, py2, pz2,
                        layer="frame", use_ac1024=use_template
                    ))
                    
                    # 添加单元编号 (在线段中点)
                    if show_frame_labels:
                        mid_x = (px1 + px2) / 2
                        mid_y = (py1 + py2) / 2
                        mid_z = (pz1 + pz2) / 2
                        entities_content.append(_generate_dxf_text_3d(
                            mid_x, mid_y, mid_z, str(fname), label_height,
                            layer="jointtext", use_ac1024=use_template
                        ))
                    
                    # 添加节点编号 (在节点位置，避免重复)
                    if show_point_labels:
                        if point_i not in group_labeled_points:
                            entities_content.append(_generate_dxf_text_3d(
                                px1, py1, pz1, str(point_i), label_height,
                                layer="jointtable", use_ac1024=use_template
                            ))
                            group_labeled_points.add(point_i)
                        if point_j not in group_labeled_points:
                            entities_content.append(_generate_dxf_text_3d(
                                px2, py2, pz2, str(point_j), label_height,
                                layer="jointtable", use_ac1024=use_template
                            ))
                            group_labeled_points.add(point_j)
                    
                    count += 1
                
                print(f"组 '{group_name}': {count} 根杆件")
                total_count += count
                
                # 更新下一组的X偏移
                x_offset += group_width + group_gap
        else:
            # 导出全部或选中
            if selected_only:
                frame_names, _ = get_selected_objects(model)
            else:
                ret = model.FrameObj.GetNameList(0, [])
                if isinstance(ret, (list, tuple)) and len(ret) >= 2:
                    frame_names = list(ret[1]) if ret[1] else []
                else:
                    frame_names = []
            
            if not frame_names:
                print("没有杆件数据")
                return 0
            
            for fname in frame_names:
                ret = model.FrameObj.GetPoints(str(fname), "", "")
                if not isinstance(ret, (list, tuple)) or len(ret) < 2:
                    continue
                
                point_i, point_j = ret[0], ret[1]
                if point_i not in point_coords or point_j not in point_coords:
                    continue
                
                x1, y1, z1 = point_coords[point_i]
                x2, y2, z2 = point_coords[point_j]
                
                # 应用投影
                px1, py1, pz1 = _project_point(x1, y1, z1, projection)
                px2, py2, pz2 = _project_point(x2, y2, z2, projection)
                
                entities_content.append(_generate_dxf_line_3d(
                    px1, py1, pz1, px2, py2, pz2,
                    layer="frame", use_ac1024=use_template
                ))
                
                # 添加单元编号 (在线段中点)
                if show_frame_labels:
                    mid_x = (px1 + px2) / 2
                    mid_y = (py1 + py2) / 2
                    mid_z = (pz1 + pz2) / 2
                    entities_content.append(_generate_dxf_text_3d(
                        mid_x, mid_y, mid_z, str(fname), label_height,
                        layer="jointtext", use_ac1024=use_template
                    ))
                
                # 添加节点编号 (在节点位置，避免重复)
                if show_point_labels:
                    if point_i not in labeled_points:
                        entities_content.append(_generate_dxf_text_3d(
                            px1, py1, pz1, str(point_i), label_height,
                            layer="jointtable", use_ac1024=use_template
                        ))
                        labeled_points.add(point_i)
                    if point_j not in labeled_points:
                        entities_content.append(_generate_dxf_text_3d(
                            px2, py2, pz2, str(point_j), label_height,
                            layer="jointtable", use_ac1024=use_template
                        ))
                        labeled_points.add(point_j)
                
                total_count += 1
        
        if total_count == 0:
            print("没有有效的杆件数据")
            return 0
        
        # 写入文件
        if use_template and os.path.exists(DXF_TEMPLATE):
            before, after = _read_template(DXF_TEMPLATE)
            entities_bytes = "".join(entities_content).encode("utf-8")
            with open(output_file, "wb") as f:
                f.write(before)
                f.write(entities_bytes)
                f.write(after)
        else:
            with open(output_file, "w", encoding="gbk") as f:
                _write_dxf_header(f)
                for entity in entities_content:
                    f.write(entity)
                _write_dxf_footer(f)
        
        print(f"导出完成: {total_count} 根杆件 -> {output_file}")
        return total_count
    finally:
        Units.set_present_units(model, original_units)


# =============================================================================
# 使用示例
# =============================================================================

if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    try:
        from application import Application
        
        app = Application()
        model = app.model
        
        # 导出三维线框模型 (按组，每组不同视角)
        export_3d_model(
            model, "model_3d.dxf", 
            group_names=["01-外环桁架", "02-内圈桁架", "03-外立面构件"],
            projection=["iso", "iso", "iso"],
            show_point_labels=True,
            show_frame_labels=False
        )
        
        # 导出三维线框模型 (全部)
        # export_3d_model(model, "model_3d.dxf", selected_only=False)
        
        # 导出杆件表格到 DXF
        # export_frame_table(model, "frames_out.dxf", selected_only=False, use_template=True)
        
        # 导出节点表格到 DXF
        export_point_table(model, "points_out.dxf", selected_only=True, use_template=True)
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
