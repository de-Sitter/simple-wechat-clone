#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple WeChat Clone - 工具模块
提供网络、消息处理、输入验证等通用工具函数

主要功能:
- 网络工具：IP地址获取、连接测试、端口验证
- 消息处理：消息格式化、输入清理、长度验证
- 输入验证：IP、端口、昵称、密码格式验证
- 界面工具：安全打印、清屏、进度显示
- 系统工具：配置管理、依赖检查、系统信息

作者: de-Sitter
版本: 1.0
"""

import socket
import threading
import time
import re
import os
import sys
import json
import platform
import subprocess
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any
import ipaddress


# ================================
# 全局配置和常量
# ================================
class UtilsConfig:
    """工具模块配置"""
    
    # 网络配置
    DEFAULT_TIMEOUT = 5
    PORT_RANGE_MIN = 1024
    PORT_RANGE_MAX = 65535
    COMMON_PORTS = [8888, 9999, 8080, 3000, 5000]
    
    # 消息配置
    MAX_MESSAGE_LENGTH = 500
    MAX_NICKNAME_LENGTH = 20
    MAX_PASSWORD_LENGTH = 50
    MESSAGE_ENCODING = 'utf-8'
    
    # 时间格式
    TIMESTAMP_FORMAT = "%H:%M:%S"
    FULL_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
    
    # 颜色代码（用于终端彩色输出）
    COLORS = {
        'RED': '\033[91m',
        'GREEN': '\033[92m',
        'YELLOW': '\033[93m',
        'BLUE': '\033[94m',
        'PURPLE': '\033[95m',
        'CYAN': '\033[96m',
        'WHITE': '\033[97m',
        'BOLD': '\033[1m',
        'UNDERLINE': '\033[4m',
        'END': '\033[0m'
    }


# 线程锁，用于安全打印
_print_lock = threading.Lock()


# ================================
# 网络工具函数
# ================================
def get_local_ip() -> str:
    """
    获取本机IP地址
    
    Returns:
        str: 本机IP地址，获取失败返回127.0.0.1
    """
    try:
        # 方法1：通过连接外部服务获取本机IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # 连接到Google DNS，不会实际发送数据
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            return local_ip
    except Exception:
        try:
            # 方法2：通过主机名获取IP
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            if local_ip != "127.0.0.1":
                return local_ip
        except Exception:
            pass
    
    # 方法3：默认返回本地回环地址
    return "127.0.0.1"


def get_all_local_ips() -> List[str]:
    """
    获取所有网络接口的IP地址
    
    Returns:
        List[str]: IP地址列表
    """
    ip_list = []
    
    try:
        # 获取主机名对应的所有IP
        hostname = socket.gethostname()
        ips = socket.getaddrinfo(hostname, None, socket.AF_INET)
        
        for ip_info in ips:
            ip = ip_info[4][0]
            if ip not in ip_list and ip != "127.0.0.1":
                ip_list.append(ip)
    except Exception:
        pass
    
    # 添加通过外部连接获取的IP
    main_ip = get_local_ip()
    if main_ip not in ip_list:
        ip_list.insert(0, main_ip)
    
    return ip_list


def validate_ip(ip_address: str) -> bool:
    """
    验证IP地址格式是否正确
    
    Args:
        ip_address: 要验证的IP地址字符串
        
    Returns:
        bool: 有效返回True，无效返回False
    """
    try:
        # 使用ipaddress模块验证
        ipaddress.IPv4Address(ip_address)
        return True
    except ipaddress.AddressValueError:
        return False
    except Exception:
        # 备用验证方法
        try:
            parts = ip_address.split('.')
            if len(parts) != 4:
                return False
            
            for part in parts:
                num = int(part)
                if not (0 <= num <= 255):
                    return False
            
            return True
        except (ValueError, AttributeError):
            return False


def validate_port(port: Any) -> bool:
    """
    验证端口号是否有效
    
    Args:
        port: 端口号（可以是int或str）
        
    Returns:
        bool: 有效返回True，无效返回False
    """
    try:
        port_num = int(port)
        return UtilsConfig.PORT_RANGE_MIN <= port_num <= UtilsConfig.PORT_RANGE_MAX
    except (ValueError, TypeError):
        return False


def check_port_available(port: int, host: str = "localhost") -> bool:
    """
    检查指定端口是否可用
    
    Args:
        port: 端口号
        host: 主机地址，默认为localhost
        
    Returns:
        bool: 端口可用返回True，被占用返回False
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex((host, port))
            return result != 0  # 0表示连接成功（端口被占用）
    except Exception:
        return False


