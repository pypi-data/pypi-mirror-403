# -*- coding: utf-8 -*-
"""
SAP2000 AI Agent - API Key 配置工具

快速配置通义千问 API Key
"""

import os
import sys


def setup_api_key():
    """交互式配置 API Key"""
    print("=" * 60)
    print("  SAP2000 AI Agent - API Key 配置")
    print("=" * 60)
    print()
    
    config_file = os.path.join(os.path.dirname(__file__), "config.ini")
    
    # 读取现有配置
    existing_key = ""
    try:
        import configparser
        config = configparser.ConfigParser()
        config.read(config_file, encoding="utf-8")
        if config.has_option("API", "DASHSCOPE_API_KEY"):
            existing_key = config.get("API", "DASHSCOPE_API_KEY").strip()
    except:
        pass
    
    if existing_key:
        print(f"当前 API Key: {existing_key[:10]}...{existing_key[-10:]}")
        print()
        choice = input("是否更新 API Key? (y/n): ").strip().lower()
        if choice != 'y':
            print("已取消")
            return
        print()
    
    # 获取 API Key
    print("请访问以下地址获取通义千问 API Key:")
    print("https://dashscope.console.aliyun.com/apiKey")
    print()
    
    api_key = input("请输入 API Key: ").strip()
    
    if not api_key:
        print("错误: API Key 不能为空")
        return
    
    if not api_key.startswith("sk-"):
        print("警告: API Key 格式可能不正确（通常以 sk- 开头）")
        choice = input("是否继续? (y/n): ").strip().lower()
        if choice != 'y':
            print("已取消")
            return
    
    # 写入配置文件
    try:
        import configparser
        config = configparser.ConfigParser()
        
        # 读取现有配置（如果存在）
        if os.path.exists(config_file):
            config.read(config_file, encoding="utf-8")
        
        # 确保 section 存在
        if not config.has_section("API"):
            config.add_section("API")
        if not config.has_section("Agent"):
            config.add_section("Agent")
        
        # 设置 API Key
        config.set("API", "DASHSCOPE_API_KEY", api_key)
        
        # 设置默认 Agent 配置（如果不存在）
        if not config.has_option("Agent", "provider"):
            config.set("Agent", "provider", "qwen")
        if not config.has_option("Agent", "model_name"):
            config.set("Agent", "model_name", "qwen-plus")
        
        # 写入文件
        with open(config_file, "w", encoding="utf-8") as f:
            config.write(f)
        
        print()
        print("✓ API Key 配置成功!")
        print(f"✓ 配置文件: {config_file}")
        print()
        print("下一步:")
        print("1. 打开 SAP2000 并加载模型")
        print("2. 运行 SapAgent.exe")
        print("3. 访问 https://www.spancore.cn/tools/sap2000-agent")
        print()
        
    except Exception as e:
        print(f"错误: 配置失败 - {e}")
        return


if __name__ == "__main__":
    try:
        setup_api_key()
    except KeyboardInterrupt:
        print("\n已取消")
    except Exception as e:
        print(f"\n错误: {e}")
    
    input("\n按 Enter 键退出...")
