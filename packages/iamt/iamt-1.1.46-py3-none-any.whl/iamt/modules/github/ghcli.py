"""GitHub CLI 模块 - 在远程 Linux 主机上安装和配置 GitHub CLI

该模块通过 SSH 连接执行远程命令，实现 GitHub CLI 的自动化部署。
"""

from fabric import Connection, task

from .._utils.github import download_file, resolve_version


# region 模块常量配置

# GitHub CLI 下载 URL 模板
GH_DOWNLOAD_URL_TEMPLATE = "https://github.com/cli/cli/releases/download/v{version}/gh_{version}_linux_{arch}.tar.gz"

# GitHub CLI latest release 重定向 URL (用于获取最新版本号)
GH_LATEST_RELEASE_URL = "https://github.com/cli/cli/releases/latest"

# 架构映射 (uname -m -> GitHub CLI 架构名称)
GH_ARCH_MAP = {
    "x86_64": "amd64",
    "aarch64": "arm64",
    "armv7l": "armv6",
}

# 默认安装目录
GH_INSTALL_DIR = "/usr/local/bin"

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
        GitHub CLI 架构名称 (如 amd64, arm64)
    """
    # 优先从 hostvars 获取架构信息
    if hasattr(conn, "hostvars") and conn.hostvars:
        arch = conn.hostvars.get("architecture", "")
        if arch:
            return GH_ARCH_MAP.get(arch, "amd64")
    
    # 回退方案：直接执行命令获取
    result = conn.run("uname -m", hide=True)
    arch = result.stdout.strip()
    return GH_ARCH_MAP.get(arch, "amd64")


def _download_gh_tarball(version: str, arch: str, dest_dir: str) -> str:
    """下载 GitHub CLI 压缩包到本地
    
    Args:
        version: 版本号
        arch: 架构标识
        dest_dir: 下载目标目录
        
    Returns:
        下载后的压缩包路径
    """
    version_number = resolve_version(version, GH_LATEST_RELEASE_URL)
    url = GH_DOWNLOAD_URL_TEMPLATE.format(version=version_number, arch=arch)
    filename = f"gh_{version_number}_linux_{arch}.tar.gz"
    return download_file(url, dest_dir, filename)

# endregion


# region Task 函数

@task
def install_gh(conn: Connection, version: str = "latest", install_dir: str = GH_INSTALL_DIR) -> None:
    """下载并安装 GitHub CLI (本地下载模式)
    
    先将 CLI 安装包下载到本地，然后上传到服务器并安装。
    适用于本地网络条件较好的场景。
    
    Args:
        conn: Fabric 连接对象
        version: 版本号，默认为 "latest"，也可以指定具体版本如 "2.40.0"
        install_dir: 安装目录路径，默认为 /usr/local/bin
    """
    arch = _get_remote_arch(conn)
    print(f"[INFO] 目标架构: {arch}")
    print(f"[INFO] 安装版本: {version}")
    
    remote_tmp_dir = "/tmp/gh_install"
    remote_tarball = f"{remote_tmp_dir}/gh.tar.gz"
    
    # region 下载并上传压缩包
    print(f"\n[任务] 下载 GitHub CLI {version}")
    tarball_path = _download_gh_tarball(version, arch, str(conn.artifacts_dir))
    
    print("\n[任务] 上传压缩包到远程主机")
    conn.run(f"mkdir -p {remote_tmp_dir}", env=ENV_LANG_C)
    conn.put(tarball_path, remote_tarball)
    print(f"  上传完成: {remote_tarball}")
    # endregion
    
    # region 解压并安装
    print("\n[任务] 解压并安装 GitHub CLI")
    conn.run(f"tar -xzf {remote_tarball} -C {remote_tmp_dir}", env=ENV_LANG_C)
    
    # 查找解压后的目录
    result = conn.run(f"ls -d {remote_tmp_dir}/gh_*_linux_{arch}", hide=True)
    extracted_dir = result.stdout.strip()
    
    # 安装二进制文件
    conn.sudo(f"cp {extracted_dir}/bin/gh {install_dir}/gh", env=ENV_LANG_C)
    conn.sudo(f"chmod +x {install_dir}/gh", env=ENV_LANG_C)
    print(f"  gh 已安装到: {install_dir}/gh")
    # endregion
    
    # region 清理临时文件
    print("\n[任务] 清理临时文件")
    conn.run(f"rm -rf {remote_tmp_dir}", env=ENV_LANG_C)
    print("  清理完成")
    # endregion
    
    # region 验证安装
    print("\n[任务] 验证安装")
    result = conn.run(f"{install_dir}/gh --version", hide=True)
    print(f"  {result.stdout.strip()}")
    # endregion
    
    print(f"\n[OK] GitHub CLI {version} 安装完成 (本地下载模式)")


@task
def install_gh_remote(conn: Connection, version: str = "latest", install_dir: str = GH_INSTALL_DIR) -> None:
    """下载并安装 GitHub CLI (远程下载模式)
    
    直接在远程主机上下载安装包并安装。
    适用于远程主机网络条件较好的场景。
    
    Args:
        conn: Fabric 连接对象
        version: 版本号，默认为 "latest"，也可以指定具体版本如 "2.40.0"
        install_dir: 安装目录路径，默认为 /usr/local/bin
    """
    arch = _get_remote_arch(conn)
    version_number = resolve_version(version, GH_LATEST_RELEASE_URL)
    print(f"[INFO] 目标架构: {arch}")
    print(f"[INFO] 安装版本: {version_number}")
    
    download_url = GH_DOWNLOAD_URL_TEMPLATE.format(version=version_number, arch=arch)
    print(f"[INFO] 下载地址: {download_url}")
    
    remote_tmp_dir = "/tmp/gh_install"
    remote_tarball = f"{remote_tmp_dir}/gh.tar.gz"
    
    # region 在远程主机上下载压缩包
    print(f"\n[任务] 在远程主机上下载 GitHub CLI {version}")
    conn.run(f"mkdir -p {remote_tmp_dir}", env=ENV_LANG_C)
    conn.run(f"curl -fsSL -o {remote_tarball} '{download_url}'", env=ENV_LANG_C)
    print(f"  下载完成: {remote_tarball}")
    # endregion
    
    # region 解压并安装
    print("\n[任务] 解压并安装 GitHub CLI")
    conn.run(f"tar -xzf {remote_tarball} -C {remote_tmp_dir}", env=ENV_LANG_C)
    
    # 查找解压后的目录
    result = conn.run(f"ls -d {remote_tmp_dir}/gh_*_linux_{arch}", hide=True)
    extracted_dir = result.stdout.strip()
    
    # 安装二进制文件
    conn.sudo(f"cp {extracted_dir}/bin/gh {install_dir}/gh", env=ENV_LANG_C)
    conn.sudo(f"chmod +x {install_dir}/gh", env=ENV_LANG_C)
    print(f"  gh 已安装到: {install_dir}/gh")
    # endregion
    
    # region 清理临时文件
    print("\n[任务] 清理临时文件")
    conn.run(f"rm -rf {remote_tmp_dir}", env=ENV_LANG_C)
    print("  清理完成")
    # endregion
    
    # region 验证安装
    print("\n[任务] 验证安装")
    result = conn.run(f"{install_dir}/gh --version", hide=True)
    print(f"  {result.stdout.strip()}")
    # endregion
    
    print(f"\n[OK] GitHub CLI {version} 安装完成 (远程下载模式)")

# endregion
