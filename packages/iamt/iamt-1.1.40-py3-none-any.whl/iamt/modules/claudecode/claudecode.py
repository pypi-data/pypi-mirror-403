"""Claude Code 模块 - 在远程 Linux 主机上安装和配置 Claude Code CLI

该模块通过 SSH 连接执行远程命令，实现 Claude Code 的自动化部署。
https://docs.claude.ai/docs/claude-code
"""

import hashlib
import json
import urllib.request
from pathlib import Path

from fabric import Connection, task


# region 模块常量配置

# Claude Code 发布存储桶 URL
GCS_BUCKET = "https://storage.googleapis.com/claude-code-dist-86c565f3-f756-42ad-8dfa-d59b1c096819/claude-code-releases"

# 默认下载目录 (相对于用户 home)
DOWNLOAD_DIR = ".claude/downloads"

# 环境变量 (使用英文输出避免中文乱码)
ENV_LANG_C = {"LANG": "C", "LC_ALL": "C"}

# endregion


# region 辅助函数


def _detect_platform(conn: Connection) -> str:
    """检测远程主机的平台类型
    
    Args:
        conn: Fabric 连接对象
        
    Returns:
        平台标识符，如 "linux-x64", "linux-arm64", "darwin-x64", "darwin-arm64", "linux-x64-musl"
    """
    # 检测操作系统
    os_result = conn.run("uname -s", hide=True, env=ENV_LANG_C)
    os_name = os_result.stdout.strip()
    
    if os_name == "Darwin":
        os_type = "darwin"
    elif os_name == "Linux":
        os_type = "linux"
    else:
        raise ValueError(f"不支持的操作系统: {os_name}")
    
    # 检测架构
    arch_result = conn.run("uname -m", hide=True, env=ENV_LANG_C)
    arch_name = arch_result.stdout.strip()
    
    if arch_name in ("x86_64", "amd64"):
        arch = "x64"
    elif arch_name in ("arm64", "aarch64"):
        arch = "arm64"
    else:
        raise ValueError(f"不支持的架构: {arch_name}")
    
    # Linux 系统需要检测是否为 musl
    if os_type == "linux":
        musl_check = conn.run(
            "[ -f /lib/libc.musl-x86_64.so.1 ] || [ -f /lib/libc.musl-aarch64.so.1 ] || ldd /bin/ls 2>&1 | grep -q musl",
            warn=True,
            hide=True,
            env=ENV_LANG_C
        )
        if musl_check.ok:
            return f"linux-{arch}-musl"
    
    return f"{os_type}-{arch}"


def _download_latest_version() -> str:
    """从 GCS 获取最新版本号
    
    Returns:
        最新版本号字符串
    """
    url = f"{GCS_BUCKET}/latest"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        return response.read().decode().strip()


def _download_manifest(version: str) -> dict:
    """下载指定版本的 manifest.json
    
    Args:
        version: 版本号
        
    Returns:
        manifest 字典
    """
    url = f"{GCS_BUCKET}/{version}/manifest.json"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode())


def _get_checksum_from_manifest(manifest: dict, platform: str) -> str:
    """从 manifest 中提取指定平台的 checksum
    
    Args:
        manifest: manifest 字典
        platform: 平台标识符
        
    Returns:
        SHA256 checksum (64位十六进制字符串)
    """
    platforms = manifest.get("platforms", {})
    platform_info = platforms.get(platform)
    
    if not platform_info:
        raise ValueError(f"平台 {platform} 在 manifest 中未找到")
    
    checksum = platform_info.get("checksum", "")
    
    # 验证 checksum 格式 (SHA256 = 64个十六进制字符)
    if not checksum or len(checksum) != 64 or not all(c in "0123456789abcdef" for c in checksum):
        raise ValueError(f"无效的 checksum 格式: {checksum}")
    
    return checksum


