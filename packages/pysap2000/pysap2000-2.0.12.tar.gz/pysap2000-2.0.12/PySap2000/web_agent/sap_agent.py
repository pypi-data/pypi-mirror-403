# -*- coding: utf-8 -*-
"""
SAP2000 Web Agent v1.0

Connect your local SAP2000 to www.spancore.cn

Usage:
    Double-click to run, or:
    python sap_agent.py --server wss://www.spancore.cn/ws/sap/agent/
"""

import asyncio
import json
import sys
import os

# Server configuration
DEFAULT_SERVER = "wss://www.spancore.cn/ws/sap/agent/"
DEFAULT_TOKEN = "public"

# For development
DEV_SERVER = "ws://localhost:8000/ws/sap/agent/"

# 自定义协议名称
PROTOCOL_NAME = "sapagent"


def register_url_protocol():
    """注册 sapagent:// 自定义协议到 Windows 注册表"""
    if sys.platform != 'win32':
        return
    
    try:
        import winreg
        
        # 获取当前 exe 路径
        if getattr(sys, 'frozen', False):
            # PyInstaller 打包后的 exe
            exe_path = sys.executable
        else:
            # 开发模式，使用 python 解释器
            exe_path = sys.executable
            script_path = os.path.abspath(__file__)
            exe_path = f'"{exe_path}" "{script_path}"'
        
        # 检查是否已注册
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{PROTOCOL_NAME}", 0, winreg.KEY_READ)
            existing_path, _ = winreg.QueryValueEx(key, "ExecutablePath")
            winreg.CloseKey(key)
            
            # 如果路径相同，跳过注册
            if existing_path == exe_path:
                print(f"[Protocol] sapagent:// already registered")
                return
        except WindowsError:
            pass  # 未注册，继续
        
        # 注册协议
        # HKEY_CURRENT_USER\Software\Classes\sapagent
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{PROTOCOL_NAME}")
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "URL:SapAgent Protocol")
        winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")
        winreg.SetValueEx(key, "ExecutablePath", 0, winreg.REG_SZ, exe_path)  # 保存路径用于检查
        winreg.CloseKey(key)
        
        # HKEY_CURRENT_USER\Software\Classes\sapagent\shell\open\command
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{PROTOCOL_NAME}\\shell\\open\\command")
        if getattr(sys, 'frozen', False):
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f'"{exe_path}" "%1"')
        else:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f'{exe_path} "%1"')
        winreg.CloseKey(key)
        
        print(f"[Protocol] Registered sapagent:// protocol")
        
    except Exception as e:
        print(f"[Protocol] Failed to register: {e}")


def get_sap_model():
    """Connect to SAP2000 and return model object"""
    try:
        import comtypes.client
        sap = comtypes.client.GetActiveObject('CSI.SAP2000.API.SapObject')
        model = sap.SapModel
        
        # Get version and filename
        version = model.GetVersion()
        ver_str = version[0] if isinstance(version, (list, tuple)) else ""
        filename = model.GetModelFilename(False) or "Untitled"
        print(f"Connected to SAP2000 v{ver_str} | {filename}")
        
        return model
    except Exception as e:
        error_code = str(e)
        print("\n" + "=" * 50)
        print("❌ 无法连接到 SAP2000")
        print("=" * 50)
        
        if "-2147467262" in error_code or "不支持此接口" in error_code:
            print("\n可能的原因：")
            print("  1. SAP2000 软件未安装")
            print("  2. SAP2000 版本不兼容（需要 v20 或更高版本）")
            print("  3. SAP2000 未正常注册 COM 组件")
            print("\n解决方案：")
            print("  • 请确保已安装 SAP2000 v20 或更高版本")
            print("  • 以管理员身份运行 SAP2000 一次以注册 COM 组件")
            print("  • 重启电脑后再试")
        else:
            print("\n请确保：")
            print("  1. SAP2000 正在运行")
            print("  2. SAP2000 中已打开一个模型文件")
            print("  3. SAP2000 版本为 v20 或更高")
        
        print(f"\n详细错误信息: {e}")
        print("=" * 50 + "\n")
        return None


def get_model_info(model):
    """Get basic model information"""
    filename = model.GetModelFilename(False) or "Untitled"
    units_code = model.GetPresentUnits()
    units_map = {5: "kN-mm-C", 6: "kN-m-C", 9: "N-mm-C", 10: "N-m-C"}
    units = units_map.get(units_code, f"Code {units_code}")
    
    return {
        "command": "model_info",
        "filename": filename,
        "units": units,
        "stats": {
            "points": model.PointObj.Count(),
            "frames": model.FrameObj.Count(),
            "areas": model.AreaObj.Count(),
            "groups": model.GroupDef.Count()
        }
    }


def get_point_coord(model, point_name: str):
    """Get point coordinates"""
    try:
        ret = model.PointObj.GetCoordCartesian(str(point_name), 0.0, 0.0, 0.0)
        if isinstance(ret, (list, tuple)) and len(ret) >= 3:
            return {"x": ret[0], "y": ret[1], "z": ret[2]}
        return {"error": f"Point '{point_name}' not found"}
    except Exception as e:
        return {"error": str(e)}


def get_frame_info(model, frame_name: str):
    """Get frame information"""
    try:
        ret = model.FrameObj.GetPoints(str(frame_name), "", "")
        if not isinstance(ret, (list, tuple)) or len(ret) < 2:
            return {"error": f"Frame '{frame_name}' not found"}
        
        point_i, point_j = ret[0], ret[1]
        
        ret = model.FrameObj.GetSection(str(frame_name), "", "")
        section = ret[0] if isinstance(ret, (list, tuple)) else ""
        
        coord_i = model.PointObj.GetCoordCartesian(point_i, 0.0, 0.0, 0.0)
        coord_j = model.PointObj.GetCoordCartesian(point_j, 0.0, 0.0, 0.0)
        
        dx = coord_j[0] - coord_i[0]
        dy = coord_j[1] - coord_i[1]
        dz = coord_j[2] - coord_i[2]
        length = (dx**2 + dy**2 + dz**2) ** 0.5
        
        return {
            "point_i": point_i,
            "point_j": point_j,
            "section": section,
            "length": length
        }
    except Exception as e:
        return {"error": str(e)}


