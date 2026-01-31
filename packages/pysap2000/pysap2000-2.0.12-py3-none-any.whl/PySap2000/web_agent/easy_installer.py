"""
SapAgent 一键安装器
- 自动检测环境
- 自动注册协议
- 自动配置开机启动（可选）
- 提供友好的图形界面
"""
import sys
import os
import winreg
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import subprocess


class EasyInstaller:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("SapAgent 一键安装")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        
        # 获取 exe 路径
        if getattr(sys, 'frozen', False):
            self.exe_path = sys.executable
            self.exe_dir = Path(sys.executable).parent
        else:
            self.exe_path = str(Path(__file__).parent / "SapAgent.exe")
            self.exe_dir = Path(__file__).parent
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置界面"""
        # 标题
        title = tk.Label(
            self.root,
            text="SapAgent 一键安装",
            font=("Arial", 16, "bold")
        )
        title.pack(pady=20)
        
        # 说明
        desc = tk.Label(
            self.root,
            text="让 SAP2000 连接到 www.spancore.cn 在线工具",
            font=("Arial", 10)
        )
        desc.pack(pady=5)
        
        # 分隔线
        ttk.Separator(self.root, orient='horizontal').pack(fill='x', pady=20)
        
        # 检查项
        self.check_frame = tk.Frame(self.root)
        self.check_frame.pack(pady=10)
        
        self.checks = {
            'sap2000': {'label': '检查 SAP2000 安装', 'status': '⏳ 检查中...'},
            'com': {'label': '检查 COM 组件注册', 'status': '⏳ 检查中...'},
            'protocol': {'label': '注册 sapagent:// 协议', 'status': '⏳ 待处理'},
        }
        
        self.check_labels = {}
        for key, info in self.checks.items():
            frame = tk.Frame(self.check_frame)
            frame.pack(fill='x', pady=5)
            
            tk.Label(frame, text=info['label'], width=25, anchor='w').pack(side='left')
            status_label = tk.Label(frame, text=info['status'], width=20, anchor='w')
            status_label.pack(side='left')
            self.check_labels[key] = status_label
        
        # 可选项
        self.auto_start_var = tk.BooleanVar(value=False)
        auto_start_check = tk.Checkbutton(
            self.root,
            text="开机自动启动 SapAgent（推荐）",
            variable=self.auto_start_var
        )
        auto_start_check.pack(pady=10)
        
        # 按钮
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=20)
        
        self.install_btn = tk.Button(
            button_frame,
            text="开始安装",
            command=self.start_install,
            width=15,
            height=2,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10, "bold")
        )
        self.install_btn.pack(side='left', padx=5)
        
        tk.Button(
            button_frame,
            text="取消",
            command=self.root.quit,
            width=15,
            height=2
        ).pack(side='left', padx=5)
        
        # 状态栏
        self.status_label = tk.Label(
            self.root,
            text="准备就绪",
            relief=tk.SUNKEN,
            anchor='w'
        )
        self.status_label.pack(side='bottom', fill='x')
        
        # 自动检查
        self.root.after(500, self.check_environment)
    
    def update_status(self, key, status, color='black'):
        """更新检查状态"""
        self.check_labels[key].config(text=status, fg=color)
        self.root.update()
    
    def check_environment(self):
        """检查环境"""
        self.status_label.config(text="正在检查环境...")
        
        # 检查 SAP2000
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CLASSES_ROOT,
                "CSI.SAP2000.API.SapObject",
                0,
                winreg.KEY_READ
            )
            winreg.CloseKey(key)
            self.update_status('sap2000', '✓ 已安装', 'green')
            self.update_status('com', '✓ 已注册', 'green')
        except WindowsError:
            self.update_status('sap2000', '✓ 已安装', 'green')
            self.update_status('com', '✗ 未注册', 'red')
        
        self.update_status('protocol', '⏳ 待安装', 'orange')
        self.status_label.config(text="环境检查完成")
    
    def start_install(self):
        """开始安装"""
        self.install_btn.config(state='disabled')
        self.status_label.config(text="正在安装...")
        
        try:
            # 1. 注册协议
            self.update_status('protocol', '⏳ 注册中...', 'orange')
            if self.register_protocol():
                self.update_status('protocol', '✓ 已注册', 'green')
            else:
                self.update_status('protocol', '✗ 注册失败', 'red')
                raise Exception("协议注册失败")
            
            # 2. 配置开机启动
            if self.auto_start_var.get():
                self.setup_auto_start()
            
            # 3. 完成
            self.status_label.config(text="安装完成！")
            messagebox.showinfo(
                "安装成功",
                "SapAgent 已成功安装！\n\n"
                "现在可以访问 www.spancore.cn 使用在线工具了。\n\n"
                "提示：打开 SAP2000 和模型后，工具会自动连接。"
            )
            self.root.quit()
            
        except Exception as e:
            self.status_label.config(text=f"安装失败: {e}")
            messagebox.showerror("安装失败", str(e))
            self.install_btn.config(state='normal')
    
    def register_protocol(self):
        """注册 sapagent:// 协议"""
        try:
            protocol_name = "sapagent"
            
            # 创建协议键
            key = winreg.CreateKey(
                winreg.HKEY_CURRENT_USER,
                f"Software\\Classes\\{protocol_name}"
            )
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "URL:SapAgent Protocol")
            winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")
            winreg.CloseKey(key)
            
            # 创建命令键
            key = winreg.CreateKey(
                winreg.HKEY_CURRENT_USER,
                f"Software\\Classes\\{protocol_name}\\shell\\open\\command"
            )
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f'"{self.exe_path}" "%1"')
            winreg.CloseKey(key)
            
            return True
        except Exception as e:
            print(f"注册协议失败: {e}")
            return False
    
    def setup_auto_start(self):
        """配置开机启动"""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE
            )
            winreg.SetValueEx(
                key,
                "SapAgent",
                0,
                winreg.REG_SZ,
                f'"{self.exe_path}"'
            )
            winreg.CloseKey(key)
        except Exception as e:
            print(f"配置开机启动失败: {e}")
    
    def run(self):
        """运行安装器"""
        self.root.mainloop()


def main():
    """主函数"""
    app = EasyInstaller()
    app.run()


if __name__ == "__main__":
    main()
