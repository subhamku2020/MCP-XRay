from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from core.models import GraphData


def save_snapshot(graph: GraphData, snapshot_dir: Path) -> Path:
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    repo = graph.summary.get("repo", "repo")
    path = snapshot_dir / f"{repo}_{ts}.json"
    path.write_text(graph.model_dump_json(indent=2), encoding="utf-8")
    return path


def load_snapshot(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def tool_key(t: Dict[str, Any]) -> str:
    return f"{t.get('file_path')}::{t.get('tool_name')}"


def diff_snapshots(old_path: Path, new_path: Path) -> Dict[str, List[Dict[str, Any]]]:
    old = load_snapshot(old_path)
    new = load_snapshot(new_path)

    old_tools = {tool_key(t): t for t in old.get("tools", [])}
    new_tools = {tool_key(t): t for t in new.get("tools", [])}

    added = [new_tools[k] for k in sorted(new_tools.keys() - old_tools.keys())]
    removed = [old_tools[k] for k in sorted(old_tools.keys() - new_tools.keys())]

    modified = []
    for key in sorted(old_tools.keys() & new_tools.keys()):
        o = old_tools[key]
        n = new_tools[key]
        watched = ["permission", "risk", "resource", "action", "source"]
        changes = {field: {"old": o.get(field), "new": n.get(field)} for field in watched if o.get(field) != n.get(field)}
        if changes:
            modified.append({"tool": key, "changes": changes, "old": o, "new": n})

    return {"added": added, "removed": removed, "modified": modified}
