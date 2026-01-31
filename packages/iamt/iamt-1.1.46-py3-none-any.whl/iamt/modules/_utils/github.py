"""GitHub 相关的通用辅助函数

包含从 GitHub 下载文件和解析版本号的功能。
"""

import json
import os
import urllib.request
from pathlib import Path
from typing import Callable


# region 文件下载


def download_file(
    url: str,
    dest_dir: str | Path,
    filename: str | None = None,
    skip_existing: bool = True,
    progress_callback: Callable[[int, int, int], None] | None = None,
) -> str:
    """下载文件到本地目录

    通用的文件下载函数，支持进度显示和跳过已存在文件。

    Args:
        url: 下载 URL
        dest_dir: 下载目标目录
        filename: 保存的文件名，默认从 URL 中提取
        skip_existing: 是否跳过已存在的文件，默认为 True
        progress_callback: 自定义进度回调函数，签名为 (block_num, block_size, total_size)

    Returns:
        下载后的文件完整路径
    """
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    if filename is None:
        filename = url.rsplit("/", 1)[-1]

    dest_path = dest_dir / filename

    if skip_existing and dest_path.exists():
        print(f"  文件已存在: {dest_path}")
        return str(dest_path)

    print(f"  正在下载: {url}")

    def default_progress_hook(block_num: int, block_size: int, total_size: int) -> None:
        if total_size > 0:
            percent = min(100, block_num * block_size * 100 // total_size)
            print(f"\r  下载进度: {percent}%", end="", flush=True)

    hook = progress_callback or default_progress_hook
    urllib.request.urlretrieve(url, str(dest_path), hook)
    print(f"\n  下载完成: {dest_path}")

    return str(dest_path)


# endregion


# region 版本解析


def resolve_version(version: str, latest_release_url: str, strip_v: bool = True) -> str:
    """解析版本号，返回实际的版本号

    通过 GitHub releases/latest 重定向 URL 获取最新版本号，
    适用于大多数 GitHub 项目的版本获取。

    Args:
        version: 版本号，可以是 "latest" 或具体版本号如 "0.40.1"
        latest_release_url: 用于获取最新版本号的重定向 URL，
                           例如 "https://github.com/nvm-sh/nvm/releases/latest"
        strip_v: 是否移除版本号的 v 前缀，默认为 True

    Returns:
        实际的版本号，例如 "0.40.1"
    """
    if version == "latest":
        # 通过 HTTP 重定向获取最新版本号
        req = urllib.request.Request(latest_release_url, method="HEAD")
        req.add_header("User-Agent", "Mozilla/5.0")
        with urllib.request.urlopen(req) as response:
            # 重定向后的 URL 格式: https://github.com/xxx/releases/tag/v0.40.1 或 /tag/7.16.6
            final_url = response.geturl()
            tag = final_url.rsplit("/", 1)[-1]
            return tag.lstrip("v") if strip_v else tag

    # 根据 strip_v 参数决定是否移除 'v' 前缀
    return version.lstrip("v") if strip_v else version


def resolve_version_via_api(version: str, api_url: str, strip_v: bool = True) -> str:
    """通过 GitHub API 解析版本号

    适用于某些项目的 releases/latest 重定向不可用的情况。

    Args:
        version: 版本号，可以是 "latest" 或具体版本号如 "5.12.1"
        api_url: GitHub API URL，
                例如 "https://api.github.com/repos/v2fly/v2ray-core/releases/latest"
        strip_v: 是否移除版本号的 v 前缀，默认为 True

    Returns:
        实际的版本号，例如 "5.12.1"
    """
    if version == "latest":
        req = urllib.request.Request(api_url)
        req.add_header("User-Agent", "Mozilla/5.0")
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            tag = data["tag_name"]
            return tag.lstrip("v") if strip_v else tag

    return version.lstrip("v") if strip_v else version


# endregion
