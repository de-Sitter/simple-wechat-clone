#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple WeChat Clone - 服务器端程序
实现聊天室"主人"模式的TCP服务器

主要功能:
- 创建TCP服务器监听客户端连接
- 验证客户端密码
- 管理多个客户端连接
- 实时转发消息给所有连接的客户端
- 处理连接断开和异常情况

作者: de-Sitter
版本: 1.0
"""

import socket
import threading
import json
import time
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# 导入工具模块
try:
    from utils import get_local_ip, format_message, validate_port, safe_print
except ImportError:
    # 如果utils模块不存在，定义基本的替代函数
    def get_local_ip():
        """获取本机IP地址的简单实现"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def format_message(sender, content):
        """格式化消息的简单实现"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        return f"[{timestamp}] {sender}: {content}"
    
    def validate_port(port):
        """验证端口号的简单实现"""
        return isinstance(port, int) and 1024 <= port <= 65535
    
    def safe_print(message):
        """安全打印函数的简单实现"""
        print(message)


# ================================
# 服务器配置类
# ================================
class ServerConfig:
    """服务器配置参数"""
    
    # 网络配置
    DEFAULT_PORT = 8888
    MAX_CLIENTS = 5
    BUFFER_SIZE = 1024
    CONNECTION_TIMEOUT = 30
    
    # 消息配置
    ENCODING = 'utf-8'
    MAX_MESSAGE_SIZE = 500
    MAX_PASSWORD_LENGTH = 20
    
    # 服务器状态
    SERVER_NAME = "ChatRoom"
    HEARTBEAT_INTERVAL = 30


# ================================
# 客户端连接类
# ================================
class ClientConnection:
    """表示一个客户端连接的类"""
    
    def __init__(self, socket_obj: socket.socket, address: Tuple[str, int], nickname: str = ""):
        """
        初始化客户端连接
        
        Args:
            socket_obj: 客户端socket对象
            address: 客户端地址(IP, 端口)
            nickname: 客户端昵称
        """
        self.socket = socket_obj
        self.address = address
        self.nickname = nickname or f"User_{address[1]}"  # 默认昵称
        self.connected_time = datetime.now()
        self.last_activity = datetime.now()
        self.is_active = True
        
    def send_message(self, message: str) -> bool:
        """
        向客户端发送消息
        
        Args:
            message: 要发送的消息
            
        Returns:
            bool: 发送成功返回True，失败返回False
        """
        try:
            # 将消息编码并发送
            encoded_message = message.encode(ServerConfig.ENCODING)
            self.socket.send(encoded_message)
            self.last_activity = datetime.now()
            return True
        except Exception as e:
            safe_print(f"❌ 向 {self.nickname} 发送消息失败: {e}")
            self.is_active = False
            return False
    
    def close(self):
        """关闭客户端连接"""
        try:
            self.is_active = False
            self.socket.close()
        except:
            pass


# ================================
# 聊天服务器类
# ================================
class ChatServer:
    """聊天服务器主类"""
    
    def __init__(self):
        """初始化聊天服务器"""
        self.server_socket: Optional[socket.socket] = None
        self.clients: Dict[str, ClientConnection] = {}  # 客户端连接字典
        self.room_password: str = ""
        self.server_ip: str = ""
        self.server_port: int = ServerConfig.DEFAULT_PORT
        self.is_running: bool = False
        self.message_lock = threading.Lock()  # 消息发送锁
        self.clients_lock = threading.Lock()  # 客户端列表锁
        
    def setup_server(self) -> bool:
        """
        设置服务器参数
        
        Returns:
            bool: 设置成功返回True，失败返回False
        """
        try:
            # 获取本机IP地址
            self.server_ip = get_local_ip()
            safe_print(f"🌐 检测到本机IP地址: {self.server_ip}")
            
            # 设置服务器端口
            port_input = input(f"📡 请设置服务器端口 (默认: {ServerConfig.DEFAULT_PORT}): ").strip()
            if port_input:
                try:
                    port = int(port_input)
                    if validate_port(port):
                        self.server_port = port
                    else:
                        safe_print("⚠️  端口号无效，使用默认端口")
                except ValueError:
                    safe_print("⚠️  端口号格式错误，使用默认端口")
            
            # 设置房间密码
            while True:
                password = input("🔐 请设置聊天室密码 (1-20个字符): ").strip()
                if 1 <= len(password) <= ServerConfig.MAX_PASSWORD_LENGTH:
                    self.room_password = password
                    break
                else:
                    safe_print("❌ 密码长度必须在1-20个字符之间，请重新输入")
            
            safe_print("✅ 服务器参数设置完成")
            return True
            
        except KeyboardInterrupt:
            safe_print("\n🛑 设置被用户中断")
            return False
        except Exception as e:
            safe_print(f"❌ 服务器设置失败: {e}")
            return False
    
    def start_server(self) -> bool:
        """
        启动TCP服务器
        
        Returns:
            bool: 启动成功返回True，失败返回False
        """
        try:
            # 创建TCP socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # 设置socket选项，允许地址重用
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # 绑定地址和端口
            self.server_socket.bind((self.server_ip, self.server_port))
            
            # 开始监听连接
            self.server_socket.listen(ServerConfig.MAX_CLIENTS)
            
            self.is_running = True
            safe_print(f"🚀 服务器启动成功!")
            safe_print("="*50)
            safe_print(f"📍 服务器地址: {self.server_ip}:{self.server_port}")
            safe_print(f"🔑 房间密码: {self.room_password}")
            safe_print(f"👥 最大连接数: {ServerConfig.MAX_CLIENTS}")
            safe_print("="*50)
            safe_print("📋 请将以下信息告诉你的朋友:")
            safe_print(f"   IP地址: {self.server_ip}")
            safe_print(f"   端口号: {self.server_port}")
            safe_print(f"   密码: {self.room_password}")
            safe_print("="*50)
            safe_print("⏳ 等待客户端连接...")
            
            return True
            
        except OSError as e:
            if "Address already in use" in str(e):
                safe_print(f"❌ 端口 {self.server_port} 已被占用，请尝试其他端口")
            else:
                safe_print(f"❌ 服务器启动失败: {e}")
            return False
        except Exception as e:
            safe_print(f"❌ 服务器启动异常: {e}")
            return False
    
    def authenticate_client(self, client_socket: socket.socket) -> bool:
        """
        验证客户端密码
        
        Args:
            client_socket: 客户端socket对象
            
        Returns:
            bool: 验证成功返回True，失败返回False
        """
        try:
            # 设置接收超时
            client_socket.settimeout(30)
            
            # 发送密码请求
            client_socket.send("PASSWORD_REQUEST".encode(ServerConfig.ENCODING))
            
            # 接收客户端密码
            password_data = client_socket.recv(ServerConfig.BUFFER_SIZE)
            client_password = password_data.decode(ServerConfig.ENCODING).strip()
            
            # 验证密码
            if client_password == self.room_password:
                client_socket.send("AUTH_SUCCESS".encode(ServerConfig.ENCODING))
                time.sleep(0.1)
                return True
            else:
                client_socket.send("AUTH_FAILED".encode(ServerConfig.ENCODING))
                return False
                
        except socket.timeout:
            safe_print("⏰ 客户端认证超时")
            return False
        except Exception as e:
            safe_print(f"❌ 客户端认证过程出错: {e}")
            return False
        finally:
            # 恢复socket为阻塞模式
            client_socket.settimeout(None)
    
    def get_client_nickname(self, client_socket: socket.socket) -> str:
        """
        获取客户端昵称
        
        Args:
            client_socket: 客户端socket对象
            
        Returns:
            str: 客户端昵称
        """
        try:
            # 请求客户端昵称
            client_socket.send("NICKNAME_REQUEST".encode(ServerConfig.ENCODING))
            
            # 接收昵称
            nickname_data = client_socket.recv(ServerConfig.BUFFER_SIZE)
            nickname = nickname_data.decode(ServerConfig.ENCODING).strip()
            
            # 验证昵称格式
            if nickname and len(nickname) <= 20 and nickname.isalnum():
                return nickname
            else:
                return f"User_{int(time.time()) % 10000}"
                
        except:
            return f"User_{int(time.time()) % 10000}"
    
    def handle_client(self, client_connection: ClientConnection):
        """
        处理单个客户端的消息
        
        Args:
            client_connection: 客户端连接对象
        """
        client_id = f"{client_connection.address[0]}:{client_connection.address[1]}"
        
        try:
            # 发送欢迎消息
            welcome_msg = f"🎉 欢迎 {client_connection.nickname} 加入聊天室!"
            self.broadcast_message("系统", welcome_msg, exclude_client=client_id)
            safe_print(f"👋 {client_connection.nickname} ({client_connection.address[0]}) 加入了聊天室")
            
            # 发送当前在线用户列表
            online_users = [client.nickname for client in self.clients.values() if client.is_active]
            users_msg = f"👥 当前在线用户: {', '.join(online_users)}"
            client_connection.send_message(format_message("系统", users_msg))
            
            # 持续接收客户端消息
            while client_connection.is_active and self.is_running:
                try:
                    # 接收消息
                    data = client_connection.socket.recv(ServerConfig.BUFFER_SIZE)
                    
                    if not data:
                        # 客户端断开连接
                        break
                    
                    message = data.decode(ServerConfig.ENCODING).strip()
                    
                    if not message:
                        continue
                    
                    # 处理特殊命令
                    if message.startswith('/'):
                        self.handle_command(client_connection, message)
                    else:
                        # 普通聊天消息
                        formatted_msg = format_message(client_connection.nickname, message)
                        safe_print(formatted_msg)
                        
                        # 广播消息给其他客户端
                        self.broadcast_message(client_connection.nickname, message, exclude_client=client_id)
                    
                    # 更新活动时间
                    client_connection.last_activity = datetime.now()
                    
                except socket.timeout:
                    # 接收超时，检查客户端是否仍然活跃
                    continue
                except ConnectionResetError:
                    # 客户端强制断开连接
                    break
                except Exception as e:
                    safe_print(f"❌ 处理客户端 {client_connection.nickname} 消息时出错: {e}")
                    break
                    
        except Exception as e:
            safe_print(f"❌ 客户端处理线程异常: {e}")
        finally:
            # 清理客户端连接
            self.remove_client(client_id)
            client_connection.close()
            
            # 通知其他客户端
            leave_msg = f"👋 {client_connection.nickname} 离开了聊天室"
            self.broadcast_message("系统", leave_msg)
            safe_print(f"📤 {client_connection.nickname} ({client_connection.address[0]}) 离开了聊天室")
    
    def handle_command(self, client_connection: ClientConnection, command: str):
        """
        处理客户端命令
        
        Args:
            client_connection: 客户端连接对象
            command: 命令字符串
        """
        try:
            if command == '/quit':
                # 客户端请求退出
                client_connection.send_message(format_message("系统", "再见! 👋"))
                client_connection.is_active = False
                
            elif command == '/help':
                # 显示帮助信息
                help_text = """