def _download_binary(version: str, platform: str, dest_path: Path) -> None:
    """下载 Claude Code 二进制文件到本地
    
    Args:
        version: 版本号
        platform: 平台标识符
        dest_path: 本地保存路径
    """
    url = f"{GCS_BUCKET}/{version}/{platform}/claude"
    
    print(f"  正在下载: {url}")
    
    def progress_hook(block_num: int, block_size: int, total_size: int) -> None:
        if total_size > 0:
            percent = min(100, block_num * block_size * 100 // total_size)
            print(f"\r  下载进度: {percent}%", end="", flush=True)
    
    urllib.request.urlretrieve(url, str(dest_path), progress_hook)
    print(f"\n  下载完成: {dest_path}")


def _verify_checksum(file_path: Path, expected_checksum: str) -> bool:
    """验证文件的 SHA256 checksum
    
    Args:
        file_path: 文件路径
        expected_checksum: 期望的 checksum
        
    Returns:
        验证是否通过
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    actual_checksum = sha256_hash.hexdigest()
    return actual_checksum == expected_checksum


# endregion


# region Task 函数


@task
def install_claude_code(conn: Connection, target: str = "stable") -> None:
    """下载并安装 Claude Code CLI
    
    先将 Claude Code 二进制文件下载到本地，验证 checksum，
    然后上传到服务器并执行安装。
    
    Args:
        conn: Fabric 连接对象
        target: 安装目标版本，可选值:
               - "stable": 稳定版本 (默认)
               - "latest": 最新版本
               - 具体版本号: 如 "1.2.3" 或 "1.2.3-beta.1"
    """
    # region 验证 target 参数
    if target not in ("stable", "latest"):
        # 验证版本号格式: x.y.z 或 x.y.z-suffix
        import re
        if not re.match(r"^\d+\.\d+\.\d+(-[^\s]+)?$", target):
            raise ValueError(f"无效的 target 参数: {target}，应为 'stable'、'latest' 或有效的版本号")
    # endregion
    
    # region 获取系统信息
    user_home = conn.hostvars.get("user_home", "~")
    download_dir = f"{user_home}/{DOWNLOAD_DIR}"
    platform = _detect_platform(conn)
    # endregion
    
    print(f"[INFO] 目标平台: {platform}")
    print(f"[INFO] 安装目标: {target}")
    print(f"[INFO] 下载目录: {download_dir}")
    
    # region 获取版本信息
    print("\n[任务] 获取版本信息")
    version = _download_latest_version()
    print(f"  最新版本: {version}")
    # endregion
    
    # region 下载 manifest 并获取 checksum
    print("\n[任务] 下载 manifest")
    manifest = _download_manifest(version)
    checksum = _get_checksum_from_manifest(manifest, platform)
    print(f"  平台: {platform}")
    print(f"  Checksum: {checksum}")
    # endregion
    
    # region 下载二进制文件到本地
    print("\n[任务] 下载 Claude Code 二进制文件")
    local_binary_name = f"claude-{version}-{platform}"
    local_binary_path = conn.artifacts_dir / local_binary_name
    
    # 检查本地是否已存在且 checksum 正确
    if local_binary_path.exists():
        print(f"  本地文件已存在: {local_binary_path}")
        print("  验证 checksum...")
        if _verify_checksum(local_binary_path, checksum):
            print("  Checksum 验证通过，跳过下载")
        else:
            print("  Checksum 验证失败，重新下载")
            local_binary_path.unlink()
            _download_binary(version, platform, local_binary_path)
    else:
        _download_binary(version, platform, local_binary_path)
    # endregion
    
    # region 验证本地文件 checksum
    print("\n[任务] 验证文件完整性")
    if not _verify_checksum(local_binary_path, checksum):
        local_binary_path.unlink()
        raise RuntimeError("Checksum 验证失败，文件可能已损坏")
    print("  Checksum 验证通过")
    # endregion
    
    # region 上传到远程服务器
    print("\n[任务] 上传到远程服务器")
    conn.run(f"mkdir -p {download_dir}", env=ENV_LANG_C)
    remote_binary_path = f"{download_dir}/claude-{version}-{platform}"
    
    # 使用进度显示上传
    result = conn.put(str(local_binary_path), remote_binary_path)
    print(f"  上传完成: {result.remote}")
    # endregion
    
    # region 设置可执行权限
    print("\n[任务] 设置可执行权限")
    conn.run(f"chmod +x {remote_binary_path}", env=ENV_LANG_C)
    print("  权限设置完成")
    # endregion
    
    # region 执行安装
    print("\n[任务] 执行 Claude Code 安装")
    install_cmd = f"{remote_binary_path} install"
    if target:
        install_cmd += f" {target}"
    
    conn.run(install_cmd, env=ENV_LANG_C, pty=True)
    # endregion
    
    # region 清理远程临时文件
    print("\n[任务] 清理远程临时文件")
    conn.run(f"rm -f {remote_binary_path}", env=ENV_LANG_C)
    print("  清理完成")
    # endregion
    
    print(f"\n[OK] Claude Code 安装完成")
    print("[提示] 请重新登录或执行 'source ~/.bashrc' (或 ~/.zshrc) 以使 claude 命令生效")


# endregion
