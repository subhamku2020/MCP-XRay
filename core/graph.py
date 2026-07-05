from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List

from pyvis.network import Network

from core.infer import infer_permission
from core.models import GraphData, PermissionRecord, ToolRecord


NODE_COLORS = {
    "repo": "#4f46e5",
    "file": "#64748b",
    "mcp_server": "#0891b2",
    "tool": "#16a34a",
    "permission": "#f59e0b",
    "resource": "#9333ea",
    "risk": "#ef4444",
}

RISK_COLORS = {
    "critical": "#7f1d1d",
    "high": "#dc2626",
    "medium": "#f97316",
    "low": "#22c55e",
    "unknown": "#6b7280",
}


def _node(nodes: Dict[str, Dict[str, Any]], node_id: str, label: str, node_type: str, **extra: Any) -> None:
    if node_id not in nodes:
        nodes[node_id] = {
            "id": node_id,
            "label": label,
            "type": node_type,
            **extra,
        }


def _edge(edges: List[Dict[str, Any]], source: str, target: str, label: str) -> None:
    edge = {"source": source, "target": target, "label": label}
    if edge not in edges:
        edges.append(edge)


def build_graph(repo_name: str, tools: List[ToolRecord]) -> GraphData:
    nodes: Dict[str, Dict[str, Any]] = {}
    edges: List[Dict[str, Any]] = []
    enriched_tools: List[Dict[str, Any]] = []

    repo_id = f"repo:{repo_name}"
    _node(nodes, repo_id, repo_name, "repo")

    for tool in tools:
        perm: PermissionRecord = infer_permission(tool)

        file_id = f"file:{tool.file_path}"
        server_id = f"server:{tool.server_name}:{tool.file_path}"
        tool_id = f"tool:{tool.file_path}:{tool.tool_name}"
        perm_id = f"perm:{perm.permission}:{tool.file_path}:{tool.tool_name}"
        resource_id = f"resource:{perm.resource}"
        risk_id = f"risk:{perm.risk}"

        _node(nodes, file_id, tool.file_path, "file")
        _node(nodes, server_id, tool.server_name, "mcp_server")
        _node(
            nodes,
            tool_id,
            tool.tool_name,
            "tool",
            description=tool.description,
            language=tool.language,
            file_path=tool.file_path,
        )
        _node(
            nodes,
            perm_id,
            perm.permission,
            "permission",
            action=perm.action,
            source=perm.source,
            reason=perm.reason,
        )
        _node(nodes, resource_id, perm.resource, "resource")
        _node(nodes, risk_id, perm.risk, "risk")

        _edge(edges, repo_id, file_id, "contains")
        _edge(edges, file_id, server_id, "defines")
        _edge(edges, server_id, tool_id, "exposes")
        _edge(edges, tool_id, perm_id, "requires")
        _edge(edges, perm_id, resource_id, "acts_on")
        _edge(edges, perm_id, risk_id, "risk")

        enriched_tools.append({
            **tool.model_dump(),
            **perm.model_dump(),
        })

    risk_counts = Counter(t["risk"] for t in enriched_tools)
    source_counts = Counter(t["source"] for t in enriched_tools)

    summary = {
        "repo": repo_name,
        "tool_count": len(enriched_tools),
        "permission_count": len({t["permission"] for t in enriched_tools}),
        "resource_count": len({t["resource"] for t in enriched_tools}),
        "critical_count": risk_counts.get("critical", 0),
        "high_count": risk_counts.get("high", 0),
        "medium_count": risk_counts.get("medium", 0),
        "low_count": risk_counts.get("low", 0),
        "unknown_count": risk_counts.get("unknown", 0),
        "declared_count": source_counts.get("declared", 0),
        "inferred_count": source_counts.get("inferred", 0),
        "unknown_source_count": source_counts.get("unknown", 0),
    }

    return GraphData(
        nodes=list(nodes.values()),
        edges=edges,
        summary=summary,
        tools=enriched_tools,
    )


def render_pyvis_html(graph: GraphData, output_path: str) -> str:
    net = Network(height="760px", width="100%", bgcolor="#0f172a", font_color="#e5e7eb", directed=True)
    net.barnes_hut(gravity=-28000, central_gravity=0.25, spring_length=170, spring_strength=0.02)

    for node in graph.nodes:
        node_type = node.get("type", "unknown")
        color = NODE_COLORS.get(node_type, "#94a3b8")
        if node_type == "risk":
            color = RISK_COLORS.get(node["label"], "#6b7280")

        title_lines = [f"<b>{node['label']}</b>", f"Type: {node_type}"]
        for key in ["description", "file_path", "action", "source", "reason"]:
            if node.get(key):
                title_lines.append(f"{key}: {node[key]}")

        net.add_node(
            node["id"],
            label=node["label"],
            title="<br>".join(title_lines),
            color=color,
            shape="dot" if node_type not in {"repo", "file"} else "box",
            size=24 if node_type in {"repo", "risk"} else 18,
        )

    for edge in graph.edges:
        net.add_edge(edge["source"], edge["target"], label=edge.get("label", ""), arrows="to")

    net.set_options("""
    const options = {
      "nodes": {
        "borderWidth": 1,
        "font": { "size": 16, "face": "Inter" }
      },
      "edges": {
        "color": { "color": "#94a3b8", "highlight": "#ffffff" },
        "font": { "size": 12, "align": "middle", "color": "#e5e7eb" },
        "smooth": { "type": "dynamic" }
      },
      "physics": {
        "enabled": true,
        "stabilization": { "iterations": 120 }
      },
      "interaction": {
        "hover": true,
        "navigationButtons": true,
        "keyboard": true
      }
    }
    """)

    net.write_html(output_path, notebook=False)
    return output_path
