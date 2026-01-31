"""iFrp - frpc 管理工具 TUI"""
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress
import questionary
from questionary import Style

import config
import downloader
import runner

console = Console()

# 自定义样式
custom_style = Style([
    ("qmark", "fg:cyan bold"),
    ("question", "fg:white bold"),
    ("answer", "fg:green"),
    ("pointer", "fg:cyan bold"),
    ("highlighted", "fg:cyan bold"),
    ("selected", "fg:green"),
])

def clear_screen():
    console.clear()

def show_banner():
    """显示横幅"""
    banner = """
    ╦╔═╗╦═╗╔═╗
    ║╠╣ ╠╦╝╠═╝
    ╩╚  ╩╚═╩   frpc 管理工具
    """
    console.print(Panel(banner, style="cyan"))

def show_status():
    """显示当前状态"""
    # frpc 版本
    version = downloader.get_current_version()
    status = runner.get_status()

    table = Table(show_header=False, box=None)
    table.add_column("Key", style="dim")
    table.add_column("Value")

    table.add_row("frpc 版本", version or "[red]未安装[/red]")
    table.add_row("运行状态",
        f"[green]运行中 (PID: {status['pid']})[/green]" if status["running"]
        else "[yellow]未运行[/yellow]")

    cfg = config.load_config()
    server_info = config.get_server_info(cfg)
    if server_info["serverAddr"]:
        table.add_row("服务器", f"{server_info['serverAddr']}:{server_info['serverPort']}")
    else:
        table.add_row("服务器", "[red]未配置[/red]")

    proxies = config.get_proxies(cfg)
    table.add_row("代理规则", f"{len(proxies)} 条")

    console.print(Panel(table, title="状态", border_style="blue"))

def menu_download():
    """下载/更新 frpc"""
    console.print("\n[cyan]正在获取最新版本信息...[/cyan]")
    try:
        release = downloader.get_latest_release()
        latest_version = release.get("tag_name", "unknown")
        current_version = downloader.get_current_version()

        console.print(f"最新版本: [green]{latest_version}[/green]")
        if current_version:
            console.print(f"当前版本: [yellow]{current_version}[/yellow]")

        url = downloader.find_download_url(release)
        if not url:
            console.print("[red]未找到适合当前系统的下载链接[/red]")
            return

        if not questionary.confirm("是否下载?", style=custom_style).ask():
            return

        with Progress() as progress:
            archive_path = downloader.download_frpc(url, progress)

        console.print("[cyan]正在解压...[/cyan]")
        frpc_path = downloader.extract_frpc(archive_path)
        console.print(f"[green]frpc 已安装到: {frpc_path}[/green]")

    except Exception as e:
        console.print(f"[red]下载失败: {e}[/red]")

def menu_config_server():
    """配置服务器"""
    cfg = config.load_config()
    server_info = config.get_server_info(cfg)

    console.print("\n[cyan]服务器配置[/cyan]")
    if server_info["serverAddr"]:
        console.print(f"当前: {server_info['serverAddr']}:{server_info['serverPort']}")

    addr = questionary.text(
        "服务器地址:",
        default=server_info["serverAddr"],
        style=custom_style
    ).ask()
    if addr is None:
        return

    port = questionary.text(
        "服务器端口:",
        default=str(server_info["serverPort"]),
        style=custom_style
    ).ask()
    if port is None:
        return

    token = questionary.password(
        "认证Token:",
        default=server_info["token"],
        style=custom_style
    ).ask()
    if token is None:
        return

    try:
        port = int(port)
    except ValueError:
        console.print("[red]端口必须是数字[/red]")
        return

    cfg = config.set_server_info(cfg, addr, port, token)
    config.save_config(cfg)
    console.print("[green]服务器配置已保存[/green]")

def menu_config_proxy():
    """配置代理规则"""
    cfg = config.load_config()
    proxies = config.get_proxies(cfg)

    choices = ["添加新规则"]
    for p in proxies:
        choices.append(f"编辑: {p['name']} ({p['type']} {p['localPort']} -> {p['remotePort']})")
    choices.append("返回")

    choice = questionary.select("代理规则管理:", choices=choices, style=custom_style).ask()
    if choice is None or choice == "返回":
        return

    if choice == "添加新规则":
        add_proxy_rule(cfg)
    else:
        # 编辑现有规则
        proxy_name = choice.split(":")[1].split("(")[0].strip()
        edit_proxy_rule(cfg, proxy_name)

