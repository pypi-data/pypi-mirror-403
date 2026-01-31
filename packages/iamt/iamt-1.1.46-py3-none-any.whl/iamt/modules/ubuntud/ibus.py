"""IBus 输入法模块 - 在远程 Ubuntu 主机上安装和配置 IBus 输入法框架

该模块通过 SSH 连接执行远程命令，实现 IBus 及中文输入法的自动化部署。
"""

from fabric import Connection, task


# region 模块常量配置

# 需要安装的 IBus 相关包
IBUS_PACKAGES = [
    "ibus",
    "ibus-libpinyin",
    "ibus-rime",
]

# 环境变量 (使用英文输出避免中文乱码)
ENV_LANG_C = {"LANG": "C", "LC_ALL": "C"}

# endregion


# region Task 函数

@task
def install_ibus(conn: Connection) -> None:
    """安装 IBus 输入法框架及中文输入法
    
    安装 ibus、ibus-libpinyin 和 ibus-rime，并重启 ibus 服务。
    
    Args:
        conn: Fabric 连接对象
    """
    packages_str = " ".join(IBUS_PACKAGES)
    
    # region 安装 IBus 及输入法
    print("[任务] 安装 IBus 输入法框架")
    conn.sudo("apt-get update", env=ENV_LANG_C)
    conn.sudo(f"apt-get install -y {packages_str}", env=ENV_LANG_C)
    print("  IBus 及输入法已安装")
    # endregion
    
    # region 重启 IBus
    print("\n[任务] 重启 IBus 服务")
    conn.run("ibus restart || true", env=ENV_LANG_C, warn=True)
    print("  IBus 已重启")
    # endregion
    
    print("\n[OK] IBus 输入法安装完成")
    print("[提示] 请通过「设置 -> 键盘 -> 输入源」添加已安装的输入法")

# endregion
