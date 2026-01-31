# -*- coding: utf-8 -*-
"""
测试配置文件读取
"""

import os
import sys

# 添加路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_config():
    """测试配置读取"""
    print("=" * 60)
    print("  测试配置文件读取")
    print("=" * 60)
    print()
    
    # 导入 load_config
    from web_agent.sap_agent import load_config
    
    config = load_config()
    
    print(f"配置文件路径: {config['config_file']}")
    print(f"API Key: {config['api_key'][:10]}...{config['api_key'][-10:] if config['api_key'] else '(未设置)'}")
    print(f"提供商: {config['provider']}")
    print(f"模型: {config['model_name']}")
    print()
    
    if not config['api_key']:
        print("❌ API Key 未设置")
        print(f"请编辑配置文件: {config['config_file']}")
        return False
    
    print("✓ 配置读取成功")
    print()
    
    # 测试 Agent 初始化
    print("测试 Agent 初始化...")
    
    # 先检查 LangChain 是否可用
    try:
        from langchain_agent import LANGCHAIN_AVAILABLE
        if not LANGCHAIN_AVAILABLE:
            print("❌ LangChain 未安装")
            print("请运行: pip install -r PySap2000/web_agent/requirements.txt")
            return False
    except ImportError:
        print("❌ langchain_agent 模块未找到")
        print("请运行: pip install -r PySap2000/web_agent/requirements.txt")
        return False
    
    from web_agent.sap_agent import get_or_create_agent
    
    agent = get_or_create_agent()
    
    if agent is None:
        print("❌ Agent 初始化失败")
        return False
    
    print("✓ Agent 初始化成功")
    print()
    
    # 测试简单对话（不需要 SAP2000）
    print("测试对话功能...")
    try:
        # 清空历史
        agent.clear_history()
        
        response = agent.chat("中国的首都是哪里？请简短回答。")
        print(f"问题: 中国的首都是哪里？")
        print(f"回答: {response}")
        print()
        print("✓ 对话功能正常")
        return True
    except Exception as e:
        print(f"❌ 对话失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        success = test_config()
        if success:
            print()
            print("=" * 60)
            print("  所有测试通过！")
            print("=" * 60)
        else:
            print()
            print("=" * 60)
            print("  测试失败，请检查配置")
            print("=" * 60)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
    
    input("\n按 Enter 键退出...")
