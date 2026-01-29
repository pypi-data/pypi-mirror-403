"""Visual Studio Code 模块 - 在远程 Ubuntu 主机上安装和配置 VSCode

该模块通过 SSH 连接执行远程命令，实现 VSCode 的自动化部署。
"""

from fabric import Connection, task

from .._utils.arch import normalize_arch
from .._utils.github import download_file


# region 模块常量配置

# VSCode 下载 URL 模板
VSCODE_DOWNLOAD_URL_TEMPLATE = "https://code.visualstudio.com/sha/download?build=stable&os=linux-deb-{arch}"

# 架构映射 (dpkg -> VSCode 架构名称)
VSCODE_ARCH_MAP = {
    "amd64": "x64",
    "arm64": "arm64",
    "armhf": "armhf",
}

# 环境变量 (使用英文输出避免中文乱码)
ENV_LANG_C = {"LANG": "C", "LC_ALL": "C"}

# endregion


# region 辅助函数

def _get_remote_arch(conn: Connection) -> str:
    """获取远程主机的架构标识
    
    优先使用 hostvars 中已收集的架构信息，避免重复执行命令
    
    Args:
        conn: Fabric 连接对象
        
    Returns:
        VSCode 架构名称 (如 x64, arm64)
    """
    # 优先从 hostvars 获取架构信息
    if hasattr(conn, "hostvars") and conn.hostvars:
        arch = conn.hostvars.get("architecture", "")
        if arch:
            dpkg_arch = normalize_arch(arch)
            return VSCODE_ARCH_MAP.get(dpkg_arch, "x64")
    
    # 回退方案：直接执行命令获取
    result = conn.run("uname -m", hide=True)
    arch = result.stdout.strip()
    dpkg_arch = normalize_arch(arch)
    return VSCODE_ARCH_MAP.get(dpkg_arch, "x64")

# endregion


# region Task 函数

@task
def install_vscode(conn: Connection) -> None:
    """下载并安装 Visual Studio Code (本地下载模式)
    
    先将 VSCode 安装包下载到本地，然后上传到服务器并安装。
    适用于本地网络条件较好的场景。
    
    Args:
        conn: Fabric 连接对象
    """
    arch = _get_remote_arch(conn)
    print(f"[INFO] 目标架构: {arch}")
    
    remote_tmp_dir = "/tmp/vscode_install"
    remote_deb = f"{remote_tmp_dir}/vscode.deb"
    
    # region 下载并上传安装包
    print("\n[任务] 下载 Visual Studio Code")
    url = VSCODE_DOWNLOAD_URL_TEMPLATE.format(arch=arch)
    filename = f"vscode_{arch}.deb"
    deb_path = download_file(url, conn.artifacts_dir, filename)
    
    print("\n[任务] 上传安装包到远程主机")
    conn.run(f"mkdir -p {remote_tmp_dir}", env=ENV_LANG_C)
    conn.put(deb_path, remote_deb)
    print(f"  上传完成: {remote_deb}")
    # endregion
    
    # region 安装依赖和 VSCode
    print("\n[任务] 安装 Visual Studio Code")
    # 更新包索引
    conn.sudo("apt-get update", env=ENV_LANG_C)
    # 安装 .deb 包及其依赖
    conn.sudo(f"DEBIAN_FRONTEND=noninteractive apt-get install -y {remote_deb}", env=ENV_LANG_C)
    print("  VSCode 已安装")
    # endregion
    
    # region 清理临时文件
    print("\n[任务] 清理临时文件")
    conn.run(f"rm -rf {remote_tmp_dir}", env=ENV_LANG_C)
    print("  清理完成")
    # endregion
    
    # region 验证安装
    print("\n[任务] 验证安装")
    result = conn.run("code --version", hide=True)
    print(f"  {result.stdout.strip()}")
    # endregion
    
    print("\n[OK] Visual Studio Code 安装完成 (本地下载模式)")


@task
def install_vscode_remote(conn: Connection) -> None:
    """下载并安装 Visual Studio Code (远程下载模式)
    
    直接在远程主机上下载安装包并安装。
    适用于远程主机网络条件较好的场景。
    
    Args:
        conn: Fabric 连接对象
    """
    arch = _get_remote_arch(conn)
    print(f"[INFO] 目标架构: {arch}")
    
    download_url = VSCODE_DOWNLOAD_URL_TEMPLATE.format(arch=arch)
    print(f"[INFO] 下载地址: {download_url}")
    
    remote_tmp_dir = "/tmp/vscode_install"
    remote_deb = f"{remote_tmp_dir}/vscode.deb"
    
    # region 在远程主机上下载安装包
    print("\n[任务] 在远程主机上下载 Visual Studio Code")
    conn.run(f"mkdir -p {remote_tmp_dir}", env=ENV_LANG_C)
    conn.run(f"curl -fsSL -o {remote_deb} '{download_url}'", env=ENV_LANG_C)
    print(f"  下载完成: {remote_deb}")
    # endregion
    
    # region 安装依赖和 VSCode
    print("\n[任务] 安装 Visual Studio Code")
    # 更新包索引
    conn.sudo("apt-get update", env=ENV_LANG_C)
    # 安装 .deb 包及其依赖
    conn.sudo(f"apt-get install -y {remote_deb}", env=ENV_LANG_C)
    print("  VSCode 已安装")
    # endregion
    
    # region 清理临时文件
    print("\n[任务] 清理临时文件")
    conn.run(f"rm -rf {remote_tmp_dir}", env=ENV_LANG_C)
    print("  清理完成")
    # endregion
    
    # region 验证安装
    print("\n[任务] 验证安装")
    result = conn.run("code --version", hide=True)
    print(f"  {result.stdout.strip()}")
    # endregion
    
    print("\n[OK] Visual Studio Code 安装完成 (远程下载模式)")

# endregion