def get_model_geometry(model):
    """Get all points and frames for 3D visualization (optimized with DatabaseTables)"""
    try:
        points = {}
        frames = {}
        
        # Try to use DatabaseTables for faster batch retrieval
        try:
            # Get point coordinates from table
            ret = model.DatabaseTables.GetTableForDisplayArray(
                "Joint Coordinates", ["Joint", "GlobalX", "GlobalY", "GlobalZ"], "", 0, [], 0, []
            )
            if isinstance(ret, (list, tuple)) and len(ret) >= 5 and ret[5] == 0:
                fields = list(ret[2])
                num_records = ret[3]
                data = ret[4]
                num_fields = len(fields)
                
                joint_idx = fields.index("Joint") if "Joint" in fields else -1
                x_idx = fields.index("GlobalX") if "GlobalX" in fields else -1
                y_idx = fields.index("GlobalY") if "GlobalY" in fields else -1
                z_idx = fields.index("GlobalZ") if "GlobalZ" in fields else -1
                
                if joint_idx >= 0 and x_idx >= 0:
                    for i in range(num_records):
                        base = i * num_fields
                        name = data[base + joint_idx]
                        if name:
                            points[name] = {
                                "x": float(data[base + x_idx]) if data[base + x_idx] else 0,
                                "y": float(data[base + y_idx]) if data[base + y_idx] else 0,
                                "z": float(data[base + z_idx]) if data[base + z_idx] else 0
                            }
                print(f"  -> Got {len(points)} points from table")
            
            # Get frame connectivity from table
            ret = model.DatabaseTables.GetTableForDisplayArray(
                "Connectivity - Frame", ["Frame", "JointI", "JointJ"], "", 0, [], 0, []
            )
            if isinstance(ret, (list, tuple)) and len(ret) >= 5 and ret[5] == 0:
                fields = list(ret[2])
                num_records = ret[3]
                data = ret[4]
                num_fields = len(fields)
                
                frame_idx = fields.index("Frame") if "Frame" in fields else -1
                ji_idx = fields.index("JointI") if "JointI" in fields else -1
                jj_idx = fields.index("JointJ") if "JointJ" in fields else -1
                
                if frame_idx >= 0 and ji_idx >= 0:
                    for i in range(num_records):
                        base = i * num_fields
                        name = data[base + frame_idx]
                        if name:
                            frames[name] = {
                                "point_i": data[base + ji_idx] if ji_idx >= 0 else "",
                                "point_j": data[base + jj_idx] if jj_idx >= 0 else ""
                            }
                print(f"  -> Got {len(frames)} frames from table")
        except Exception as e:
            print(f"  -> Table error: {e}")
            # Fallback to individual API calls
            pass
        
        # Fallback if tables didn't work
        if not points:
            print("  -> Using fallback for points...")
            ret = model.PointObj.GetNameList(0, [])
            if isinstance(ret, (list, tuple)) and len(ret) >= 2:
                point_names = ret[1] if ret[1] else []
                for name in point_names:
                    coord = model.PointObj.GetCoordCartesian(str(name), 0.0, 0.0, 0.0)
                    if isinstance(coord, (list, tuple)) and len(coord) >= 3:
                        points[name] = {"x": coord[0], "y": coord[1], "z": coord[2]}
                print(f"  -> Got {len(points)} points from API")
        
        if not frames:
            print("  -> Using fallback for frames...")
            ret = model.FrameObj.GetNameList(0, [])
            if isinstance(ret, (list, tuple)) and len(ret) >= 2:
                frame_names = ret[1] if ret[1] else []
                for name in frame_names:
                    pts = model.FrameObj.GetPoints(str(name), "", "")
                    if isinstance(pts, (list, tuple)) and len(pts) >= 2:
                        frames[name] = {"point_i": pts[0], "point_j": pts[1]}
                print(f"  -> Got {len(frames)} frames from API")
        
        return {
            "command": "model_geometry",
            "points": points,
            "frames": frames
        }
    except Exception as e:
        print(f"  -> Error: {e}")
        return {"error": str(e)}


def get_group_geometry(model, group_name):
    """Get points and frames for a specific group"""
    try:
        print(f"  -> Getting geometry for group: {group_name}")
        points = {}
        frames = {}
        
        # Get frames in the group
        ret = model.GroupDef.GetAssignments(group_name, 0, [], [])
        if not isinstance(ret, (list, tuple)) or len(ret) < 3:
            print(f"  -> Error: Cannot get group assignments")
            return {"error": f"无法获取组 {group_name} 的内容"}
        
        obj_types = ret[1] if ret[1] else []
        obj_names = ret[2] if ret[2] else []
        print(f"  -> Group has {len(obj_names)} objects")
        
        # Filter frame objects (type 2)
        frame_names = [obj_names[i] for i in range(len(obj_types)) if obj_types[i] == 2]
        print(f"  -> Found {len(frame_names)} frames in group")
        
        # Get frame connectivity and collect point names
        point_names_set = set()
        for name in frame_names:
            pts = model.FrameObj.GetPoints(str(name), "", "")
            if isinstance(pts, (list, tuple)) and len(pts) >= 2:
                frames[name] = {"point_i": pts[0], "point_j": pts[1]}
                point_names_set.add(pts[0])
                point_names_set.add(pts[1])
        
        # Get point coordinates
        for name in point_names_set:
            coord = model.PointObj.GetCoordCartesian(str(name), 0.0, 0.0, 0.0)
            if isinstance(coord, (list, tuple)) and len(coord) >= 3:
                points[name] = {"x": coord[0], "y": coord[1], "z": coord[2]}
        
        print(f"  -> Got {len(points)} points, {len(frames)} frames")
        
        return {
            "command": "group_geometry",
            "group_name": group_name,
            "points": points,
            "frames": frames
        }
    except Exception as e:
        print(f"  -> Error: {e}")
        return {"error": str(e)}


# ==================== 后处理功能 ====================

# 添加 PySap2000 路径
import sys
import os

# 处理 PyInstaller 打包后的路径
if getattr(sys, 'frozen', False):
    # 打包后，使用 _MEIPASS 临时目录
    pysap_root = sys._MEIPASS
else:
    # 开发模式，使用相对路径
    pysap_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if pysap_root not in sys.path:
    sys.path.insert(0, pysap_root)



def get_steel_usage(model, group_by="section"):
    """Calculate steel usage by section or material using PySap2000"""
    try:
        from statistics import SteelUsage
        
        usage = SteelUsage.calculate(model, group_by=group_by)
        
        # Convert to response format
        results = []
        if group_by == "section" and usage.by_section:
            for name, weight in sorted(usage.by_section.items(), key=lambda x: -x[1]):
                results.append({"name": name, "weight": weight / 1000})  # kg -> t
        elif group_by == "material" and usage.by_material:
            for name, weight in sorted(usage.by_material.items(), key=lambda x: -x[1]):
                results.append({"name": name, "weight": weight / 1000})
        
        return {
            "command": "steel_usage",
            "group_by": group_by,
            "total_weight": usage.total / 1000,  # kg -> t
            "data": results
        }
    except Exception as e:
        return {"error": str(e)}


def _get_usage_history_file(model) -> str:
    """获取用钢量历史记录文件路径"""
    filepath = model.GetModelFilepath() or ""
    filename = model.GetModelFilename(False) or "model"
    if filepath and filename:
        return os.path.join(filepath, f"{filename}_usage_history.json")
    return "usage_history.json"


def _load_usage_history(history_file: str) -> dict:
    """加载历史记录"""
    if os.path.exists(history_file):
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def _save_usage_history(history_file: str, history: dict):
    """保存历史记录"""
    try:
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except IOError:
        pass


