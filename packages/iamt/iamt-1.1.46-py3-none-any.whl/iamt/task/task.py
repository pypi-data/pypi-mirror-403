import inspect
import importlib
from pathlib import Path

from fabric import Task as FabricTask


class Task:
    """任务管理类"""

    def _scan_tasks(self) -> dict[str, dict]:
        """扫描 modules 目录下所有子目录中的 task
        
        Returns:
            任务字典，键为任务名，值包含 task、source、module 信息
        """
        tasks = {}
        modules_path = Path(__file__).parent.parent / "modules"

        # region 遍历 modules 目录下的非下划线开头的子目录
        for module_dir in modules_path.iterdir():
            if not module_dir.is_dir() or module_dir.name.startswith("_"):
                continue

            # region 扫描子目录下不以下划线开头的 Python 文件
            for py_file in module_dir.glob("*.py"):
                if py_file.name.startswith("_"):
                    continue

                module_name = py_file.stem
                import_path = f".modules.{module_dir.name}.{module_name}"

                try:
                    module = importlib.import_module(import_path, package="iamt")
                    source_file = py_file.name

                    for name, obj in vars(module).items():
                        if isinstance(obj, FabricTask):
                            tasks[name] = {
                                "task": obj,
                                "source": source_file,
                                "module": module_dir
                            }
                except ImportError as e:
                    print(f"警告: 无法导入模块 {import_path}: {e}")
            # endregion
        # endregion

        return tasks

    def ls(self) -> None:
        """列出所有可用任务及其参数、描述和位置"""
        print("可用任务:")
        for name, task_info in (self._scan_tasks()).items():
            task_obj = task_info["task"]
            sig = inspect.signature(task_obj.body)
            params = [p for p in sig.parameters.keys() if p != 'ctx']
            params_str = f"({', '.join(params)})" if params else "()"
            doc = (task_obj.body.__doc__ or "").strip().split('\n')[0]
            location = f"@ {task_info['module'].name}/{task_info['source']}"
            print(f"  {name}{params_str}: {doc} {location}")

    def run(self) -> None:
        """交互式选择并运行任务"""
        from prompt_toolkit import prompt
        from ..completers.customCompleter import CustomCompleter, CustomValidator
        from ..client_config.client_config import ClientConfig

        if not self._scan_tasks():
            print("没有可用的任务")
            return

        # region 构建 模块名.task函数名 格式的选项列表
        task_options = {
            f"{task_info['module'].name}.{name}": f"{task_info['module'].name}.{name}"
            for name, task_info in (self._scan_tasks()).items()
        }
        completer = CustomCompleter(task_options)
        validator = CustomValidator(completer, error_msg="无效的任务，请从补全列表中选择")
        # endregion

        # region 模糊搜索选择
        try:
            selected_key = prompt(
                "请选择要运行的任务 (Tab补全, 支持模糊搜索): ",
                completer=completer,
                validator=validator
            ).strip()
        except (KeyboardInterrupt, EOFError):
            print("\n已取消选择")
            return

        if not selected_key or selected_key not in task_options:
            print(f"无效的选择: {selected_key}")
            return
        # endregion

        # region 执行选中的任务
        task_name = selected_key.split(".")[-1]
        task_info = (self._scan_tasks())[task_name]
        task_obj = task_info["task"]
        config = ClientConfig()
        conn = config.connect()
        if conn is None:
            return
        doc = (task_obj.body.__doc__ or "").strip()
        if doc:
            print(f"\n{doc}\n")
        try:
            task_obj(conn)
        except Exception as e:
            print(f"任务 '{task_name}' 执行失败: {e}")
        # endregion
