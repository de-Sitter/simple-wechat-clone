# Simple WeChat Clone

A lightweight, command-line peer-to-peer chat application built with Python. This project enables real-time text communication between two devices over TCP networks, supporting local area network (LAN).

## 🌟 Features

- **Peer-to-Peer Architecture**: One device acts as server (host), another as client (guest)
- **Real-time Messaging**: Instant text communication with timestamps
- **Network Support**: Works on local area network (LAN)
- **Simple Authentication**: Password-protected chat rooms
- **Multi-threaded**: Simultaneous message sending and receiving
- **Cross-Platform**: Compatible with Windows, macOS, and Linux
- **No Database Required**: Lightweight implementation without external dependencies
- **Command-Line Interface**: Clean, terminal-based user experience

### File Descriptions

- **`main.py`**: Application launcher with menu system for mode selection
- **`server.py`**: TCP server implementation for hosting chat rooms
- **`client.py`**: TCP client implementation for joining chat rooms
- **`utils.py`**: Network utilities, message formatting, and validation functions

## 🚀 Quick Start

### Prerequisites

- Python 3.6 or higher
- Network connection (LAN)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/de-Sitter/simple-wechat-clone.git
   cd simple-wechat-clone
   ```
2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Usage Guide

#### Method 1: Running from source
```bash
cd src
python main.py
```
#### Method 2: Running exe file directly
1. MacOS/Linux
```bash
cd Mac.dist
./main.bin
```
2. Windows
```bash
cd Windows.dist
./main.exe
```
### Starting a Chat Session
#### Step 1: Host Creates Chat Room
1. Run the application 
 2. Select option **1** (Create Chat Room)
 3. Set server port (default: 8888)
 4. Set room password
 5. Share your IP address and password with the guest
 #### Step 2: Guest Joins Chat Room
 1. Run the application
 2. Select option **2** (Join Chat Room)
 3. Enter host's IP address
 4. Enter port number (default: 8888)
 5. Enter room password
 6. Set your nickname
 #### Step 3: Start Chatting
 1. Type messages and press Enter to send
 2. Messages appear in real-time for both users
 3. Use /quit to exit the chat

## Happy Chatting! 💬





