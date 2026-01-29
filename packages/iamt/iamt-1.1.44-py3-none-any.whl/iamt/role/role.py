import inspect
import importlib
from pathlib import Path


class Role:
    """Role 管理类"""

    def _scan_roles(self) -> dict[str, dict]:
        """扫描 modules 目录下所有 roles 文件夹中定义的函数
        
        Returns:
            角色字典，键为函数名，值包含 func、module、source 信息
        """
        roles = {}
        modules_path = Path(__file__).parent.parent / "modules"

        # region 遍历 modules 目录下的非下划线开头的文件夹
        for module_dir in modules_path.iterdir():
            if not module_dir.is_dir() or module_dir.name.startswith("_"):
                continue

            roles_dir = module_dir / "roles"
            if not roles_dir.exists() or not roles_dir.is_dir():
                continue

            # region 扫描 roles 目录下的所有 Python 文件
            for py_file in roles_dir.glob("*.py"):
                if py_file.name.startswith("_"):
                    continue

                # 构建模块导入路径
                relative_path = py_file.relative_to(Path(__file__).parent.parent)
                module_name = ".".join(relative_path.with_suffix("").parts)

                try:
                    module = importlib.import_module(f".{module_name}", package="iamt")
                    # 查找在该模块中定义的函数（排除导入的函数）
                    for name, obj in vars(module).items():
                        if inspect.isfunction(obj) and obj.__module__ == module.__name__:
                            roles[name] = {
                                "func": obj,
                                "module": module_dir.name,
                                "source": py_file.name
                            }
                except ImportError as e:
                    print(f"警告: 无法导入模块 {module_name}: {e}")
            # endregion
        # endregion

        return roles

    def ls(self):
        """列出所有可用的 roles"""
        print("可用 roles:")
        for name, info in (self._scan_roles()).items():
            print(f"  {name} @ {info['module']}/roles/{info['source']}")

    def run(self):
        """交互式选择并运行 role"""
        from prompt_toolkit import prompt
        from prompt_toolkit.completion import FuzzyWordCompleter
        from rich.console import Console
        from ..client_config.client_config import ClientConfig

        console = Console()

        if not self._scan_roles():
            print("没有可用的 roles")
            return

        # region 构建模块名.函数名格式的选项列表
        role_options = {
            f"{info['module']}.{name}": name
            for name, info in (self._scan_roles()).items()
        }
        completer = FuzzyWordCompleter(list(role_options.keys()))
        # endregion

        # region 模糊搜索选择
        try:
            selected_key = prompt(
                "请选择要运行的 role (Tab补全, 支持模糊搜索): ",
                completer=completer
            ).strip()
        except (KeyboardInterrupt, EOFError):
            print("\n已取消选择")
            return

        if not selected_key or selected_key not in role_options:
            print(f"无效的选择: {selected_key}")
            return
        # endregion

        # region 执行选中的 role
        selected = role_options[selected_key]
        role_info = (self._scan_roles())[selected]
        role_func = role_info["func"]
        config = ClientConfig()
        conn = config.connect()
        if conn is None:
            return

        # region 询问是否保存配置
        import questionary
        from ..utils.config_saver import save_task_config
        from ..utils.task_tracker import TaskTracker

        save_config = questionary.confirm(
            "是否在执行后保存运行配置?",
            default=False,
        ).ask()
        # endregion

        # region 使用 TaskTracker 追踪 task 调用
        tracker = TaskTracker()
        if save_config:
            tracker.patch_all_modules()

        try:
            role_func(conn)
        except Exception as e:
            console.print(f"[red]Role '{selected}' 执行失败: {e}[/red]")
            tracker.unpatch_all()
            return
        finally:
            tracker.unpatch_all()
        # endregion

        # region 保存配置文件
        if save_config and tracker.calls:
            save_task_config(
                hostname=config._current_host or "",
                tasks=tracker.calls,
                config_name=selected,
                suffix=".role.yaml",
            )
        # endregion
        # endregion
