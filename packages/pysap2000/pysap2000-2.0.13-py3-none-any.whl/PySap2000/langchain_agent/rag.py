# -*- coding: utf-8 -*-
"""
SAP2000 RAG 知识库模块

基于 CSI_AI_Ready_Texts 文档实现检索增强生成（RAG）功能。
支持中文分词、关键词匹配、TF-IDF 加权。

特性：
- 中文分词支持（jieba，可选）
- 搜索结果缓存
- 文档结构化解析（函数签名、参数、返回值）
- 多种搜索策略
"""

import os
import re
import hashlib
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Set
from dataclasses import dataclass, field
from functools import lru_cache
import threading
import time

# 尝试导入 jieba，不强制依赖
try:
    import jieba
    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False


@dataclass
class FunctionInfo:
    """函数信息（从文档中提取）"""
    name: str = ""
    signature: str = ""
    description: str = ""
    parameters: List[str] = field(default_factory=list)
    returns: str = ""
    remarks: str = ""


@dataclass
class Document:
    """文档数据类"""
    filename: str
    content: str
    title: str  # 从文件名提取的标题
    # 结构化信息
    function_info: Optional[FunctionInfo] = None
    # 分词后的词集合（用于快速匹配）
    tokens: Set[str] = field(default_factory=set)
    # 关键词（高权重词）
    keywords: Set[str] = field(default_factory=set)


