from fabric import Connection, task
from invoke.exceptions import UnexpectedExit


@task
def run_line(conn: Connection, command: str, sudo: bool = False) -> None:
    """在目标服务器上执行一行命令

    Args:
        conn: Fabric Connection 对象
        command: 要执行的命令
        sudo: 是否使用 sudo 执行，默认 False
    """
    # 使用 bash -ilc 以 interactive login shell 方式执行，确保加载 ~/.bashrc（nvm 等工具需要）
    wrapped_command = f'bash -ilc {command!r}'
    try:
        if sudo:
            conn.sudo(wrapped_command)
        else:
            conn.run(wrapped_command)
    except UnexpectedExit as e:
        print(f"\n命令执行失败 (退出码: {e.result.exited})")
