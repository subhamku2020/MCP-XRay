from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlparse


def is_github_url(value: str) -> bool:
    value = value.strip()
    return value.startswith("https://github.com/") or value.startswith("git@github.com:")


def repo_name_from_url(url: str) -> str:
    if url.startswith("git@github.com:"):
        tail = url.split(":", 1)[1]
        return tail.replace(".git", "").split("/")[-1]
    parsed = urlparse(url)
    return Path(parsed.path.replace(".git", "")).name


def clone_or_update_repo(repo_url: str, workspace: Path) -> Path:
    workspace.mkdir(parents=True, exist_ok=True)
    repo_name = repo_name_from_url(repo_url)
    target = workspace / repo_name

    if target.exists() and (target / ".git").exists():
        subprocess.run(["git", "-C", str(target), "pull", "--ff-only"], check=False)
        return target

    if target.exists():
        shutil.rmtree(target)

    subprocess.run(["git", "clone", "--depth", "1", repo_url, str(target)], check=True)
    return target


def resolve_scan_target(value: str, workspace: Path) -> Path:
    value = value.strip()
    if is_github_url(value):
        return clone_or_update_repo(value, workspace)

    path = Path(value).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"Path not found: {path}")
    return path