📋 聊天室命令帮助:
/help - 显示此帮助信息
/quit - 退出聊天室
/users - 查看在线用户列表
/time - 显示当前时间
"""
                client_connection.send_message(help_text)
                
            elif command == '/users':
                # 显示在线用户列表
                with self.clients_lock:
                    online_users = [client.nickname for client in self.clients.values() if client.is_active]
                users_text = f"👥 在线用户 ({len(online_users)}): {', '.join(online_users)}"
                client_connection.send_message(format_message("系统", users_text))
                
            elif command == '/time':
                # 显示当前时间
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                client_connection.send_message(format_message("系统", f"🕒 当前时间: {current_time}"))
                
            else:
                # 未知命令
                client_connection.send_message(format_message("系统", f"❓ 未知命令: {command}，输入 /help 查看帮助"))
                
        except Exception as e:
            safe_print(f"❌ 处理命令时出错: {e}")
    
    def broadcast_message(self, sender: str, message: str, exclude_client: str = ""):
        """
        广播消息给所有客户端
        
        Args:
            sender: 发送者名称
            message: 消息内容
            exclude_client: 排除的客户端ID（不发送给此客户端）
        """
        if not self.clients:
            return
        
        formatted_message = format_message(sender, message)
        
        with self.message_lock:
            # 获取要断开的客户端列表
            clients_to_remove = []
            
            for client_id, client_conn in self.clients.items():
                if client_id == exclude_client:
                    continue
                    
                if not client_conn.is_active:
                    clients_to_remove.append(client_id)
                    continue
                
                # 尝试发送消息
                if not client_conn.send_message(formatted_message):
                    clients_to_remove.append(client_id)
            
            # 移除失效的客户端连接
            for client_id in clients_to_remove:
                self.remove_client(client_id)
    
    def remove_client(self, client_id: str):
        """
        移除客户端连接
        
        Args:
            client_id: 客户端ID
        """
        with self.clients_lock:
            if client_id in self.clients:
                del self.clients[client_id]
    
    def accept_connections(self):
        """
        接受新的客户端连接（在独立线程中运行）
        """
        while self.is_running:
            try:
                # 接受新连接
                client_socket, client_address = self.server_socket.accept()
                
                safe_print(f"🔗 新连接来自: {client_address[0]}:{client_address[1]}")
                
                # 检查连接数限制
                if len(self.clients) >= ServerConfig.MAX_CLIENTS:
                    client_socket.send("SERVER_FULL".encode(ServerConfig.ENCODING))
                    client_socket.close()
                    safe_print(f"❌ 拒绝连接 {client_address[0]} - 服务器已满")
                    continue
                
                # 验证客户端
                if not self.authenticate_client(client_socket):
                    client_socket.close()
                    safe_print(f"❌ 客户端 {client_address[0]} 认证失败")
                    continue
                
                # 获取客户端昵称
                nickname = self.get_client_nickname(client_socket)
                
                # 创建客户端连接对象
                client_connection = ClientConnection(client_socket, client_address, nickname)
                client_id = f"{client_address[0]}:{client_address[1]}"
                
                # 添加到客户端列表
                with self.clients_lock:
                    self.clients[client_id] = client_connection
                
                # 为客户端创建处理线程
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_connection,),
                    name=f"Client-{nickname}",
                    daemon=True
                )
                client_thread.start()
                
                safe_print(f"✅ 客户端 {nickname} 连接成功，当前在线: {len(self.clients)}")
                
            except OSError:
                # 服务器socket被关闭
                break
            except Exception as e:
                if self.is_running:
                    safe_print(f"❌ 接受连接时出错: {e}")
                break
    
    def server_input_handler(self):
        """
        处理服务器端输入（在独立线程中运行）
        """
        safe_print("\n💬 服务器已启动，你可以输入消息与客户端聊天")
        safe_print("💡 输入 '/quit' 关闭服务器，'/help' 查看命令帮助")
        safe_print("─"*50)
        
        while self.is_running:
            try:
                server_input = input().strip()
                
                if not server_input:
                    continue
                
                if server_input == '/quit':
                    # 关闭服务器
                    safe_print("🛑 正在关闭服务器...")
                    self.shutdown()
                    break
                    
                elif server_input == '/help':
                    # 显示服务器命令帮助
                    help_text = """