class SAP2000KnowledgeBase:
    """SAP2000 知识库"""
    
    # 搜索缓存配置
    CACHE_SIZE = 100  # 缓存最近 100 次搜索
    CACHE_TTL = 3600  # 缓存有效期 1 小时
    
    def __init__(self, docs_dir: Optional[str] = None):
        """
        初始化知识库
        
        Args:
            docs_dir: 文档目录路径，优先级：
                      1. 传入参数
                      2. 环境变量 SAP_DOCS_PATH
                      3. 默认相对路径 docs/CSI_AI_Ready_Texts
        """
        if docs_dir is None:
            docs_dir = os.getenv("SAP_DOCS_PATH")
        
        if docs_dir is None:
            current_dir = Path(__file__).parent.parent
            docs_dir = current_dir / "docs" / "CSI_AI_Ready_Texts"
        
        self.docs_dir = Path(docs_dir)
        self.documents: List[Document] = []
        
        # 搜索缓存
        self._cache: Dict[str, Tuple[List[Tuple[Document, float]], float]] = {}
        self._cache_lock = threading.Lock()
        
        # 倒排索引（词 -> 文档索引列表）
        self._inverted_index: Dict[str, Set[int]] = {}
        
        self._load_documents()
        self._build_index()
    
    def _load_documents(self):
        """加载所有文档"""
        if not self.docs_dir.exists():
            print(f"[RAG] 文档目录不存在: {self.docs_dir}")
            return
        
        for filepath in self.docs_dir.glob("*.txt"):
            try:
                content = filepath.read_text(encoding='utf-8', errors='ignore')
                title = self._extract_title(filepath.stem)
                
                # 解析函数信息
                func_info = self._parse_function_info(content)
                
                # 分词
                tokens = self._tokenize(content + " " + title)
                
                # 提取关键词
                keywords = self._extract_keywords(filepath.stem, func_info)
                
                self.documents.append(Document(
                    filename=filepath.name,
                    content=content,
                    title=title,
                    function_info=func_info,
                    tokens=tokens,
                    keywords=keywords
                ))
            except Exception as e:
                print(f"[RAG] 加载文档失败 {filepath}: {e}")
        
        print(f"[RAG] 已加载 {len(self.documents)} 个文档")
        if JIEBA_AVAILABLE:
            print("[RAG] 中文分词已启用 (jieba)")
    
    def _build_index(self):
        """构建倒排索引"""
        for idx, doc in enumerate(self.documents):
            for token in doc.tokens:
                if token not in self._inverted_index:
                    self._inverted_index[token] = set()
                self._inverted_index[token].add(idx)
            # 关键词也加入索引
            for kw in doc.keywords:
                if kw not in self._inverted_index:
                    self._inverted_index[kw] = set()
                self._inverted_index[kw].add(idx)
        
        print(f"[RAG] 倒排索引已构建，共 {len(self._inverted_index)} 个词条")
    
    def _extract_title(self, filename: str) -> str:
        """从文件名提取可读标题"""
        title = filename
        prefixes = [
            "SAP2000_API_Fuctions_",  # 注意原文档有拼写错误
            "SAP2000_API_Functions_",
            "Database_Tables_",
        ]
        for prefix in prefixes:
            if title.startswith(prefix):
                title = title[len(prefix):]
                break
        
        # 替换下划线为空格
        title = title.replace("_", " ")
        title = re.sub(r'\s+', ' ', title).strip()
        return title
    
    def _parse_function_info(self, content: str) -> Optional[FunctionInfo]:
        """从文档内容解析函数信息"""
        info = FunctionInfo()
        
        # 提取函数名（通常在开头）
        name_match = re.search(r'^([A-Za-z_][A-Za-z0-9_\.]+)\s*[\(\n]', content, re.MULTILINE)
        if name_match:
            info.name = name_match.group(1)
        
        # 提取函数签名
        sig_match = re.search(r'((?:Function|Sub|def)\s+[^\n]+)', content, re.IGNORECASE)
        if sig_match:
            info.signature = sig_match.group(1).strip()
        
        # 提取描述（通常在 Description 或开头几行）
        desc_match = re.search(r'Description[:\s]*\n([^\n]+(?:\n[^\n]+)*?)(?=\n\s*\n|\nParameters|\nRemarks|\nReturn)', content, re.IGNORECASE)
        if desc_match:
            info.description = desc_match.group(1).strip()
        
        # 提取参数
        params_match = re.search(r'Parameters[:\s]*\n((?:[^\n]+\n)*?)(?=\n\s*\n|\nRemarks|\nReturn|\nExample)', content, re.IGNORECASE)
        if params_match:
            params_text = params_match.group(1)
            # 解析每个参数
            param_lines = [line.strip() for line in params_text.split('\n') if line.strip()]
            info.parameters = param_lines[:10]  # 最多保留 10 个参数
        
        # 提取返回值
        return_match = re.search(r'Return[s]?[:\s]*\n([^\n]+)', content, re.IGNORECASE)
        if return_match:
            info.returns = return_match.group(1).strip()
        
        # 提取备注
        remarks_match = re.search(r'Remarks[:\s]*\n([^\n]+(?:\n[^\n]+)*?)(?=\n\s*\n|\nExample|\nSee Also|$)', content, re.IGNORECASE)
        if remarks_match:
            info.remarks = remarks_match.group(1).strip()[:500]  # 限制长度
        
        return info if info.name or info.description else None
    
    def _tokenize(self, text: str) -> Set[str]:
        """
        分词
        
        支持中英文混合分词：
        - 英文：按空格和标点分割
        - 中文：使用 jieba 分词（如果可用）
        """
        tokens = set()
        text_lower = text.lower()
        
        # 英文分词
        english_tokens = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', text_lower)
        tokens.update(t for t in english_tokens if len(t) >= 2)
        
        # 中文分词
        if JIEBA_AVAILABLE:
            chinese_text = re.sub(r'[a-zA-Z0-9_]+', ' ', text)
            chinese_tokens = jieba.cut(chinese_text)
            tokens.update(t.strip() for t in chinese_tokens if len(t.strip()) >= 2)
        else:
            # 降级：简单按标点分割中文
            chinese_parts = re.findall(r'[\u4e00-\u9fff]+', text)
            for part in chinese_parts:
                # 2-4 字的中文词
                for i in range(len(part)):
                    for length in [2, 3, 4]:
                        if i + length <= len(part):
                            tokens.add(part[i:i+length])
        
        return tokens
    
    def _extract_keywords(self, filename: str, func_info: Optional[FunctionInfo]) -> Set[str]:
        """提取关键词（高权重词）"""
        keywords = set()
        
        # 从文件名提取
        # 例如: "Object_Model_Frame_Object_AddByCoord" -> ["frame", "addbycoord", "object"]
        parts = filename.lower().split('_')
        keywords.update(p for p in parts if len(p) >= 3 and p not in {'sap2000', 'api', 'fuctions', 'functions', 'the', 'and', 'for'})
        
        # 从函数信息提取
        if func_info:
            if func_info.name:
                # 分割驼峰命名
                name_parts = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)', func_info.name)
                keywords.update(p.lower() for p in name_parts if len(p) >= 3)
                keywords.add(func_info.name.lower())
        
        return keywords
    
    def _calculate_relevance(self, query: str, doc: Document, query_tokens: Set[str]) -> float:
        """
        计算查询与文档的相关性分数
        
        使用多种信号：
        1. 关键词匹配（高权重）
        2. 标题匹配
        3. 内容词频
        4. 完整查询匹配
        """
        score = 0.0
        query_lower = query.lower()
        
        # 1. 关键词匹配（权重最高）
        keyword_matches = query_tokens & doc.keywords
        score += len(keyword_matches) * 8.0
        
        # 2. 标题匹配
        title_lower = doc.title.lower()
        for token in query_tokens:
            if token in title_lower:
                score += 5.0
        
        # 3. 内容词匹配
        token_matches = query_tokens & doc.tokens
        score += len(token_matches) * 2.0
        
        # 4. 完整查询匹配
        content_lower = doc.content.lower()
        if query_lower in content_lower:
            score += 15.0
        elif query_lower in title_lower:
            score += 20.0
        
        # 5. 函数名精确匹配
        if doc.function_info and doc.function_info.name:
            func_name_lower = doc.function_info.name.lower()
            if query_lower in func_name_lower or func_name_lower in query_lower:
                score += 25.0
        
        return score
    
    def _get_cache_key(self, query: str, top_k: int) -> str:
        """生成缓存键"""
        return hashlib.md5(f"{query}:{top_k}".encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[List[Tuple[Document, float]]]:
        """从缓存获取结果"""
        with self._cache_lock:
            if cache_key in self._cache:
                results, timestamp = self._cache[cache_key]
                if time.time() - timestamp < self.CACHE_TTL:
                    return results
                else:
                    del self._cache[cache_key]
        return None
    
    def _set_cache(self, cache_key: str, results: List[Tuple[Document, float]]):
        """设置缓存"""
        with self._cache_lock:
            # 清理过期缓存
            if len(self._cache) >= self.CACHE_SIZE:
                current_time = time.time()
                expired_keys = [
                    k for k, (_, ts) in self._cache.items()
                    if current_time - ts > self.CACHE_TTL
                ]
                for k in expired_keys:
                    del self._cache[k]
                # 如果还是满了，删除最旧的
                if len(self._cache) >= self.CACHE_SIZE:
                    oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
                    del self._cache[oldest_key]
            
            self._cache[cache_key] = (results, time.time())
    
    def search(self, query: str, top_k: int = 3) -> List[Tuple[Document, float]]:
        """
        搜索相关文档
        
        Args:
            query: 查询字符串
            top_k: 返回前 k 个结果
            
        Returns:
            (文档, 相关性分数) 列表
        """
        if not self.documents:
            return []
        
        # 检查缓存
        cache_key = self._get_cache_key(query, top_k)
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached
        
        # 分词
        query_tokens = self._tokenize(query)
        
        # 使用倒排索引快速筛选候选文档
        candidate_indices: Set[int] = set()
        for token in query_tokens:
            if token in self._inverted_index:
                candidate_indices.update(self._inverted_index[token])
        
        # 如果没有匹配，搜索所有文档
        if not candidate_indices:
            candidate_indices = set(range(len(self.documents)))
        
        # 计算相关性
        results = []
        for idx in candidate_indices:
            doc = self.documents[idx]
            score = self._calculate_relevance(query, doc, query_tokens)
            if score > 0:
                results.append((doc, score))
        
        # 排序
        results.sort(key=lambda x: x[1], reverse=True)
        results = results[:top_k]
        
        # 缓存结果
        self._set_cache(cache_key, results)
        
        return results
    
    def get_context(self, query: str, max_chars: int = 4000) -> str:
        """
        获取查询相关的上下文文本
        
        Args:
            query: 查询字符串
            max_chars: 最大字符数
            
        Returns:
            相关文档内容的拼接
        """
        results = self.search(query, top_k=3)
        
        if not results:
            return ""
        
        context_parts = []
        total_chars = 0
        
        for doc, score in results:
            content = doc.content[:1500]
            
            if total_chars + len(content) > max_chars:
                remaining = max_chars - total_chars
                if remaining > 200:
                    content = content[:remaining]
                else:
                    break
            
            context_parts.append(f"### {doc.title}\n{content}")
            total_chars += len(content)
        
        return "\n\n".join(context_parts)
    
    def clear_cache(self):
        """清空搜索缓存"""
        with self._cache_lock:
            self._cache.clear()


# 全局知识库实例（懒加载）
_knowledge_base: Optional[SAP2000KnowledgeBase] = None
_kb_lock = threading.Lock()


def get_knowledge_base() -> SAP2000KnowledgeBase:
    """获取知识库单例（线程安全）"""
    global _knowledge_base
    if _knowledge_base is None:
        with _kb_lock:
            if _knowledge_base is None:
                _knowledge_base = SAP2000KnowledgeBase()
    return _knowledge_base


def search_sap_docs(query: str, top_k: int = 3) -> str:
    """
    搜索 SAP2000 文档（供 LangChain 工具使用）
    
    Args:
        query: 搜索查询
        top_k: 返回结果数量
        
    Returns:
        搜索结果的格式化字符串
    """
    kb = get_knowledge_base()
    results = kb.search(query, top_k)
    
    if not results:
        return "未找到相关文档。建议：\n1. 尝试使用英文关键词（如 FrameObj, AddByPoint）\n2. 使用更具体的 API 名称"
    
    output = []
    for i, (doc, score) in enumerate(results, 1):
        # 构建结果
        parts = [f"**{i}. {doc.title}** (相关度: {score:.1f})"]
        
        # 添加函数信息（如果有）
        if doc.function_info:
            fi = doc.function_info
            if fi.name:
                parts.append(f"   函数: `{fi.name}`")
            if fi.signature:
                parts.append(f"   签名: `{fi.signature[:100]}`")
            if fi.description:
                parts.append(f"   描述: {fi.description[:200]}")
            if fi.parameters:
                params_str = "; ".join(fi.parameters[:5])
                if len(fi.parameters) > 5:
                    params_str += f" ... (共{len(fi.parameters)}个参数)"
                parts.append(f"   参数: {params_str[:200]}")
            if fi.returns:
                parts.append(f"   返回: {fi.returns[:100]}")
        else:
            # 没有结构化信息，显示内容摘要
            summary = doc.content[:300].replace('\n', ' ')
            parts.append(f"   摘要: {summary}...")
        
        output.append("\n".join(parts))
    
    return "\n\n".join(output)
