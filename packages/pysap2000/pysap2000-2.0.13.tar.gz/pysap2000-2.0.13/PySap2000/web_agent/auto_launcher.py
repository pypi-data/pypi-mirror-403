"""
SapAgent 自动启动器
- 检测到网页请求时自动启动
- 最小化到系统托盘
- 自动重连
"""
import sys
import os
import subprocess
import time
from pathlib import Path

def is_sapagent_running():
    """检查 SapAgent 是否已运行"""
    try:
        import psutil
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == 'SapAgent.exe':
                return True
        return False
    except:
        return False


def start_sapagent():
    """启动 SapAgent"""
    # 获取 SapAgent.exe 路径
    if getattr(sys, 'frozen', False):
        # 打包后
        exe_dir = Path(sys.executable).parent
    else:
        # 开发模式
        exe_dir = Path(__file__).parent
    
    sapagent_exe = exe_dir / "SapAgent.exe"
    
    if not sapagent_exe.exists():
        print(f"错误: 找不到 SapAgent.exe: {sapagent_exe}")
        return False
    
    try:
        # 启动 SapAgent（最小化）
        subprocess.Popen(
            [str(sapagent_exe)],
            creationflags=subprocess.CREATE_NO_WINDOW,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print("✓ SapAgent 已启动")
        return True
    except Exception as e:
        print(f"✗ 启动失败: {e}")
        return False


def main():
    """主函数"""
    print("SapAgent 自动启动器")
    print("=" * 50)
    
    # 检查是否已运行
    if is_sapagent_running():
        print("✓ SapAgent 已在运行")
        return
    
    # 启动 SapAgent
    print("启动 SapAgent...")
    if start_sapagent():
        print("\n✓ 启动成功！")
        print("SapAgent 正在后台运行")
        print("可以关闭此窗口")
        time.sleep(2)
    else:
        print("\n✗ 启动失败")
        input("按回车键退出...")


if __name__ == "__main__":
    main()
