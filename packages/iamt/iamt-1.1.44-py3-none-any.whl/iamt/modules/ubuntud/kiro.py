from fabric import Connection, task

from .._utils.github import download_file


# region Kiro IDE 安装任务


@task
def install_kiro(conn: Connection, version: str = "0.8.86") -> None:
    """下载、上传并安装 Kiro IDE deb 包
    
    Args:
        conn: Fabric 连接对象
        version: Kiro IDE 版本号，默认为 0.8.86
    """
    deb_filename = f"kiro-ide-{version}-stable-linux-x64.deb"
    
    # region 下载 deb 包到本地
    print(f"\n[任务] 下载 Kiro IDE {version}")
    download_url = f"https://prod.download.desktop.kiro.dev/releases/stable/linux-x64/signed/{version}/deb/{deb_filename}"
    deb_path = download_file(download_url, conn.artifacts_dir, deb_filename)
    # endregion
    
    # region 上传 deb 包到服务器
    print("\n[任务] 上传 deb 包到服务器")
    remote_deb_path = f"/tmp/{deb_filename}"
    conn.put(deb_path, remote_deb_path)
    print(f"  上传完成: {remote_deb_path}")
    # endregion
    
    # region 安装 deb 包
    print("\n[任务] 安装 Kiro IDE")
    # 使用 dpkg 安装，如果有依赖问题则用 apt-get -f install 修复
    conn.sudo(f"dpkg -i {remote_deb_path}", warn=True)
    conn.sudo("apt-get install -f -y", warn=True)
    print("  安装完成")
    # endregion


# endregion
