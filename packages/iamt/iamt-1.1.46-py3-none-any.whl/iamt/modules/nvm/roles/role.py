from rich.console import Console

from ..nvm import Connection, install_nvm, set_nodejs_mirror
from ..._utils.steps import Step, run_steps

console = Console()


def setup_nvm(c: Connection) -> None:
    """在远程服务器上安装配置 NVM
    
    执行以下步骤:
    1. 下载并安装 NVM
    2. 配置 Node.js 镜像源
    
    Args:
        c: Fabric 连接对象
    """
    steps: list[Step] = [
        ("安装 NVM", install_nvm),
        ("配置 Node.js 镜像源", set_nodejs_mirror),
    ]
    run_steps(c, steps)
    console.print("[bold green]✓ NVM 安装配置完成[/bold green]")
