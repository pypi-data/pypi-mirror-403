"""
SapAgent 环境诊断工具
检查 SAP2000 COM 组件注册状态和运行环境
"""
import sys
import os
import platform

def check_windows():
    """检查 Windows 版本"""
    print("=" * 60)
    print("1. 检查 Windows 版本")
    print("=" * 60)
    
    system = platform.system()
    version = platform.version()
    machine = platform.machine()
    
    print(f"操作系统: {system}")
    print(f"版本: {version}")
    print(f"架构: {machine}")
    
    if system != "Windows":
        print("❌ 错误: SapAgent 只支持 Windows 系统")
        return False
    
    if machine != "AMD64":
        print("⚠️  警告: 建议使用 64 位 Windows 系统")
    
    print("✓ Windows 版本检查通过\n")
    return True


def check_com_registration():
    """检查 SAP2000 COM 组件注册"""
    print("=" * 60)
    print("2. 检查 SAP2000 COM 组件注册")
    print("=" * 60)
    
    try:
        import winreg
        
        # 检查 COM 注册
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CLASSES_ROOT,
                "CSI.SAP2000.API.SapObject",
                0,
                winreg.KEY_READ
            )
            
            # 获取 CLSID
            try:
                clsid_key = winreg.OpenKey(key, "CLSID")
                clsid, _ = winreg.QueryValueEx(clsid_key, "")
                print(f"COM CLSID: {clsid}")
                winreg.CloseKey(clsid_key)
            except:
                pass
            
            winreg.CloseKey(key)
            print("✓ SAP2000 COM 组件已注册\n")
            return True
            
        except WindowsError:
            print("❌ 错误: SAP2000 COM 组件未注册")
            print("\n解决方案:")
            print("  1. 以管理员身份运行 SAP2000")
            print("  2. 打开任意模型文件")
            print("  3. 关闭 SAP2000")
            print("  4. 重启电脑\n")
            return False
            
    except ImportError:
        print("❌ 错误: 无法导入 winreg 模块")
        return False


def check_sap2000_running():
    """检查 SAP2000 是否运行"""
    print("=" * 60)
    print("3. 检查 SAP2000 运行状态")
    print("=" * 60)
    
    try:
        import comtypes.client
        
        try:
            sap = comtypes.client.GetActiveObject('CSI.SAP2000.API.SapObject')
            model = sap.SapModel
            
            # 获取版本
            version = model.GetVersion()
            ver_str = version[0] if isinstance(version, (list, tuple)) else "未知"
            
            # 获取文件名
            filename = model.GetModelFilename(False) or "未命名"
            
            print(f"SAP2000 版本: {ver_str}")
            print(f"当前模型: {filename}")
            print("✓ SAP2000 正在运行且已打开模型\n")
            return True
            
        except Exception as e:
            error_code = str(e)
            
            if "-2147467262" in error_code or "不支持此接口" in error_code:
                print("❌ 错误: COM 组件未正确注册")
                print("\n这是最常见的问题！")
                print("\n解决方案:")
                print("  1. 关闭所有 SAP2000 窗口")
                print("  2. 右键点击 SAP2000 图标 → 以管理员身份运行")
                print("  3. 打开任意模型文件")
                print("  4. 关闭 SAP2000")
                print("  5. 重启电脑")
                print("  6. 正常打开 SAP2000 和模型")
                print("  7. 再次运行此诊断工具\n")
            else:
                print("❌ 错误: 无法连接到 SAP2000")
                print("\n可能的原因:")
                print("  1. SAP2000 未运行")
                print("  2. SAP2000 中没有打开模型")
                print("\n解决方案:")
                print("  1. 启动 SAP2000")
                print("  2. 打开或创建一个模型文件")
                print("  3. 再次运行此诊断工具\n")
            
            print(f"详细错误: {e}\n")
            return False
            
    except ImportError as e:
        print(f"❌ 错误: 无法导入 comtypes 模块: {e}")
        return False


def check_network():
    """检查网络连接"""
    print("=" * 60)
    print("4. 检查网络连接")
    print("=" * 60)
    
    try:
        import socket
        
        # 测试 DNS 解析
        try:
            socket.gethostbyname("www.spancore.cn")
            print("✓ DNS 解析正常")
        except:
            print("❌ 错误: 无法解析 www.spancore.cn")
            return False
        
        # 测试 HTTPS 连接
        try:
            import urllib.request
            urllib.request.urlopen("https://www.spancore.cn", timeout=5)
            print("✓ HTTPS 连接正常")
        except Exception as e:
            print(f"❌ 错误: 无法连接到 www.spancore.cn: {e}")
            return False
        
        print("✓ 网络连接检查通过\n")
        return True
        
    except ImportError:
        print("⚠️  警告: 无法检查网络连接（缺少必要模块）\n")
        return True


def main():
    print("\n" + "=" * 60)
    print("SapAgent 环境诊断工具")
    print("=" * 60)
    print()
    
    results = []
    
    # 1. 检查 Windows
    results.append(("Windows 版本", check_windows()))
    
    # 2. 检查 COM 注册
    results.append(("COM 组件注册", check_com_registration()))
    
    # 3. 检查 SAP2000 运行
    results.append(("SAP2000 运行状态", check_sap2000_running()))
    
    # 4. 检查网络
    results.append(("网络连接", check_network()))
    
    # 总结
    print("=" * 60)
    print("诊断结果总结")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✓ 通过" if passed else "❌ 失败"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False
    
    print()
    
    if all_passed:
        print("🎉 所有检查通过！SapAgent.exe 应该可以正常运行。")
    else:
        print("⚠️  存在问题，请按照上面的解决方案进行修复。")
        print("\n最常见的问题是 COM 组件未注册，请：")
        print("  1. 以管理员身份运行 SAP2000")
        print("  2. 打开模型文件")
        print("  3. 关闭 SAP2000")
        print("  4. 重启电脑")
    
    print("\n" + "=" * 60)
    print()
    
    input("按回车键退出...")


if __name__ == "__main__":
    main()
