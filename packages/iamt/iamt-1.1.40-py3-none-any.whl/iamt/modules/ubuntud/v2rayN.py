"""v2rayN 模块 - 在远程 Ubuntu 主机上安装 v2rayN

该模块通过 SSH 连接执行远程命令，实现 v2rayN 的自动化部署。
v2rayN 是一个基于 V2Ray 内核的图形化客户端。
"""

from fabric import Connection, task

from .._utils.arch import normalize_arch
from .._utils.github import download_file, resolve_version


# region 模块常量配置

# v2rayN GitHub releases URL 模板
# 注意：v2rayN Linux 版本只提供 64 位版本
V2RAYN_RELEASE_URL_TEMPLATE = "https://github.com/2dust/v2rayN/releases/download/{version}/v2rayN-linux-64.deb"

# v2rayN latest release 重定向 URL (用于获取最新版本号)
V2RAYN_LATEST_RELEASE_URL = "https://github.com/2dust/v2rayN/releases/latest"

# 环境变量 (使用英文输出避免中文乱码)
ENV_LANG_C = {"LANG": "C", "LC_ALL": "C"}

# endregion


# region 辅助函数

def _check_arch_compatibility(conn: Connection) -> None:
    """检查远程主机架构是否支持 v2rayN
    
    v2rayN Linux 版本仅支持 x86_64 架构
    
    Args:
        conn: Fabric 连接对象
        
    Raises:
        RuntimeError: 如果架构不支持
    """
    # 优先从 hostvars 获取架构信息
    if hasattr(conn, "hostvars") and conn.hostvars:
        arch = conn.hostvars.get("architecture", "")
        if arch:
            dpkg_arch = normalize_arch(arch)
            if dpkg_arch != "amd64":
                raise RuntimeError(f"v2rayN Linux 版本仅支持 x86_64 架构，当前架构: {arch}")
            return
    
    # 回退方案：直接执行命令获取
    result = conn.run("uname -m", hide=True)
    arch = result.stdout.strip()
    dpkg_arch = normalize_arch(arch)
    if dpkg_arch != "amd64":
        raise RuntimeError(f"v2rayN Linux 版本仅支持 x86_64 架构，当前架构: {arch}")


def _download_v2rayn_deb(dest_dir: str, version: str) -> str:
    """下载 v2rayN .deb 包到本地
    
    Args:
        dest_dir: 下载目标目录
        version: v2rayN 版本号
        
    Returns:
        下载后的 .deb 包路径
    """
    url = V2RAYN_RELEASE_URL_TEMPLATE.format(version=version)
    filename = f"v2rayN-linux-64-{version}.deb"
    return download_file(url, dest_dir, filename)

# endregion


# region Task 函数

@task
def install_v2rayn(conn: Connection, version: str = "latest") -> None:
    """下载并安装 v2rayN (本地下载模式)
    
    先将 v2rayN 安装包下载到本地，然后上传到服务器并安装。
    适用于本地网络条件较好的场景。
    
    注意：v2rayN Linux 版本仅支持 x86_64 架构
    
    Args:
        conn: Fabric 连接对象
        version: v2rayN 版本号，默认 "latest" 自动获取最新版本
    """
    # 解析版本号
    actual_version = resolve_version(version, V2RAYN_LATEST_RELEASE_URL, strip_v=False)
    
    # 检查架构兼容性
    _check_arch_compatibility(conn)
    print(f"[INFO] v2rayN 版本: {actual_version}")
    
    remote_tmp_dir = "/tmp/v2rayn_install"
    remote_deb = f"{remote_tmp_dir}/v2rayn.deb"
    
    # region 下载并上传压缩包
    print("\n[任务] 下载 v2rayN")
    deb_path = _download_v2rayn_deb(str(conn.artifacts_dir), actual_version)
    
    print("\n[任务] 上传安装包到远程主机")
    conn.run(f"mkdir -p {remote_tmp_dir}", env=ENV_LANG_C)
    conn.put(deb_path, remote_deb)
    print(f"  上传完成: {remote_deb}")
    # endregion
    
    # region 安装依赖和 v2rayN
    print("\n[任务] 安装 v2rayN")
    # 更新包索引
    conn.sudo("apt-get update", env=ENV_LANG_C)
    # 安装 .deb 包及其依赖
    conn.sudo(f"apt-get install -y {remote_deb}", env=ENV_LANG_C)
    print("  v2rayN 已安装")
    # endregion
    
    # region 清理临时文件
    print("\n[任务] 清理临时文件")
    conn.run(f"rm -rf {remote_tmp_dir}", env=ENV_LANG_C)
    print("  清理完成")
    # endregion
    
    print("\n[OK] v2rayN 安装完成")

# endregion
