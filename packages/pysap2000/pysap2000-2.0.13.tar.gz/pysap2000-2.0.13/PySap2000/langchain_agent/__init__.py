# -*- coding: utf-8 -*-
"""
SAP2000 LangChain Agent - 自然语言控制 SAP2000

Usage:
    from PySap2000.langchain_agent import SapAgent
    
    agent = SapAgent()
    response = agent.chat("获取模型的用钢量")

特性:
    - Human-in-the-loop: 修改操作需要用户确认
    - 工具分类: QUERY_TOOLS (查询) / MODIFY_TOOLS (修改)
    - 模块化工具: tools/ 目录下按功能分类
"""

try:
    from langchain.tools import tool
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

if LANGCHAIN_AVAILABLE:
    from .agent import SapAgent
    from .tools import get_sap_tools, QUERY_TOOLS, MODIFY_TOOLS
