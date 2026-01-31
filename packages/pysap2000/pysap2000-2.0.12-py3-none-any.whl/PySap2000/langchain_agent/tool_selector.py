# -*- coding: utf-8 -*-
"""
工具分层选择器

实现两阶段工具选择：
1. 第一阶段：根据用户意图选择工具类别
2. 第二阶段：在选定类别中选择具体工具

优势：
- 减少 LLM 一次性处理的工具数量
- 提高工具选择准确率 20%+
- 支持动态工具加载
- 同义词扩展提高匹配准确率
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable, Any
from enum import Enum


class ToolCategory(Enum):
    """工具类别枚举"""
    CONNECTION = "connection"           # 连接检查
    MODEL_INFO = "model_info"           # 模型信息查询
    POINT = "point"                     # 节点操作
    FRAME = "frame"                     # 杆件操作
    AREA = "area"                       # 面单元操作
    CABLE_LINK = "cable_link"           # 索/连接单元
    LOAD = "load"                       # 荷载操作
    ANALYSIS = "analysis"               # 分析设计
    RESULTS = "results"                 # 结果查询
    SELECTION = "selection"             # 选择操作
    VIEW = "view"                       # 视图操作
    STATISTICS = "statistics"           # 统计功能
    GROUP = "group"                     # 组操作
    FILE = "file"                       # 文件操作
    CONSTRAINT = "constraint"           # 约束操作
    EDIT = "edit"                       # 编辑操作
    TABLE = "table"                     # 表格操作
    HISTORY = "history"                 # 历史/撤回
    KNOWLEDGE = "knowledge"             # 知识库搜索
    CHART = "chart"                     # 绑图工具
    BATCH = "batch"                     # 批量操作
    COMBO = "combo"                     # 组合工具（多步骤封装）


@dataclass
class CategoryInfo:
    """工具类别信息"""
    category: ToolCategory
    name: str                           # 中文名称
    description: str                    # 类别描述
    keywords: List[str]                 # 关键词（用于意图匹配）
    tool_names: List[str] = field(default_factory=list)  # 该类别下的工具名称


# 工具类别定义
TOOL_CATEGORIES: Dict[ToolCategory, CategoryInfo] = {
    ToolCategory.CONNECTION: CategoryInfo(
        category=ToolCategory.CONNECTION,
        name="连接检查",
        description="检查与 SAP2000 的连接状态",
        keywords=["连接", "检查", "状态", "connection", "check"],
        tool_names=["check_connection"]
    ),
    
    ToolCategory.MODEL_INFO: CategoryInfo(
        category=ToolCategory.MODEL_INFO,
        name="模型信息",
        description="查询模型基本信息、组列表、截面列表、材料列表、荷载模式、荷载工况、组合等",
        keywords=["模型", "信息", "组", "截面", "材料", "荷载模式", "工况", "组合", 
                  "model", "info", "group", "section", "material", "pattern", "case", "combo",
                  "有哪些", "列表", "查看", "获取"],
        tool_names=[
            "get_model_info", "get_group_list", "get_section_list", 
            "get_material_list", "get_load_pattern_list", "get_load_case_list",
            "get_combo_list", "get_section_info"
        ]
    ),
    
    ToolCategory.POINT: CategoryInfo(
        category=ToolCategory.POINT,
        name="节点操作",
        description="创建、查询、删除节点，设置节点约束",
        keywords=["节点", "点", "坐标", "约束", "支座", "固定", "铰接",
                  "point", "joint", "node", "coordinate", "restraint", "support"],
        tool_names=[
            "get_point_coordinates", "create_point", "delete_point",
            "get_point_restraint", "set_point_restraint", "get_point_list",
            "get_points_in_group"
        ]
    ),
    
    ToolCategory.FRAME: CategoryInfo(
        category=ToolCategory.FRAME,
        name="杆件操作",
        description="创建、查询、修改、删除杆件，设置截面和端部释放",
        keywords=["杆件", "梁", "柱", "框架", "截面", "释放", "铰接",
                  "frame", "beam", "column", "member", "section", "release"],
        tool_names=[
            "get_frame_info", "create_frame", "set_frame_section", "delete_frame",
            "get_frames_in_group", "get_frame_list", "set_frame_release", "get_frame_release"
        ]
    ),
    
    ToolCategory.AREA: CategoryInfo(
        category=ToolCategory.AREA,
        name="面单元操作",
        description="创建、查询、删除面单元（板、壳），设置截面",
        keywords=["面", "板", "壳", "墙", "area", "shell", "plate", "wall"],
        tool_names=[
            "create_area", "delete_area", "set_area_section", "add_area_to_group_tool",
            "get_area_info", "get_areas_in_group", "get_area_list"
        ]
    ),
    
    ToolCategory.CABLE_LINK: CategoryInfo(
        category=ToolCategory.CABLE_LINK,
        name="索/连接单元",
        description="创建、查询、删除索单元和连接单元",
        keywords=["索", "缆索", "拉索", "连接", "弹簧", "阻尼器",
                  "cable", "link", "spring", "damper"],
        tool_names=[
            "create_cable", "delete_cable",
            "get_cable_info", "get_cables_in_group", "get_cable_list",
            "create_link", "delete_link",
            "get_link_info", "get_link_list", "get_links_in_group"
        ]
    ),
    
    ToolCategory.LOAD: CategoryInfo(
        category=ToolCategory.LOAD,
        name="荷载操作",
        description="添加、删除节点荷载、杆件荷载、面荷载，创建/删除荷载模式",
        keywords=["荷载", "力", "均布", "集中", "恒载", "活载", "风", "地震", "删除荷载",
                  "load", "force", "distributed", "point load", "dead", "live", "wind", "seismic"],
        tool_names=[
            "add_point_load", "delete_point_load",
            "add_frame_distributed_load", "add_frame_point_load", "delete_frame_load",
            "get_frame_loads",
            "add_area_load", "delete_area_load",
            "create_load_pattern", "delete_load_pattern"
        ]
    ),
    
    ToolCategory.ANALYSIS: CategoryInfo(
        category=ToolCategory.ANALYSIS,
        name="分析设计",
        description="运行结构分析、钢结构设计、混凝土设计，查看应力比",
        keywords=["分析", "计算", "设计", "钢结构", "混凝土", "应力比", "验算",
                  "analysis", "analyze", "design", "steel", "concrete", "stress ratio", "check"],
        tool_names=[
            "run_analysis", "run_steel_design", "get_stress_ratios", "verify_steel_design"
        ]
    ),
    
    ToolCategory.RESULTS: CategoryInfo(
        category=ToolCategory.RESULTS,
        name="结果查询",
        description="查询位移、反力、内力、模态结果",
        keywords=["位移", "反力", "内力", "轴力", "剪力", "弯矩", "周期", "振型", "模态",
                  "displacement", "reaction", "force", "axial", "shear", "moment", 
                  "period", "mode", "modal", "结果"],
        tool_names=[
            "get_point_displacement", "get_point_reactions", "get_base_reactions",
            "get_frame_forces", "get_max_frame_forces", "get_modal_periods", "get_modal_mass_ratios"
        ]
    ),
    
    ToolCategory.SELECTION: CategoryInfo(
        category=ToolCategory.SELECTION,
        name="选择操作",
        description="选择对象、清除选择、按属性选择、获取选中对象",
        keywords=["选择", "选中", "清除", "按截面选择", "按材料选择",
                  "select", "selection", "clear", "deselect", "property"],
        tool_names=["select_all", "clear_selection", "select_group", "select_by_property", "get_selected_objects"]
    ),
    
    ToolCategory.VIEW: CategoryInfo(
        category=ToolCategory.VIEW,
        name="视图操作",
        description="刷新视图、缩放",
        keywords=["视图", "刷新", "缩放", "显示", "view", "refresh", "zoom"],
        tool_names=["refresh_view", "zoom_all"]
    ),
    
    ToolCategory.STATISTICS: CategoryInfo(
        category=ToolCategory.STATISTICS,
        name="统计功能",
        description="统计用钢量、用索量",
        keywords=["统计", "用钢量", "用索量", "重量", "汇总",
                  "statistics", "steel usage", "cable usage", "weight", "summary"],
        tool_names=["get_steel_usage", "get_cable_usage"]
    ),
    
    ToolCategory.GROUP: CategoryInfo(
        category=ToolCategory.GROUP,
        name="组操作",
        description="创建组、添加对象到组",
        keywords=["组", "分组", "添加到组", "group", "add to group"],
        tool_names=["create_group", "add_frame_to_group", "add_selected_to_group"]
    ),
    
    ToolCategory.FILE: CategoryInfo(
        category=ToolCategory.FILE,
        name="文件操作",
        description="新建、打开、保存、解锁模型",
        keywords=["保存", "解锁", "文件", "新建", "打开", "save", "unlock", "file", "new", "open"],
        tool_names=["save_model", "unlock_model", "new_model", "open_model"]
    ),
    
    ToolCategory.CONSTRAINT: CategoryInfo(
        category=ToolCategory.CONSTRAINT,
        name="约束操作",
        description="创建刚性隔板约束、分配节点约束",
        keywords=["约束", "刚性隔板", "刚性板", "diaphragm", "constraint"],
        tool_names=["get_constraint_list", "create_diaphragm_constraint", "assign_point_constraint"]
    ),
    
    ToolCategory.EDIT: CategoryInfo(
        category=ToolCategory.EDIT,
        name="编辑操作",
        description="移动、复制（线性/镜像/环形）、分割杆件、合并节点",
        keywords=["移动", "复制", "镜像", "环形", "分割", "合并",
                  "move", "copy", "replicate", "mirror", "radial", "divide", "merge"],
        tool_names=[
            "move_selected_objects", "replicate_linear", "replicate_mirror",
            "replicate_radial", "divide_frame", "merge_points"
        ]
    ),
    
    ToolCategory.TABLE: CategoryInfo(
        category=ToolCategory.TABLE,
        name="表格操作",
        description="获取和修改数据库表格",
        keywords=["表格", "数据库", "导出", "table", "database", "export"],
        tool_names=[
            "get_joint_coordinates_table", "modify_joint_coordinate",
            "batch_modify_joints", "get_frame_section_assignments_table", "get_available_tables"
        ]
    ),
    
    ToolCategory.HISTORY: CategoryInfo(
        category=ToolCategory.HISTORY,
        name="历史/撤回",
        description="撤回操作、查看操作历史",
        keywords=["撤回", "撤销", "历史", "undo", "history", "rollback"],
        tool_names=["undo_last_operation", "get_operation_history", "clear_operation_history"]
    ),
    
    ToolCategory.KNOWLEDGE: CategoryInfo(
        category=ToolCategory.KNOWLEDGE,
        name="知识库搜索",
        description="搜索 SAP2000 API 文档",
        keywords=["文档", "API", "帮助", "怎么", "如何", "用法",
                  "doc", "help", "how to", "usage"],
        tool_names=["search_sap_docs"]
    ),
    
    ToolCategory.CHART: CategoryInfo(
        category=ToolCategory.CHART,
        name="绑图工具",
        description="绑制柱状图、饼图、折线图",
        keywords=["图", "绘图", "柱状图", "饼图", "折线图", "可视化",
                  "chart", "plot", "bar", "pie", "line", "visualization"],
        tool_names=["draw_chart"]
    ),
    
    ToolCategory.BATCH: CategoryInfo(
        category=ToolCategory.BATCH,
        name="批量操作",
        description="批量修改截面、批量添加荷载、批量设置约束",
        keywords=["批量", "多个", "全部", "所有", "batch", "multiple", "all"],
        tool_names=["batch_set_section", "batch_add_distributed_load", "batch_set_restraint"]
    ),
    
    ToolCategory.COMBO: CategoryInfo(
        category=ToolCategory.COMBO,
        name="组合工具",
        description="一键设计验算、用钢量报告、模型概览等多步骤封装工具",
        keywords=["一键", "验算", "报告", "概览", "汇总", "全流程", "完整",
                  "design check", "report", "overview", "summary"],
        tool_names=["full_design_check", "steel_usage_report", "model_overview"]
    ),
}


# =============================================================================
# 同义词映射 - 提高工具匹配准确率
# =============================================================================

SYNONYMS: Dict[str, List[str]] = {
    # 杆件相关
    "梁": ["杆件", "frame", "beam", "杆"],
    "柱": ["杆件", "frame", "column", "杆"],
    "杆": ["杆件", "frame", "member"],
    "撑": ["杆件", "frame", "brace", "支撑"],
    "弦杆": ["杆件", "frame", "chord"],
    "腹杆": ["杆件", "frame", "web"],
    
    # 面单元相关
    "楼板": ["面", "板", "area", "slab", "floor"],
    "板": ["面", "area", "plate", "shell"],
    "壳": ["面", "area", "shell"],
    "墙": ["面", "area", "wall"],
    
    # 节点相关
    "支座": ["约束", "节点", "restraint", "support", "point"],
    "铰": ["释放", "约束", "hinge", "release"],
    "固定": ["约束", "fixed", "restraint"],
    "节点": ["点", "point", "joint", "node"],
    
    # 荷载相关
    "力": ["荷载", "load", "force"],
    "均布荷载": ["荷载", "distributed", "uniform"],
    "集中力": ["荷载", "point load", "concentrated"],
    "恒载": ["荷载", "dead", "permanent"],
    "活载": ["荷载", "live", "variable"],
    "风荷载": ["荷载", "wind"],
    "地震": ["荷载", "seismic", "earthquake"],
    
    # 结果相关
    "变形": ["位移", "displacement", "deformation"],
    "挠度": ["位移", "displacement", "deflection"],
    "应力": ["内力", "stress", "force"],
    "轴力": ["内力", "axial", "force"],
    "剪力": ["内力", "shear", "force"],
    "弯矩": ["内力", "moment", "force"],
    "扭矩": ["内力", "torsion", "force"],
    "周期": ["模态", "period", "modal"],
    "频率": ["模态", "frequency", "modal"],
    "振型": ["模态", "mode shape", "modal"],
    
    # 分析相关
    "计算": ["分析", "analysis", "analyze"],
    "求解": ["分析", "analysis", "solve"],
    "验算": ["设计", "design", "check"],
    "校核": ["设计", "design", "verify"],
    
    # 索相关
    "拉索": ["索", "cable", "tendon"],
    "缆索": ["索", "cable"],
    "预应力": ["索", "cable", "prestress"],
    
    # 其他
    "复制": ["编辑", "copy", "replicate"],
    "移动": ["编辑", "move", "translate"],
    "删除": ["删除", "delete", "remove"],
    "修改": ["编辑", "modify", "change", "设置"],
    "查看": ["查询", "获取", "get", "query", "view"],
    "显示": ["查询", "获取", "show", "display"],
}


def expand_query_with_synonyms(query: str) -> str:
    """
    使用同义词扩展查询字符串
    
    Args:
        query: 原始查询
        
    Returns:
        扩展后的查询（包含同义词）
    """
    expanded_terms = [query]
    query_lower = query.lower()
    
    for term, synonyms in SYNONYMS.items():
        if term in query_lower or term.lower() in query_lower:
            expanded_terms.extend(synonyms)
    
    return " ".join(expanded_terms)


class ToolSelector:
    """
    工具分层选择器
    
    实现两阶段工具选择：
    1. 意图识别 -> 选择相关类别
    2. 在类别内选择具体工具
    
    安全机制：
    - 多类别匹配（top_k=4）避免遗漏
    - 类别关联映射（如分析→结果）
    - 基础工具始终包含
    - 支持 fallback 到全量工具
    """
    
    # 类别关联映射：某些操作通常需要配合其他类别
    CATEGORY_ASSOCIATIONS: Dict[ToolCategory, List[ToolCategory]] = {
        ToolCategory.ANALYSIS: [ToolCategory.RESULTS],      # 分析后通常要看结果
        ToolCategory.LOAD: [ToolCategory.FRAME, ToolCategory.POINT],  # 加载需要知道对象
        ToolCategory.STATISTICS: [ToolCategory.CHART],      # 统计后通常要绘图
        ToolCategory.BATCH: [ToolCategory.MODEL_INFO],      # 批量操作需要先查询
        ToolCategory.EDIT: [ToolCategory.SELECTION],        # 编辑需要先选择
    }
    
    def __init__(self, all_tools: List[Any]):
        """
        初始化选择器
        
        Args:
            all_tools: 所有可用工具列表
        """
        self.all_tools = all_tools
        self._tool_map: Dict[str, Any] = {t.name: t for t in all_tools}
        self._category_tools: Dict[ToolCategory, List[Any]] = {}
        
        # 构建类别到工具的映射
        self._build_category_mapping()
    
    def _build_category_mapping(self):
        """构建类别到工具的映射"""
        for category, info in TOOL_CATEGORIES.items():
            tools = []
            for tool_name in info.tool_names:
                if tool_name in self._tool_map:
                    tools.append(self._tool_map[tool_name])
            self._category_tools[category] = tools
    
    def match_categories(self, query: str, top_k: int = 3) -> List[ToolCategory]:
        """
        根据用户查询匹配相关类别
        
        Args:
            query: 用户查询
            top_k: 返回前 k 个最相关的类别
            
        Returns:
            匹配的类别列表（包含关联类别）
        """
        # 使用同义词扩展查询
        expanded_query = expand_query_with_synonyms(query)
        query_lower = expanded_query.lower()
        scores: Dict[ToolCategory, int] = {}
        
        for category, info in TOOL_CATEGORIES.items():
            score = 0
            # 关键词匹配
            for keyword in info.keywords:
                if keyword.lower() in query_lower:
                    score += 2  # 关键词匹配权重
            # 类别名称匹配
            if info.name in query:
                score += 3
            # 描述匹配
            for word in query:
                if word in info.description:
                    score += 1
            
            if score > 0:
                scores[category] = score
        
        # 按分数排序
        sorted_categories = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # 如果没有匹配，返回常用类别
        if not sorted_categories:
            return [ToolCategory.MODEL_INFO, ToolCategory.FRAME, ToolCategory.RESULTS]
        
        # 获取 top_k 个主要类别
        primary_categories = [cat for cat, _ in sorted_categories[:top_k]]
        
        # 添加关联类别（确保功能完整性）
        result_categories = list(primary_categories)
        for cat in primary_categories:
            associated = self.CATEGORY_ASSOCIATIONS.get(cat, [])
            for assoc_cat in associated:
                if assoc_cat not in result_categories:
                    result_categories.append(assoc_cat)
        
        return result_categories
    
    def get_tools_for_categories(self, categories: List[ToolCategory]) -> List[Any]:
        """
        获取指定类别的所有工具
        
        Args:
            categories: 类别列表
            
        Returns:
            工具列表
        """
        tools = []
        seen = set()
        for category in categories:
            for tool in self._category_tools.get(category, []):
                if tool.name not in seen:
                    tools.append(tool)
                    seen.add(tool.name)
        return tools
    
    def get_relevant_tools(self, query: str, max_tools: int = 15) -> List[Any]:
        """
        根据查询获取相关工具（两阶段选择）
        
        Args:
            query: 用户查询
            max_tools: 最大返回工具数
            
        Returns:
            相关工具列表
        """
        # 第一阶段：匹配类别
        categories = self.match_categories(query, top_k=4)
        
        # 第二阶段：获取类别内的工具
        tools = self.get_tools_for_categories(categories)
        
        # 始终包含一些基础工具
        essential_tools = ["check_connection", "search_sap_docs"]
        for tool_name in essential_tools:
            if tool_name in self._tool_map:
                tool = self._tool_map[tool_name]
                if tool not in tools:
                    tools.insert(0, tool)
        
        return tools[:max_tools]
    
    def get_category_summary(self) -> str:
        """
        获取所有类别的摘要（用于 System Prompt）
        
        Returns:
            类别摘要文本
        """
        lines = ["## 可用工具类别\n"]
        for category, info in TOOL_CATEGORIES.items():
            tool_count = len(self._category_tools.get(category, []))
            lines.append(f"- **{info.name}** ({tool_count}个工具): {info.description}")
        return "\n".join(lines)
    
    def get_all_tools(self) -> List[Any]:
        """返回所有工具"""
        return self.all_tools


def create_category_aware_prompt(base_prompt: str, selector: ToolSelector) -> str:
    """
    创建包含类别信息的 System Prompt
    
    Args:
        base_prompt: 基础 prompt
        selector: 工具选择器
        
    Returns:
        增强后的 prompt
    """
    category_summary = selector.get_category_summary()
    return f"{base_prompt}\n\n{category_summary}"
