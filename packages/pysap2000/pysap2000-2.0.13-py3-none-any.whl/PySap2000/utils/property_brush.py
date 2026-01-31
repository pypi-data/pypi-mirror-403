# -*- coding: utf-8 -*-
"""
property_brush.py - 属性刷工具

将源对象的属性（荷载、组、截面等）复制到目标对象
支持 Area 和 Frame 对象

Usage:
    from PySap2000.application import Application
    from PySap2000.selection import get_selected_objects
    from PySap2000.utils.property_brush import AreaBrush, FrameBrush
    
    app = Application()
    model = app.model
    
    # 面单元属性刷
    AreaBrush.copy_all(model, "1", ["2", "3", "4"])
    
    # 杆件属性刷
    FrameBrush.copy_all(model, "1", ["2", "3", "4"])
    
    # 获取选中对象
    selected = get_selected_objects(model)
"""

from typing import List, Union


class AreaBrush:
    """面单元属性刷"""
    
    @staticmethod
    def copy_load_uniform_to_frame(
        model,
        source: str,
        target: str,
        replace: bool = True
    ) -> int:
        """复制均布荷载到框架"""
        result = model.AreaObj.GetLoadUniformToFrame(source, 0, [], [], [], [], [], [])
        if not isinstance(result, (list, tuple)) or len(result) < 8:
            return -1
        
        num_items = result[0]
        if num_items == 0:
            return 0
            
        load_pats = result[2]
        csys_list = result[3]
        dirs = result[4]
        values = result[5]
        dist_types = result[6]
        
        count = 0
        for i in range(num_items):
            ret = model.AreaObj.SetLoadUniformToFrame(
                target,
                load_pats[i],
                values[i],
                dirs[i],
                dist_types[i],
                replace,
                csys_list[i],
                0  # ItemType.OBJECT
            )
            if ret == 0:
                count += 1
        
        return count
    
    @staticmethod
    def copy_load_uniform(
        model,
        source: str,
        target: str,
        replace: bool = True
    ) -> int:
        """复制面均布荷载"""
        result = model.AreaObj.GetLoadUniform(source, 0, [], [], [], [], [])
        if not isinstance(result, (list, tuple)) or len(result) < 7:
            return -1
        
        num_items = result[0]
        if num_items == 0:
            return 0
            
        load_pats = result[2]
        csys_list = result[3]
        dirs = result[4]
        values = result[5]
        
        count = 0
        for i in range(num_items):
            ret = model.AreaObj.SetLoadUniform(
                target,
                load_pats[i],
                dirs[i],
                values[i],
                csys_list[i],
                replace,
                0  # ItemType.OBJECT
            )
            if ret == 0:
                count += 1
        
        return count


    @staticmethod
    def copy_groups(
        model,
        source: str,
        target: str,
        skip_all: bool = True
    ) -> int:
        """复制组分配"""
        result = model.AreaObj.GetGroupAssign(source, 0, [])
        if not isinstance(result, (list, tuple)) or len(result) < 3:
            return -1
        
        groups = result[1]
        if not groups:
            return 0
        
        count = 0
        for group in groups:
            if skip_all and group == "ALL":
                continue
            ret = model.AreaObj.SetGroupAssign(target, group, False, 0)
            if ret == 0:
                count += 1
        
        return count
    
    @staticmethod
    def copy_property(model, source: str, target: str) -> bool:
        """复制面属性（截面）"""
        result = model.AreaObj.GetProperty(source, "")
        if isinstance(result, (list, tuple)) and len(result) >= 2:
            prop_name = result[0]
            ret = model.AreaObj.SetProperty(target, prop_name, 0)
            return ret == 0
        return False
    
    @staticmethod
    def copy_local_axes(model, source: str, target: str) -> bool:
        """复制局部轴"""
        result = model.AreaObj.GetLocalAxes(source, 0.0, False)
        if isinstance(result, (list, tuple)) and len(result) >= 3:
            angle = result[0]
            ret = model.AreaObj.SetLocalAxes(target, angle, 0)
            return ret == 0
        return False
    
    @staticmethod
    def copy_modifiers(model, source: str, target: str) -> bool:
        """复制刚度修正系数"""
        result = model.AreaObj.GetModifiers(source, [])
        if isinstance(result, (list, tuple)) and len(result) >= 2:
            modifiers = list(result[0]) if result[0] else None
            if modifiers:
                ret = model.AreaObj.SetModifiers(target, modifiers, 0)
                return ret == 0
        return False

    
    @staticmethod
    def copy_all(
        model,
        source: str,
        targets: Union[str, List[str]],
        include_loads: bool = True,
        include_groups: bool = True,
        include_property: bool = False,
        include_local_axes: bool = False,
        include_modifiers: bool = False
    ) -> dict:
        """复制所有指定属性到目标面单元"""
        if isinstance(targets, str):
            targets = [targets]
        
        success = 0
        failed = 0
        
        for target in targets:
            try:
                if include_loads:
                    AreaBrush.copy_load_uniform_to_frame(model, source, target)
                    AreaBrush.copy_load_uniform(model, source, target)
                if include_groups:
                    AreaBrush.copy_groups(model, source, target)
                if include_property:
                    AreaBrush.copy_property(model, source, target)
                if include_local_axes:
                    AreaBrush.copy_local_axes(model, source, target)
                if include_modifiers:
                    AreaBrush.copy_modifiers(model, source, target)
                success += 1
            except Exception:
                failed += 1
        
        return {"success": success, "failed": failed}


