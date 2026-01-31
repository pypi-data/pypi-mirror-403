"""配置管理模块"""
import os
from pathlib import Path
from typing import Optional
import toml

# 默认配置目录
CONFIG_DIR = Path(__file__).parent / "frpc"
CONFIG_FILE = CONFIG_DIR / "config.toml"

# 默认配置模板
DEFAULT_CONFIG = {
    "serverAddr": "",
    "serverPort": 7000,
    "auth.method": "token",
    "auth.token": "",
    "proxies": []
}

def ensure_config_dir():
    """确保配置目录存在"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

def load_config() -> dict:
    """加载配置文件"""
    ensure_config_dir()
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return toml.load(f)
    return DEFAULT_CONFIG.copy()

def save_config(config: dict):
    """保存配置文件"""
    ensure_config_dir()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        toml.dump(config, f)

def get_server_info(config: dict) -> dict:
    """获取服务器信息"""
    return {
        "serverAddr": config.get("serverAddr", ""),
        "serverPort": config.get("serverPort", 7000),
        "token": config.get("auth.token", "")
    }

def set_server_info(config: dict, addr: str, port: int, token: str) -> dict:
    """设置服务器信息"""
    config["serverAddr"] = addr
    config["serverPort"] = port
    config["auth.method"] = "token"
    config["auth.token"] = token
    return config

def add_proxy(config: dict, name: str, proxy_type: str,
              local_ip: str, local_port: int, remote_port: int) -> dict:
    """添加代理规则"""
    if "proxies" not in config:
        config["proxies"] = []

    # 检查是否已存在同名代理
    for i, p in enumerate(config["proxies"]):
        if p.get("name") == name:
            config["proxies"][i] = {
                "name": name,
                "type": proxy_type,
                "localIP": local_ip,
                "localPort": local_port,
                "remotePort": remote_port
            }
            return config

    config["proxies"].append({
        "name": name,
        "type": proxy_type,
        "localIP": local_ip,
        "localPort": local_port,
        "remotePort": remote_port
    })
    return config

def remove_proxy(config: dict, name: str) -> dict:
    """删除代理规则"""
    if "proxies" in config:
        config["proxies"] = [p for p in config["proxies"] if p.get("name") != name]
    return config

def get_proxies(config: dict) -> list:
    """获取所有代理规则"""
    return config.get("proxies", [])
