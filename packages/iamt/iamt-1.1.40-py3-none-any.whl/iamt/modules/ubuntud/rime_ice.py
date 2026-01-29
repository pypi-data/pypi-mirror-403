"""Rime Ice 模块 - 在远程 Ubuntu 主机上安装 rime-ice 输入法配置

该模块通过 SSH 连接执行远程命令，实现 rime-ice 配置的自动化部署。
rime-ice 是一个开源的 Rime 输入法配置方案。
"""

from datetime import datetime
from pathlib import Path
from fabric import Connection, task

from .._utils.github import download_file


# region 模块常量配置

# rime-ice 仓库下载 URL
RIME_ICE_DOWNLOAD_URL = "https://github.com/iDvel/rime-ice/archive/refs/heads/main.zip"

# 环境变量 (使用英文输出避免中文乱码)
ENV_LANG_C = {"LANG": "C", "LC_ALL": "C"}

# 模板目录
TEMPLATES_DIR = Path(__file__).parent / "templates"

# endregion


# region 辅助函数

def _find_rime_config_dir(conn: Connection) -> str | None:
    """查找 rime 配置目录
    
    按优先级检查常见的 rime 配置目录位置
    
    Args:
        conn: Fabric 连接对象
        
    Returns:
        rime 配置目录路径，未找到返回 None
    """
    user_home = conn.hostvars.get("user_home", "~")
    
    # 常见的 rime 配置目录位置
    candidates = [
        f"{user_home}/.local/share/fcitx5/rime",  # fcitx5
        f"{user_home}/.config/ibus/rime",          # ibus
        f"{user_home}/.config/fcitx/rime",         # fcitx4
    ]
    
    for path in candidates:
        result = conn.run(f"test -d {path} && echo exists", hide=True, warn=True)
        if result.ok and "exists" in result.stdout:
            return path
    
    return None


def _get_rime_parent_dir(rime_dir: str) -> str:
    """获取 rime 配置目录的父目录"""
    return "/".join(rime_dir.rsplit("/", 1)[:-1]) or "/"

# endregion


# region Task 函数

@task
def install_rime_ice(conn: Connection) -> None:
    """安装 rime-ice 输入法配置
    
    执行以下步骤：
    1. 查找 rime 配置目录
    2. 备份现有 rime 文件夹 (格式: 日期_rime_bak)
    3. 创建新的空 rime 文件夹
    4. 下载 rime-ice 仓库并上传到远程服务器
    5. 解压并复制内容到 rime 文件夹
    
    Args:
        conn: Fabric 连接对象
    """
    # region 查找 rime 配置目录
    print("\n[任务] 查找 rime 配置目录")
    rime_dir = _find_rime_config_dir(conn)
    if rime_dir is None:
        print("  [错误] 未找到 rime 配置目录，请先安装 fcitx5-rime 或 ibus-rime")
        return
    print(f"  找到配置目录: {rime_dir}")
    # endregion
    
    # region 备份现有 rime 文件夹
    print("\n[任务] 备份现有 rime 配置")
    parent_dir = _get_rime_parent_dir(rime_dir)
    backup_name = f"{datetime.now().strftime('%Y%m%d')}_rime_bak"
    backup_path = f"{parent_dir}/{backup_name}"
    
    # 检查是否已存在同名备份
    result = conn.run(f"test -d {backup_path} && echo exists", hide=True, warn=True)
    if result.ok and "exists" in result.stdout:
        print(f"  [警告] 备份目录已存在: {backup_path}，将覆盖")
        conn.run(f"rm -rf {backup_path}", env=ENV_LANG_C)
    
    conn.run(f"mv {rime_dir} {backup_path}", env=ENV_LANG_C)
    print(f"  备份完成: {backup_path}")
    # endregion
    
    # region 创建新的空 rime 文件夹
    print("\n[任务] 创建新的 rime 配置目录")
    conn.run(f"mkdir -p {rime_dir}", env=ENV_LANG_C)
    print(f"  创建完成: {rime_dir}")
    # endregion
    
    # region 下载并上传 rime-ice
    print("\n[任务] 下载 rime-ice")
    local_zip = download_file(
        RIME_ICE_DOWNLOAD_URL,
        conn.artifacts_dir,
        "rime-ice-main.zip",
    )
    
    print("\n[任务] 上传 rime-ice 到远程主机")
    remote_tmp_dir = "/tmp/rime_ice_install"
    remote_zip = f"{remote_tmp_dir}/rime-ice-main.zip"
    
    conn.run(f"mkdir -p {remote_tmp_dir}", env=ENV_LANG_C)
    conn.put(local_zip, remote_zip)
    print(f"  上传完成: {remote_zip}")
    # endregion
    
    # region 解压并复制内容
    print("\n[任务] 解压并安装 rime-ice")
    conn.run(f"unzip -q -o {remote_zip} -d {remote_tmp_dir}", env=ENV_LANG_C)
    # 复制 rime-ice-main 目录下的所有内容到 rime 配置目录
    conn.run(f"cp -r {remote_tmp_dir}/rime-ice-main/* {rime_dir}/", env=ENV_LANG_C)
    print(f"  安装完成: {rime_dir}")
    # endregion
    
    # region 复制用户自定义配置文件
    print("\n[任务] 复制用户自定义配置文件")
    if "ibus" in rime_dir:
        custom_file = TEMPLATES_DIR / "ibus" / "ibus_rime.custom.yaml"
        if custom_file.exists():
            conn.put(str(custom_file), f"{rime_dir}/ibus_rime.custom.yaml")
            print("  已复制: ibus_rime.custom.yaml")
        else:
            print(f"  [警告] 自定义配置文件不存在: {custom_file}")
    # endregion
    
    # region 重启输入法框架
    print("\n[任务] 重启输入法框架")
    # 根据配置目录判断使用的输入法框架
    if "fcitx5" in rime_dir:
        conn.run("fcitx5 -r -d 2>/dev/null || true", env=ENV_LANG_C, warn=True)
        print("  fcitx5 已重启")
    elif "ibus" in rime_dir:
        conn.run("ibus restart 2>/dev/null || true", env=ENV_LANG_C, warn=True)
        print("  ibus 已重启")
    elif "fcitx" in rime_dir:
        conn.run("fcitx -r -d 2>/dev/null || true", env=ENV_LANG_C, warn=True)
        print("  fcitx 已重启")
    # endregion
    
    # region 清理临时文件
    print("\n[任务] 清理临时文件")
    conn.run(f"rm -rf {remote_tmp_dir}", env=ENV_LANG_C)
    print("  清理完成")
    # endregion
    
    print("\n[OK] rime-ice 安装完成")
    print(f"  配置目录: {rime_dir}")
    print(f"  备份位置: {backup_path}")
    print("  请重新部署 rime 输入法以使配置生效")

# endregion
