# -*- coding: utf-8 -*-
"""
rhino_utils.py - Rhino 工具函数集合

提供 SAP2000 到 Rhino 的数据转换和导出功能
"""

import os
import json
from typing import Optional, List


def export_to_json(model, output_file: str = None, unit_scale: float = 0.001, 
                   use_batch: bool = True) -> str:
    """
    从 SAP2000 提取数据并导出为 JSON
    
    Args:
        model: SAP2000 model 对象
        output_file: 输出文件路径（可选，默认保存到模型文件夹）
        unit_scale: 单位缩放（默认 0.001，mm → m）
        use_batch: 是否使用批量提取模式（默认 True，大模型提速 10-50 倍）
        
    Returns:
        JSON 文件路径
        
    Example:
        from PySap2000.application import Application
        from PySap2000.visualization.rhino import rhino_utils
        
        app = Application()
        json_file = rhino_utils.export_to_json(app.model)
        print(f"已导出: {json_file}")
    """
    from PySap2000.geometry.model_extractor import ModelExtractor
    
    print("Extracting SAP2000 model data...")
    
    # 提取数据
    extractor = ModelExtractor(model, unit_scale=unit_scale)
    
    if use_batch:
        print("Using batch extraction mode")
        model_3d = extractor.extract_all_elements_batch()
    else:
        print("Using sequential extraction mode")
        model_3d = extractor.extract_all_elements()
    
    # 确定输出路径
    if output_file is None:
        model_path = model.GetModelFilepath()
        if model_path:
            model_dir = os.path.dirname(model_path)
            model_name = os.path.splitext(os.path.basename(model_path))[0]
            output_file = os.path.join(model_dir, f"{model_name}_model_data.json")
        else:
            output_file = "sap_model_data.json"
    
    # 导出 JSON
    model_3d.to_json(output_file)
    print(f"Total elements: {len(model_3d.elements)}")
    
    return output_file


def check_json_update(model, json_file: str) -> bool:
    """
    检查 JSON 文件是否需要更新
    
    Args:
        model: SAP2000 model 对象
        json_file: JSON 文件路径
        
    Returns:
        True 表示需要更新，False 表示不需要
    """
    if not os.path.exists(json_file):
        return True
    
    model_path = model.GetModelFilepath()
    if not model_path or not os.path.exists(model_path):
        return True
    
    # 比较修改时间
    model_time = os.path.getmtime(model_path)
    json_time = os.path.getmtime(json_file)
    
    if model_time > json_time:
        print(f"⚠ SAP2000 模型已更新，需要重新提取")
        return True
    else:
        print(f"✓ JSON 文件是最新的")
        return False


def load_json(json_file: str) -> dict:
    """
    加载 JSON 数据
    
    Args:
        json_file: JSON 文件路径
        
    Returns:
        模型数据字典
        
    Example:
        # 在 Rhino Python 中使用
        from PySap2000.visualization.rhino import rhino_utils
        
        data = rhino_utils.load_json("model_data.json")
        print(f"单元数量: {len(data['elements'])}")
    """
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def import_from_json(json_file: str, layer_name: str = "SAP2000_Model", 
                     num_segments: int = 8, create_solid: bool = True,
                     organize_by_group: bool = False, organize_by_type: bool = False,
                     num_threads: int = 4):
    """
    从 JSON 文件导入模型到 Rhino
    
    Args:
        json_file: JSON 文件路径
        layer_name: 图层名称
        num_segments: 圆形截面分段数
        create_solid: 是否创建实体
        organize_by_group: 是否按组创建子图层
        organize_by_type: 是否按类型创建子图层
        num_threads: 线程数（默认4，仅实体模式有效）
        
    Returns:
        创建的对象 GUID 列表
        
    Example:
        # 在 Rhino Python 中使用（需要先 pip install PySap2000）
        from PySap2000.visualization.rhino import rhino_utils
        
        guids = rhino_utils.import_from_json("model_data.json", num_threads=4)
        print(f"创建了 {len(guids)} 个对象")
        
    Note:
        此函数需要在 Rhino Python 环境中运行
        需要先在 Rhino Python 中安装: pip install PySap2000
    """
    from .rhino_builder import RhinoBuilder
    from PySap2000.geometry.element_geometry import Model3D
    
    # 加载 JSON（不打印消息，由 RhinoBuilder 统一输出）
    with open(json_file, 'r', encoding='utf-8') as f:
        json_str = f.read()
    
    # 转换为 Model3D 对象
    model_3d = Model3D.from_json(json_str)
    
    # 使用 RhinoBuilder 生成
    builder = RhinoBuilder()
    result = builder.build_model(
        model_3d,
        layer_name=layer_name,
        num_segments=num_segments,
        create_solid=create_solid,
        organize_by_group=organize_by_group,
        organize_by_type=organize_by_type,
        num_threads=num_threads
    )
    
    return result['guids']

