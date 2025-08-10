#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple WeChat Clone - 客户端程序
实现聊天室"客人"模式的TCP客户端

主要功能:
- 连接到指定的聊天室服务器
- 进行密码验证和昵称设置
- 实时发送和接收聊天消息
- 处理各种网络异常情况
- 支持聊天命令功能

作者: de-Sitter
版本: 1.0
"""

import socket
import threading
import time
import sys
import os
import re
from datetime import datetime
from typing import Optional, Tuple
import platform

try:
    import readline
except ImportError:
    import pyreadline3 as readline 

IS_WINDOWS = platform.system().lower() == 'windows'


# 导入工具模块
try:
    from utils import format_message, validate_ip, validate_port, safe_print
except ImportError:
    # 如果utils模块不存在，定义基本的替代函数
    def format_message(sender, content):
        """格式化消息的简单实现"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        return f"[{timestamp}] {sender}: {content}"
    
    def validate_ip(ip):
        """验证IP地址的简单实现"""
        try:
            parts = ip.split('.')
            return len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts)
        except:
            return False
    
    def validate_port(port):
        """验证端口号的简单实现"""
        return isinstance(port, int) and 1024 <= port <= 65535
    
    def safe_print(message):
        """安全打印函数的简单实现"""
        print(message)


# ================================
# 客户端配置类
# ================================
class ClientConfig:
    """客户端配置参数"""
    
    # 网络配置
    CONNECTION_TIMEOUT = 10
    RECEIVE_TIMEOUT = 1
    BUFFER_SIZE = 1024
    RETRY_ATTEMPTS = 3
    
    # 消息配置
    ENCODING = 'utf-8'
    MAX_MESSAGE_SIZE = 500
    MAX_NICKNAME_LENGTH = 20
    
    # 界面配置
    CHAT_PROMPT = "💬 "
    SYSTEM_PREFIX = "📢 "
    ERROR_PREFIX = "❌ "
    INFO_PREFIX = "ℹ️  "