def get_free_port(start_port: int = 8888, max_attempts: int = 100) -> Optional[int]:
    """
    获取一个可用的端口号
    
    Args:
        start_port: 起始端口号
        max_attempts: 最大尝试次数
        
    Returns:
        Optional[int]: 可用端口号，找不到返回None
    """
    for i in range(max_attempts):
        port = start_port + i
        if port > UtilsConfig.PORT_RANGE_MAX:
            break
        
        if check_port_available(port):
            return port
    
    return None


def test_connection(host: str, port: int, timeout: float = UtilsConfig.DEFAULT_TIMEOUT) -> Tuple[bool, str]:
    """
    测试到指定主机和端口的连接
    
    Args:
        host: 主机地址
        port: 端口号
        timeout: 超时时间（秒）
        
    Returns:
        Tuple[bool, str]: (连接是否成功, 结果描述)
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            start_time = time.time()
            result = s.connect_ex((host, port))
            end_time = time.time()
            
            if result == 0:
                response_time = int((end_time - start_time) * 1000)
                return True, f"连接成功，响应时间: {response_time}ms"
            else:
                return False, "连接被拒绝或超时"
                
    except socket.gaierror:
        return False, "无法解析主机地址"
    except socket.timeout:
        return False, f"连接超时（{timeout}秒）"
    except Exception as e:
        return False, f"连接错误: {str(e)}"


def ping_host(host: str) -> Tuple[bool, str]:
    """
    使用ping命令测试主机连通性
    
    Args:
        host: 主机地址
        
    Returns:
        Tuple[bool, str]: (ping是否成功, 结果描述)
    """
    try:
        # 根据操作系统选择ping命令参数
        if platform.system().lower() == "windows":
            cmd = ["ping", "-n", "1", "-w", "3000", host]
        else:
            cmd = ["ping", "-c", "1", "-W", "3", host]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            return True, "主机可达"
        else:
            return False, "主机不可达"
            
    except subprocess.TimeoutExpired:
        return False, "ping超时"
    except FileNotFoundError:
        return False, "ping命令不可用"
    except Exception as e:
        return False, f"ping错误: {str(e)}"


# ================================
# 消息处理工具函数
# ================================
def format_message(sender: str, content: str, timestamp: Optional[datetime] = None) -> str:
    """
    格式化聊天消息
    
    Args:
        sender: 发送者名称
        content: 消息内容
        timestamp: 时间戳，None则使用当前时间
        
    Returns:
        str: 格式化后的消息
    """
    if timestamp is None:
        timestamp = datetime.now()
    
    time_str = timestamp.strftime(UtilsConfig.TIMESTAMP_FORMAT)
    
    # 清理发送者名称和内容
    clean_sender = sanitize_input(sender, max_length=UtilsConfig.MAX_NICKNAME_LENGTH)
    clean_content = sanitize_input(content, max_length=UtilsConfig.MAX_MESSAGE_LENGTH)
    
    return f"[{time_str}] {clean_sender}: {clean_content}"


def parse_message(formatted_message: str) -> Optional[Dict[str, str]]:
    """
    解析格式化的消息
    
    Args:
        formatted_message: 格式化的消息字符串
        
    Returns:
        Optional[Dict[str, str]]: 解析结果字典，包含timestamp、sender、content，失败返回None
    """
    try:
        # 使用正则表达式解析消息格式：[时间] 发送者: 内容
        pattern = r'^\[(\d{2}:\d{2}:\d{2})\] ([^:]+): (.+)$'
        match = re.match(pattern, formatted_message.strip())
        
        if match:
            return {
                'timestamp': match.group(1),
                'sender': match.group(2).strip(),
                'content': match.group(3).strip()
            }
        else:
            return None
            
    except Exception:
        return None


def sanitize_input(text: str, max_length: Optional[int] = None, allow_newlines: bool = False) -> str:
    """
    清理和验证用户输入
    
    Args:
        text: 要清理的文本
        max_length: 最大长度限制
        allow_newlines: 是否允许换行符
        
    Returns:
        str: 清理后的文本
    """
    if not isinstance(text, str):
        text = str(text)
    
    # 移除首尾空白
    text = text.strip()
    
    # 处理换行符
    if not allow_newlines:
        text = text.replace('\n', ' ').replace('\r', ' ')
    
    # 移除控制字符（保留基本的空白字符）
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    # 压缩多个连续空格为单个空格
    text = re.sub(r'\s+', ' ', text)
    
    # 长度限制
    if max_length and len(text) > max_length:
        text = text[:max_length].rstrip()
    
    return text


def truncate_message(message: str, max_length: int = UtilsConfig.MAX_MESSAGE_LENGTH) -> str:
    """
    截断过长的消息
    
    Args:
        message: 原始消息
        max_length: 最大长度
        
    Returns:
        str: 截断后的消息
    """
    if len(message) <= max_length:
        return message
    
    # 截断并添加省略号
    return message[:max_length-3] + "..."


def encode_message(message: str, encoding: str = UtilsConfig.MESSAGE_ENCODING) -> bytes:
    """
    编码消息为字节
    
    Args:
        message: 要编码的消息
        encoding: 编码方式
        
    Returns:
        bytes: 编码后的字节数据
    """
    try:
        return message.encode(encoding)
    except UnicodeEncodeError:
        # 如果编码失败，使用错误处理机制
        return message.encode(encoding, errors='replace')


def decode_message(data: bytes, encoding: str = UtilsConfig.MESSAGE_ENCODING) -> str:
    """
    解码字节数据为消息
    
    Args:
        data: 字节数据
        encoding: 编码方式
        
    Returns:
        str: 解码后的消息
    """
    try:
        return data.decode(encoding)
    except UnicodeDecodeError:
        # 如果解码失败，使用错误处理机制
        return data.decode(encoding, errors='replace')


# ================================
# 输入验证工具函数
# ================================
def validate_nickname(nickname: str) -> Tuple[bool, str]:
    """
    验证昵称格式
    
    Args:
        nickname: 昵称字符串
        
    Returns:
        Tuple[bool, str]: (是否有效, 错误信息)
    """
    if not nickname:
        return False, "昵称不能为空"
    
    # 长度检查
    if len(nickname) > UtilsConfig.MAX_NICKNAME_LENGTH:
        return False, f"昵称长度不能超过{UtilsConfig.MAX_NICKNAME_LENGTH}个字符"
    
    # 字符检查：只允许字母、数字、中文、下划线
    if not re.match(r'^[\w\u4e00-\u9fa5]+$', nickname):
        return False, "昵称只能包含字母、数字、中文和下划线"
    
    # 禁止的昵称
    forbidden_names = ['admin', 'root', 'system', 'server', '系统', '管理员', '服务器']
    if nickname.lower() in forbidden_names:
        return False, "此昵称不可用"
    
    return True, "昵称有效"


def validate_password(password: str) -> Tuple[bool, str]:
    """
    验证密码格式
    
    Args:
        password: 密码字符串
        
    Returns:
        Tuple[bool, str]: (是否有效, 错误信息)
    """
    if not password:
        return False, "密码不能为空"
    
    # 长度检查
    if len(password) > UtilsConfig.MAX_PASSWORD_LENGTH:
        return False, f"密码长度不能超过{UtilsConfig.MAX_PASSWORD_LENGTH}个字符"
    
    # 基本字符检查
    if not re.match(r'^[^\s]+$', password):
        return False, "密码不能包含空格"
    
    return True, "密码有效"


def validate_message(message: str) -> Tuple[bool, str]:
    """
    验证消息内容
    
    Args:
        message: 消息内容
        
    Returns:
        Tuple[bool, str]: (是否有效, 错误信息)
    """
    if not message.strip():
        return False, "消息不能为空"
    
    # 长度检查
    if len(message) > UtilsConfig.MAX_MESSAGE_LENGTH:
        return False, f"消息长度不能超过{UtilsConfig.MAX_MESSAGE_LENGTH}个字符"
    
    return True, "消息有效"


# ================================
# 界面工具函数
# ================================
def safe_print(*args, **kwargs):
    """
    线程安全的打印函数
    
    Args:
        *args: 打印参数
        **kwargs: 打印关键字参数
    """
    with _print_lock:
        print(*args, **kwargs)


def colored_print(message: str, color: str = 'WHITE', bold: bool = False, end: str = '\n'):
    """
    彩色打印函数
    
    Args:
        message: 要打印的消息
        color: 颜色名称
        bold: 是否加粗
        end: 结尾字符
    """
    color_code = UtilsConfig.COLORS.get(color.upper(), UtilsConfig.COLORS['WHITE'])
    bold_code = UtilsConfig.COLORS['BOLD'] if bold else ''
    end_code = UtilsConfig.COLORS['END']
    
    colored_message = f"{bold_code}{color_code}{message}{end_code}"
    safe_print(colored_message, end=end)


def print_banner(title: str, width: int = 50, char: str = '='):
    """
    打印横幅标题
    
    Args:
        title: 标题文本
        width: 横幅宽度
        char: 装饰字符
    """
    safe_print(char * width)
    safe_print(f"{title:^{width}}")
    safe_print(char * width)


def print_progress_bar(current: int, total: int, width: int = 30, desc: str = "进度"):
    """
    打印进度条
    
    Args:
        current: 当前进度
        total: 总进度
        width: 进度条宽度
        desc: 描述文本
    """
    if total == 0:
        return
    
    percent = min(100, int((current / total) * 100))
    filled_width = int((current / total) * width)
    
    bar = "█" * filled_width + "░" * (width - filled_width)
    safe_print(f"\r{desc}: |{bar}| {percent}% ({current}/{total})", end='', flush=True)
    
    if current >= total:
        safe_print()  # 完成后换行


def clear_screen():
    """清屏函数"""
    os.system('cls' if os.name == 'nt' else 'clear')


# ================================
# 时间工具函数
# ================================
def get_timestamp(format_str: str = UtilsConfig.TIMESTAMP_FORMAT) -> str:
    """
    获取当前时间戳字符串
    
    Args:
        format_str: 时间格式字符串
        
    Returns:
        str: 格式化的时间字符串
    """
    return datetime.now().strftime(format_str)


def get_full_timestamp() -> str:
    """
    获取完整的时间戳字符串
    
    Returns:
        str: 完整的时间戳
    """
    return get_timestamp(UtilsConfig.FULL_TIMESTAMP_FORMAT)


def format_duration(seconds: float) -> str:
    """
    格式化时长为可读字符串
    
    Args:
        seconds: 秒数
        
    Returns:
        str: 格式化的时长字符串
    """
    if seconds < 60:
        return f"{seconds:.1f}秒"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}分{secs}秒"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}小时{minutes}分"


# ================================
# 配置工具函数
# ================================
def load_config(config_file: str = "config.json") -> Dict[str, Any]:
    """
    加载配置文件
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        Dict[str, Any]: 配置字典
    """
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {}
    except Exception as e:
        safe_print(f"❌ 加载配置文件失败: {e}")
        return {}


def save_config(config: Dict[str, Any], config_file: str = "config.json") -> bool:
    """
    保存配置文件
    
    Args:
        config: 配置字典
        config_file: 配置文件路径
        
    Returns:
        bool: 保存成功返回True，失败返回False
    """
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        safe_print(f"❌ 保存配置文件失败: {e}")
        return False


# ================================
# 系统工具函数
# ================================
def get_system_info() -> Dict[str, str]:
    """
    获取系统信息
    
    Returns:
        Dict[str, str]: 系统信息字典
    """
    try:
        return {
            'platform': platform.platform(),
            'system': platform.system(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'hostname': socket.gethostname(),
            'local_ip': get_local_ip()
        }
    except Exception:
        return {'error': '无法获取系统信息'}


def check_python_version(min_version: Tuple[int, int] = (3, 6)) -> Tuple[bool, str]:
    """
    检查Python版本
    
    Args:
        min_version: 最低版本要求
        
    Returns:
        Tuple[bool, str]: (版本是否满足, 版本信息)
    """
    current_version = sys.version_info[:2]
    version_str = f"{current_version[0]}.{current_version[1]}"
    
    if current_version >= min_version:
        return True, f"Python {version_str} (满足要求)"
    else:
        min_version_str = f"{min_version[0]}.{min_version[1]}"
        return False, f"Python {version_str} (需要 {min_version_str} 或更高版本)"


def check_dependencies(modules: List[str]) -> Dict[str, bool]:
    """
    检查模块依赖
    
    Args:
        modules: 模块名称列表
        
    Returns:
        Dict[str, bool]: 模块可用性字典
    """
    results = {}
    for module in modules:
        try:
            __import__(module)
            results[module] = True
        except ImportError:
            results[module] = False
    
    return results


# ================================
# 文件工具函数
# ================================
def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除不安全字符
    
    Args:
        filename: 原始文件名
        
    Returns:
        str: 清理后的文件名
    """
    # 移除或替换不安全字符
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        filename = filename.replace(char, '_')
    
    # 移除首尾的点和空格
    filename = filename.strip('. ')
    
    # 确保文件名不为空
    if not filename:
        filename = "unnamed"
    
    return filename


