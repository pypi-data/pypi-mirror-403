# -*- coding: utf-8 -*-
"""
RAG 知识库搜索工具
"""

from langchain.tools import tool
import json


@tool
def search_sap_docs(query: str) -> str:
    """
    搜索 SAP2000 API 文档和知识库。
    
    当用户询问 SAP2000 的 API 用法、函数参数、功能说明等问题时使用此工具。
    
    Args:
        query: 搜索关键词，如 "FrameObj.AddByPoint" 或 "如何创建杆件"
    
    Returns:
        相关文档内容的摘要
    """
    try:
        from ..rag import search_sap_docs as rag_search
        return rag_search(query, top_k=3)
    except Exception as e:
        return json.dumps({"错误": f"搜索失败: {str(e)}"}, ensure_ascii=False)