# ================================
# 聊天客户端类
# ================================
class ChatClient:
    """聊天客户端主类"""
    
    def __init__(self):
        """初始化聊天客户端"""
        self.client_socket: Optional[socket.socket] = None
        self.server_ip: str = ""
        self.server_port: int = 0
        self.room_password: str = ""
        self.nickname: str = ""
        self.is_connected: bool = False
        self.is_running: bool = False
        self.receive_thread: Optional[threading.Thread] = None
        self.input_lock = threading.Lock()  # 输入锁，防止输出干扰
        self.current_input_buffer = ""
    
    def get_connection_info(self) -> bool:
        """
        获取服务器连接信息
        
        Returns:
            bool: 获取成功返回True，失败返回False
        """
        try:
            safe_print("🔗 请输入聊天室连接信息")
            safe_print("─"*40)
            
            # 获取服务器IP地址
            while True:
                ip_input = input("🌐 服务器IP地址: ").strip()
                if not ip_input:
                    safe_print("❌ IP地址不能为空，请重新输入")
                    continue
                
                if validate_ip(ip_input):
                    self.server_ip = ip_input
                    break
                else:
                    safe_print("❌ IP地址格式无效，请输入正确的IP地址 (如: 192.168.1.100)")
            
            # 获取服务器端口
            while True:
                port_input = input("📡 服务器端口 (默认: 8888): ").strip()
                if not port_input:
                    self.server_port = 8888
                    break
                
                try:
                    port = int(port_input)
                    if validate_port(port):
                        self.server_port = port
                        break
                    else:
                        safe_print("❌ 端口号无效，请输入 1024-65535 之间的数字")
                except ValueError:
                    safe_print("❌ 端口号格式错误，请输入数字")
            
            # 获取房间密码
            while True:
                password = input("🔐 聊天室密码: ").strip()
                if password:
                    self.room_password = password
                    break
                else:
                    safe_print("❌ 密码不能为空，请重新输入")
            
            # 获取用户昵称
            while True:
                nickname = input("👤 你的昵称: ").strip()
                if not nickname:
                    safe_print("❌ 昵称不能为空，请重新输入")
                    continue
                
                if len(nickname) > ClientConfig.MAX_NICKNAME_LENGTH:
                    safe_print(f"❌ 昵称长度不能超过{ClientConfig.MAX_NICKNAME_LENGTH}个字符")
                    continue
                
                # 检查昵称格式（只允许字母、数字、中文）
                if re.match(r'^[\w\u4e00-\u9fa5]+$', nickname):
                    self.nickname = nickname
                    break
                else:
                    safe_print("❌ 昵称只能包含字母、数字和中文，请重新输入")
            
            safe_print("\n✅ 连接信息设置完成")
            safe_print(f"📍 目标服务器: {self.server_ip}:{self.server_port}")
            safe_print(f"👤 你的昵称: {self.nickname}")
            
            return True
            
        except KeyboardInterrupt:
            safe_print("\n🛑 设置被用户中断")
            return False
        except Exception as e:
            safe_print(f"❌ 获取连接信息失败: {e}")
            return False
    
    def connect_to_server(self) -> bool:
        """
        连接到服务器
        
        Returns:
            bool: 连接成功返回True，失败返回False
        """
        max_attempts = ClientConfig.RETRY_ATTEMPTS
        
        for attempt in range(1, max_attempts + 1):
            try:
                safe_print(f"🔄 正在连接服务器... (尝试 {attempt}/{max_attempts})")
                
                # 创建socket连接
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.settimeout(ClientConfig.CONNECTION_TIMEOUT)
                
                # 连接服务器
                self.client_socket.connect((self.server_ip, self.server_port))
                
                safe_print("✅ 成功连接到服务器")
                self.is_connected = True
                return True
                
            except socket.timeout:
                safe_print(f"⏰ 连接超时 (尝试 {attempt}/{max_attempts})")
            except ConnectionRefusedError:
                safe_print(f"❌ 服务器拒绝连接 (尝试 {attempt}/{max_attempts})")
                safe_print("   请检查服务器是否正在运行，IP地址和端口是否正确")
            except socket.gaierror:
                safe_print(f"❌ 无法解析服务器地址 (尝试 {attempt}/{max_attempts})")
                safe_print("   请检查IP地址是否正确")
            except Exception as e:
                safe_print(f"❌ 连接失败: {e} (尝试 {attempt}/{max_attempts})")
            
            # 清理失败的连接
            if self.client_socket:
                try:
                    self.client_socket.close()
                except:
                    pass
                self.client_socket = None
            
            # 如果不是最后一次尝试，等待一段时间再重试
            if attempt < max_attempts:
                safe_print("⏳ 等待2秒后重试...")
                time.sleep(2)
        
        safe_print(f"❌ 经过{max_attempts}次尝试，仍无法连接到服务器")
        return False
    
    def authenticate(self) -> bool:
        """
        进行服务器认证
        
        Returns:
            bool: 认证成功返回True，失败返回False
        """
        try:
            safe_print("🔐 正在进行身份验证...")
            
            # 等待服务器的密码请求
            request = self.client_socket.recv(ClientConfig.BUFFER_SIZE).decode(ClientConfig.ENCODING)
            
            if request != "PASSWORD_REQUEST":
                safe_print(f"❌ 服务器响应异常: {request}")
                return False
            
            # 发送密码
            self.client_socket.send(self.room_password.encode(ClientConfig.ENCODING))
            
            # 等待认证结果
            auth_result = self.client_socket.recv(ClientConfig.BUFFER_SIZE).decode(ClientConfig.ENCODING)
            
            if auth_result == "AUTH_SUCCESS":
                safe_print("✅ 身份验证成功")
                
                # 等待昵称请求
                nickname_request = self.client_socket.recv(ClientConfig.BUFFER_SIZE).decode(ClientConfig.ENCODING)
                
                if nickname_request == "NICKNAME_REQUEST":
                    # 发送昵称
                    self.client_socket.send(self.nickname.encode(ClientConfig.ENCODING))
                    safe_print(f"👤 昵称已设置为: {self.nickname}")
                
                return True
                
            elif auth_result == "AUTH_FAILED":
                safe_print("❌ 密码错误，认证失败")
                return False
            elif auth_result == "SERVER_FULL":
                safe_print("❌ 服务器已满，无法加入聊天室")
                return False
            else:
                safe_print(f"❌ 认证过程异常: {auth_result}")
                return False
                
        except socket.timeout:
            safe_print("⏰ 认证超时")
            return False
        except Exception as e:
            safe_print(f"❌ 认证过程出错: {e}")
            return False
    
    def receive_messages(self):
        """
        接收服务器消息的线程函数
        """
        self.client_socket.settimeout(ClientConfig.RECEIVE_TIMEOUT)
        
        while self.is_running and self.is_connected:
            try:
                # 接收消息
                data = self.client_socket.recv(ClientConfig.BUFFER_SIZE)
                
                if not data:
                    # 服务器断开连接
                    safe_print("\n🔌 服务器已断开连接")
                    self.is_connected = False
                    break
                
                message = data.decode(ClientConfig.ENCODING)
                
                # 显示消息（需要处理输出冲突）
                #with self.input_lock:
                # 保存当前输入状态

                current_input = ""
                try:
                    current_input = readline.get_line_buffer()
                except:
                    current_input = self.current_input_buffer

                print(f"\r{' ' * 50}\r", end='')  # 清除当前行
                print(message)  # 显示新消息
                if IS_WINDOWS:
                    print(" ") # Windows系统需要额外添加一行，防止输入内容将对方消息覆盖
                if current_input:
                    print(f"💬 {current_input}", end='', flush=True)
                    self.current_input_buffer = current_input
                else:
                    print("💬 ", end='', flush=True)  # 重新显示输入提示
                
            except socket.timeout:
                # 接收超时，继续循环
                continue
            except ConnectionResetError:
                safe_print("\n🔌 与服务器的连接被重置")
                self.is_connected = False
                break
            except Exception as e:
                if self.is_running and self.is_connected:
                    safe_print(f"\n❌ 接收消息时出错: {e}")
                    self.is_connected = False
                break
        
        safe_print("\n📤 消息接收线程已退出")
    
    def send_message(self, message: str) -> bool:
        """
        发送消息到服务器
        
        Args:
            message: 要发送的消息
            
        Returns:
            bool: 发送成功返回True，失败返回False
        """
        try:
            if not self.is_connected or not self.client_socket:
                return False
            
            # 检查消息长度
            if len(message) > ClientConfig.MAX_MESSAGE_SIZE:
                safe_print(f"❌ 消息长度超过限制 ({ClientConfig.MAX_MESSAGE_SIZE} 字符)")
                return False
            
            # 发送消息
            encoded_message = message.encode(ClientConfig.ENCODING)
            self.client_socket.sendall(encoded_message)
            return True
            
        except Exception as e:
            safe_print(f"❌ 发送消息失败: {e}")
            self.is_connected = False
            return False
    
    def handle_user_input(self):
        """
        处理用户输入的主循环
        """
        safe_print("\n🎉 成功加入聊天室！")
        safe_print("💡 输入消息并按回车发送，输入 '/quit' 退出聊天")
        safe_print("💡 输入 '/help' 查看可用命令")
        safe_print("─"*50)
        
        while self.is_running and self.is_connected:
            try:
                #with self.input_lock:
                user_input = input(ClientConfig.CHAT_PROMPT).strip()
                
                if not user_input:
                    continue
                
                # 处理退出命令
                if user_input.lower() in ['/quit', '/exit', '/q']:
                    safe_print("👋 正在退出聊天室...")
                    self.send_message('/quit')
                    break
                
                # 处理帮助命令
                elif user_input.lower() == '/help':
                    self.show_client_help()
                    continue
                
                # 处理清屏命令
                elif user_input.lower() in ['/clear', '/cls']:
                    os.system('cls' if os.name == 'nt' else 'clear')
                    safe_print("🎉 重新连接到聊天室")
                    safe_print("─"*50)
                    continue
                
                # 处理时间命令
                elif user_input.lower() == '/time':
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    safe_print(f"🕒 当前时间: {current_time}")
                    continue
                
                # 发送普通消息
                else:
                    if not self.send_message(user_input):
                        safe_print("❌ 消息发送失败，可能已断开连接")
                        break

                self.current_input_buffer = ""
                
            except KeyboardInterrupt:
                safe_print("\n🛑 检测到中断信号，正在退出...")
                self.send_message('/quit')
                break
            except EOFError:
                safe_print("\n📄 输入结束，正在退出...")
                self.send_message('/quit')
                break
            except Exception as e:
                safe_print(f"❌ 处理用户输入时出错: {e}")
                break
    
    def show_client_help(self):
        """显示客户端帮助信息"""
        help_text = """
📋 聊天室客户端命令帮助:
────────────────────────
💬 聊天命令:
   直接输入文字 - 发送聊天消息
   /quit 或 /exit - 退出聊天室
   /help - 显示此帮助信息
   /clear 或 /cls - 清屏
   /time - 显示当前时间
   
📞 服务器命令 (发送给服务器):
   /users - 查看在线用户列表
   /help - 查看服务器命令帮助
   
💡 使用技巧:
   • 按 Ctrl+C 可以快速退出
   • 消息最长不超过500个字符
   • 支持中文和表情符号
   • 连接断开会自动提示
"""
        safe_print(help_text)
    
    def disconnect(self):
        """断开与服务器的连接"""
        safe_print("🔌 正在断开连接...")
        
        self.is_running = False
        self.is_connected = False
        
        # 等待接收线程结束
        if self.receive_thread and self.receive_thread.is_alive():
            try:
                self.receive_thread.join(timeout=2)
            except:
                pass
        
        # 关闭socket连接
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
            self.client_socket = None
        
        safe_print("✅ 已断开连接")
    
    def run(self) -> bool:
        """
        运行客户端的主函数
        
        Returns:
            bool: 运行成功返回True，失败返回False
        """
        try:
            # 获取连接信息
            if not self.get_connection_info():
                return False
            
            # 连接到服务器
            if not self.connect_to_server():
                return False
            
            # 进行身份验证
            if not self.authenticate():
                self.disconnect()
                return False
            
            # 设置运行状态
            self.is_running = True
            
            # 启动消息接收线程
            self.receive_thread = threading.Thread(
                target=self.receive_messages,
                name="MessageReceiver",
                daemon=True
            )
            self.receive_thread.start()
            
            # 等待一下确保接收线程启动
            time.sleep(0.5)
            
            # 开始处理用户输入
            self.handle_user_input()
            
            return True
            
        except Exception as e:
            safe_print(f"❌ 客户端运行异常: {e}")
            return False
        finally:
            self.disconnect()


