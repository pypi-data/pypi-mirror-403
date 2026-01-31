# iFrp

A simple TUI tool for managing [frpc](https://github.com/fatedier/frp) client.

[中文文档](README_CN.md)

## Features

- Auto download/update latest frpc from GitHub Releases
- TUI interface for server configuration
- Manage proxy rules (TCP/UDP/HTTP/HTTPS)
- Start/Stop frpc process with ease

## Installation

### Using pip (Recommended)

```bash
pip install ifrp
```

### Using pipx

```bash
pipx install ifrp
```

### Using uv

```bash
uv tool install ifrp
```

### One-line Install

**Linux/macOS:**
```bash
curl -fsSL https://raw.githubusercontent.com/lanbinleo/iFrp/main/install.sh | bash
```

**Windows (PowerShell):**
```powershell
irm https://raw.githubusercontent.com/lanbinleo/iFrp/main/install.ps1 | iex
```

## Usage

```bash
ifrp
```

## Menu Options

```
1. Download/Update frpc  - Download latest version from GitHub
2. Configuration         - Configure server and proxy rules
3. Start frpc            - Start frpc client
4. Stop frpc             - Stop running frpc
5. Exit
```

## Configuration

Config file is stored at `frpc/config.toml`:

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

## Requirements

- Python 3.10+
- frp server (frps) running on your server

## License

[MIT](LICENSE)
