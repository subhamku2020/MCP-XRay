from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ToolRecord(BaseModel):
    repo_name: str
    file_path: str
    language: str
    server_name: str = "unknown-mcp-server"
    tool_name: str
    description: str = ""
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    declared_permission: Optional[str] = None
    declared_action: Optional[str] = None
    declared_resource: Optional[str] = None
    declared_risk: Optional[str] = None
    code_snippet: str = ""
    evidence: List[str] = Field(default_factory=list)


class PermissionRecord(BaseModel):
    permission: str
    action: str
    resource: str
    risk: str
    source: str
    reason: str


class GraphData(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    summary: Dict[str, Any]
    tools: List[Dict[str, Any]]
