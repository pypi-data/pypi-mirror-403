from fabric import Connection, task

from .._utils.arch import normalize_arch
from .._utils.github import download_file


# region 模块常量配置

# Antigravity APT 仓库配置
ANTIGRAVITY_REPO_BASE = "https://us-central1-apt.pkg.dev/projects/antigravity-auto-updater-dev"
ANTIGRAVITY_PACKAGES_URL = f"{ANTIGRAVITY_REPO_BASE}/dists/antigravity-debian/main/binary-{{arch}}/Packages"

# 环境变量 (使用英文输出避免中文乱码)
ENV_LANG_C = {"LANG": "C", "LC_ALL": "C"}

# endregion


# region 辅助函数

def _get_remote_arch(conn: Connection) -> str:
    """获取远程主机的 dpkg 架构标识
    
    优先使用 hostvars 中已收集的架构信息
    
    Args:
        conn: Fabric 连接对象
        
    Returns:
        dpkg 架构名称 (如 amd64, arm64)
    """
    if hasattr(conn, "hostvars") and conn.hostvars:
        arch = conn.hostvars.get("architecture", "")
        if arch:
            return normalize_arch(arch)
    
    result = conn.run("uname -m", hide=True)
    return normalize_arch(result.stdout.strip())


def _download_antigravity_deb(arch: str, dest_dir: str) -> str:
    """从 APT 仓库下载 Antigravity .deb 包到本地
    
    直接从仓库的 Packages 索引获取包信息，无需远程主机配置 APT 源。
    
    Args:
        arch: dpkg 架构标识 (如 amd64, arm64)
        dest_dir: 下载目标目录
        
    Returns:
        下载后的 .deb 包路径
    """
    import urllib.request
    
    # region 获取 Packages 索引并解析
    packages_url = ANTIGRAVITY_PACKAGES_URL.format(arch=arch)
    print(f"  正在获取包索引: {packages_url}")
    
    with urllib.request.urlopen(packages_url) as response:
        packages_content = response.read().decode("utf-8")
    
    filename = None
    version = None
    for line in packages_content.split("\n"):
        if line.startswith("Filename:"):
            filename = line.split(":", 1)[1].strip()
        elif line.startswith("Version:"):
            version = line.split(":", 1)[1].strip()
    
    if not filename:
        raise RuntimeError("无法从 Packages 索引中解析 .deb 文件路径")
    # endregion
    
    # region 下载 .deb 文件
    deb_url = f"{ANTIGRAVITY_REPO_BASE}/{filename}"
    local_filename = f"antigravity_{version}_{arch}.deb" if version else f"antigravity_{arch}.deb"
    return download_file(deb_url, dest_dir, local_filename)
    # endregion

# endregion


# region Task 函数

@task
def install_antigravity(conn: Connection) -> None:
    """在 Ubuntu 上安装 antigravity"""
    
    # region 检查系统类型
    dist_info: dict = conn.hostvars["distribution"]
    dist_id: str = dist_info.get("id", "").lower()
    
    if dist_id not in ("ubuntu", "debian"):
        print(f"不支持的发行版: {dist_id}，仅支持 Ubuntu 和 Debian")
        return
    # endregion
    
    # region 配置 APT 仓库
    keyring_dir = "/etc/apt/keyrings"
    keyring_file = f"{keyring_dir}/antigravity-repo-key.gpg"
    sources_list = "/etc/apt/sources.list.d/antigravity.list"
    repo_url = "https://us-central1-apt.pkg.dev/projects/antigravity-auto-updater-dev/"
    key_url = "https://us-central1-apt.pkg.dev/doc/repo-signing-key.gpg"
    
    # 创建 keyrings 目录
    conn.sudo(f"mkdir -p {keyring_dir}")
    
    # 下载并转换 GPG 密钥
    print("正在下载 GPG 密钥...")
    conn.sudo(f"curl -fsSL {key_url} -o /tmp/repo-signing-key.gpg", hide=True)
    conn.sudo(f"gpg --dearmor --yes -o {keyring_file} /tmp/repo-signing-key.gpg", hide=True)
    conn.sudo("rm -f /tmp/repo-signing-key.gpg", hide=True)
    
    # 添加 APT 源
    print("正在配置 APT 源...")
    sources_content = f"deb [signed-by={keyring_file}] {repo_url} antigravity-debian main"
    conn.run(f"echo '{sources_content}' > /tmp/antigravity.list")
    conn.sudo(f"mv /tmp/antigravity.list {sources_list}")
    # endregion
    
    # region 安装 antigravity
    print("正在更新软件包索引...")
    conn.sudo("apt-get update", hide=True)
    
    print("正在安装 antigravity...")
    result = conn.sudo("apt-get install -y antigravity", hide=True, warn=True)
    
    if result.ok:
        print("antigravity 安装完成")
    else:
        print("antigravity 安装失败，请检查错误信息")
    # endregion


@task
def install_antigravity_local(conn: Connection) -> None:
    """在 Ubuntu 上安装 antigravity (本地下载模式)
    
    先将安装包下载到本地 artifacts 目录，然后上传到服务器并安装。
    适用于本地网络条件较好或远程主机无法访问外网的场景。
    """
    # region 检查系统类型
    dist_info: dict = conn.hostvars["distribution"]
    dist_id: str = dist_info.get("id", "").lower()
    
    if dist_id not in ("ubuntu", "debian"):
        print(f"不支持的发行版: {dist_id}，仅支持 Ubuntu 和 Debian")
        return
    # endregion
    
    arch = _get_remote_arch(conn)
    print(f"[INFO] 目标架构: {arch}")
    
    remote_tmp_dir = "/tmp/antigravity_install"
    remote_deb = f"{remote_tmp_dir}/antigravity.deb"
    
    # region 下载并上传安装包
    print("\n[任务] 下载 antigravity 安装包")
    deb_path = _download_antigravity_deb(arch, conn.artifacts_dir)
    
    print("\n[任务] 上传安装包到远程主机")
    conn.run(f"mkdir -p {remote_tmp_dir}", env=ENV_LANG_C)
    conn.put(deb_path, remote_deb)
    print(f"  上传完成: {remote_deb}")
    # endregion
    
    # region 安装 antigravity
    print("\n[任务] 安装 antigravity")
    conn.sudo("apt-get update", env=ENV_LANG_C, hide=True)
    result = conn.sudo(
        f"DEBIAN_FRONTEND=noninteractive apt-get install -y {remote_deb}",
        env=ENV_LANG_C,
        warn=True
    )
    
    if result.ok:
        print("  antigravity 已安装")
    else:
        print("  antigravity 安装失败，请检查错误信息")
        return
    # endregion
    
    # region 清理临时文件
    print("\n[任务] 清理临时文件")
    conn.run(f"rm -rf {remote_tmp_dir}", env=ENV_LANG_C)
    print("  清理完成")
    # endregion
    
    print("\n[OK] antigravity 安装完成 (本地下载模式)")

# endregion