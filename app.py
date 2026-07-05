from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from core.git_utils import resolve_scan_target
from core.graph import render_pyvis_html
from core.scanner import scan_repo
from core.snapshot import diff_snapshots, save_snapshot


APP_ROOT = Path(__file__).resolve().parent
WORKSPACE = APP_ROOT / ".workspace"
SNAPSHOTS = APP_ROOT / "snapshots"
GRAPH_HTML = APP_ROOT / ".workspace" / "graph.html"


st.set_page_config(page_title="MCP-XRay", layout="wide")

st.title("MCP-XRay")
st.caption("GitHub/local repository scanner for MCP tools and permission graph visualization.")

with st.sidebar:
    st.header("Scan source")
    mode = st.radio("Scan mode", ["Local folder", "GitHub URL"], index=0)

    if mode == "Local folder":
        source = st.text_input("Local folder path", value="samples/demo_repo")
    else:
        source = st.text_input("GitHub repo URL", value="https://github.com/org/repo")

    scan_button = st.button("Scan", type="primary")

    st.divider()
    st.header("Snapshot diff")
    snapshot_files = sorted(SNAPSHOTS.glob("*.json")) if SNAPSHOTS.exists() else []
    old_snap = st.selectbox("Old snapshot", [""] + [str(p) for p in snapshot_files], index=0)
    new_snap = st.selectbox("New snapshot", [""] + [str(p) for p in snapshot_files], index=0)
    diff_button = st.button("Compare snapshots")


if scan_button:
    try:
        with st.spinner("Scanning repository..."):
            target = resolve_scan_target(source, WORKSPACE)
            graph = scan_repo(target)
            st.session_state["graph"] = graph.model_dump()
            saved = save_snapshot(graph, SNAPSHOTS)
            st.session_state["last_snapshot"] = str(saved)

        st.success(f"Scan completed. Snapshot saved: {saved}")
    except Exception as exc:
        st.error(f"Scan failed: {exc}")


if diff_button:
    if old_snap and new_snap:
        result = diff_snapshots(Path(old_snap), Path(new_snap))
        st.subheader("Snapshot diff")
        c1, c2, c3 = st.columns(3)
        c1.metric("Added tools", len(result["added"]))
        c2.metric("Removed tools", len(result["removed"]))
        c3.metric("Modified tools", len(result["modified"]))

        st.write("### Added")
        st.dataframe(pd.DataFrame(result["added"]), use_container_width=True)

        st.write("### Removed")
        st.dataframe(pd.DataFrame(result["removed"]), use_container_width=True)

        st.write("### Modified")
        st.json(result["modified"])
    else:
        st.warning("Select both old and new snapshots.")


graph_dict = st.session_state.get("graph")

if not graph_dict:
    st.info("Run a scan to see the graph. For a quick test, scan `samples/demo_repo`.")
    st.stop()


summary = graph_dict["summary"]
tools = graph_dict["tools"]

st.subheader("Summary")
cols = st.columns(8)
cols[0].metric("Tools", summary["tool_count"])
cols[1].metric("Permissions", summary["permission_count"])
cols[2].metric("Resources", summary["resource_count"])
cols[3].metric("Critical", summary["critical_count"])
cols[4].metric("High", summary["high_count"])
cols[5].metric("Medium", summary["medium_count"])
cols[6].metric("Low", summary["low_count"])
cols[7].metric("Unknown", summary["unknown_count"])

tab_graph, tab_table, tab_json = st.tabs(["Graph", "Tool table", "Graph JSON"])

with tab_graph:
    from core.models import GraphData
    graph = GraphData(**graph_dict)
    GRAPH_HTML.parent.mkdir(parents=True, exist_ok=True)
    render_pyvis_html(graph, str(GRAPH_HTML))
    components.html(GRAPH_HTML.read_text(encoding="utf-8"), height=800, scrolling=True)

with tab_table:
    df = pd.DataFrame(tools)
    if not df.empty:
        show_cols = [
            "tool_name",
            "permission",
            "risk",
            "source",
            "action",
            "resource",
            "server_name",
            "file_path",
            "language",
            "reason",
        ]
        st.dataframe(df[[c for c in show_cols if c in df.columns]], use_container_width=True)

        st.download_button(
            "Download tools CSV",
            df.to_csv(index=False),
            file_name="mcp_xray_tools.csv",
            mime="text/csv",
        )
    else:
        st.warning("No tools detected.")

with tab_json:
    st.download_button(
        "Download graph JSON",
        json.dumps(graph_dict, indent=2),
        file_name="mcp_xray_graph.json",
        mime="application/json",
    )
    st.json(graph_dict)
