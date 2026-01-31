# -*- coding: utf-8 -*-
"""
basic_usage.py - PySap2000 基本使用示例
展示新 API 的使用方式
"""

from PySap2000 import Application
from PySap2000.structure_core import Point, Frame, Material, Section
from PySap2000.types_for_points import PointSupport, PointSupportType
from PySap2000.loads import PointLoad, FrameLoad, FrameLoadDirection
from PySap2000.loading import LoadCase, LoadCaseType
from PySap2000.results import PointResults, FrameResults


def example_create_simple_beam():
    """
    示例：创建简支梁
    """
    with Application() as app:
        # 设置单位 (kN, m, C)
        app.set_units(6)
        
        # ========== 创建节点 ==========
        app.create_object(Point(no=1, x=0, y=0, z=0))
        app.create_object(Point(no=2, x=5, y=0, z=0))
        app.create_object(Point(no=3, x=10, y=0, z=0))
        
        # ========== 创建杆件 (Frame) ==========
        app.create_object(Frame(no=1, start_point=1, end_point=2, section="W14X30"))
        app.create_object(Frame(no=2, start_point=2, end_point=3, section="W14X30"))
        
        # ========== 添加支座 ==========
        app.create_object(PointSupport(points=[1], type=PointSupportType.FIXED))
        app.create_object(PointSupport(points=[3], type=PointSupportType.HINGED))
        
        # ========== 创建荷载工况 ==========
        app.create_object(LoadCase(name="DEAD", type=LoadCaseType.DEAD, self_weight_multiplier=1.0))
        app.create_object(LoadCase(name="LIVE", type=LoadCaseType.LIVE))
        
        # ========== 添加荷载 ==========
        # Point 荷载
        app.create_object(PointLoad(load_case="LIVE", points=[2], fz=-10))
        
        # Frame 均布荷载
        app.create_object(FrameLoad(
            load_case="LIVE",
            frames=[1, 2],
            direction=FrameLoadDirection.GRAVITY,
            value1=-5, value2=-5
        ))
        
        # ========== 运行分析 ==========
        app.calculate()
        
        # ========== 获取结果 ==========
        point_results = PointResults(app.model)
        disp = point_results.get_displacement("2", load_case="LIVE")
        print(f"Point 2 位移: Uz = {disp.uz:.6f} m")
        
        frame_results = FrameResults(app.model)
        forces = frame_results.get_internal_forces("1", load_case="LIVE")
        print(f"Frame 1 内力:")
        for f in forces:
            print(f"  位置 {f.station:.2f}: M3 = {f.m3:.2f} kN·m")


def example_get_model_info():
    """
    示例：获取模型信息
    """
    with Application() as app:
        # 获取所有 Point
        points = app.get_object_list(Point)
        print(f"Point 数量: {len(points)}")
        for point in points[:5]:
            print(f"  Point {point.no}: ({point.x}, {point.y}, {point.z})")
        
        # 获取所有 Frame
        frames = app.get_object_list(Frame)
        print(f"\nFrame 数量: {len(frames)}")
        for frame in frames[:5]:
            print(f"  Frame {frame.no}: {frame.start_point} -> {frame.end_point}, Section: {frame.section}")


def example_batch_operations():
    """
    示例：批量操作
    """
    with Application() as app:
        app.begin_modification()
        
        # 批量创建 Point
        for i in range(100):
            app.create_object(Point(no=i+1, x=i*1.0, y=0, z=0))
        
        # 批量创建 Frame
        for i in range(99):
            app.create_object(Frame(no=i+1, start_point=i+1, end_point=i+2, section="W14X30"))
        
        app.finish_modification()
        print("批量创建完成: 100 个 Point, 99 个 Frame")


def example_property_brush():
    """
    示例：属性刷工具
    将源对象的属性（荷载、组、截面等）复制到目标对象
    """
    from PySap2000.utils.property_brush import AreaBrush, FrameBrush, get_selected_objects
    
    with Application() as app:
        model = app.model
        
        # ========== 面单元属性刷 ==========
        # 复制单个面的荷载和组到另一个面
        AreaBrush.copy_all(model, source="1", targets="2")
        
        # 批量复制，指定要复制的属性
        AreaBrush.copy_all(
            model,
            source="1",
            targets=["2", "3", "4"],
            include_loads=True,        # 复制荷载
            include_groups=True,       # 复制组
            include_property=True,     # 复制面属性(截面)
            include_local_axes=True,   # 复制局部轴
            include_modifiers=True     # 复制刚度修正
        )
        
        # ========== 杆件属性刷 ==========
        FrameBrush.copy_all(
            model,
            source="1",
            targets=["2", "3"],
            include_groups=True,       # 复制组
            include_section=True,      # 复制截面
            include_modifiers=True,    # 复制刚度修正
            include_releases=True,     # 复制端部释放
            include_local_axes=True,   # 复制局部轴
            include_material=True      # 复制材料覆盖
        )
        
        # ========== 刷选中的对象 ==========
        selected = get_selected_objects(model)
        
        # 把源面的属性刷到所有选中的面
        if selected["areas"]:
            result = AreaBrush.copy_all(model, source="1", targets=selected["areas"])
            print(f"面单元刷完成: 成功 {result['success']}, 失败 {result['failed']}")
        
        # 把源杆件的属性刷到所有选中的杆件
        if selected["frames"]:
            result = FrameBrush.copy_all(model, source="1", targets=selected["frames"])
            print(f"杆件刷完成: 成功 {result['success']}, 失败 {result['failed']}")


if __name__ == "__main__":
    # 运行示例前请确保 SAP2000 已启动
    example_get_model_info()
