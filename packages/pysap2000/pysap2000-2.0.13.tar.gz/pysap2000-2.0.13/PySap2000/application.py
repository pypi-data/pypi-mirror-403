# -*- coding: utf-8 -*-
"""
application.py - SAP2000 Application 连接管理器
参考 dlubal.api 设计模式

Usage:
    from PySap2000 import Application
    from PySap2000.structure_core import Point, Member
    
    with Application() as app:
        # 创建节点
        app.create_object(Point(no=1, x=0, y=0, z=0))
        app.create_object(Point(no=2, x=10, y=0, z=0))
        
        # 创建杆件
        app.create_object(Member(no=1, start_point=1, end_point=2, section="W14X30"))
        
        # 运行分析
        app.calculate()
        
        # 获取结果
        results = app.get_results()
"""

import comtypes.client
from typing import Optional, List, Union, TypeVar, Type
from PySap2000.exceptions import ConnectionError, ObjectError


T = TypeVar('T')


class Application:
    """
    SAP2000 应用程序连接管理器
    
    参考 dlubal.api.rfem.Application 设计:
    - Context Manager 管理连接生命周期
    - 统一的 CRUD 接口
    - 批量操作支持
    """
    
    def __init__(self, attach_to_instance: bool = True, program_path: str = ""):
        """
        初始化 SAP2000 连接
        
        Args:
            attach_to_instance: True 连接已运行的实例，False 启动新实例
            program_path: SAP2000 程序路径（启动新实例时使用）
        """
        self._sap_object = None
        self._model = None
        self._in_modification = False
        
        if attach_to_instance:
            self._attach_to_instance()
        else:
            self._start_application(program_path)
    
    def _attach_to_instance(self):
        """连接到已运行的 SAP2000 实例"""
        try:
            self._sap_object = comtypes.client.GetActiveObject('CSI.SAP2000.API.SapObject')
            self._model = self._sap_object.SapModel
            self._print_connection_info()
        except Exception as e:
            raise ConnectionError(f"Cannot connect to SAP2000, please make sure it is running: {e}")
    
    def _start_application(self, program_path: str = ""):
        """启动新的 SAP2000 实例"""
        try:
            helper = comtypes.client.CreateObject('SAP2000v1.Helper')
            helper = helper.QueryInterface(comtypes.gen.SAP2000v1.cHelper)
            if program_path:
                self._sap_object = helper.CreateObject(program_path)
            else:
                self._sap_object = helper.CreateObjectProgID('CSI.SAP2000.API.SapObject')
            self._sap_object.ApplicationStart()
            self._model = self._sap_object.SapModel
            self._print_connection_info()
        except Exception as e:
            raise ConnectionError(f"Cannot start SAP2000: {e}")
    
    def _print_connection_info(self):
        """打印连接信息"""
        version_info = self._model.GetVersion()
        version = version_info[0] if isinstance(version_info, (list, tuple)) else ""
        filename = self._model.GetModelFilename(False) or "Untitled"
        print(f"Connected to SAP2000 v{version} | {filename}")
    
    def __enter__(self):
        """Context Manager 入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context Manager 退出，确保结束修改模式"""
        if self._in_modification:
            self.finish_modification()
        return False
    
    @property
    def model(self):
        """获取原始 SapModel 对象（用于高级操作或兼容旧代码）"""
        return self._model
    
    # ==================== 修改模式管理 ====================
    
    def begin_modification(self):
        """
        开始批量修改模式
        禁用视图刷新以提升性能
        """
        if not self._in_modification:
            self._model.View.RefreshView(0, False)
            self._in_modification = True
    
    def finish_modification(self):
        """
        结束批量修改模式
        刷新视图
        """
        if self._in_modification:
            self._model.View.RefreshView(0, True)
            self._in_modification = False
    
    # ==================== 统一 CRUD 接口 ====================
    
    def create_object(self, obj) -> int:
        """
        创建单个对象
        
        Args:
            obj: 要创建的对象 (Point, Member, Material, Section 等)
            
        Returns:
            0 表示成功
            
        Example:
            app.create_object(Point(no=1, x=0, y=0, z=0))
            app.create_object(Member(no=1, start_point=1, end_point=2))
        """
        if hasattr(obj, '_create'):
            return obj._create(self._model)
        raise ObjectError(f"对象类型 {type(obj).__name__} 不支持 create 操作")
    
    def create_object_list(self, objs: List) -> int:
        """
        批量创建对象
        
        Args:
            objs: 对象列表
            
        Returns:
            0 表示成功
        """
        self.begin_modification()
        try:
            for obj in objs:
                self.create_object(obj)
        finally:
            self.finish_modification()
        return 0
    
    def get_object(self, obj: T) -> T:
        """
        获取单个对象
        
        Args:
            obj: 带有 no 属性的对象，用于指定要获取的对象编号
            
        Returns:
            填充了数据的对象
            
        Example:
            node = app.get_object(Node(no=1))
            print(node.x, node.y, node.z)
        """
        if hasattr(obj, '_get'):
            return obj._get(self._model)
        raise ObjectError(f"对象类型 {type(obj).__name__} 不支持 get 操作")
    
    def get_object_list(self, obj_type: Type[T], nos: List[Union[int, str]] = None) -> List[T]:
        """
        批量获取对象
        
        Args:
            obj_type: 对象类型
            nos: 对象编号列表，None 表示获取所有
            
        Returns:
            对象列表
        """
        if hasattr(obj_type, '_get_all'):
            return obj_type._get_all(self._model, nos)
        raise ObjectError(f"对象类型 {obj_type.__name__} 不支持 get_all 操作")
    
    def update_object(self, obj) -> int:
        """
        更新单个对象
        
        Args:
            obj: 要更新的对象
            
        Returns:
            0 表示成功
        """
        if hasattr(obj, '_update'):
            return obj._update(self._model)
        raise ObjectError(f"对象类型 {type(obj).__name__} 不支持 update 操作")
    
    def delete_object(self, obj) -> int:
        """
        删除单个对象
        
        Args:
            obj: 要删除的对象（需要 no 属性）
            
        Returns:
            0 表示成功
        """
        if hasattr(obj, '_delete'):
            return obj._delete(self._model)
        raise ObjectError(f"对象类型 {type(obj).__name__} 不支持 delete 操作")
    
    # ==================== 模型操作 ====================
    
    def new_model(self, units: int = 6) -> int:
        """
        创建新模型
        
        Args:
            units: 单位制 (6=kN_m_C, 9=N_mm_C, 10=kN_mm_C)
            
        Returns:
            0 表示成功
        """
        return self._model.InitializeNewModel(units)
    
    def open_model(self, path: str) -> int:
        """
        打开模型文件
        
        Args:
            path: 模型文件路径
            
        Returns:
            0 表示成功
        """
        return self._model.File.OpenFile(path)
    
    def save_model(self, path: str = "") -> int:
        """
        保存模型
        
        Args:
            path: 保存路径，空字符串表示保存到当前位置
            
        Returns:
            0 表示成功
        """
        if path:
            return self._model.File.Save(path)
        return self._model.File.Save()
    
    def close_model(self, save_changes: bool = False) -> int:
        """
        关闭模型
        
        Args:
            save_changes: 是否保存更改
        """
        # SAP2000 没有直接的 close model，这里用 InitializeNewModel 替代
        return 0
    
    # ==================== 分析操作 ====================
    
    def calculate(self) -> int:
        """
        运行分析
        
        Returns:
            0 表示成功
        """
        # 设置分析模型
        self._model.Analyze.SetRunCaseFlag("", True, True)
        # 运行分析
        return self._model.Analyze.RunAnalysis()
    
    def delete_results(self) -> int:
        """
        删除分析结果
        
        Returns:
            0 表示成功
        """
        return self._model.Analyze.DeleteResults("", True)
    
    # ==================== 结果获取 ====================
    
    def get_results(self, result_type: str, load_case: str = "", load_combo: str = ""):
        """
        获取分析结果
        
        Args:
            result_type: 结果类型 ('displacement', 'reaction', 'member_force' 等)
            load_case: 荷载工况名称
            load_combo: 荷载组合名称
            
        Returns:
            结果数据
        """
        # 设置输出工况
        self._model.Results.Setup.DeselectAllCasesAndCombosForOutput()
        if load_case:
            self._model.Results.Setup.SetCaseSelectedForOutput(load_case)
        if load_combo:
            self._model.Results.Setup.SetComboSelectedForOutput(load_combo)
        
        # 根据类型返回结果
        # 具体实现在 results 模块中
        return None
    
    # ==================== 辅助方法 ====================
    
    def set_units(self, units: int) -> int:
        """
        设置单位制
        
        Args:
            units: 单位制代码
                1 = lb_in_F
                2 = lb_ft_F
                3 = kip_in_F
                4 = kip_ft_F
                5 = kN_mm_C
                6 = kN_m_C
                7 = kgf_mm_C
                8 = kgf_m_C
                9 = N_mm_C
                10 = N_m_C
                11 = Ton_mm_C
                12 = Ton_m_C
                13 = kN_cm_C
                14 = kgf_cm_C
                15 = N_cm_C
                16 = Ton_cm_C
        """
        return self._model.SetPresentUnits(units)
    
    # 单位代码映射表
    UNIT_NAMES = {
        1: "lb_in_F",
        2: "lb_ft_F",
        3: "kip_in_F",
        4: "kip_ft_F",
        5: "kN_mm_C",
        6: "kN_m_C",
        7: "kgf_mm_C",
        8: "kgf_m_C",
        9: "N_mm_C",
        10: "N_m_C",
        11: "Ton_mm_C",
        12: "Ton_m_C",
        13: "kN_cm_C",
        14: "kgf_cm_C",
        15: "N_cm_C",
        16: "Ton_cm_C",
    }
    
    def get_units(self) -> int:
        """获取当前单位制代码"""
        return self._model.GetPresentUnits()
    
    def get_units_name(self) -> str:
        """
        获取当前单位制名称
        
        Returns:
            单位名称如 "kN_m_C", "N_mm_C" 等
        """
        code = self.get_units()
        return self.UNIT_NAMES.get(code, "Unknown")
    
    def get_database_units(self) -> int:
        """
        获取数据库单位制
        
        API: GetDatabaseUnits() -> eUnits
        
        注意: 所有数据在模型内部以数据库单位存储，
        需要时转换为当前显示单位
        
        Returns:
            单位制代码 (同 set_units)
        """
        return self._model.GetDatabaseUnits()
    
    def get_database_units_name(self) -> str:
        """
        获取数据库单位制名称
        
        Returns:
            单位名称如 "kN_m_C", "N_mm_C" 等
        """
        code = self.get_database_units()
        return self.UNIT_NAMES.get(code, "Unknown")
    
    def refresh_view(self):
        """刷新视图"""
        self._model.View.RefreshView(0, True)
    
    # ==================== 模型信息 ====================
    
    def get_model_filename(self, include_path: bool = True) -> str:
        """
        获取模型文件名
        
        API: GetModelFilename(IncludePath) -> String
        
        Args:
            include_path: 是否包含完整路径
            
        Returns:
            模型文件名
        """
        return self._model.GetModelFilename(include_path)
    
    def get_model_filepath(self) -> str:
        """
        获取模型文件路径
        
        API: GetModelFilepath() -> String
        
        Returns:
            模型文件所在目录路径
        """
        return self._model.GetModelFilepath()
    
    def get_model_is_locked(self) -> bool:
        """
        获取模型锁定状态
        
        API: GetModelIsLocked() -> Boolean
        
        注意: 模型锁定时，大部分定义和分配无法修改
        
        Returns:
            True 表示已锁定
        """
        return self._model.GetModelIsLocked()
    
    def set_model_is_locked(self, lock_it: bool) -> int:
        """
        设置模型锁定状态
        
        API: SetModelIsLocked(LockIt) -> Long
        
        Args:
            lock_it: True 锁定模型，False 解锁模型
            
        Returns:
            0 表示成功
        """
        return self._model.SetModelIsLocked(lock_it)
    
    # ==================== 合并容差 ====================
    
    def get_merge_tol(self) -> float:
        """
        获取自动合并容差
        
        API: GetMergeTol(MergeTol) -> Long
        
        Returns:
            合并容差 [L]
        """
        result = self._model.GetMergeTol()
        if isinstance(result, tuple):
            return result[0]
        return result
    
    def set_merge_tol(self, merge_tol: float) -> int:
        """
        设置自动合并容差
        
        API: SetMergeTol(MergeTol) -> Long
        
        Args:
            merge_tol: 合并容差 [L]
            
        Returns:
            0 表示成功
        """
        return self._model.SetMergeTol(merge_tol)
    
    # ==================== 坐标系 ====================
    
    def get_present_coord_system(self) -> str:
        """
        获取当前坐标系名称
        
        API: GetPresentCoordSystem() -> String
        
        Returns:
            坐标系名称
        """
        return self._model.GetPresentCoordSystem()
    
    def set_present_coord_system(self, csys: str) -> int:
        """
        设置当前坐标系
        
        API: SetPresentCoordSystem(CSys) -> Long
        
        Args:
            csys: 坐标系名称
            
        Returns:
            0 表示成功
        """
        return self._model.SetPresentCoordSystem(csys)
    
    # ==================== 项目信息 ====================
    
    def get_project_info(self) -> dict:
        """
        获取项目信息
        
        API: GetProjectInfo(NumberItems, Item[], Data[]) -> Long
        
        Returns:
            项目信息字典 {item_name: data}
        """
        result = self._model.GetProjectInfo()
        if isinstance(result, tuple) and len(result) >= 3:
            num_items = result[0]
            items = result[1]
            data = result[2]
            if num_items > 0 and items and data:
                return dict(zip(items, data))
        return {}
    
    def set_project_info(self, item: str, data: str) -> int:
        """
        设置项目信息
        
        API: SetProjectInfo(Item, Data) -> Long
        
        Args:
            item: 项目信息项名称 (如 "Company Name", "Project Name")
            data: 项目信息数据
            
        Returns:
            0 表示成功
        """
        return self._model.SetProjectInfo(item, data)
    
    # ==================== 用户注释 ====================
    
    def get_user_comment(self) -> str:
        """
        获取用户注释和日志
        
        API: GetUserComment(Comment) -> Long
        
        Returns:
            用户注释内容
        """
        result = self._model.GetUserComment()
        if isinstance(result, tuple):
            return result[0]
        return ""
    
    def set_user_comment(
        self, 
        comment: str, 
        num_lines: int = 1, 
        replace: bool = False
    ) -> int:
        """
        设置用户注释
        
        API: SetUserComment(Comment, NumLines, Replace) -> Long
        
        Args:
            comment: 注释内容
            num_lines: 在注释前添加的空行数 (replace=True 时忽略)
            replace: True 替换所有现有注释，False 追加
            
        Returns:
            0 表示成功
        """
        return self._model.SetUserComment(comment, num_lines, replace)
    
    # ==================== 版本信息 ====================
    
    def get_version(self) -> tuple:
        """
        获取 SAP2000 版本信息
        
        API: GetVersion(Version, MyVersionNumber) -> Long
        
        Returns:
            (版本名称, 版本号) 如 ("26.3.0", 26.3)
        """
        result = self._model.GetVersion()
        # comtypes 返回 [version, version_number, ret]
        if isinstance(result, (list, tuple)) and len(result) >= 2:
            return (result[0], result[1])
        return ("", 0.0)