📋 服务器命令帮助:
/quit - 关闭服务器
/help - 显示此帮助信息
/status - 显示服务器状态
/users - 显示在线用户列表
/kick <用户名> - 踢出指定用户
直接输入文字 - 发送系统消息
"""
                    safe_print(help_text)
                    
                elif server_input == '/status':
                    # 显示服务器状态
                    safe_print(f"📊 服务器状态:")
                    safe_print(f"   地址: {self.server_ip}:{self.server_port}")
                    safe_print(f"   在线用户: {len(self.clients)}/{ServerConfig.MAX_CLIENTS}")
                    safe_print(f"   运行时间: {datetime.now() - getattr(self, 'start_time', datetime.now())}")
                    
                elif server_input == '/users':
                    # 显示在线用户
                    if self.clients:
                        safe_print("👥 在线用户列表:")
                        for client in self.clients.values():
                            if client.is_active:
                                safe_print(f"   {client.nickname} ({client.address[0]})")
                    else:
                        safe_print("👤 当前没有用户在线")
                        
                elif server_input.startswith('/kick '):
                    # 踢出用户
                    username = server_input[6:].strip()
                    self.kick_user(username)
                    
                else:
                    # 发送系统消息
                    safe_print(format_message("服务器管理员", server_input))
                    self.broadcast_message("服务器管理员", server_input)
                    
            except KeyboardInterrupt:
                safe_print("\n🛑 检测到中断信号，正在关闭服务器...")
                self.shutdown()
                break
            except EOFError:
                safe_print("\n📄 输入结束，正在关闭服务器...")
                self.shutdown()
                break
            except Exception as e:
                safe_print(f"❌ 服务器输入处理错误: {e}")
    
    def kick_user(self, username: str):
        """
        踢出指定用户
        
        Args:
            username: 要踢出的用户名
        """
        with self.clients_lock:
            for client_id, client_conn in self.clients.items():
                if client_conn.nickname == username and client_conn.is_active:
                    client_conn.send_message(format_message("系统", "你已被管理员踢出聊天室"))
                    client_conn.is_active = False
                    safe_print(f"👢 已踢出用户: {username}")
                    self.broadcast_message("系统", f"{username} 被管理员踢出聊天室", exclude_client=client_id)
                    return
        
        safe_print(f"❌ 未找到用户: {username}")
    
    def shutdown(self):
        """关闭服务器"""
        safe_print("🔄 正在关闭服务器...")
        
        self.is_running = False
        
        # 通知所有客户端服务器关闭
        self.broadcast_message("系统", "🛑 服务器即将关闭，感谢使用！")
        
        # 关闭所有客户端连接
        with self.clients_lock:
            for client_conn in self.clients.values():
                client_conn.close()
            self.clients.clear()
        
        # 关闭服务器socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        safe_print("✅ 服务器已关闭")
    
    def run(self):
        """运行服务器的主函数"""
        try:
            # 记录启动时间
            self.start_time = datetime.now()
            
            # 设置服务器参数
            if not self.setup_server():
                return False
            
            # 启动服务器
            if not self.start_server():
                return False
            
            # 启动接受连接的线程
            accept_thread = threading.Thread(
                target=self.accept_connections,
                name="AcceptConnections",
                daemon=True
            )
            accept_thread.start()
            
            # 启动服务器输入处理线程
            input_thread = threading.Thread(
                target=self.server_input_handler,
                name="ServerInput",
                daemon=True
            )
            input_thread.start()
            
            # 等待线程结束
            try:
                while self.is_running:
                    time.sleep(1)
            except KeyboardInterrupt:
                safe_print("\n🛑 接收到中断信号")
            
            return True
            
        except Exception as e:
            safe_print(f"❌ 服务器运行异常: {e}")
            return False
        finally:
            self.shutdown()


# ================================
# 主函数
# ================================
def main():
    """
    服务器模式的主函数
    """
    try:
        safe_print("🏠 启动聊天室创建模式")
        safe_print("📡 正在初始化服务器...")
        
        # 创建服务器实例
        server = ChatServer()
        
        # 运行服务器
        success = server.run()
        
        if success:
            safe_print("✅ 服务器运行完毕")
        else:
            safe_print("❌ 服务器运行失败")
            
    except KeyboardInterrupt:
        safe_print("\n🛑 服务器被用户中断")
    except Exception as e:
        safe_print(f"❌ 服务器主函数异常: {e}")
    finally:
        safe_print("👋 服务器模式已退出")


# ================================
# 程序入口
# ================================
if __name__ == "__main__":
    main()