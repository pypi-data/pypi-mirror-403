# -*- coding: utf-8 -*-
"""
SAP2000 LangGraph Agent - 自然语言控制 SAP2000

支持多种 LLM：
- 通义千问 (qwen-plus, qwen-max)
- DeepSeek (deepseek-chat)
- 智谱 AI (glm-4-flash, glm-4)
- OpenAI (gpt-4o-mini, gpt-4o)

特性：
- Human-in-the-loop: 修改操作需要用户确认
- 工具分类: 查询类工具自动执行，修改类工具需确认
- 工具分层选择: 根据用户意图动态选择相关工具，提高准确率
- 多会话支持: 对话历史按 session_id 隔离
"""

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from typing import Optional, Callable, Generator, AsyncGenerator, Dict, Any, List
import os
import time
import threading

from .tools import get_sap_tools, MODIFY_TOOLS, QUERY_TOOLS
from .tool_selector import ToolSelector, create_category_aware_prompt
from .config import (
    LLM_PRESETS, SYSTEM_PROMPT, format_confirmation_message,
    format_error_with_suggestion, get_error_suggestion
)


class SapAgent:
    """SAP2000 自然语言控制 Agent（支持人机确认和工具分层选择）"""
    
    # 待确认操作的超时时间（秒）
    PENDING_TIMEOUT = 300  # 5分钟
    # 对话历史最大轮数（每轮包含用户消息和助手回复）
    # 减少到10轮以节省token，同时保持足够的上下文
    MAX_HISTORY_ROUNDS = 10
    
    def __init__(
        self,
        provider: str = "qwen",
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0,
        confirm_callback: Optional[Callable[[str, dict], bool]] = None,
        enable_tool_selection: bool = True,
        max_tools_per_query: int = 15,
        max_history_rounds: int = 10
    ):
        """
        初始化 Agent
        
        Args:
            provider: LLM 提供商 ("qwen", "deepseek", "openai")
            model_name: 模型名称，不填则使用默认值
            api_key: API Key，不填则从环境变量读取
            base_url: API 地址，不填则使用预设值
            temperature: 温度参数
            confirm_callback: 确认回调函数，接收 (tool_name, args) 返回 bool
            enable_tool_selection: 是否启用工具分层选择（默认启用）
            max_tools_per_query: 每次查询最多使用的工具数量（默认15）
            max_history_rounds: 对话历史最大轮数（默认20）
        """
        # 获取预设配置
        preset = LLM_PRESETS.get(provider, LLM_PRESETS["qwen"])
        
        self.llm = ChatOpenAI(
            model=model_name or preset["default_model"],
            api_key=api_key or os.getenv(preset["env_key"]),
            base_url=base_url or preset["base_url"],
            temperature=temperature
        )
        
        self.tools = get_sap_tools()
        self.confirm_callback = confirm_callback
        
        # 工具分层选择配置
        self.enable_tool_selection = enable_tool_selection
        self.max_tools_per_query = max_tools_per_query
        
        # 对话历史配置
        self.max_history_rounds = max_history_rounds
        
        # 初始化工具选择器
        self.tool_selector = ToolSelector(self.tools)
        
        # 增强 System Prompt（添加工具类别信息）
        self.enhanced_prompt = create_category_aware_prompt(SYSTEM_PROMPT, self.tool_selector)
        
        # 待确认的操作（支持并发，使用 session_id 作为 key）
        # 格式: {session_id: {"tool_call": ..., "messages": ..., "timestamp": ...}}
        self._pending_tool_calls: Dict[str, Dict[str, Any]] = {}
        self._pending_lock = threading.Lock()
        
        # 对话历史（按 session_id 隔离）
        # 格式: {session_id: [Message, ...]}
        self._chat_histories: Dict[str, List] = {}
        self._history_lock = threading.Lock()
        
        # 默认 session_id（用于非并发场景）
        self._default_session_id = "default"
        
        # 使用 langgraph 的 react agent（使用增强的 prompt）
        self.agent = create_react_agent(
            self.llm,
            self.tools,
            prompt=self.enhanced_prompt
        )
    
    # =========================================================================
    # 对话历史管理（按 session_id 隔离）
    # =========================================================================
    
    def _get_chat_history(self, session_id: Optional[str] = None) -> List:
        """获取指定会话的对话历史"""
        key = session_id or self._default_session_id
        with self._history_lock:
            if key not in self._chat_histories:
                self._chat_histories[key] = []
            return self._chat_histories[key]
    
    def _set_chat_history(self, history: List, session_id: Optional[str] = None):
        """设置指定会话的对话历史（带长度限制）"""
        key = session_id or self._default_session_id
        # 限制历史长度：保留最近 N 轮对话
        # 每轮大约 2-4 条消息（用户、助手、可能的工具调用和结果）
        max_messages = self.max_history_rounds * 4
        if len(history) > max_messages:
            history = history[-max_messages:]
        with self._history_lock:
            self._chat_histories[key] = history
    
    def _append_to_history(self, message, session_id: Optional[str] = None):
        """向对话历史追加消息"""
        key = session_id or self._default_session_id
        with self._history_lock:
            if key not in self._chat_histories:
                self._chat_histories[key] = []
            self._chat_histories[key].append(message)
    
    def _clear_chat_history(self, session_id: Optional[str] = None):
        """清空指定会话的对话历史"""
        key = session_id or self._default_session_id
        with self._history_lock:
            self._chat_histories.pop(key, None)
    
    # =========================================================================
    # 兼容旧接口的属性（用于非并发场景）
    # =========================================================================
    
    @property
    def chat_history(self) -> List:
        """兼容旧接口：获取默认会话的对话历史"""
        return self._get_chat_history()
    
    @chat_history.setter
    def chat_history(self, value: List):
        """兼容旧接口：设置默认会话的对话历史"""
        self._set_chat_history(value)
    
    def _create_agent_with_tools(self, tools: List[Any]):
        """
        使用指定工具创建临时 Agent
        
        Args:
            tools: 工具列表
            
        Returns:
            临时 Agent 实例
        """
        return create_react_agent(
            self.llm,
            tools,
            prompt=self.enhanced_prompt
        )
    
    def _get_tools_for_query(self, query: str) -> List[Any]:
        """
        根据查询获取相关工具
        
        Args:
            query: 用户查询
            
        Returns:
            相关工具列表
        """
        if not self.enable_tool_selection:
            return self.tools
        
        return self.tool_selector.get_relevant_tools(query, self.max_tools_per_query)
    
    def _cleanup_expired_pending(self):
        """清理过期的待确认操作"""
        current_time = time.time()
        with self._pending_lock:
            expired_keys = [
                key for key, value in self._pending_tool_calls.items()
                if current_time - value.get("timestamp", 0) > self.PENDING_TIMEOUT
            ]
            for key in expired_keys:
                del self._pending_tool_calls[key]
    
    def _get_pending(self, session_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """获取待确认的操作"""
        self._cleanup_expired_pending()
        key = session_id or self._default_session_id
        with self._pending_lock:
            return self._pending_tool_calls.get(key)
    
    def _set_pending(self, pending: Dict[str, Any], session_id: Optional[str] = None):
        """设置待确认的操作"""
        key = session_id or self._default_session_id
        pending["timestamp"] = time.time()
        with self._pending_lock:
            self._pending_tool_calls[key] = pending
    
    def _clear_pending(self, session_id: Optional[str] = None):
        """清除待确认的操作"""
        key = session_id or self._default_session_id
        with self._pending_lock:
            self._pending_tool_calls.pop(key, None)
    
    def _needs_confirmation(self, tool_name: str) -> bool:
        """判断工具是否需要用户确认"""
        return tool_name in MODIFY_TOOLS
    
    def _format_confirmation_message(self, tool_name: str, args: dict) -> str:
        """格式化确认消息（委托给 config 模块）"""
        return format_confirmation_message(tool_name, args)
    
    def chat(self, message: str, session_id: Optional[str] = None) -> str:
        """
        发送消息并获取回复
        
        Args:
            message: 用户消息
            session_id: 会话 ID（用于并发场景区分不同用户）
            
        Returns:
            Agent 回复
        """
        # 处理待确认的操作
        pending = self._get_pending(session_id)
        if pending:
            return self._handle_confirmation(message, session_id)
        
        # 获取当前会话的历史
        chat_history = self._get_chat_history(session_id)
        chat_history.append(HumanMessage(content=message))
        
        # 动态工具选择：根据用户意图选择相关工具
        relevant_tools = self._get_tools_for_query(message)
        current_agent = self._create_agent_with_tools(relevant_tools) if self.enable_tool_selection else self.agent
        
        # 调用 agent，设置递归限制为 50
        config = {"recursion_limit": 50}
        
        try:
            result = current_agent.invoke({"messages": chat_history}, config=config)
        except Exception as e:
            error_msg = str(e)
            # 处理常见错误，附带智能恢复建议
            if "recursion_limit" in error_msg.lower():
                return "操作过于复杂，请尝试分步执行或简化请求。"
            elif "api" in error_msg.lower() or "key" in error_msg.lower():
                return "API 连接失败，请检查网络和 API Key 配置。"
            else:
                # 使用智能错误建议
                return format_error_with_suggestion(error_msg)
        
        # 检查是否有需要确认的工具调用
        messages = result["messages"]
        for msg in reversed(messages):
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    tool_name = tool_call.get('name', '')
                    if self._needs_confirmation(tool_name):
                        # 需要确认，暂存操作
                        self._set_pending({
                            'tool_call': tool_call,
                            'messages': messages
                        }, session_id)
                        args = tool_call.get('args', {})
                        return self._format_confirmation_message(tool_name, args)
        
        # 获取最后一条 AI 消息
        response = messages[-1].content
        
        # 更新历史（带长度限制）
        self._set_chat_history(messages, session_id)
        
        return response
    
    def _handle_confirmation(self, user_input: str, session_id: Optional[str] = None) -> str:
        """处理用户确认"""
        pending = self._get_pending(session_id)
        self._clear_pending(session_id)
        
        if not pending:
            return "没有待确认的操作。"
        
        user_input = user_input.strip().lower()
        
        if user_input in ['确认', '是', 'yes', 'y', '好', '执行', 'ok']:
            # 用户确认，执行操作
            tool_call = pending['tool_call']
            tool_name = tool_call.get('name', '')
            args = tool_call.get('args', {})
            
            # 找到对应的工具并执行
            for tool in self.tools:
                if tool.name == tool_name:
                    try:
                        result = tool.invoke(args)
                        # 更新历史（带长度限制）
                        self._set_chat_history(pending['messages'], session_id)
                        return f"✓ 操作已执行\n\n{result}"
                    except Exception as e:
                        return f"✗ 执行失败: {str(e)}"
            
            return "✗ 找不到对应的工具"
        else:
            # 用户取消
            return "操作已取消。"
    
    def clear_history(self, session_id: Optional[str] = None):
        """清空对话历史"""
        self._clear_chat_history(session_id)
        self._clear_pending(session_id)

    def chat_stream(self, message: str, session_id: Optional[str] = None) -> Generator[dict, None, None]:
        """
        流式发送消息并获取回复（生成器版本）
        
        Args:
            message: 用户消息
            session_id: 会话 ID（用于并发场景区分不同用户）
            
        Yields:
            dict: 包含不同类型的事件
                - {"type": "thinking"} - 开始思考
                - {"type": "tool_start", "name": "工具名"} - 开始调用工具
                - {"type": "tool_end", "name": "工具名", "result": "结果"} - 工具调用完成
                - {"type": "token", "content": "文本"} - 生成的文本 token
                - {"type": "done", "content": "完整回复", "tools_used": [...]} - 完成
                - {"type": "confirm", "message": "确认消息"} - 需要确认
                - {"type": "error", "message": "错误信息"} - 错误
        """
        # 处理待确认的操作
        pending = self._get_pending(session_id)
        if pending:
            result = self._handle_confirmation(message, session_id)
            yield {"type": "done", "content": result, "tools_used": []}
            return
        
        # 获取当前会话的历史
        chat_history = self._get_chat_history(session_id)
        chat_history.append(HumanMessage(content=message))
        
        yield {"type": "thinking"}
        
        # 动态工具选择：根据用户意图选择相关工具
        relevant_tools = self._get_tools_for_query(message)
        current_agent = self._create_agent_with_tools(relevant_tools) if self.enable_tool_selection else self.agent
        
        config = {"recursion_limit": 50}
        tools_used = []
        
        try:
            # 使用 stream 方法获取流式输出
            full_response = ""
            final_messages = None
            
            for event in current_agent.stream({"messages": chat_history}, config=config):
                # 处理不同类型的事件
                if "agent" in event:
                    # Agent 的输出（包含工具调用或最终回复）
                    agent_msg = event["agent"].get("messages", [])
                    # 保存最新的消息列表
                    if agent_msg:
                        final_messages = chat_history + agent_msg
                    for msg in agent_msg:
                        if hasattr(msg, 'tool_calls') and msg.tool_calls:
                            # 工具调用
                            for tc in msg.tool_calls:
                                tool_name = tc.get('name', '')
                                tools_used.append(tool_name)
                                yield {"type": "tool_start", "name": tool_name}
                                
                                # 检查是否需要确认（在流式过程中检测）
                                if self._needs_confirmation(tool_name):
                                    self._set_pending({
                                        'tool_call': tc,
                                        'messages': final_messages or chat_history
                                    }, session_id)
                                    args = tc.get('args', {})
                                    confirm_msg = self._format_confirmation_message(tool_name, args)
                                    yield {"type": "confirm", "message": confirm_msg}
                                    return
                                    
                        elif hasattr(msg, 'content') and msg.content:
                            # 文本内容
                            content = msg.content
                            if content and content != full_response:
                                # 增量输出
                                new_content = content[len(full_response):]
                                if new_content:
                                    yield {"type": "token", "content": new_content}
                                full_response = content
                
                elif "tools" in event:
                    # 工具执行结果
                    tool_msgs = event["tools"].get("messages", [])
                    # 更新消息列表
                    if final_messages and tool_msgs:
                        final_messages = final_messages + tool_msgs
                    for msg in tool_msgs:
                        if hasattr(msg, 'name') and hasattr(msg, 'content'):
                            yield {"type": "tool_end", "name": msg.name, "result": msg.content[:200]}
            
            # 从流式事件中获取最终消息，不再重复调用 invoke
            if final_messages:
                self._set_chat_history(final_messages, session_id)
                # 获取最终回复
                final_response = full_response
                for msg in reversed(final_messages):
                    if hasattr(msg, 'content') and msg.content and not hasattr(msg, 'tool_calls'):
                        final_response = msg.content
                        break
            else:
                final_response = full_response
            
            yield {"type": "done", "content": final_response, "tools_used": tools_used}
            
        except Exception as e:
            error_msg = str(e)
            if "recursion_limit" in error_msg.lower():
                yield {"type": "error", "message": "操作过于复杂，请尝试分步执行或简化请求。"}
            elif "api" in error_msg.lower() or "key" in error_msg.lower():
                yield {"type": "error", "message": "API 连接失败，请检查网络和 API Key 配置。"}
            else:
                # 使用智能错误建议
                yield {"type": "error", "message": format_error_with_suggestion(error_msg)}

    async def chat_stream_async(self, message: str, session_id: Optional[str] = None) -> AsyncGenerator[dict, None]:
        """
        异步流式发送消息（用于 WebSocket）
        
        Args:
            message: 用户消息
            session_id: 会话 ID（用于并发场景区分不同用户）
        
        用法:
            async for event in agent.chat_stream_async(message, session_id):
                await ws.send(json.dumps(event))
        """
        start_time = time.time()
        
        # 处理待确认的操作
        pending = self._get_pending(session_id)
        if pending:
            result = self._handle_confirmation(message, session_id)
            elapsed = round(time.time() - start_time, 1)
            yield {"type": "done", "content": result, "tools_used": [], "elapsed_time": elapsed}
            return
        
        # 获取当前会话的历史
        chat_history = self._get_chat_history(session_id)
        chat_history.append(HumanMessage(content=message))
        
        yield {"type": "thinking"}
        
        # 动态工具选择：根据用户意图选择相关工具
        relevant_tools = self._get_tools_for_query(message)
        current_agent = self._create_agent_with_tools(relevant_tools) if self.enable_tool_selection else self.agent
        
        config = {"recursion_limit": 50}
        tools_used = []
        image_data = None  # 存储图片数据
        total_tokens = 0  # Token 统计
        
        try:
            # 使用 astream 进行异步流式处理
            full_response = ""
            final_messages = None  # 保存最终消息列表
            
            async for event in current_agent.astream({"messages": chat_history}, config=config):
                if "agent" in event:
                    agent_msg = event["agent"].get("messages", [])
                    # 保存最新的消息列表
                    if agent_msg:
                        final_messages = chat_history + agent_msg
                    
                    for msg in agent_msg:
                        # 尝试从消息中获取 token 使用信息
                        if hasattr(msg, 'response_metadata'):
                            metadata = msg.response_metadata
                            if 'token_usage' in metadata:
                                usage = metadata['token_usage']
                                total_tokens = usage.get('total_tokens', 0)
                            elif 'usage' in metadata:
                                usage = metadata['usage']
                                total_tokens = usage.get('total_tokens', 0)
                        
                        if hasattr(msg, 'tool_calls') and msg.tool_calls:
                            for tc in msg.tool_calls:
                                tool_name = tc.get('name', '')
                                tools_used.append(tool_name)
                                yield {"type": "tool_start", "name": tool_name}
                                
                                # 检查是否需要确认（在流式过程中检测）
                                if self._needs_confirmation(tool_name):
                                    self._set_pending({
                                        'tool_call': tc,
                                        'messages': final_messages or chat_history
                                    }, session_id)
                                    args = tc.get('args', {})
                                    confirm_msg = self._format_confirmation_message(tool_name, args)
                                    elapsed = round(time.time() - start_time, 1)
                                    yield {"type": "confirm", "message": confirm_msg, "elapsed_time": elapsed, "total_tokens": total_tokens}
                                    return
                                    
                        elif hasattr(msg, 'content') and msg.content:
                            content = msg.content
                            if content and content != full_response:
                                new_content = content[len(full_response):]
                                if new_content:
                                    yield {"type": "token", "content": new_content}
                                full_response = content
                
                elif "tools" in event:
                    tool_msgs = event["tools"].get("messages", [])
                    # 更新消息列表
                    if final_messages and tool_msgs:
                        final_messages = final_messages + tool_msgs
                    
                    for msg in tool_msgs:
                        if hasattr(msg, 'name') and hasattr(msg, 'content'):
                            tool_result = msg.content
                            # 检查工具结果中是否有图片
                            if "__image__" in tool_result:
                                try:
                                    import json
                                    result_json = json.loads(tool_result)
                                    if "__image__" in result_json:
                                        image_data = result_json["__image__"]
                                except:
                                    pass
                            yield {"type": "tool_end", "name": msg.name, "result": tool_result[:200]}
            
            # 从流式事件中获取最终消息，不再重复调用 ainvoke
            if final_messages:
                self._set_chat_history(final_messages, session_id)
                # 获取最终回复
                final_response = full_response
                for msg in reversed(final_messages):
                    if hasattr(msg, 'content') and msg.content and not hasattr(msg, 'tool_calls'):
                        final_response = msg.content
                        break
                    # 从最终消息中获取 token 统计
                    if hasattr(msg, 'response_metadata'):
                        metadata = msg.response_metadata
                        if 'token_usage' in metadata:
                            usage = metadata['token_usage']
                            total_tokens = usage.get('total_tokens', total_tokens)
                        elif 'usage' in metadata:
                            usage = metadata['usage']
                            total_tokens = usage.get('total_tokens', total_tokens)
            else:
                final_response = full_response
            
            # 从消息历史中提取图片数据（如果之前没有捕获到）
            if not image_data and final_messages:
                for msg in final_messages:
                    if hasattr(msg, 'content') and isinstance(msg.content, str) and "__image__" in msg.content:
                        try:
                            import json
                            result_json = json.loads(msg.content)
                            if "__image__" in result_json:
                                image_data = result_json["__image__"]
                                break
                        except:
                            pass
            
            # 计算耗时
            elapsed = round(time.time() - start_time, 1)
            
            done_event = {
                "type": "done", 
                "content": final_response, 
                "tools_used": tools_used,
                "elapsed_time": elapsed,
                "total_tokens": total_tokens
            }
            if image_data:
                done_event["image_data"] = image_data
            yield done_event
            
        except Exception as e:
            error_msg = str(e)
            elapsed = round(time.time() - start_time, 1)
            if "recursion_limit" in error_msg.lower():
                yield {"type": "error", "message": "操作过于复杂，请尝试分步执行或简化请求。", "elapsed_time": elapsed}
            elif "api" in error_msg.lower() or "key" in error_msg.lower():
                yield {"type": "error", "message": "API 连接失败，请检查网络和 API Key 配置。", "elapsed_time": elapsed}
            else:
                # 使用智能错误建议
                yield {"type": "error", "message": format_error_with_suggestion(error_msg), "elapsed_time": elapsed}


# =============================================================================
# 命令行入口
# =============================================================================

def main():
    """命令行交互模式"""
    print("SAP2000 智能助手")
    print("=" * 40)
    print("输入 'quit' 退出，'clear' 清空对话历史")
    print("修改操作会先询问确认")
    print()
    
    # 默认使用通义千问
    agent = SapAgent(provider="qwen")
    
    while True:
        try:
            user_input = input("你: ").strip()
            
            if not user_input:
                continue
            if user_input.lower() == "quit":
                print("再见！")
                break
            if user_input.lower() == "clear":
                agent.clear_history()
                print("对话历史已清空")
                continue
            
            response = agent.chat(user_input)
            print(f"\n助手: {response}\n")
            
        except KeyboardInterrupt:
            print("\n再见！")
            break
        except Exception as e:
            print(f"错误: {e}\n")


if __name__ == "__main__":
    main()