def get_steel_usage_detail(model, group_name="", save_history=True):
    """
    获取用钢量详情，包括按截面分组、总量、上次记录、增量
    
    Args:
        model: SapModel 对象
        group_name: 组名，空字符串表示全部杆件
        save_history: 是否保存历史记录
    """
    try:
        from statistics import SteelUsage
        from group import Group
        from datetime import datetime
        
        # 获取杆件列表
        frame_names = None
        if group_name:
            try:
                group = Group.get_by_name(model, group_name)
                frame_names = group.get_frames(model)
                print(f"  -> Group '{group_name}' has {len(frame_names)} frames")
            except Exception as e:
                print(f"  -> Error getting group: {e}")
                frame_names = []
        
        # 计算用钢量（按截面分组）
        usage = SteelUsage.calculate(model, group_by="section", frame_names=frame_names)
        
        # 按截面分组的数据
        by_section = []
        if usage.by_section:
            for name, weight in sorted(usage.by_section.items(), key=lambda x: -x[1]):
                by_section.append({
                    "section": name,
                    "weight": round(weight / 1000, 3)  # kg -> t
                })
        
        total_weight = usage.total / 1000  # kg -> t
        
        # 加载历史记录
        history_file = _get_usage_history_file(model)
        history = _load_usage_history(history_file)
        history_key = group_name or "ALL"
        
        prev_record = history.get("steel", {}).get(history_key, {})
        prev_weight = prev_record.get("total", 0) / 1000 if prev_record.get("total") else 0  # kg -> t
        prev_datetime = prev_record.get("datetime", "")
        
        # 计算增量
        change_weight = total_weight - prev_weight if prev_weight > 0 else 0
        change_percent = ((total_weight - prev_weight) / prev_weight * 100) if prev_weight > 0 else 0
        
        # 保存历史记录
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if save_history:
            if "steel" not in history:
                history["steel"] = {}
            history["steel"][history_key] = {
                "total": usage.total,  # 保存原始 kg 值
                "datetime": current_datetime
            }
            _save_usage_history(history_file, history)
        
        return {
            "command": "steel_usage_detail",
            "group_name": group_name or "全部",
            "total_weight": round(total_weight, 3),
            "by_section": by_section,
            "prev_weight": round(prev_weight, 3) if prev_weight > 0 else None,
            "prev_datetime": prev_datetime,
            "change_weight": round(change_weight, 3) if prev_weight > 0 else None,
            "change_percent": round(change_percent, 2) if prev_weight > 0 else None,
            "current_datetime": current_datetime
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


def get_cable_usage(model, group_by="section"):
    """Calculate cable usage by section or material using PySap2000"""
    try:
        from statistics import CableUsage
        
        usage = CableUsage.calculate(model, group_by=group_by)
        
        # Convert to response format
        results = []
        if group_by == "section" and usage.by_section:
            for name, weight in sorted(usage.by_section.items(), key=lambda x: -x[1]):
                results.append({"name": name, "weight": weight / 1000})  # kg -> t
        elif group_by == "material" and usage.by_material:
            for name, weight in sorted(usage.by_material.items(), key=lambda x: -x[1]):
                results.append({"name": name, "weight": weight / 1000})
        
        return {
            "command": "cable_usage",
            "group_by": group_by,
            "total_weight": usage.total / 1000,  # kg -> t
            "data": results
        }
    except Exception as e:
        return {"error": str(e)}


def get_stress_ratios(model, group_name=""):
    """Get steel design stress ratios with distribution statistics using PySap2000"""
    try:
        from design.steel import get_steel_summary_results, get_steel_design_section
        from design.enums import ItemType
        from frame.property import get_frame_section
        
        # 使用 DatabaseTables 批量获取截面信息（更快）
        section_map = {}  # frame_name -> section
        design_section_map = {}  # frame_name -> design_section
        
        try:
            # 批量获取当前截面
            ret = model.DatabaseTables.GetTableForDisplayArray(
                "Frame Assignments - Section Properties", ["Frame", "AnalSect"], "", 0, [], 0, []
            )
            if isinstance(ret, (list, tuple)) and len(ret) >= 5 and ret[5] == 0:
                fields = list(ret[2])
                num_records = ret[3]
                data = ret[4]
                num_fields = len(fields)
                frame_idx = fields.index("Frame") if "Frame" in fields else -1
                sect_idx = fields.index("AnalSect") if "AnalSect" in fields else -1
                if frame_idx >= 0 and sect_idx >= 0:
                    for i in range(num_records):
                        base = i * num_fields
                        fname = data[base + frame_idx]
                        sect = data[base + sect_idx]
                        if fname:
                            section_map[fname] = sect or ""
            print(f"  -> Got {len(section_map)} sections from table")
            
            # 批量获取设计截面
            ret = model.DatabaseTables.GetTableForDisplayArray(
                "Steel Design 1 - Summary Data - Chinese 2018", ["Frame", "DesignSect"], "", 0, [], 0, []
            )
            if isinstance(ret, (list, tuple)) and len(ret) >= 5 and ret[5] == 0:
                fields = list(ret[2])
                num_records = ret[3]
                data = ret[4]
                num_fields = len(fields)
                frame_idx = fields.index("Frame") if "Frame" in fields else -1
                dsect_idx = fields.index("DesignSect") if "DesignSect" in fields else -1
                if frame_idx >= 0 and dsect_idx >= 0:
                    for i in range(num_records):
                        base = i * num_fields
                        fname = data[base + frame_idx]
                        dsect = data[base + dsect_idx]
                        if fname:
                            design_section_map[fname] = dsect or ""
            print(f"  -> Got {len(design_section_map)} design sections from table")
        except Exception as e:
            print(f"  -> Table query failed: {e}, will use API fallback")
        
        # 自动创建 all_frame 组包含所有框架单元
        all_frame_group = "all_frame"
        
        # 获取所有框架单元
        ret = model.FrameObj.GetNameList(0, [])
        if isinstance(ret, (list, tuple)) and len(ret) >= 2:
            frame_names = ret[1] if ret[1] else []
            print(f"  -> Total frames: {len(frame_names)}")
            
            # 创建/清空 all_frame 组
            model.GroupDef.SetGroup(all_frame_group)
            model.GroupDef.Clear(all_frame_group)
            
            # 将所有框架添加到组
            for fname in frame_names:
                model.FrameObj.SetGroupAssign(fname, all_frame_group, False, 0)
            
            # 设置该组用于钢结构设计
            model.DesignSteel.SetGroup(all_frame_group, True)
            print(f"  -> Created group '{all_frame_group}' with {len(frame_names)} frames")
        
        results = []
        
        # 使用 PySap2000 获取设计结果 - 使用 GROUP 类型获取 all_frame 组的结果
        summary_results = get_steel_summary_results(model, all_frame_group, ItemType.GROUP)
        
        print(f"  -> Found {len(summary_results)} design results")
        
        # 如果没有结果，提示用户运行设计
        if len(summary_results) == 0:
            return {"error": "未获取到设计结果，请在 SAP2000 中运行钢结构设计 (Design → Steel Frame Design → Start Design)"}
        
        for sr in summary_results:
            # 获取当前截面（优先从缓存获取）
            section = section_map.get(sr.frame_name, "")
            if not section:
                try:
                    section = get_frame_section(model, sr.frame_name)
                except:
                    pass
            
            # 获取设计截面（优先从缓存获取）
            design_section = design_section_map.get(sr.frame_name, "")
            if not design_section:
                try:
                    design_section = get_steel_design_section(model, sr.frame_name)
                except:
                    pass
            
            # 如果有 error_summary，不显示应力比数值
            has_error = bool(sr.error_summary)
            has_warning = bool(sr.warning_summary)
            
            results.append({
                "name": sr.frame_name,
                "ratio": sr.ratio if not has_error else 0,
                "type": sr.ratio_type.value if hasattr(sr.ratio_type, 'value') else sr.ratio_type,
                "location": sr.location,
                "combo": sr.combo_name,
                "section": section,
                "design_section": design_section,
                "error": sr.error_summary if has_error else None,
                "warning": sr.warning_summary if has_warning else None
            })
        
        # Sort by ratio descending
        results.sort(key=lambda x: x["ratio"], reverse=True)
        
        # Statistics
        if results:
            ratios_list = [r["ratio"] for r in results]
            
            # Distribution by ranges (for chart)
            ranges = [
                (0.0, 0.2, "0-0.2"),
                (0.2, 0.4, "0.2-0.4"),
                (0.4, 0.6, "0.4-0.6"),
                (0.6, 0.7, "0.6-0.7"),
                (0.7, 0.8, "0.7-0.8"),
                (0.8, 0.9, "0.8-0.9"),
                (0.9, 1.0, "0.9-1.0"),
                (1.0, 999, ">1.0")
            ]
            distribution = []
            for low, high, label in ranges:
                count = len([r for r in ratios_list if low <= r < high])
                distribution.append({"range": label, "count": count})
            
            stats = {
                "total": len(ratios_list),
                "max": max(ratios_list),
                "min": min(ratios_list),
                "avg": sum(ratios_list) / len(ratios_list),
                "over_09": len([r for r in ratios_list if r > 0.9]),
                "over_10": len([r for r in ratios_list if r > 1.0]),
                "distribution": distribution
            }
        else:
            stats = {"total": 0, "max": 0, "min": 0, "avg": 0, "over_09": 0, "over_10": 0, "distribution": []}
        
        return {
            "command": "stress_ratios",
            "stats": stats,
            "data": results  # Return all results for coloring
        }
    except Exception as e:
        return {"error": str(e)}


def classify_by_stress_ratio(model, group_names):
    """Classify frames by stress ratio into groups (from steel_design_tools.py)"""
    try:
        from design.steel import get_steel_summary_results
        from design.enums import ItemType
        from group import Group
        
        # Default ranges
        ranges = [
            (0.0, 0.2, "应力比0-0.2"),
            (0.2, 0.4, "应力比0.2-0.4"),
            (0.4, 0.6, "应力比0.4-0.6"),
            (0.6, 0.7, "应力比0.6-0.7"),
            (0.7, 0.8, "应力比0.7-0.8"),
            (0.8, 0.9, "应力比0.8-0.9"),
            (0.9, 1.0, "应力比0.9-1.0"),
        ]
        target_groups = [r[2] for r in ranges] + ["应力比大于1"]
        
        # Create/clear target groups
        for gname in target_groups:
            model.GroupDef.SetGroup(gname)
            model.GroupDef.Clear(gname)
        
        # Get frames from source groups
        frame_set = set()
        for gname in group_names:
            try:
                group = Group.get_by_name(model, gname)
                frames = group.get_frames(model)
                frame_set.update(frames)
            except:
                pass
        
        # Classify each frame
        result = {gname: 0 for gname in target_groups}
        
        for fname in frame_set:
            summary = get_steel_summary_results(model, fname, ItemType.OBJECT)
            if not summary:
                continue
            
            ratio = summary[0].ratio
            assigned = False
            
            for low, high, gname in ranges:
                if low <= ratio < high:
                    model.FrameObj.SetGroupAssign(fname, gname, False, 0)
                    result[gname] += 1
                    assigned = True
                    break
            
            if not assigned:
                model.FrameObj.SetGroupAssign(fname, "应力比大于1", False, 0)
                result["应力比大于1"] += 1
        
        data = [{"group": k, "count": v} for k, v in result.items() if v > 0]
        
        return {
            "command": "classify_stress_ratio",
            "data": data
        }
    except Exception as e:
        return {"error": str(e)}


def replace_design_section(model, group_names, run_analysis=False):
    """Replace analysis section with design section (from steel_design_tools.py)"""
    try:
        from design.steel import get_steel_design_section
        from frame.property import get_frame_section
        from group import Group
        
        # Unlock model
        model.SetModelIsLocked(False)
        
        # Get frames from groups
        frame_set = set()
        for gname in group_names:
            try:
                group = Group.get_by_name(model, gname)
                frames = group.get_frames(model)
                frame_set.update(frames)
            except:
                pass
        
        replaced = []
        for fname in frame_set:
            design_section = get_steel_design_section(model, fname)
            if not design_section:
                continue
            
            analysis_section = get_frame_section(model, fname)
            if analysis_section == design_section:
                continue
            
            ret = model.FrameObj.SetSection(fname, design_section, 0)
            if ret == 0:
                replaced.append({
                    "frame": fname,
                    "old": analysis_section,
                    "new": design_section
                })
        
        # Run analysis if requested
        if run_analysis and replaced:
            model.Analyze.RunAnalysis()
        
        return {
            "command": "replace_design_section",
            "count": len(replaced),
            "data": replaced[:50]  # Limit output
        }
    except Exception as e:
        return {"error": str(e)}


def replace_frame_section(model, frame_name, section_name):
    """Replace a single frame's section"""
    try:
        # Unlock model
        model.SetModelIsLocked(False)
        
        # Get current section
        sec_ret = model.FrameObj.GetSection(str(frame_name), "", "")
        old_section = sec_ret[0] if isinstance(sec_ret, (list, tuple)) else ""
        
        # Set new section
        ret = model.FrameObj.SetSection(str(frame_name), str(section_name), 0)
        
        if ret == 0:
            return {
                "command": "replace_frame_section",
                "frame": frame_name,
                "old_section": old_section,
                "new_section": section_name,
                "success": True
            }
        else:
            return {"error": f"Failed to set section for frame {frame_name}"}
    except Exception as e:
        return {"error": str(e)}


def set_frame_design_section(model, frame_name, section_name, run_design=True):
    """Set design section for a single frame and optionally re-run design"""
    try:
        from design.steel import set_steel_design_section, get_steel_design_section, get_steel_summary_results, start_steel_design
        from design.enums import ItemType
        
        # Get current design section
        old_design_section = get_steel_design_section(model, str(frame_name))
        
        # Set new design section
        ret = set_steel_design_section(model, str(frame_name), str(section_name), False, ItemType.OBJECT)
        
        if ret != 0:
            return {"error": f"Failed to set design section for frame {frame_name}, ret={ret}"}
        
        result = {
            "command": "set_frame_design_section",
            "frame": frame_name,
            "old_design_section": old_design_section,
            "new_design_section": section_name,
            "success": True
        }
        
        # Re-run steel design to get updated ratio
        if run_design:
            try:
                start_steel_design(model)
                # Get new stress ratio
                summary = get_steel_summary_results(model, str(frame_name), ItemType.OBJECT)
                if summary:
                    sr = summary[0]
                    result["new_ratio"] = sr.ratio
                    result["new_combo"] = sr.combo_name
            except Exception as e:
                print(f"  -> Warning: Failed to re-run design: {e}")
        
        return result
    except Exception as e:
        return {"error": str(e)}


def set_batch_design_section(model, frame_names, section_name, run_design=True):
    """Set design section for multiple frames using DesignSteel API"""
    try:
        print(f"  -> Setting design section for {len(frame_names)} frames to '{section_name}'...")
        
        success_count = 0
        failed = []
        
        # 使用 DesignSteel.SetDesignSection API（在锁定状态下也能工作）
        for frame_name in frame_names:
            try:
                ret = model.DesignSteel.SetDesignSection(str(frame_name), str(section_name), False, 0)
                if ret == 0:
                    success_count += 1
                else:
                    failed.append(frame_name)
            except:
                failed.append(frame_name)
        
        print(f"  -> Done: {success_count} frames updated, {len(failed)} failed")
        
        result = {
            "command": "set_batch_design_section",
            "section": section_name,
            "success_count": success_count,
            "failed_count": len(failed),
            "failed": failed[:10] if failed else []
        }
        
        # Re-run steel design
        if run_design and success_count > 0:
            try:
                from design.steel import start_steel_design
                start_steel_design(model)
                result["design_updated"] = True
            except Exception as e:
                print(f"  -> Warning: Failed to re-run design: {e}")
                result["design_updated"] = False
        
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


def run_steel_design(model):
    """Run steel frame design"""
    try:
        from design.steel import start_steel_design
        
        print("  -> Running steel design...")
        start_steel_design(model)
        print("  -> Steel design completed")
        
        return {
            "command": "run_steel_design",
            "success": True,
            "message": "钢结构设计完成"
        }
    except Exception as e:
        return {"error": str(e)}


def run_analysis(model):
    """Run model analysis"""
    try:
        print("  -> Running analysis...")
        # 解锁模型
        try:
            model.SetModelIsLocked(False)
        except:
            pass
        
        # 尝试设置不显示分析完成消息框
        # 注意：这个设置可能需要在 SAP2000 的 Options -> Preferences 中手动关闭
        # "Show Analysis Complete Message Box"
        
        ret = model.Analyze.RunAnalysis()
        print(f"  -> Analysis completed, ret={ret}")
        
        # 分析完成后，模型会被锁定
        is_locked = model.GetModelIsLocked()
        print(f"  -> Model locked: {is_locked}")
        
        return {
            "command": "run_analysis",
            "success": ret == 0,
            "is_locked": is_locked,
            "message": "分析完成" if ret == 0 else f"分析返回代码: {ret}"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


def get_model_status(model):
    """Get model status including lock state and analysis state"""
    try:
        is_locked = model.GetModelIsLocked()
        
        # 检查是否有分析结果
        has_results = False
        try:
            # 尝试获取结果数量来判断是否有分析结果
            ret = model.Results.Setup.GetCaseStatus(0, [], [])
            if isinstance(ret, (list, tuple)) and len(ret) >= 2:
                statuses = ret[2] if len(ret) > 2 else []
                # status 1 = not run, 2 = could not run, 3 = run
                has_results = any(s == 3 for s in statuses) if statuses else False
        except:
            pass
        
        return {
            "command": "model_status",
            "is_locked": is_locked,
            "has_results": has_results
        }
    except Exception as e:
        return {"error": str(e)}


def get_joint_displacements(model, load_case=""):
    """Get joint displacements"""
    try:
        # Setup output
        model.Results.Setup.DeselectAllCasesAndCombosForOutput()
        if load_case:
            model.Results.Setup.SetCaseSelectedForOutput(load_case)
        else:
            # Select all cases
            ret = model.LoadCases.GetNameList(0, [])
            if isinstance(ret, (list, tuple)) and len(ret) >= 2:
                cases = ret[1] if ret[1] else []
                for case in cases:
                    model.Results.Setup.SetCaseSelectedForOutput(case)
        
        # Get displacements
        ret = model.Results.JointDispl("", 0, 0, [], [], [], [], [], [], [], [], [])
        
        results = []
        if isinstance(ret, (list, tuple)) and len(ret) >= 12:
            num = ret[0]
            names = ret[1] if ret[1] else []
            cases = ret[3] if ret[3] else []
            u1 = ret[5] if ret[5] else []
            u2 = ret[6] if ret[6] else []
            u3 = ret[7] if ret[7] else []
            
            for i in range(min(num, 500)):  # Limit results
                results.append({
                    "name": names[i] if i < len(names) else "",
                    "case": cases[i] if i < len(cases) else "",
                    "u1": u1[i] if i < len(u1) else 0,
                    "u2": u2[i] if i < len(u2) else 0,
                    "u3": u3[i] if i < len(u3) else 0
                })
        
        return {
            "command": "joint_displacements",
            "data": results
        }
    except Exception as e:
        return {"error": str(e)}


def get_base_reactions(model, load_case=""):
    """Get base reactions"""
    try:
        # Setup output
        model.Results.Setup.DeselectAllCasesAndCombosForOutput()
        if load_case:
            model.Results.Setup.SetCaseSelectedForOutput(load_case)
        
        # Get base reactions
        ret = model.Results.BaseReact(0, [], [], [], [], [], [], [], [], [])
        
        results = []
        if isinstance(ret, (list, tuple)) and len(ret) >= 10:
            num = ret[0]
            cases = ret[1] if ret[1] else []
            fx = ret[3] if ret[3] else []
            fy = ret[4] if ret[4] else []
            fz = ret[5] if ret[5] else []
            mx = ret[6] if ret[6] else []
            my = ret[7] if ret[7] else []
            mz = ret[8] if ret[8] else []
            
            for i in range(num):
                results.append({
                    "case": cases[i] if i < len(cases) else "",
                    "fx": fx[i] if i < len(fx) else 0,
                    "fy": fy[i] if i < len(fy) else 0,
                    "fz": fz[i] if i < len(fz) else 0,
                    "mx": mx[i] if i < len(mx) else 0,
                    "my": my[i] if i < len(my) else 0,
                    "mz": mz[i] if i < len(mz) else 0
                })
        
        return {
            "command": "base_reactions",
            "data": results
        }
    except Exception as e:
        return {"error": str(e)}


def get_frame_forces(model, frame_name: str, load_case=""):
    """Get frame internal forces"""
    try:
        # Setup output
        model.Results.Setup.DeselectAllCasesAndCombosForOutput()
        if load_case:
            model.Results.Setup.SetCaseSelectedForOutput(load_case)
        
        # Get frame forces
        ret = model.Results.FrameForce(
            str(frame_name), 0, 0, [], [], [], [], [], [], [], [], [], []
        )
        
        results = []
        if isinstance(ret, (list, tuple)) and len(ret) >= 13:
            num = ret[0]
            stations = ret[4] if ret[4] else []
            p = ret[5] if ret[5] else []
            v2 = ret[6] if ret[6] else []
            v3 = ret[7] if ret[7] else []
            t = ret[8] if ret[8] else []
            m2 = ret[9] if ret[9] else []
            m3 = ret[10] if ret[10] else []
            
            for i in range(num):
                results.append({
                    "station": stations[i] if i < len(stations) else 0,
                    "P": p[i] if i < len(p) else 0,
                    "V2": v2[i] if i < len(v2) else 0,
                    "V3": v3[i] if i < len(v3) else 0,
                    "T": t[i] if i < len(t) else 0,
                    "M2": m2[i] if i < len(m2) else 0,
                    "M3": m3[i] if i < len(m3) else 0
                })
        
        return {
            "command": "frame_forces",
            "frame": frame_name,
            "data": results
        }
    except Exception as e:
        return {"error": str(e)}


def get_load_cases(model):
    """Get all load cases and combinations"""
    try:
        cases = []
        combos = []
        
        # Get load cases
        ret = model.LoadCases.GetNameList(0, [])
        if isinstance(ret, (list, tuple)) and len(ret) >= 2:
            cases = list(ret[1]) if ret[1] else []
        
        # Get load combinations
        ret = model.RespCombo.GetNameList(0, [])
        if isinstance(ret, (list, tuple)) and len(ret) >= 2:
            combos = list(ret[1]) if ret[1] else []
        
        return {
            "command": "load_cases",
            "cases": cases,
            "combos": combos
        }
    except Exception as e:
        return {"error": str(e)}


def get_analysis_status(model):
    """Check if model has been analyzed"""
    try:
        # Try to get results to check if analyzed
        ret = model.Analyze.GetRunCaseFlag("", False)
        
        return {
            "command": "analysis_status",
            "analyzed": True  # If we get here, model is likely analyzed
        }
    except Exception as e:
        return {"error": str(e)}


def get_groups(model):
    """Get all group names"""
    try:
        ret = model.GroupDef.GetNameList(0, [])
        groups = []
        if isinstance(ret, (list, tuple)) and len(ret) >= 2:
            groups = list(ret[1]) if ret[1] else []
        
        return {
            "command": "groups",
            "data": groups
        }
    except Exception as e:
        return {"error": str(e)}


def get_frame_sections(model):
    """Get all frame section names"""
    try:
        ret = model.PropFrame.GetNameList(0, [])
        sections = []
        if isinstance(ret, (list, tuple)) and len(ret) >= 2:
            sections = list(ret[1]) if ret[1] else []
        
        return {
            "command": "frame_sections",
            "data": sections
        }
    except Exception as e:
        return {"error": str(e)}


def export_frame_table_dxf(model, selected_only=False, rows_per_column=90, row_height=800,
                           text_height=350, column_gap=2500, group_gap=40000, tables_per_group=5):
    """Export frame table to DXF file"""
    try:
        from export_docs.cad_export import export_frame_table
        
        # Generate output filename
        filepath = model.GetModelFilepath() or ""
        filename = model.GetModelFilename(False) or "model"
        output_file = os.path.join(filepath, f"{filename}_frames.dxf")
        
        count = export_frame_table(
            model, output_file, 
            selected_only=selected_only,
            rows_per_column=rows_per_column,
            row_height=row_height,
            text_height=text_height,
            column_gap=column_gap,
            group_gap=group_gap,
            tables_per_group=tables_per_group
        )
        
        return {
            "command": "export_frame_table",
            "count": count,
            "file": output_file
        }
    except Exception as e:
        return {"error": str(e)}


def export_point_table_dxf(model, selected_only=False, rows_per_column=90, row_height=800, 
                           text_height=350, column_gap=2500, group_gap=40000, tables_per_group=4):
    """Export point table to DXF file"""
    try:
        from export_docs.cad_export import export_point_table
        
        # Generate output filename
        filepath = model.GetModelFilepath() or ""
        filename = model.GetModelFilename(False) or "model"
        output_file = os.path.join(filepath, f"{filename}_points.dxf")
        
        count = export_point_table(
            model, output_file, 
            selected_only=selected_only,
            rows_per_column=rows_per_column,
            row_height=row_height,
            text_height=text_height,
            column_gap=column_gap,
            group_gap=group_gap,
            tables_per_group=tables_per_group
        )
        
        return {
            "command": "export_point_table",
            "count": count,
            "file": output_file
        }
    except Exception as e:
        return {"error": str(e)}


def export_3d_model_dxf(model, group_names=None, projection="iso", group_gap=400000,
                        show_point_labels=False, show_frame_labels=False, label_height=350):
    """Export 3D model to DXF file"""
    try:
        from export_docs.cad_export import export_3d_model
        
        filepath = model.GetModelFilepath() or ""
        filename = model.GetModelFilename(False) or "model"
        output_file = os.path.join(filepath, f"{filename}_3d.dxf")
        
        count = export_3d_model(
            model, output_file,
            group_names=group_names if group_names else None,
            group_gap=group_gap,
            projection=projection,
            show_point_labels=show_point_labels,
            show_frame_labels=show_frame_labels,
            label_height=label_height
        )
        
        return {
            "command": "export_3d_model",
            "count": count,
            "file": output_file
        }
    except Exception as e:
        return {"error": str(e)}


def export_csv(model, export_type="frame", selected_only=False):
    """Export to CSV file"""
    try:
        from export_docs.cad_export import export_to_csv
        
        # Generate output filename
        filepath = model.GetModelFilepath() or ""
        filename = model.GetModelFilename(False) or "model"
        suffix = "frames" if export_type == "frame" else "points"
        output_file = os.path.join(filepath, f"{filename}_{suffix}.csv")
        
        count = export_to_csv(model, output_file, export_type=export_type, selected_only=selected_only)
        
        return {
            "command": "export_csv",
            "count": count,
            "file": output_file
        }
    except Exception as e:
        return {"error": str(e)}


# =============================================================================
# AI Agent 功能
# =============================================================================

# 全局 Agent 实例
_sap_agent = None


def load_config():
    """加载配置文件"""
    # 配置文件路径：优先使用 exe 所在目录，否则使用脚本目录
    if getattr(sys, 'frozen', False):
        # 打包后，使用 exe 所在目录
        config_file = os.path.join(os.path.dirname(sys.executable), "config.ini")
    else:
        # 开发模式，使用脚本目录
        config_file = os.path.join(os.path.dirname(__file__), "config.ini")
    
    # 如果配置文件不存在，创建默认配置
    if not os.path.exists(config_file):
        default_config = """[API]
# 通义千问 API Key
# 获取地址: https://dashscope.console.aliyun.com/apiKey
DASHSCOPE_API_KEY = 

# DeepSeek API Key
# 获取地址: https://platform.deepseek.com/api_keys
DEEPSEEK_API_KEY = 

# 智谱 AI API Key
# 获取地址: https://open.bigmodel.cn/
ZHIPU_API_KEY = 

[Agent]
# AI 模型提供商: qwen, deepseek, zhipu
provider = qwen
# 模型名称
model_name = qwen-plus
"""
        try:
            with open(config_file, "w", encoding="utf-8") as f:
                f.write(default_config)
            print(f"[Config] Created default config file: {config_file}")
        except:
            pass
    
    # 读取配置
    try:
        import configparser
        config = configparser.ConfigParser()
        config.read(config_file, encoding="utf-8")
        
        # 读取 provider
        provider = config.get("Agent", "provider", fallback="qwen")
        model_name = config.get("Agent", "model_name", fallback="qwen-plus")
        base_url = config.get("Agent", "base_url", fallback="")
        
        # 根据 provider 读取对应的 API Key
        api_key = ""
        if provider == "qwen":
            api_key = os.environ.get("DASHSCOPE_API_KEY", "")
            if not api_key and config.has_option("API", "DASHSCOPE_API_KEY"):
                api_key = config.get("API", "DASHSCOPE_API_KEY").strip()
        elif provider == "deepseek":
            api_key = os.environ.get("DEEPSEEK_API_KEY", "")
            if not api_key and config.has_option("API", "DEEPSEEK_API_KEY"):
                api_key = config.get("API", "DEEPSEEK_API_KEY").strip()
        elif provider == "zhipu":
            api_key = os.environ.get("ZHIPU_API_KEY", "")
            if not api_key and config.has_option("API", "ZHIPU_API_KEY"):
                api_key = config.get("API", "ZHIPU_API_KEY").strip()
        
        return {
            "api_key": api_key,
            "provider": provider,
            "model_name": model_name,
            "base_url": base_url,
            "config_file": config_file
        }
    except Exception as e:
        print(f"[Config] Failed to load config: {e}")
        return {
            "api_key": os.environ.get("DASHSCOPE_API_KEY", ""),
            "provider": "qwen",
            "model_name": "qwen-plus",
            "base_url": "",
            "config_file": config_file
        }


def get_or_create_agent():
    """获取或创建 AI Agent 实例"""
    global _sap_agent
    
    if _sap_agent is not None:
        return _sap_agent
    
    try:
        # 在 PyInstaller 打包环境中，需要将模块路径添加到 sys.path
        if getattr(sys, 'frozen', False):
            # 打包后的 exe，模块在 _MEIPASS 目录下
            base_path = sys._MEIPASS
            if base_path not in sys.path:
                sys.path.insert(0, base_path)
        
        from langchain_agent import SapAgent, LANGCHAIN_AVAILABLE
        
        if not LANGCHAIN_AVAILABLE:
            return None
        
        # 加载配置
        config = load_config()
        api_key = config["api_key"]
        provider = config["provider"]
        
        if not api_key:
            print(f"[Agent] Warning: API Key not set for {provider}")
            print(f"[Agent] Please edit config file: {config['config_file']}")
            return None
        
        # 设置环境变量（供 LangChain 使用）
        if provider == "qwen":
            os.environ["DASHSCOPE_API_KEY"] = api_key
        elif provider == "deepseek":
            os.environ["DEEPSEEK_API_KEY"] = api_key
        
        _sap_agent = SapAgent(
            provider=provider, 
            model_name=config["model_name"],
            base_url=config.get("base_url", "")
        )
        print(f"[Agent] AI Agent initialized ({provider}/{config['model_name']})")
        return _sap_agent
    except ImportError as e:
        print(f"[Agent] LangChain not available: {e}")
        return None
    except Exception as e:
        print(f"[Agent] Failed to create agent: {e}")
        import traceback
        traceback.print_exc()
        return None


def agent_chat(message: str, stream: bool = False):
    """处理 AI 聊天请求（支持流式）"""
    try:
        agent = get_or_create_agent()
        
        if agent is None:
            config = load_config()
            error_msg = "AI Agent 未初始化"
            if not config["api_key"]:
                error_msg += f"\n\n请配置 API Key:\n1. 打开配置文件: {config['config_file']}\n2. 填写 DASHSCOPE_API_KEY\n3. 重启 SapAgent.exe"
            
            return {
                "command": "agent_chat",
                "success": False,
                "error": error_msg
            }
        
        print(f"[Agent] User: {message[:50]}...")
        
        # 调用 Agent（非流式）
        response = agent.chat(message)
        
        # 提取使用的工具（从历史消息中）
        tools_used = []
        try:
            for msg in agent.chat_history:
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    for tc in msg.tool_calls:
                        if tc.get('name') and tc['name'] not in tools_used:
                            tools_used.append(tc['name'])
        except:
            pass
        
        print(f"[Agent] Response: {response[:100]}...")
        
        return {
            "command": "agent_chat",
            "success": True,
            "response": response,
            "tools_used": tools_used
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "command": "agent_chat",
            "success": False,
            "error": str(e)
        }


async def agent_chat_stream(message: str, ws):
    """处理 AI 聊天请求（真正的流式版本，通过 WebSocket 发送）"""
    import time
    start_time = time.time()
    
    try:
        agent = get_or_create_agent()
        
        if agent is None:
            config = load_config()
            error_msg = "AI Agent 未初始化"
            if not config["api_key"]:
                error_msg += f"\n\n请配置 API Key:\n1. 打开配置文件: {config['config_file']}\n2. 填写 DASHSCOPE_API_KEY\n3. 重启 SapAgent.exe"
            
            await ws.send(json.dumps({
                "command": "agent_chat_stream",
                "success": False,
                "error": error_msg,
                "done": True
            }))
            return
        
        print(f"[Agent] User (stream): {message[:50]}...")
        
        tools_used = []
        full_response = ""
        image_data = None
        chart_data = None
        total_tokens = 0
        elapsed_time = 0
        
        try:
            # 使用异步流式方法
            async for event in agent.chat_stream_async(message):
                event_type = event.get("type")
                
                if event_type == "thinking":
                    await ws.send(json.dumps({
                        "command": "agent_chat_stream",
                        "success": True,
                        "progress": {"stage": "thinking", "message": "正在分析问题..."},
                        "done": False
                    }))
                
                elif event_type == "tool_start":
                    tool_name = event.get("name", "")
                    if tool_name and tool_name not in tools_used:
                        tools_used.append(tool_name)
                    await ws.send(json.dumps({
                        "command": "agent_chat_stream",
                        "success": True,
                        "progress": {"stage": "tool", "message": f"调用工具: {tool_name}"},
                        "done": False
                    }))
                
                elif event_type == "tool_end":
                    tool_name = event.get("name", "")
                    tool_result = event.get("result", "")
                    # 检查工具结果中是否有图片
                    if "__image__" in tool_result:
                        try:
                            result_json = json.loads(tool_result)
                            if "__image__" in result_json:
                                image_data = result_json["__image__"]
                        except:
                            pass
                    await ws.send(json.dumps({
                        "command": "agent_chat_stream",
                        "success": True,
                        "progress": {"stage": "tool_done", "message": f"工具 {tool_name} 执行完成"},
                        "done": False
                    }))
                
                elif event_type == "token":
                    # 流式输出文本
                    token = event.get("content", "")
                    full_response += token
                    await ws.send(json.dumps({
                        "command": "agent_chat_stream",
                        "success": True,
                        "chunk": token,
                        "done": False
                    }))
                
                elif event_type == "confirm":
                    # 需要确认的操作
                    confirm_msg = event.get("message", "")
                    elapsed_time = event.get("elapsed_time", round(time.time() - start_time, 1))
                    total_tokens = event.get("total_tokens", 0)
                    await ws.send(json.dumps({
                        "command": "agent_chat_stream",
                        "success": True,
                        "chunk": confirm_msg,
                        "done": True,
                        "needs_confirm": True,
                        "tools_used": tools_used,
                        "elapsed_time": elapsed_time,
                        "total_tokens": total_tokens
                    }))
                    return
                
                elif event_type == "done":
                    full_response = event.get("content", full_response)
                    tools_used = event.get("tools_used", tools_used)
                    elapsed_time = event.get("elapsed_time", round(time.time() - start_time, 1))
                    total_tokens = event.get("total_tokens", 0)
                    # 从 done 事件中获取图片数据
                    if event.get("image_data"):
                        image_data = event["image_data"]
                
                elif event_type == "error":
                    elapsed_time = event.get("elapsed_time", round(time.time() - start_time, 1))
                    await ws.send(json.dumps({
                        "command": "agent_chat_stream",
                        "success": False,
                        "error": event.get("message", "未知错误"),
                        "done": True,
                        "elapsed_time": elapsed_time
                    }))
                    return
        
        except Exception as stream_error:
            print(f"[Agent] Stream error: {stream_error}, falling back to non-stream")
            # 降级到非流式调用
            await ws.send(json.dumps({
                "command": "agent_chat_stream",
                "success": True,
                "progress": {"stage": "thinking", "message": "正在分析问题..."},
                "done": False
            }))
            
            full_response = agent.chat(message)
            
            # 提取工具和图片数据
            try:
                for msg in agent.chat_history:
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        for tc in msg.tool_calls:
                            if tc.get('name') and tc['name'] not in tools_used:
                                tools_used.append(tc['name'])
                    if hasattr(msg, 'content') and isinstance(msg.content, str):
                        if '__image__' in msg.content:
                            try:
                                tool_result = json.loads(msg.content)
                                if '__image__' in tool_result:
                                    image_data = tool_result['__image__']
                            except:
                                pass
            except:
                pass
            
            # 分块发送响应
            chunk_size = 30
            for i in range(0, len(full_response), chunk_size):
                chunk = full_response[i:i+chunk_size]
                await ws.send(json.dumps({
                    "command": "agent_chat_stream",
                    "success": True,
                    "chunk": chunk,
                    "done": False
                }))
                await asyncio.sleep(0.015)
        
        # 计算最终耗时（如果没有从 agent 获取到）
        if not elapsed_time:
            elapsed_time = round(time.time() - start_time, 1)
        
        # 发送完成信号
        done_data = {
            "command": "agent_chat_stream",
            "success": True,
            "done": True,
            "tools_used": tools_used,
            "elapsed_time": elapsed_time,
            "total_tokens": total_tokens
        }
        if image_data:
            done_data["image_data"] = image_data
        if chart_data:
            done_data["chart_data"] = chart_data
        
        await ws.send(json.dumps(done_data))
        
        print(f"[Agent] Response: {full_response[:100]}...")
        print(f"[Agent] Tools used: {tools_used}")
        print(f"[Agent] Tokens: {total_tokens}, Time: {elapsed_time}s")
        if image_data:
            print(f"[Agent] Image generated (base64)")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        elapsed_time = round(time.time() - start_time, 1)
        await ws.send(json.dumps({
            "command": "agent_chat_stream",
            "success": False,
            "error": str(e),
            "done": True,
            "elapsed_time": elapsed_time
        }))


def agent_clear_history():
    """清空 AI Agent 对话历史"""
    global _sap_agent
    
    try:
        if _sap_agent is not None:
            _sap_agent.clear_history()
        
        return {
            "command": "agent_clear_history",
            "success": True
        }
    except Exception as e:
        return {
            "command": "agent_clear_history",
            "success": False,
            "error": str(e)
        }


def agent_set_model(provider: str):
    """切换 AI 模型提供商"""
    global _sap_agent
    
    try:
        # 配置文件路径
        if getattr(sys, 'frozen', False):
            config_file = os.path.join(os.path.dirname(sys.executable), "config.ini")
        else:
            config_file = os.path.join(os.path.dirname(__file__), "config.ini")
        
        import configparser
        config = configparser.ConfigParser()
        config.read(config_file, encoding="utf-8")
        
        # 更新 provider
        if not config.has_section("Agent"):
            config.add_section("Agent")
        config.set("Agent", "provider", provider)
        
        # 设置默认模型名
        model_map = {
            "qwen": "qwen-plus",
            "deepseek": "deepseek-chat",
            "zhipu": "glm-4-flash"
        }
        config.set("Agent", "model_name", model_map.get(provider, "qwen-plus"))
        
        with open(config_file, "w", encoding="utf-8") as f:
            config.write(f)
        
        # 重置 Agent 实例
        _sap_agent = None
        
        print(f"[Agent] Switched to provider: {provider}")
        
        return {
            "command": "agent_set_model",
            "success": True,
            "provider": provider
        }
    except Exception as e:
        return {
            "command": "agent_set_model",
            "success": False,
            "error": str(e)
        }


def agent_save_config(provider: str, api_key: str, model_name: str = "", base_url: str = ""):
    """保存 AI 配置"""
    global _sap_agent
    
    try:
        # 配置文件路径
        if getattr(sys, 'frozen', False):
            config_file = os.path.join(os.path.dirname(sys.executable), "config.ini")
        else:
            config_file = os.path.join(os.path.dirname(__file__), "config.ini")
        
        import configparser
        config = configparser.ConfigParser()
        config.read(config_file, encoding="utf-8")
        
        # 确保 section 存在
        if not config.has_section("API"):
            config.add_section("API")
        if not config.has_section("Agent"):
            config.add_section("Agent")
        
        # 保存 API Key
        if provider == "qwen":
            config.set("API", "DASHSCOPE_API_KEY", api_key)
            os.environ["DASHSCOPE_API_KEY"] = api_key
        elif provider == "deepseek":
            config.set("API", "DEEPSEEK_API_KEY", api_key)
            os.environ["DEEPSEEK_API_KEY"] = api_key
        elif provider == "zhipu":
            config.set("API", "ZHIPU_API_KEY", api_key)
            os.environ["ZHIPU_API_KEY"] = api_key
        
        # 保存 provider 和 model
        config.set("Agent", "provider", provider)
        if model_name:
            config.set("Agent", "model_name", model_name)
        if base_url:
            config.set("Agent", "base_url", base_url)
        
        with open(config_file, "w", encoding="utf-8") as f:
            config.write(f)
        
        # 重置 Agent 实例以使用新配置
        _sap_agent = None
        
        print(f"[Agent] Config saved: provider={provider}, model={model_name}")
        
        return {
            "command": "agent_save_config",
            "success": True
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "command": "agent_save_config",
            "success": False,
            "error": str(e)
        }


def agent_test_connection(provider: str, api_key: str, model_name: str = "", base_url: str = ""):
    """测试 AI 连接"""
    try:
        from langchain_openai import ChatOpenAI
        
        # 根据 provider 设置默认值
        provider_defaults = {
            "qwen": ("qwen-plus", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
            "deepseek": ("deepseek-chat", "https://api.deepseek.com/v1"),
            "zhipu": ("glm-4-flash", "https://open.bigmodel.cn/api/paas/v4"),
            "openai": ("gpt-4o-mini", "https://api.openai.com/v1"),
        }
        
        if provider not in provider_defaults:
            return {
                "command": "agent_test_connection",
                "success": False,
                "error": f"不支持的提供商: {provider}"
            }
        
        default_model, default_url = provider_defaults[provider]
        
        llm = ChatOpenAI(
            model=model_name or default_model,
            api_key=api_key,
            base_url=base_url or default_url
        )
        
        # 简单测试
        response = llm.invoke("你好")
        
        return {
            "command": "agent_test_connection",
            "success": True,
            "message": "连接成功"
        }
    except Exception as e:
        return {
            "command": "agent_test_connection",
            "success": False,
            "error": str(e)
        }


def classify_by_stress_ratio(model, group_names):
    """Classify frames by stress ratio into groups"""
    try:
        from examples.steel_design_tools import classify_frame_by_stress_ratio
        
        result = classify_frame_by_stress_ratio(model, group_names)
        
        # Convert to response format
        data = []
        for group_name, frames in result.items():
            data.append({
                "group": group_name,
                "count": len(frames)
            })
        
        return {
            "command": "classify_stress_ratio",
            "data": data
        }
    except Exception as e:
        return {"error": str(e)}


def execute_command(model, command: str, params: dict):
    """Execute a command and return result"""
    if command == "get_model_info":
        return get_model_info(model)
    elif command == "get_point_coord":
        return get_point_coord(model, params.get("point_name", ""))
    elif command == "get_frame_info":
        return get_frame_info(model, params.get("frame_name", ""))
    elif command == "get_model_geometry":
        return get_model_geometry(model)
    elif command == "get_group_geometry":
        return get_group_geometry(model, params.get("group_name", ""))
    # AI Agent commands
    elif command == "agent_chat":
        return agent_chat(params.get("message", ""))
    elif command == "agent_chat_stream":
        # 流式命令需要特殊处理，返回标记
        return {"stream": True, "message": params.get("message", "")}
    elif command == "agent_clear_history":
        return agent_clear_history()
    elif command == "agent_set_model":
        return agent_set_model(params.get("provider", "qwen"))
    elif command == "agent_save_config":
        return agent_save_config(
            params.get("provider", "qwen"),
            params.get("api_key", ""),
            params.get("model_name", ""),
            params.get("base_url", "")
        )
    elif command == "agent_test_connection":
        return agent_test_connection(
            params.get("provider", "qwen"),
            params.get("api_key", ""),
            params.get("model_name", ""),
            params.get("base_url", "")
        )
    # Post-processing commands
    elif command == "get_steel_usage":
        return get_steel_usage(model, params.get("group_by", "section"))
    elif command == "get_steel_usage_detail":
        return get_steel_usage_detail(model, params.get("group_name", ""), params.get("save_history", True))
    elif command == "get_cable_usage":
        return get_cable_usage(model, params.get("group_by", "section"))
    elif command == "get_stress_ratios":
        return get_stress_ratios(model, params.get("group_name", ""))
    elif command == "get_joint_displacements":
        return get_joint_displacements(model, params.get("load_case", ""))
    elif command == "get_base_reactions":
        return get_base_reactions(model, params.get("load_case", ""))
    elif command == "get_frame_forces":
        return get_frame_forces(model, params.get("frame_name", ""), params.get("load_case", ""))
    elif command == "get_load_cases":
        return get_load_cases(model)
    elif command == "get_analysis_status":
        return get_analysis_status(model)
    elif command == "get_groups":
        return get_groups(model)
    elif command == "get_frame_sections":
        return get_frame_sections(model)
    # CAD export commands
    elif command == "export_frame_table":
        return export_frame_table_dxf(
            model, 
            params.get("selected_only", False),
            params.get("rows_per_column", 90),
            params.get("row_height", 800),
            params.get("text_height", 350),
            params.get("column_gap", 2500),
            params.get("group_gap", 40000),
            params.get("tables_per_group", 5)
        )
    elif command == "export_point_table":
        return export_point_table_dxf(
            model, 
            params.get("selected_only", False),
            params.get("rows_per_column", 90),
            params.get("row_height", 800),
            params.get("text_height", 350),
            params.get("column_gap", 2500),
            params.get("group_gap", 40000),
            params.get("tables_per_group", 4)
        )
    elif command == "export_3d_model":
        return export_3d_model_dxf(
            model, 
            params.get("group_names"),
            params.get("projection", "iso"),
            params.get("group_gap", 400000),
            params.get("show_point_labels", False),
            params.get("show_frame_labels", False),
            params.get("label_height", 350)
        )
    elif command == "export_csv":
        return export_csv(model, params.get("export_type", "frame"), params.get("selected_only", False))
    elif command == "classify_stress_ratio":
        return classify_by_stress_ratio(model, params.get("group_names", []))
    elif command == "replace_design_section":
        return replace_design_section(model, params.get("group_names", []), params.get("run_analysis", False))
    elif command == "replace_frame_section":
        return replace_frame_section(model, params.get("frame_name", ""), params.get("section_name", ""))
    elif command == "set_frame_design_section":
        return set_frame_design_section(model, params.get("frame_name", ""), params.get("section_name", ""))
    elif command == "set_batch_design_section":
        return set_batch_design_section(model, params.get("frame_names", []), params.get("section_name", ""))
    elif command == "run_steel_design":
        return run_steel_design(model)
    elif command == "run_analysis":
        return run_analysis(model)
    elif command == "get_model_status":
        return get_model_status(model)
    else:
        return {"error": f"Unknown command: {command}"}


async def run_agent(server_url: str, token: str):
    """Main agent loop"""
    import websockets
    
    url = f"{server_url}{token}/"
    print(f"Connecting to: {url}")
    
    while True:
        try:
            # 增加超时时间，避免长时间操作导致连接断开
            async with websockets.connect(url, ping_interval=None, ping_timeout=None, close_timeout=600) as ws:
                print("Connected! Waiting for commands...")
                print("-" * 40)
                
                # Send initial model info
                model_info = get_model_info(model)
                await ws.send(json.dumps(model_info))
                
                async for message in ws:
                    try:
                        request = json.loads(message)
                        command = request.get("command", "")
                        params = request.get("params", {})
                        request_id = request.get("request_id", "")
                        
                        print(f"Command: {command}")
                        
                        # 特殊处理流式命令
                        if command == "agent_chat_stream":
                            await agent_chat_stream(params.get("message", ""), ws)
                            continue
                        
                        result = execute_command(model, command, params)
                        result["request_id"] = request_id
                        
                        await ws.send(json.dumps(result))
                        
                    except json.JSONDecodeError:
                        print(f"Invalid message: {message}")
                    except Exception as e:
                        print(f"Error: {e}")
                        await ws.send(json.dumps({
                            "error": str(e),
                            "request_id": request.get("request_id", "")
                        }))
                        
        except Exception as e:
            print(f"Connection lost: {e}")
            print("Reconnecting in 3 seconds...")
            await asyncio.sleep(3)


if __name__ == "__main__":
    print("=" * 50)
    print("  SAP2000 Web Agent v1.0")
    print("  Connect SAP2000 to www.spancore.cn")
    print("=" * 50)
    print()
    
    # 注册自定义协议（首次运行时）
    register_url_protocol()
    
    # Connect to SAP2000
    model = get_sap_model()
    if not model:
        print()
        input("Press Enter to exit...")
        sys.exit(1)
    
    print()
    
    # Determine server (dev or production)
    use_dev = "--dev" in sys.argv or "-d" in sys.argv
    server = DEV_SERVER if use_dev else DEFAULT_SERVER
    token = DEFAULT_TOKEN
    
    # Parse custom server from args
    for i, arg in enumerate(sys.argv):
        if arg == "--server" and i + 1 < len(sys.argv):
            server = sys.argv[i + 1]
        if arg == "--token" and i + 1 < len(sys.argv):
            token = sys.argv[i + 1]
    
    # Run
    try:
        # Python 3.7+ use asyncio.run(), older versions use loop
        if sys.version_info >= (3, 7):
            asyncio.run(run_agent(server, token))
        else:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(run_agent(server, token))
    except KeyboardInterrupt:
        print("\nStopped by user")
    except Exception as e:
        print(f"\nError: {e}")
        input("Press Enter to exit...")
