#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
替换 GitHub Release v1.1.0 中的 TEXACO_GUI.exe 资源文件。

用法：
    1. 设置环境变量后运行：
       $env:GITHUB_TOKEN = "ghp_xxxx"
       .venv\Scripts\python scripts\upload_release.py

    2. 或运行时交互式输入 Token：
       .venv\Scripts\python scripts\upload_release.py
"""

import os
import sys
import getpass
from pathlib import Path

import requests

REPO = "Zonas-Liu/texaco_gasfier"
TAG = "v1.1.0"
ASSET_NAME = "TEXACO_GUI.exe"
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
LOCAL_EXE = PROJECT_ROOT / "dist" / ASSET_NAME


def get_token() -> str:
    """从环境变量或交互式输入获取 GitHub Token。"""
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        return token
    print("请输入 GitHub Personal Access Token（输入内容不会显示）：")
    return getpass.getpass("Token: ").strip()


def get_release(token: str) -> dict:
    """获取指定 Tag 的 Release 信息。"""
    url = f"https://api.github.com/repos/{REPO}/releases/tags/{TAG}"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


def check_repo_permission(token: str) -> None:
    """检查 Token 是否对该仓库有写权限，失败时给出明确提示。"""
    url = f"https://api.github.com/repos/{REPO}"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    data = response.json()
    permissions = data.get("permissions", {})
    if not permissions.get("push") and not permissions.get("admin"):
        print("错误：当前 Token 对该仓库没有写入权限。")
        print("请使用具有以下权限的 Token 后重试：")
        print("  - Classic PAT：勾选 repo 权限")
        print("  - Fine-grained PAT：授予 Contents 和 Releases 的 Read and write 权限")
        sys.exit(1)


def delete_asset(asset_id: int, token: str) -> None:
    """删除指定的 Release Asset。"""
    url = f"https://api.github.com/repos/{REPO}/releases/assets/{asset_id}"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
    response = requests.delete(url, headers=headers, timeout=30)
    response.raise_for_status()
    print(f"  已删除旧资源 (asset id: {asset_id})")


def upload_asset(upload_url: str, file_path: Path, token: str) -> dict:
    """上传新的 Release Asset。"""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/octet-stream",
    }
    params = {"name": file_path.name}
    with open(file_path, "rb") as f:
        response = requests.post(upload_url, headers=headers, params=params, data=f, timeout=120)
    response.raise_for_status()
    return response.json()


def main() -> int:
    if not LOCAL_EXE.exists():
        print(f"错误：本地文件不存在：{LOCAL_EXE}")
        print("请先运行 PyInstaller 打包生成 dist/TEXACO_GUI.exe")
        return 1

    token = get_token()
    print("正在检查 Token 权限...")
    check_repo_permission(token)
    print(f"正在获取 Release {TAG} 信息...")
    release = get_release(token)
    upload_url = release["upload_url"].replace("{?name,label}", "")

    # 删除同名旧资源
    old_assets = [a for a in release.get("assets", []) if a["name"] == ASSET_NAME]
    if old_assets:
        print(f"发现 {len(old_assets)} 个旧版 {ASSET_NAME}，准备删除...")
        for asset in old_assets:
            delete_asset(asset["id"], token)
    else:
        print(f"未找到旧版 {ASSET_NAME}，直接上传新文件。")

    # 上传新资源
    print(f"正在上传 {LOCAL_EXE} ({LOCAL_EXE.stat().st_size / 1024 / 1024:.2f} MB)...")
    new_asset = upload_asset(upload_url, LOCAL_EXE, token)
    print(f"上传成功！")
    print(f"  下载链接：{new_asset['browser_download_url']}")
    print(f"  资源大小：{new_asset['size'] / 1024 / 1024:.2f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
