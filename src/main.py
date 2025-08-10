#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple WeChat Clone - 主程序入口
一个简单的点对点命令行聊天应用

功能说明:
- 支持创建聊天室（作为主人/服务器）
- 支持加入聊天室（作为客人/客户端）  
- 基于TCP协议的实时文字聊天
- 命令行界面，简单易用

作者: de-Sitter
版本: 1.0
"""

import sys
import os
import time
from typing import Optional

# ================================
# 全局配置类
# ================================
class Config:
    """程序配置类 - 集中管理所有配置参数"""
    
    # ===== 网络配置 =====
    DEFAULT_PORT = 8888              # 默认监听端口号
    MAX_CONNECTIONS = 5              # 最大同时连接数
    BUFFER_SIZE = 1024               # 网络消息缓冲区大小
    CONNECTION_TIMEOUT = 30          # 连接超时时间(秒)
    
    # ===== 消息配置 =====
    MESSAGE_ENCODING = 'utf-8'       # 消息编码格式
    MAX_MESSAGE_LENGTH = 500         # 单条消息最大长度
    MAX_PASSWORD_LENGTH = 20         # 房间密码最大长度
    
    # ===== 应用信息 =====
    APP_NAME = "Simple WeChat Clone"
    APP_VERSION = "1.0"
    
    # ===== 界面显示 =====
    WELCOME_BANNER = f"""
╔══════════════════════════════════════════╗
║         {APP_NAME} v{APP_VERSION}         ║
║                                          ║
║          🔥 简单的P2P聊天应用 🔥         ║
║                                          ║
║       让两台电脑之间轻松建立即时通信     ║
╚══════════════════════════════════════════╝
"""
    
    # ===== 菜单选项定义 =====
    MENU_OPTIONS = {
        '1': {'name': '创建聊天室', 'desc': '让你的电脑作为聊天服务器', 'icon': '🏠'},
        '2': {'name': '加入聊天室', 'desc': '连接到朋友创建的聊天室', 'icon': '🚪'},
        '3': {'name': '使用帮助', 'desc': '查看详细的使用说明', 'icon': '❓'},
        '4': {'name': '退出程序', 'desc': '安全退出应用程序', 'icon': '👋'}
    }


# ================================
# 界面显示函数
# ================================
def clear_screen():
    """
    清屏函数 - 跨平台兼容
    Windows使用'cls'，Linux/Mac使用'clear'
    """
    os.system('cls' if os.name == 'nt' else 'clear')


def print_welcome():
    """显示欢迎横幅和程序介绍"""
    clear_screen()
    print(Config.WELCOME_BANNER)
    print("🎉 欢迎使用简单微信克隆版！")
    print("📱 这是一个基于命令行的即时聊天工具")
    print("💬 支持两人之间的实时文字通信")
    print("🌐 使用TCP协议，无需互联网，局域网即可使用")
    print("="*50)


def print_menu():
    """显示主菜单选项"""
    print("\n📋 请选择你要执行的操作:")
    print("─"*40)
    
    for key, option in Config.MENU_OPTIONS.items():
        print(f"  {key}. {option['icon']} {option['name']}")
        print(f"     💡 {option['desc']}")
        if key != '4':  # 最后一个选项后不加分隔线
            print()
    
    print("─"*40)


def show_help():
    """显示详细的使用帮助信息"""
    clear_screen()
    help_content = """
📚 详细使用指南
════════════════════════════════════════════════════

🏠 创建聊天室 (主人模式)
────────────────────────
• 功能说明: 将你的电脑设置为聊天服务器
• 使用步骤:
  1️⃣  选择"创建聊天室"选项
  2️⃣  设置房间密码(用于保护聊天室)
  3️⃣  程序会显示你的IP地址和端口号
  4️⃣  将IP地址和密码告诉朋友
  5️⃣  等待朋友连接，然后开始聊天

• 注意事项:
  ⚠️  你的电脑将持续运行服务器
  ⚠️  关闭程序会断开所有连接
  ⚠️  确保防火墙允许程序访问网络

🚪 加入聊天室 (客人模式)
────────────────────────
• 功能说明: 连接到朋友创建的聊天室
• 使用步骤:
  1️⃣  选择"加入聊天室"选项
  2️⃣  输入朋友的IP地址
  3️⃣  输入端口号(通常是8888)
  4️⃣  输入房间密码
  5️⃣  连接成功后开始聊天