# ================================
# 连接测试函数
# ================================
def test_connection(ip: str, port: int) -> bool:
    """
    测试到服务器的连接
    
    Args:
        ip: 服务器IP地址
        port: 服务器端口
        
    Returns:
        bool: 连接测试成功返回True，失败返回False
    """
    try:
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.settimeout(3)
        test_socket.connect((ip, port))
        test_socket.close()
        return True
    except:
        return False


# ================================
# 主函数
# ================================
def main():
    """
    客户端模式的主函数
    """
    try:
        safe_print("🚪 启动聊天室加入模式")
        safe_print("🔗 正在初始化客户端...")
        
        # 创建客户端实例
        client = ChatClient()
        
        # 运行客户端
        success = client.run()
        
        if success:
            safe_print("✅ 聊天会话结束")
        else:
            safe_print("❌ 客户端运行失败")
            safe_print("💡 请检查:")
            safe_print("   1. 服务器是否正在运行")
            safe_print("   2. IP地址和端口是否正确")
            safe_print("   3. 密码是否正确")
            safe_print("   4. 网络连接是否正常")
            
    except KeyboardInterrupt:
        safe_print("\n🛑 客户端被用户中断")
    except Exception as e:
        safe_print(f"❌ 客户端主函数异常: {e}")
    finally:
        safe_print("👋 客户端模式已退出")


# ================================
# 程序入口
# ================================
if __name__ == "__main__":
    main()