class FrameBrush:
    """杆件属性刷"""
    
    @staticmethod
    def copy_groups(
        model,
        source: str,
        target: str,
        skip_all: bool = True
    ) -> int:
        """复制组分配"""
        result = model.FrameObj.GetGroupAssign(source, 0, [])
        if not isinstance(result, (list, tuple)) or len(result) < 3:
            return -1
        
        groups = result[1]
        if not groups:
            return 0

        
        count = 0
        for group in groups:
            if skip_all and group == "ALL":
                continue
            ret = model.FrameObj.SetGroupAssign(target, group, False, 0)
            if ret == 0:
                count += 1
        
        return count
    
    @staticmethod
    def copy_section(model, source: str, target: str) -> bool:
        """复制截面属性"""
        result = model.FrameObj.GetSection(source, "", "")
        if isinstance(result, (list, tuple)) and len(result) >= 3:
            prop_name = result[0]
            ret = model.FrameObj.SetSection(target, prop_name, 0)
            return ret == 0
        return False
    
    @staticmethod
    def copy_modifiers(model, source: str, target: str) -> bool:
        """复制刚度修正系数"""
        result = model.FrameObj.GetModifiers(source, [])
        if isinstance(result, (list, tuple)) and len(result) >= 2:
            modifiers = list(result[0]) if result[0] else None
            if modifiers:
                ret = model.FrameObj.SetModifiers(target, modifiers, 0)
                return ret == 0
        return False
    
    @staticmethod
    def copy_releases(model, source: str, target: str) -> bool:
        """复制端部释放"""
        result = model.FrameObj.GetReleases(source, [], [], [], [])
        if isinstance(result, (list, tuple)) and len(result) >= 5:
            ii = list(result[0]) if result[0] else [False] * 6
            jj = list(result[1]) if result[1] else [False] * 6
            start_value = list(result[2]) if result[2] else [0.0] * 6
            end_value = list(result[3]) if result[3] else [0.0] * 6
            ret = model.FrameObj.SetReleases(target, ii, jj, start_value, end_value, 0)
            return ret == 0
        return False
    
    @staticmethod
    def copy_local_axes(model, source: str, target: str) -> bool:
        """复制局部轴"""
        result = model.FrameObj.GetLocalAxes(source, 0.0, False)
        if isinstance(result, (list, tuple)) and len(result) >= 3:
            angle = result[0]
            ret = model.FrameObj.SetLocalAxes(target, angle, 0)
            return ret == 0
        return False

    
    @staticmethod
    def copy_material_overwrite(model, source: str, target: str) -> bool:
        """复制材料覆盖"""
        result = model.FrameObj.GetMaterialOverwrite(source, "")
        if isinstance(result, (list, tuple)) and len(result) >= 2:
            mat_name = result[0]
            if mat_name:
                ret = model.FrameObj.SetMaterialOverwrite(target, mat_name, 0)
                return ret == 0
        return False
    
    @staticmethod
    def copy_all(
        model,
        source: str,
        targets: Union[str, List[str]],
        include_groups: bool = True,
        include_section: bool = False,
        include_modifiers: bool = False,
        include_releases: bool = False,
        include_local_axes: bool = False,
        include_material: bool = False
    ) -> dict:
        """复制所有指定属性到目标杆件"""
        if isinstance(targets, str):
            targets = [targets]
        
        success = 0
        failed = 0
        
        for target in targets:
            try:
                if include_groups:
                    FrameBrush.copy_groups(model, source, target)
                if include_section:
                    FrameBrush.copy_section(model, source, target)
                if include_modifiers:
                    FrameBrush.copy_modifiers(model, source, target)
                if include_releases:
                    FrameBrush.copy_releases(model, source, target)
                if include_local_axes:
                    FrameBrush.copy_local_axes(model, source, target)
                if include_material:
                    FrameBrush.copy_material_overwrite(model, source, target)
                success += 1
            except Exception:
                failed += 1
        
        return {"success": success, "failed": failed}


# =============================================================================
# 使用示例
# =============================================================================

if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from application import Application
    from selection import get_selected_objects
    
    app = Application()
    model = app.model
    
    selected = get_selected_objects(model)
    if selected["frames"]:
        FrameBrush.copy_all(model, source="997", targets=selected["frames"])
