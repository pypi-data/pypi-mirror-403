"""NVM 模块 - 在远程 Linux 主机上安装和配置 Node Version Manager

该模块通过 SSH 连接执行远程命令，实现 NVM 的自动化部署。
https://github.com/nvm-sh/nvm
"""

from fabric import Connection, task

from iamt.modules._utils.github import download_file, resolve_version


# region 模块常量配置

# NVM 下载 URL 模板
NVM_DOWNLOAD_URL_TEMPLATE = "https://github.com/nvm-sh/nvm/archive/refs/tags/v{version}.tar.gz"

# NVM latest release 重定向 URL (用于获取最新版本号)
NVM_LATEST_RELEASE_URL = "https://github.com/nvm-sh/nvm/releases/latest"

# 默认安装目录 (相对于用户 home)
NVM_INSTALL_DIR = ".nvm"

# 环境变量 (使用英文输出避免中文乱码)
ENV_LANG_C = {"LANG": "C", "LC_ALL": "C"}

# endregion


# region 辅助函数

def _download_nvm_tarball(version: str, dest_dir: str) -> tuple[str, str]:
    """下载 NVM 压缩包到本地
    
    Args:
        version: 版本号
        dest_dir: 下载目标目录
        
    Returns:
        (下载后的压缩包路径, 实际版本号)
    """
    version_number = resolve_version(version, NVM_LATEST_RELEASE_URL)
    url = NVM_DOWNLOAD_URL_TEMPLATE.format(version=version_number)
    filename = f"nvm-{version_number}.tar.gz"
    dest_path = download_file(url, dest_dir, filename)
    return dest_path, version_number


def _get_shell_rc_file(conn: Connection) -> str:
    """获取用户的 shell 配置文件路径
    
    Args:
        conn: Fabric 连接对象
        
    Returns:
        shell 配置文件路径 (如 ~/.bashrc, ~/.zshrc)
    """
    result = conn.run("echo $SHELL", hide=True)
    shell = result.stdout.strip()
    
    if "zsh" in shell:
        return "~/.zshrc"
    return "~/.bashrc"

# endregion


# region Task 函数

@task
def install_nvm(conn: Connection, version: str = "latest") -> None:
    """下载并安装 NVM (本地下载模式)
    
    先将 NVM 安装包下载到本地，然后上传到服务器并安装。
    适用于本地网络条件较好的场景。
    
    Args:
        conn: Fabric 连接对象
        version: 版本号，默认为 "latest"，也可以指定具体版本如 "0.40.1"
    """
    # region 获取用户 home 目录
    user_home = conn.hostvars.get("user_home", "~")
    nvm_dir = f"{user_home}/{NVM_INSTALL_DIR}"
    # endregion
    
    print(f"[INFO] 安装版本: {version}")
    print(f"[INFO] 安装目录: {nvm_dir}")
    
    remote_tmp_dir = "/tmp/nvm_install"
    remote_tarball = f"{remote_tmp_dir}/nvm.tar.gz"
    
    # region 下载并上传压缩包
    print(f"\n[任务] 下载 NVM {version}")
    tarball_path, version_number = _download_nvm_tarball(version, conn.artifacts_dir)
    
    print("\n[任务] 上传压缩包到远程主机")
    conn.run(f"mkdir -p {remote_tmp_dir}", env=ENV_LANG_C)
    conn.put(tarball_path, remote_tarball)
    print(f"  上传完成: {remote_tarball}")
    # endregion
    
    # region 解压并安装
    print("\n[任务] 解压并安装 NVM")
    conn.run(f"tar -xzf {remote_tarball} -C {remote_tmp_dir}", env=ENV_LANG_C)
    
    # 创建 NVM 目录并移动文件
    conn.run(f"rm -rf {nvm_dir}", env=ENV_LANG_C)
    conn.run(f"mv {remote_tmp_dir}/nvm-{version_number} {nvm_dir}", env=ENV_LANG_C)
    print(f"  NVM 已安装到: {nvm_dir}")
    # endregion
    
    # region 配置 shell 环境
    print("\n[任务] 配置 shell 环境")
    rc_file = _get_shell_rc_file(conn)
    
    nvm_config = f'''
# NVM Configuration
export NVM_DIR="{nvm_dir}"
[ -s "$NVM_DIR/nvm.sh" ] && \\. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \\. "$NVM_DIR/bash_completion"
'''
    
    # 检查是否已配置
    result = conn.run(f"grep -q 'NVM_DIR' {rc_file} 2>/dev/null", warn=True, hide=True)
    if result.ok:
        print(f"  NVM 配置已存在于 {rc_file}，跳过")
    else:
        conn.run(f"cat >> {rc_file} << 'EOF'{nvm_config}EOF", env=ENV_LANG_C)
        print(f"  NVM 配置已添加到 {rc_file}")
    # endregion
    
    # region 清理临时文件
    print("\n[任务] 清理临时文件")
    conn.run(f"rm -rf {remote_tmp_dir}", env=ENV_LANG_C)
    print("  清理完成")
    # endregion
    
    # region 验证安装
    print("\n[任务] 验证安装")
    result = conn.run(f'bash -c "source {nvm_dir}/nvm.sh && nvm --version"', hide=True)
    print(f"  NVM 版本: {result.stdout.strip()}")
    # endregion
    
    print(f"\n[OK] NVM {version_number} 安装完成")
    print(f"[提示] 请执行 'source {rc_file}' 或重新登录以使 nvm 命令生效")


@task
def set_nodejs_mirror(conn: Connection, mirror: str = "https://mirrors.cernet.edu.cn/nodejs-release/") -> None:
    """配置 NVM 的 Node.js 下载镜像源
    
    通过设置远程服务器rc文件当中的 NVM_NODEJS_ORG_MIRROR 环境变量来加速 Node.js 下载。
    
    Args:
        conn: Fabric 连接对象
        mirror: 镜像源 URL，默认为 CERNET 镜像
    """
    rc_file = _get_shell_rc_file(conn)
    env_line = f'export NVM_NODEJS_ORG_MIRROR="{mirror}"'
    
    print(f"[INFO] 配置 Node.js 镜像源: {mirror}")
    print(f"[INFO] 配置文件: {rc_file}")
    
    # region 检查并更新配置
    # 检查是否已存在 NVM_NODEJS_ORG_MIRROR 配置
    result = conn.run(f"grep -q 'NVM_NODEJS_ORG_MIRROR' {rc_file} 2>/dev/null", warn=True, hide=True)
    
    if result.ok:
        # 已存在，使用 sed 替换
        conn.run(
            f"sed -i 's|^export NVM_NODEJS_ORG_MIRROR=.*|{env_line}|' {rc_file}",
            env=ENV_LANG_C
        )
        print("  已更新 NVM_NODEJS_ORG_MIRROR 配置")
    else:
        # 不存在，追加到文件末尾
        conn.run(f'echo \'{env_line}\' >> {rc_file}', env=ENV_LANG_C)
        print("  已添加 NVM_NODEJS_ORG_MIRROR 配置")
    # endregion
    
    print("\n[OK] Node.js 镜像源配置完成")
    print(f"[提示] 请执行 'source {rc_file}' 或重新登录以使配置生效")

# endregion
