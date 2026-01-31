from rich.console import Console

from ..v2rayN import Connection, install_v2rayn
from ..vscode import install_vscode
from ..kiro import install_kiro
from ..chrome import install_chrome
from ..ibus import install_ibus
from ..._utils.steps import Step, run_steps
from ...github.ghcli import install_gh

console = Console()


def setup_ubuntu_desktop(c: Connection):
    """配置 Ubuntu 桌面开发环境
    
    安装 v2rayN、VSCode、Kiro、Chrome
    """
    steps: list[Step] = [
        # ("安装 v2rayN", install_v2rayn),
        ("安装 VSCode", install_vscode),
        # ("安装 Kiro IDE", install_kiro),
        ("安装 Google Chrome", install_chrome),
        ("安装 ghcli",install_gh),
        # ("安装中文输入法",install_ibus)
    ]
    run_steps(c, steps)
    console.print("[bold green]✓ Ubuntu 桌面开发环境配置完成[/bold green]")