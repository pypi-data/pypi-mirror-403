from pathlib import Path

import fire
import yaml
from rich.console import Console
from rich.columns import Columns
from rich.panel import Panel

from .client_config.client_config import ClientConfig
from .dcd.dcd import DCD
from .task.task import Task
from .role.role import Role
from .run_file.run_file import RunFile
from .run_line.run_line import RunLine

class ENTRY:
    """这个一个灵活的自动化运维工具
    
    CLI入口,按 'q' 退出
    """

    def __init__(self):
        self.dcd = DCD()
        self.task = Task()
        self.role = Role()
        self.runline=RunLine()
        self.rfx = RunFile().x
        self.rler = RunLine().select_and_exec_remote
        self.rlel = RunLine().select_and_exec_local


    def _scan_modules(self) -> list[str]:
        """扫描 modules 目录下的所有模块
        
        Returns:
            模块名称列表
        """
        modules_path = Path(__file__).parent / "modules"
        return [
            d.name for d in modules_path.iterdir()
            if d.is_dir() and not d.name.startswith("_")
        ]

    def list_modules(self):
        """列出所有可用模块"""
        console = Console()
        columns = Columns(self._scan_modules(), equal=True, expand=True, column_first=False)
        panel = Panel(columns, title="可用模块", border_style="blue")
        console.print(panel)

    def list_hostvars(self, hostname: str | None = None):
        """列出主机变量
        
        Args:
            hostname: 主机名，为空则使用默认主机
        """
        config = ClientConfig()
        conn = config.connect(hostname)
        if conn is None:
            return
        console = Console()
        console.print(config.hostvars)

    def test(self, hostname: str | None = None):
        """测试连接
        
        Args:
            hostname: 主机名，为空则使用默认主机
        """
        config = ClientConfig()
        conn = config.connect(hostname)
        if conn:
            print(f"连接成功: {config.hostvars.get('hostname', 'unknown')}")




def main() -> None:
    try:
        fire.Fire(ENTRY)
    except KeyboardInterrupt:
        print("\n操作已取消")
        exit(0)
