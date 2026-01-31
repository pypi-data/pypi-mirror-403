"""frpc 进程管理模块"""
import subprocess
import os
import sys
from pathlib import Path
from typing import Optional

from config import CONFIG_FILE, CONFIG_DIR
from downloader import get_frpc_path

# PID 文件路径
PID_FILE = CONFIG_DIR / "frpc.pid"

# 当前会话的进程引用（用于读取输出）
_frpc_process: Optional[subprocess.Popen] = None

def _save_pid(pid: int):
    """保存 PID 到文件"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(PID_FILE, "w") as f:
        f.write(str(pid))

def _load_pid() -> Optional[int]:
    """从文件加载 PID"""
    if not PID_FILE.exists():
        return None
    try:
        with open(PID_FILE, "r") as f:
            return int(f.read().strip())
    except (ValueError, IOError):
        return None

def _remove_pid():
    """删除 PID 文件"""
    if PID_FILE.exists():
        PID_FILE.unlink()

def _is_process_running(pid: int) -> bool:
    """检查指定 PID 的进程是否在运行"""
    if sys.platform == "win32":
        # Windows: 使用 tasklist 检查
        try:
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                capture_output=True, text=True, timeout=5
            )
            return str(pid) in result.stdout
        except Exception:
            return False
    else:
        # Unix: 使用 os.kill(pid, 0)
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

def start_frpc() -> tuple[bool, str]:
    """启动 frpc 进程"""
    global _frpc_process

    # 检查是否已有进程在运行
    existing_pid = _load_pid()
    if existing_pid and _is_process_running(existing_pid):
        return False, f"frpc 已在运行中 (PID: {existing_pid})"

    frpc_path = get_frpc_path()
    if not frpc_path:
        return False, "frpc 未安装，请先下载"

    if not CONFIG_FILE.exists():
        return False, "配置文件不存在，请先配置"

    try:
        # 使用 CREATE_NEW_PROCESS_GROUP 让进程独立运行
        kwargs = {}
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

        _frpc_process = subprocess.Popen(
            [str(frpc_path), "-c", str(CONFIG_FILE)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            **kwargs
        )
        _save_pid(_frpc_process.pid)
        return True, f"frpc 已启动 (PID: {_frpc_process.pid})"
    except Exception as e:
        return False, f"启动失败: {e}"

def stop_frpc() -> tuple[bool, str]:
    """停止 frpc 进程"""
    global _frpc_process

    pid = _load_pid()
    if not pid:
        return False, "frpc 未在运行（无 PID 记录）"

    if not _is_process_running(pid):
        _remove_pid()
        return False, "frpc 未在运行（进程已结束）"

    try:
        if sys.platform == "win32":
            # Windows: 使用 taskkill
            subprocess.run(["taskkill", "/PID", str(pid), "/F"],
                          capture_output=True, timeout=10)
        else:
            # Unix: 发送 SIGTERM
            os.kill(pid, 15)

        _remove_pid()
        _frpc_process = None
        return True, f"frpc 已停止 (PID: {pid})"
    except Exception as e:
        return False, f"停止失败: {e}"

def is_running() -> bool:
    """检查 frpc 是否在运行"""
    pid = _load_pid()
    if not pid:
        return False
    return _is_process_running(pid)

def get_status() -> dict:
    """获取 frpc 状态"""
    pid = _load_pid()
    if pid and _is_process_running(pid):
        return {"running": True, "pid": pid}
    else:
        # 清理无效的 PID 文件
        if pid:
            _remove_pid()
        return {"running": False, "pid": None}

def check_before_start() -> tuple[str, Optional[int]]:
    """
    启动前检查状态
    返回: (状态码, PID)
    状态码:
    - "ready": 可以直接启动
    - "running": 已有进程在运行
    - "stale": PID文件存在但进程已结束
    """
    pid = _load_pid()
    if not pid:
        return "ready", None
    if _is_process_running(pid):
        return "running", pid
    else:
        return "stale", pid

def cleanup_stale_pid():
    """清理过期的 PID 文件"""
    _remove_pid()
