from __future__ import annotations

from pathlib import Path
from typing import List

from core.extractors import TEXT_EXTENSIONS, extract_tools_from_file
from core.graph import build_graph
from core.models import GraphData, ToolRecord


IGNORE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    ".next",
    ".cache",
    "target",
}


def should_ignore(path: Path) -> bool:
    return any(part in IGNORE_DIRS for part in path.parts)


def discover_candidate_files(repo_root: Path) -> List[Path]:
    files: List[Path] = []

    for path in repo_root.rglob("*"):
        if should_ignore(path):
            continue

        if not path.is_file():
            continue

        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue

        lower = str(path).lower()
        if any(token in lower for token in ["mcp", "tool", "server", "agent", "config", ".json", ".yaml", ".yml"]):
            files.append(path)

    return files


def scan_repo(repo_root: Path) -> GraphData:
    repo_root = repo_root.resolve()
    repo_name = repo_root.name

    tools: List[ToolRecord] = []
    for path in discover_candidate_files(repo_root):
        try:
            tools.extend(extract_tools_from_file(path, repo_root, repo_name))
        except Exception as exc:
            print(f"[WARN] Failed to scan {path}: {exc}")

    return build_graph(repo_name, tools)