def add_proxy_rule(cfg: dict):
    """添加代理规则"""
    console.print("\n[cyan]添加代理规则[/cyan]")

    name = questionary.text("规则名称:", style=custom_style).ask()
    if not name:
        return

    proxy_type = questionary.select(
        "代理类型:",
        choices=["tcp", "udp", "http", "https"],
        style=custom_style
    ).ask()
    if not proxy_type:
        return

    local_ip = questionary.text("本地IP:", default="127.0.0.1", style=custom_style).ask()
    if not local_ip:
        return

    local_port = questionary.text("本地端口:", style=custom_style).ask()
    if not local_port:
        return

    remote_port = questionary.text("远程端口:", style=custom_style).ask()
    if not remote_port:
        return

    try:
        local_port = int(local_port)
        remote_port = int(remote_port)
    except ValueError:
        console.print("[red]端口必须是数字[/red]")
        return

    cfg = config.add_proxy(cfg, name, proxy_type, local_ip, local_port, remote_port)
    config.save_config(cfg)
    console.print(f"[green]代理规则 '{name}' 已添加[/green]")

def edit_proxy_rule(cfg: dict, name: str):
    """编辑代理规则"""
    action = questionary.select(
        f"操作 '{name}':",
        choices=["删除", "返回"],
        style=custom_style
    ).ask()

    if action == "删除":
        if questionary.confirm(f"确定删除 '{name}'?", style=custom_style).ask():
            cfg = config.remove_proxy(cfg, name)
            config.save_config(cfg)
            console.print(f"[green]代理规则 '{name}' 已删除[/green]")

def menu_start():
    """启动 frpc"""
    # 先检查状态
    status, pid = runner.check_before_start()

    if status == "running":
        console.print(f"[yellow]发现 frpc 已在运行中 (PID: {pid})[/yellow]")
        if questionary.confirm("是否停止现有进程并重新启动?", style=custom_style).ask():
            runner.stop_frpc()
            console.print("[cyan]正在重新启动...[/cyan]")
        else:
            return
    elif status == "stale":
        console.print(f"[yellow]发现残留的 PID 记录 ({pid})，但进程已不存在[/yellow]")
        runner.cleanup_stale_pid()
        console.print("[cyan]已清理，正在启动...[/cyan]")

    success, msg = runner.start_frpc()
    if success:
        console.print(f"[green]{msg}[/green]")
    else:
        console.print(f"[red]{msg}[/red]")

def menu_stop():
    """停止 frpc"""
    success, msg = runner.stop_frpc()
    if success:
        console.print(f"[green]{msg}[/green]")
    else:
        console.print(f"[yellow]{msg}[/yellow]")

def menu_config():
    """配置管理子菜单"""
    while True:
        choice = questionary.select(
            "配置管理:",
            choices=[
                "服务器设置",
                "代理规则",
                "查看配置文件",
                "返回主菜单"
            ],
            style=custom_style
        ).ask()

        if choice is None or choice == "返回主菜单":
            break
        elif choice == "服务器设置":
            menu_config_server()
        elif choice == "代理规则":
            menu_config_proxy()
        elif choice == "查看配置文件":
            show_config_file()

def show_config_file():
    """显示配置文件内容"""
    if config.CONFIG_FILE.exists():
        with open(config.CONFIG_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        console.print(Panel(content, title="config.toml", border_style="green"))
    else:
        console.print("[yellow]配置文件不存在[/yellow]")

def main_menu():
    """主菜单"""
    while True:
        clear_screen()
        show_banner()
        show_status()

        choice = questionary.select(
            "请选择操作:",
            choices=[
                "下载/更新 frpc",
                "配置管理",
                "启动 frpc",
                "停止 frpc",
                "退出"
            ],
            style=custom_style
        ).ask()

        if choice is None or choice == "退出":
            # 退出前停止 frpc
            if runner.is_running():
                if questionary.confirm("frpc 正在运行，是否停止?", style=custom_style).ask():
                    runner.stop_frpc()
            console.print("[cyan]再见！[/cyan]")
            break
        elif choice == "下载/更新 frpc":
            menu_download()
        elif choice == "配置管理":
            menu_config()
        elif choice == "启动 frpc":
            menu_start()
        elif choice == "停止 frpc":
            menu_stop()

        if choice != "退出":
            questionary.press_any_key_to_continue("按任意键继续...").ask()

def main():
    """入口函数"""
    try:
        main_menu()
    except KeyboardInterrupt:
        console.print("\n[yellow]已取消[/yellow]")
        if runner.is_running():
            runner.stop_frpc()
        sys.exit(0)

if __name__ == "__main__":
    main()
