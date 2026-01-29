"""Google Chrome 模块 - 在远程 Ubuntu 主机上安装和配置 Chrome 浏览器

该模块通过 SSH 连接执行远程命令，实现 Chrome 浏览器的自动化部署。
"""

from fabric import Connection, task

from .._utils.arch import normalize_arch
from .._utils.github import download_file


# region 模块常量配置

# Chrome 下载 URL 模板
CHROME_DOWNLOAD_URL_TEMPLATE = "https://dl.google.com/linux/direct/google-chrome-stable_current_{arch}.deb"

# 架构映射 (dpkg -> Chrome 架构名称)
CHROME_ARCH_MAP = {
    "amd64": "amd64",
    "arm64": "arm64",
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
        Chrome 架构名称 (如 amd64, arm64)
    """
    # 优先从 hostvars 获取架构信息
    if hasattr(conn, "hostvars") and conn.hostvars:
        arch = conn.hostvars.get("architecture", "")
        if arch:
            dpkg_arch = normalize_arch(arch)
            return CHROME_ARCH_MAP.get(dpkg_arch, "amd64")
    
    # 回退方案：直接执行命令获取
    result = conn.run("uname -m", hide=True)
    arch = result.stdout.strip()
    dpkg_arch = normalize_arch(arch)
    return CHROME_ARCH_MAP.get(dpkg_arch, "amd64")

# endregion


# region Task 函数

@task
def install_chrome(conn: Connection) -> None:
    """下载并安装 Google Chrome 浏览器 (本地下载模式)
    
    先将 Chrome 安装包下载到本地，然后上传到服务器并安装。
    适用于本地网络条件较好的场景。
    
    Args:
        conn: Fabric 连接对象
    """
    arch = _get_remote_arch(conn)
    print(f"[INFO] 目标架构: {arch}")
    
    remote_tmp_dir = "/tmp/chrome_install"
    remote_deb = f"{remote_tmp_dir}/google-chrome-stable.deb"
    
    # region 下载并上传安装包
    print("\n[任务] 下载 Google Chrome")
    url = CHROME_DOWNLOAD_URL_TEMPLATE.format(arch=arch)
    filename = f"google-chrome-stable_{arch}.deb"
    deb_path = download_file(url, conn.artifacts_dir, filename)
    
    print("\n[任务] 上传安装包到远程主机")
    conn.run(f"mkdir -p {remote_tmp_dir}", env=ENV_LANG_C)
    conn.put(deb_path, remote_deb)
    print(f"  上传完成: {remote_deb}")
    # endregion
    
    # region 安装依赖和 Chrome
    print("\n[任务] 安装 Google Chrome")
    # 更新包索引
    conn.sudo("apt-get update", env=ENV_LANG_C)
    # 安装 .deb 包及其依赖
    conn.sudo(f"apt-get install -y {remote_deb}", env=ENV_LANG_C)
    print("  Chrome 已安装")
    # endregion
    
    # region 清理临时文件
    print("\n[任务] 清理临时文件")
    conn.run(f"rm -rf {remote_tmp_dir}", env=ENV_LANG_C)
    print("  清理完成")
    # endregion
    
    # region 验证安装
    print("\n[任务] 验证安装")
    result = conn.run("google-chrome --version", hide=True)
    print(f"  {result.stdout.strip()}")
    # endregion
    
    print("\n[OK] Google Chrome 安装完成 (本地下载模式)")

# endregion 
