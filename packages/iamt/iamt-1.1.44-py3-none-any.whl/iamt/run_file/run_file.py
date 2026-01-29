from pathlib import Path

import yaml
import questionary
from rich.console import Console

from ..client_config.client_config import ClientConfig
from ..task.task import Task


class RunFile:
    """从配置文件执行 task 函数"""

    def x(self) -> None:
        """从当前目录的配置文件执行 task 函数"""

        console = Console()

        # region 扫描配置文件
        config_suffixes = [".dcd.yaml", ".role.yaml"]
        task_config_files: list[Path] = []
        for suffix in config_suffixes:
            task_config_files.extend(Path.cwd().glob(f"*{suffix}"))

        if not task_config_files:
            console.print(f"[yellow]当前目录未找到配置文件 ({', '.join(config_suffixes)})[/yellow]")
            return
        # endregion

        # region 选择配置文件
        if len(task_config_files) == 1:
            selected_file = task_config_files[0]
        else:
            file_choices = [f.name for f in task_config_files]
            selected_name = questionary.select("请选择配置文件:", choices=file_choices).ask()
            if selected_name is None:
                console.print("[yellow]已取消[/yellow]")
                return
            selected_file = Path.cwd() / selected_name
        # endregion

        # region 读取并验证配置
        try:
            config_data = yaml.safe_load(selected_file.read_text(encoding="utf-8"))
        except Exception as e:
            console.print(f"[red]读取配置文件失败: {e}[/red]")
            return

        hostname = config_data.get("hostname", "")
        tasks = config_data.get("tasks", [])

        if not hostname:
            console.print("[red]配置文件缺少 hostname[/red]")
            return
        if not tasks:
            console.print("[red]配置文件缺少 tasks[/red]")
            return
        # endregion

        # region 验证 hostname 并创建连接
        client_config = ClientConfig()
        if not client_config.config_file.exists():
            console.print("[red]未找到 iamt.yaml 配置文件[/red]")
            return

        iamt_config = yaml.safe_load(client_config.config_file.read_text(encoding="utf-8"))
        if hostname not in iamt_config.get("hosts", {}):
            console.print(f"[red]iamt.yaml 中未找到主机: {hostname}[/red]")
            return

        conn = client_config.connect(hostname)
        if conn is None:
            console.print("[red]无法连接到服务器[/red]")
            return
        # endregion

        # region 显示配置信息并确认
        console.print(f"[cyan]配置文件: {selected_file.name}[/cyan]")
        console.print(f"[cyan]目标主机: {hostname}[/cyan]")
        console.print("[cyan]待执行任务:[/cyan]")
        for t in tasks:
            console.print(f"  - {t['task']}: {t['args']}")

        if not questionary.confirm("确认执行?", default=True).ask():
            console.print("[yellow]已取消[/yellow]")
            return
        # endregion

        # region 执行 tasks
        task_scanner = Task()
        scanned_tasks = task_scanner._scan_tasks()

        for task_call in tasks:
            task_name = task_call["task"]
            task_args = task_call.get("args", {}).copy()

            # 解析 task 名称 (格式: module.function)
            parts = task_name.split(".")
            if len(parts) != 2:
                console.print(f"[red]无效的 task 名称: {task_name}[/red]")
                continue

            func_name = parts[1]

            # 从扫描结果中获取 task
            if func_name not in scanned_tasks:
                console.print(f"[red]未找到 task 函数: {task_name}[/red]")
                continue

            task_obj = scanned_tasks[func_name]["task"]

            # 执行 task
            console.print(f"[cyan]执行: {task_name}[/cyan]")
            try:
                task_obj(conn, **task_args)
            except Exception as e:
                console.print(f"[red]执行失败: {e}[/red]")
                return

        console.print("[green]所有任务执行完成[/green]")
        # endregion