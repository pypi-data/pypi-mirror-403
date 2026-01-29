import sys
import subprocess
from prompt_toolkit import prompt

from ..client_config.client_config import ClientConfig
from ..completers.customCompleter import CustomCompleter, CustomValidator
from ..modules.runlinetask.runlinetask import run_line
from .commands import python_pkgs, node_pkgs, cmds, winget_pkgs,powershell_cmds,bash_cmds


class RunLine:
    """命令行执行管理类"""

    def select_and_exec_remote(self):
        """交互式选择命令并在远程服务器上执行"""
        # region 合并命令字典并创建补全器
        all_commands = {**python_pkgs, **node_pkgs, **cmds,**bash_cmds}
        completer = CustomCompleter(all_commands)
        validator = CustomValidator(completer, error_msg="无效的命令，请从补全列表中选择")
        # endregion

        # region 交互式选择命令
        try:
            selected_cmd = prompt(
                "请选择要执行的命令 (Tab补全, 支持模糊搜索): ",
                completer=completer,
                validator=validator
            ).strip()
        except (KeyboardInterrupt, EOFError):
            print("\n已取消选择")
            return

        if not selected_cmd or selected_cmd not in all_commands:
            print(f"无效的选择: {selected_cmd}")
            return
        # endregion

        # region 连接服务器并执行命令
        config = ClientConfig()
        conn = config.connect()
        if conn is None:
            return
        print(f"\n执行命令: {selected_cmd}\n")
        run_line(conn, selected_cmd)
        # endregion

    def select_and_exec_local(self):
        """交互式选择命令并在本地 shell 中执行"""
        # region 合并命令字典并创建补全器
        all_commands = {**python_pkgs, **node_pkgs, **cmds, **winget_pkgs, **powershell_cmds}
        completer = CustomCompleter(all_commands)
        # validator = CustomValidator(completer, error_msg="无效的命令，请从补全列表中选择")
        # endregion

        # region 交互式选择命令
        try:
            selected_cmd = prompt(
                "请选择要执行的命令 (Tab补全, 支持模糊搜索): ",
                completer=completer,
                # validator=validator
            ).strip()
        except (KeyboardInterrupt, EOFError):
            sys.stderr.write("\n已取消选择\n")
            return

        # if not selected_cmd or selected_cmd not in all_commands:
        #     sys.stderr.write(f"无效的选择: {selected_cmd}\n")
        #     return
        # endregion

        # region 在当前 shell 中执行命令
        sys.stderr.write(f"\n执行命令: {selected_cmd}\n\n")
        try:
            subprocess.run(selected_cmd, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            sys.stderr.write(f"\n命令执行失败，退出码: {e.returncode}\n")
        except KeyboardInterrupt:
            sys.stderr.write("\n命令执行被中断\n")
        # endregion