"""frpc 下载管理模块"""
import platform
import zipfile
import tarfile
import os
from pathlib import Path
import httpx
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

GITHUB_API = "https://api.github.com/repos/fatedier/frp/releases/latest"
FRPC_DIR = Path(__file__).parent / "frpc"

def get_system_info() -> tuple[str, str]:
    """获取系统信息，返回 (os, arch)"""
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "windows":
        os_name = "windows"
    elif system == "linux":
        os_name = "linux"
    elif system == "darwin":
        os_name = "darwin"
    else:
        os_name = system

    if machine in ("x86_64", "amd64"):
        arch = "amd64"
    elif machine in ("aarch64", "arm64"):
        arch = "arm64"
    elif machine in ("i386", "i686", "x86"):
        arch = "386"
    else:
        arch = machine

    return os_name, arch

def get_latest_release() -> dict:
    """获取最新版本信息"""
    with httpx.Client(follow_redirects=True, timeout=30) as client:
        resp = client.get(GITHUB_API)
        resp.raise_for_status()
        return resp.json()

def find_download_url(release: dict) -> str | None:
    """找到适合当前系统的下载链接"""
    os_name, arch = get_system_info()
    pattern = f"frp_*_{os_name}_{arch}"

    for asset in release.get("assets", []):
        name = asset.get("name", "")
        if os_name in name and arch in name:
            if os_name == "windows" and name.endswith(".zip"):
                return asset.get("browser_download_url")
            elif os_name != "windows" and name.endswith(".tar.gz"):
                return asset.get("browser_download_url")
    return None

def download_frpc(url: str, progress: Progress) -> Path:
    """下载 frpc"""
    FRPC_DIR.mkdir(parents=True, exist_ok=True)
    filename = url.split("/")[-1]
    download_path = FRPC_DIR / filename

    task = progress.add_task("[cyan]下载中...", total=None)

    with httpx.Client(follow_redirects=True, timeout=60) as client:
        with client.stream("GET", url) as resp:
            resp.raise_for_status()
            total = int(resp.headers.get("content-length", 0))
            progress.update(task, total=total)

            with open(download_path, "wb") as f:
                for chunk in resp.iter_bytes(chunk_size=8192):
                    f.write(chunk)
                    progress.update(task, advance=len(chunk))

    return download_path

def extract_frpc(archive_path: Path) -> Path:
    """解压并提取 frpc 可执行文件"""
    os_name, _ = get_system_info()
    frpc_name = "frpc.exe" if os_name == "windows" else "frpc"
    frpc_path = FRPC_DIR / frpc_name

    if archive_path.suffix == ".zip":
        with zipfile.ZipFile(archive_path, "r") as zf:
            for name in zf.namelist():
                if name.endswith(frpc_name):
                    # 提取到 frpc 目录
                    with zf.open(name) as src:
                        with open(frpc_path, "wb") as dst:
                            dst.write(src.read())
                    break
    elif archive_path.name.endswith(".tar.gz"):
        with tarfile.open(archive_path, "r:gz") as tf:
            for member in tf.getmembers():
                if member.name.endswith(frpc_name):
                    f = tf.extractfile(member)
                    if f:
                        with open(frpc_path, "wb") as dst:
                            dst.write(f.read())
                    break

    # 设置可执行权限 (Linux/macOS)
    if os_name != "windows":
        os.chmod(frpc_path, 0o755)

    # 删除压缩包
    archive_path.unlink()

    return frpc_path

def get_frpc_path() -> Path | None:
    """获取 frpc 可执行文件路径"""
    os_name, _ = get_system_info()
    frpc_name = "frpc.exe" if os_name == "windows" else "frpc"
    frpc_path = FRPC_DIR / frpc_name
    return frpc_path if frpc_path.exists() else None

def get_current_version() -> str | None:
    """获取当前安装的 frpc 版本"""
    import subprocess
    frpc_path = get_frpc_path()
    if not frpc_path:
        return None
    try:
        result = subprocess.run(
            [str(frpc_path), "-v"],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip()
    except Exception:
        return None
