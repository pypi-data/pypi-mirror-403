# iFrp

一个简单的 [frpc](https://github.com/fatedier/frp) 客户端管理工具，提供 TUI 界面。

[English](README.md)

## 功能

- 自动下载/更新最新版 frpc（从 GitHub Releases）
- TUI 界面配置服务器连接信息
- 管理代理规则（TCP/UDP/HTTP/HTTPS）
- 启动/停止 frpc 进程

## 安装

### 使用 pip（推荐）

```bash
pip install ifrp
```

### 使用 pipx

```bash
pipx install ifrp
```

### 使用 uv

```bash
uv tool install ifrp
```

### 一键安装

**Linux/macOS:**
```bash
curl -fsSL https://raw.githubusercontent.com/lanbinleo/iFrp/main/install.sh | bash
```

**Windows (PowerShell):**
```powershell
irm https://raw.githubusercontent.com/lanbinleo/iFrp/main/install.ps1 | iex
```

## 使用

```bash
ifrp
```

## 主菜单

```
1. 下载/更新 frpc  - 从 GitHub 下载最新版本
2. 配置管理       - 配置服务器和代理规则
3. 启动 frpc      - 启动 frpc 客户端
4. 停止 frpc      - 停止运行中的 frpc
5. 退出
```

## 配置文件

配置文件存储在 `frpc/config.toml`：

```toml
serverAddr = "your-server.com"
serverPort = 7000
auth.method = "token"
auth.token = "your-token"

[[proxies]]
name = "ssh"
type = "tcp"
localIP = "127.0.0.1"
localPort = 22
remotePort = 6000
```

## 环境要求

- Python 3.10+
- 服务端需要运行 frp server (frps)

## 许可证

[MIT](LICENSE)