def ensure_directory(directory: str) -> bool:
    """
    确保目录存在，不存在则创建
    
    Args:
        directory: 目录路径
        
    Returns:
        bool: 成功返回True，失败返回False
    """
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except Exception as e:
        safe_print(f"❌ 创建目录失败: {e}")
        return False


# ================================
# 数据处理工具函数
# ================================
def format_bytes(bytes_count: int) -> str:
    """
    格式化字节数为可读字符串
    
    Args:
        bytes_count: 字节数
        
    Returns:
        str: 格式化的字节字符串
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_count < 1024.0:
            return f"{bytes_count:.1f} {unit}"
        bytes_count /= 1024.0
    return f"{bytes_count:.1f} PB"


def generate_random_string(length: int = 8, charset: str = "abcdefghijklmnopqrstuvwxyz0123456789") -> str:
    """
    生成随机字符串
    
    Args:
        length: 字符串长度
        charset: 字符集
        
    Returns:
        str: 随机字符串
    """
    import random
    return ''.join(random.choice(charset) for _ in range(length))


# ================================
# 调试工具函数
# ================================
def debug_print(message: str, enable: bool = True):
    """
    调试打印函数
    
    Args:
        message: 调试消息
        enable: 是否启用调试输出
    """
    if enable:
        timestamp = get_timestamp()
        safe_print(f"[DEBUG {timestamp}] {message}")


def log_function_call(func_name: str, args: tuple = (), kwargs: dict = None):
    """
    记录函数调用
    
    Args:
        func_name: 函数名
        args: 位置参数
        kwargs: 关键字参数
    """
    kwargs = kwargs or {}
    timestamp = get_timestamp()
    safe_print(f"[CALL {timestamp}] {func_name}({args}, {kwargs})")


# ================================
# 模块测试函数
# ================================
def test_utils():
    """测试工具模块的主要功能"""
    safe_print("🧪 开始测试工具模块...")
    
    # 测试网络功能
    safe_print("\n📡 测试网络功能:")
    local_ip = get_local_ip()
    safe_print(f"本机IP: {local_ip}")
    safe_print(f"IP验证: {validate_ip(local_ip)}")
    safe_print(f"端口验证: {validate_port(8888)}")
    
    # 测试消息处理
    safe_print("\n💬 测试消息处理:")
    test_message = format_message("测试用户", "这是一条测试消息")
    safe_print(f"格式化消息: {test_message}")
    parsed = parse_message(test_message)
    safe_print(f"解析结果: {parsed}")
    
    # 测试输入验证
    safe_print("\n✅ 测试输入验证:")
    nickname_valid, nickname_msg = validate_nickname("TestUser123")
    safe_print(f"昵称验证: {nickname_valid} - {nickname_msg}")
    
    # 测试系统信息
    safe_print("\n🖥️  系统信息:")
    sys_info = get_system_info()
    for key, value in sys_info.items():
        safe_print(f"{key}: {value}")
    
    safe_print("\n✅ 工具模块测试完成!")


# ================================
# 主函数（用于测试）
# ================================
if __name__ == "__main__":
    test_utils()