• 注意事项:
  ⚠️  确保与朋友在同一网络环境
  ⚠️  IP地址和密码必须正确
  ⚠️  网络不稳定可能导致断连

💡 聊天技巧
────────────
• 聊天命令:
  📝 直接输入文字发送消息
  🚪 输入 '/quit' 退出聊天
  📊 输入 '/help' 查看聊天帮助

• 网络要求:
  🌐 两台电脑需在同一局域网内
  🔧 或者通过VPN连接到同一网络
  📶 确保网络连接稳定

🔧 故障排除
────────────
• 连接失败:
  ❌ 检查IP地址是否正确
  ❌ 检查端口号是否正确
  ❌ 检查密码是否正确
  ❌ 检查防火墙设置
  ❌ 检查网络连接

• 聊天中断:
  🔄 重新启动程序
  🔄 检查网络连接
  🔄 联系网络管理员

📞 技术支持
────────────
如果遇到问题，请检查:
1. Python版本 (需要3.6+)
2. 网络连接状态
3. 防火墙设置
4. 程序文件完整性

"""
    print(help_content)
    input("\n按回车键返回主菜单...")


# ================================
# 输入处理函数
# ================================
def get_user_choice() -> str:
    """
    获取并验证用户的菜单选择
    
    Returns:
        str: 用户选择的有效选项 ('1', '2', '3', '4')
    """
    while True:
        try:
            choice = input("\n👆 请输入选项编号 (1-4): ").strip()
            
            # 验证输入是否为有效选项
            if choice in Config.MENU_OPTIONS:
                return choice
            else:
                print("❌ 输入无效！请输入 1、2、3 或 4")
                
        except KeyboardInterrupt:
            # 用户按下 Ctrl+C
            print("\n\n🛑 检测到中断信号 (Ctrl+C)")
            print("👋 程序即将退出...")
            sys.exit(0)
            
        except EOFError:
            # 输入流结束 (Ctrl+D 或管道输入结束)
            print("\n\n📄 输入流结束")
            print("👋 程序即将退出...")
            sys.exit(0)
            
        except Exception as e:
            print(f"❌ 输入处理错误: {e}")
            print("请重新输入")


# ================================
# 环境检查函数
# ================================
def validate_environment() -> bool:
    """
    验证程序运行环境是否满足要求
    
    Returns:
        bool: True表示环境验证通过，False表示验证失败
    """
    try:
        print("🔍 正在检查运行环境...")
        
        # 检查Python版本
        if sys.version_info < (3, 6):
            print("❌ Python版本过低!")
            print(f"   当前版本: {sys.version}")
            print("   要求版本: Python 3.6 或更高")
            return False
        
        print(f"✅ Python版本检查通过: {sys.version_info.major}.{sys.version_info.minor}")
        
        # 检查必要的内置模块
        required_modules = ['socket', 'threading', 'json', 'time']
        for module_name in required_modules:
            try:
                __import__(module_name)
                print(f"✅ 模块 {module_name} 可用")
            except ImportError:
                print(f"❌ 缺少必要模块: {module_name}")
                return False
        
        print("✅ 所有环境检查通过!")
        return True
        
    except Exception as e:
        print(f"❌ 环境检查过程中发生错误: {e}")
        return False


# ================================
# 模式运行函数
# ================================
def run_server_mode():
    """
    运行服务器模式 (创建聊天室)
    动态导入server模块并执行主函数
    """
    try:
        print("\n🏠 正在启动聊天室创建模式...")
        print("⏳ 正在加载服务器模块...")
        
        # 检查server.py文件是否存在
        # 在使用nuitka编译为可执行文件时请注释掉这一段判断内容，因为nuitka会将os.path.exists('server.py')识别为字符串
        # if not os.path.exists('server.py'):
        #     print("❌ 错误: 找不到 server.py 文件!")
        #     print("请确保 server.py 文件在当前目录下")
        #     return
        
        # 动态导入server模块
        try:
            import server
            print("✅ 服务器模块加载成功")
        except ImportError as e:
            print(f"❌ 服务器模块导入失败: {e}")
            return
        
        # 调用服务器主函数
        print("🚀 启动服务器...")
        server.main()
        
    except KeyboardInterrupt:
        print("\n\n🛑 服务器模式被用户中断")
        print("💾 正在安全关闭...")
    except Exception as e:
        print(f"❌ 服务器模式运行错误: {e}")
        print("请检查错误信息并重试")
    finally:
        print("\n📤 已退出服务器模式")
        input("按回车键返回主菜单...")


def run_client_mode():
    """
    运行客户端模式 (加入聊天室)
    动态导入client模块并执行主函数
    """
    try:
        print("\n🚪 正在启动聊天室加入模式...")
        print("⏳ 正在加载客户端模块...")
        
        # 检查client.py文件是否存在
        # 在使用nuitka编译为可执行文件时请注释掉这一段判断内容，因为nuitka会将os.path.exists('server.py')识别为字符串
        # if not os.path.exists('client.py'):
        #     print("❌ 错误: 找不到 client.py 文件!")
        #     print("请确保 client.py 文件在当前目录下")
        #     return
        
        # 动态导入client模块
        try:
            import client
            print("✅ 客户端模块加载成功")
        except ImportError as e:
            print(f"❌ 客户端模块导入失败: {e}")
            return
        
        # 调用客户端主函数
        print("🚀 启动客户端...")
        client.main()
        
    except KeyboardInterrupt:
        print("\n\n🛑 客户端模式被用户中断")
        print("💾 正在安全退出...")
    except Exception as e:
        print(f"❌ 客户端模式运行错误: {e}")
        print("请检查错误信息并重试")
    finally:
        print("\n📤 已退出客户端模式")
        input("按回车键返回主菜单...")


# ================================
# 主程序函数
# ================================
def main():
    """
    主函数 - 程序的核心控制流程
    
    功能:
    1. 验证运行环境
    2. 显示欢迎界面
    3. 处理用户选择
    4. 调用对应的功能模块
    5. 程序退出处理
    """
    try:
        # 第一步: 环境验证
        if not validate_environment():
            print("\n❌ 环境验证失败，程序无法正常运行")
            print("请检查Python版本和相关依赖")
            input("按回车键退出...")
            sys.exit(1)
        
        print("\n🎉 环境验证完成，准备启动程序")
        time.sleep(1)  # 给用户一点时间看到成功信息
        
        # 第二步: 主程序循环
        while True:
            # 显示欢迎界面和菜单
            print_welcome()
            print_menu()
            
            # 获取用户选择
            user_choice = get_user_choice()
            
            # 根据用户选择执行对应功能
            if user_choice == '1':
                # 创建聊天室 (服务器模式)
                run_server_mode()
                
            elif user_choice == '2':
                # 加入聊天室 (客户端模式)
                run_client_mode()
                
            elif user_choice == '3':
                # 显示使用帮助
                show_help()
                
            elif user_choice == '4':
                # 退出程序
                print("\n👋 感谢使用 Simple WeChat Clone!")
                print("✨ 希望这个小工具为你带来了便利")
                print("🔄 欢迎下次使用!")
                
                # 倒计时退出
                for i in range(3, 0, -1):
                    print(f"⏰ 程序将在 {i} 秒后退出...", end='\r')
                    time.sleep(1)
                
                print("\n🚪 再见!")
                break
                
    except KeyboardInterrupt:
        # 处理用户中断 (Ctrl+C)
        print("\n\n🛑 程序被用户中断")
        print("👋 感谢使用，再见!")
        
    except Exception as e:
        # 处理未预期的错误
        print(f"\n❌ 程序运行时发生未预期的错误:")
        print(f"   错误类型: {type(e).__name__}")
        print(f"   错误信息: {e}")
        print("\n🔧 建议:")
        print("   1. 重新启动程序")
        print("   2. 检查文件完整性")
        print("   3. 检查Python环境")
        
    finally:
        # 程序清理和安全退出
        print("\n💾 正在进行程序清理...")
        time.sleep(0.5)
        print("✅ 程序已安全退出")
        sys.exit(0)


# ================================
# 程序入口点
# ================================
if __name__ == "__main__":
    """
    程序入口点
    
    当用户直接运行此文件时 (python main.py)，
    会执行main()函数启动整个应用程序
    
    这种写法的好处:
    1. 允许其他模块导入此文件而不自动执行main()
    2. 明确标识程序的入口点
    3. 符合Python最佳实践
    """
    main()