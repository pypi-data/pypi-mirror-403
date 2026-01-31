"""V2Ray 模块 - 在远程 Linux 主机上安装和配置 V2Ray Core

该模块通过 SSH 连接执行远程命令，实现 V2Ray Core 的自动化部署。
注意: v2rayN 是 Windows GUI 客户端，Linux 服务器应安装 v2ray-core。
# https://github.com/v2fly/v2ray-core
"""

import tempfile

from fabric import Connection, task

from .._utils.arch import normalize_arch
from .._utils.github import download_file, resolve_version_via_api


# region 模块常量配置

# V2Ray Core 下载 URL 模板
V2RAY_DOWNLOAD_URL_TEMPLATE = "https://github.com/v2fly/v2ray-core/releases/download/v{version}/v2ray-linux-{arch}.zip"

# V2Ray latest release API URL
V2RAY_LATEST_RELEASE_API = "https://api.github.com/repos/v2fly/v2ray-core/releases/latest"

# 架构映射 (dpkg -> V2Ray 架构名称)
V2RAY_ARCH_MAP = {
    "amd64": "64",
    "arm64": "arm64-v8a",
    "armhf": "arm32-v7a",
}

# 默认安装目录
V2RAY_INSTALL_DIR = "/usr/local/bin"
V2RAY_CONFIG_DIR = "/usr/local/etc/v2ray"

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
        V2Ray 架构名称 (如 64, arm64-v8a)
    """
    # 优先从 hostvars 获取架构信息
    if hasattr(conn, "hostvars") and conn.hostvars:
        arch = conn.hostvars.get("architecture", "")
        if arch:
            dpkg_arch = normalize_arch(arch)
            return V2RAY_ARCH_MAP.get(dpkg_arch, "64")
    
    # 回退方案：直接执行命令获取
    result = conn.run("uname -m", hide=True)
    arch = result.stdout.strip()
    dpkg_arch = normalize_arch(arch)
    return V2RAY_ARCH_MAP.get(dpkg_arch, "64")


def _download_v2ray_zip(version: str, arch: str, dest_dir: str) -> str:
    """下载 V2Ray Core 压缩包到本地
    
    Args:
        version: 版本号
        arch: 架构标识
        dest_dir: 下载目标目录
        
    Returns:
        下载后的压缩包路径
    """
    version_number = resolve_version_via_api(version, V2RAY_LATEST_RELEASE_API)
    url = V2RAY_DOWNLOAD_URL_TEMPLATE.format(version=version_number, arch=arch)
    filename = f"v2ray-{version_number}-linux-{arch}.zip"
    return download_file(url, dest_dir, filename)

# endregion


# region Task 函数

@task
def install_v2ray(conn: Connection, version: str = "latest") -> None:
    """下载并安装 V2Ray Core (本地下载模式)
    
    先将 V2Ray 安装包下载到本地，然后上传到服务器并安装。
    适用于本地网络条件较好的场景。
    
    Args:
        conn: Fabric 连接对象
        version: 版本号，默认为 "latest"，也可以指定具体版本如 "5.12.1"
    """
    arch = _get_remote_arch(conn)
    print(f"[INFO] 目标架构: {arch}")
    print(f"[INFO] 安装版本: {version}")
    
    remote_tmp_dir = "/tmp/v2ray_install"
    remote_zip = f"{remote_tmp_dir}/v2ray.zip"
    
    # region 下载并上传压缩包
    print(f"\n[任务] 下载 V2Ray Core {version}")
    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = _download_v2ray_zip(version, arch, temp_dir)
        
        print("\n[任务] 上传压缩包到远程主机")
        conn.run(f"mkdir -p {remote_tmp_dir}", env=ENV_LANG_C)
        conn.put(zip_path, remote_zip)
        print(f"  上传完成: {remote_zip}")
    # endregion
    
    # region 解压并安装
    print("\n[任务] 解压并安装 V2Ray Core")
    # 确保 unzip 已安装
    conn.sudo("bash -c 'apt-get update && apt-get install -y unzip'", env=ENV_LANG_C, hide=True)
    
    conn.run(f"unzip -o {remote_zip} -d {remote_tmp_dir}", env=ENV_LANG_C)
    
    # 创建配置目录
    conn.sudo(f"mkdir -p {V2RAY_CONFIG_DIR}", env=ENV_LANG_C)
    
    # 安装二进制文件
    conn.sudo(f"cp {remote_tmp_dir}/v2ray {V2RAY_INSTALL_DIR}/v2ray", env=ENV_LANG_C)
    conn.sudo(f"chmod +x {V2RAY_INSTALL_DIR}/v2ray", env=ENV_LANG_C)
    print(f"  v2ray 已安装到: {V2RAY_INSTALL_DIR}/v2ray")
    
    # 复制配置文件示例 (如果不存在)
    result = conn.run(f"test -f {V2RAY_CONFIG_DIR}/config.json", warn=True, hide=True)
    if result.failed:
        conn.sudo(f"cp {remote_tmp_dir}/config.json {V2RAY_CONFIG_DIR}/config.json", env=ENV_LANG_C)
        print(f"  配置文件已复制到: {V2RAY_CONFIG_DIR}/config.json")
    else:
        print("  配置文件已存在，跳过复制")
    
    # 复制 geoip 和 geosite 数据文件
    conn.sudo(f"cp {remote_tmp_dir}/geoip.dat {V2RAY_CONFIG_DIR}/geoip.dat", env=ENV_LANG_C)
    conn.sudo(f"cp {remote_tmp_dir}/geosite.dat {V2RAY_CONFIG_DIR}/geosite.dat", env=ENV_LANG_C)
    print("  地理位置数据文件已安装")
    # endregion
    
    # region 清理临时文件
    print("\n[任务] 清理临时文件")
    conn.run(f"rm -rf {remote_tmp_dir}", env=ENV_LANG_C)
    print("  清理完成")
    # endregion
    
    # region 验证安装
    print("\n[任务] 验证安装")
    result = conn.run(f"{V2RAY_INSTALL_DIR}/v2ray version", hide=True)
    print(f"  {result.stdout.strip()}")
    # endregion
    
    print(f"\n[OK] V2Ray Core {version} 安装完成 (本地下载模式)")
    print(f"[提示] 配置文件位置: {V2RAY_CONFIG_DIR}/config.json")
    print(f"[提示] 启动命令: {V2RAY_INSTALL_DIR}/v2ray run -c {V2RAY_CONFIG_DIR}/config.json")


@task
def install_v2ray_remote(conn: Connection, version: str = "latest") -> None:
    """下载并安装 V2Ray Core (远程下载模式)
    
    直接在远程主机上下载安装包并安装。
    适用于远程主机网络条件较好的场景。
    
    Args:
        conn: Fabric 连接对象
        version: 版本号，默认为 "latest"，也可以指定具体版本如 "5.12.1"
    """
    arch = _get_remote_arch(conn)
    version_number = resolve_version_via_api(version, V2RAY_LATEST_RELEASE_API)
    print(f"[INFO] 目标架构: {arch}")
    print(f"[INFO] 安装版本: {version_number}")
    
    download_url = V2RAY_DOWNLOAD_URL_TEMPLATE.format(version=version_number, arch=arch)
    print(f"[INFO] 下载地址: {download_url}")
    
    remote_tmp_dir = "/tmp/v2ray_install"
    remote_zip = f"{remote_tmp_dir}/v2ray.zip"
    
    # region 在远程主机上下载压缩包
    print(f"\n[任务] 在远程主机上下载 V2Ray Core {version}")
    conn.run(f"mkdir -p {remote_tmp_dir}", env=ENV_LANG_C)
    conn.run(f"curl -fsSL -o {remote_zip} '{download_url}'", env=ENV_LANG_C)
    print(f"  下载完成: {remote_zip}")
    # endregion
    
    # region 解压并安装
    print("\n[任务] 解压并安装 V2Ray Core")
    # 确保 unzip 已安装
    conn.sudo("apt-get update && apt-get install -y unzip", env=ENV_LANG_C, hide=True)
    
    conn.run(f"unzip -o {remote_zip} -d {remote_tmp_dir}", env=ENV_LANG_C)
    
    # 创建配置目录
    conn.sudo(f"mkdir -p {V2RAY_CONFIG_DIR}", env=ENV_LANG_C)
    
    # 安装二进制文件
    conn.sudo(f"cp {remote_tmp_dir}/v2ray {V2RAY_INSTALL_DIR}/v2ray", env=ENV_LANG_C)
    conn.sudo(f"chmod +x {V2RAY_INSTALL_DIR}/v2ray", env=ENV_LANG_C)
    print(f"  v2ray 已安装到: {V2RAY_INSTALL_DIR}/v2ray")
    
    # 复制配置文件示例 (如果不存在)
    result = conn.run(f"test -f {V2RAY_CONFIG_DIR}/config.json", warn=True, hide=True)
    if result.failed:
        conn.sudo(f"cp {remote_tmp_dir}/config.json {V2RAY_CONFIG_DIR}/config.json", env=ENV_LANG_C)
        print(f"  配置文件已复制到: {V2RAY_CONFIG_DIR}/config.json")
    else:
        print("  配置文件已存在，跳过复制")
    
    # 复制 geoip 和 geosite 数据文件
    conn.sudo(f"cp {remote_tmp_dir}/geoip.dat {V2RAY_CONFIG_DIR}/geoip.dat", env=ENV_LANG_C)
    conn.sudo(f"cp {remote_tmp_dir}/geosite.dat {V2RAY_CONFIG_DIR}/geosite.dat", env=ENV_LANG_C)
    print("  地理位置数据文件已安装")
    # endregion
    
    # region 清理临时文件
    print("\n[任务] 清理临时文件")
    conn.run(f"rm -rf {remote_tmp_dir}", env=ENV_LANG_C)
    print("  清理完成")
    # endregion
    
    # region 验证安装
    print("\n[任务] 验证安装")
    result = conn.run(f"{V2RAY_INSTALL_DIR}/v2ray version", hide=True)
    print(f"  {result.stdout.strip()}")
    # endregion
    
    print(f"\n[OK] V2Ray Core {version} 安装完成 (远程下载模式)")
    print(f"[提示] 配置文件位置: {V2RAY_CONFIG_DIR}/config.json")
    print(f"[提示] 启动命令: {V2RAY_INSTALL_DIR}/v2ray run -c {V2RAY_CONFIG_DIR}/config.json")

# endregion
