from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from core.models import ToolRecord


MCP_PY_DECORATOR_PATTERNS = ["tool", "mcp.tool", "server.tool", "app.tool"]
TEXT_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".yaml", ".yml"}


def _safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def _literal(node: ast.AST) -> Any:
    try:
        return ast.literal_eval(node)
    except Exception:
        return None


def _decorator_name(dec: ast.AST) -> str:
    target = dec.func if isinstance(dec, ast.Call) else dec

    if isinstance(target, ast.Name):
        return target.id

    if isinstance(target, ast.Attribute):
        parts = [target.attr]
        value = target.value
        while isinstance(value, ast.Attribute):
            parts.append(value.attr)
            value = value.value
        if isinstance(value, ast.Name):
            parts.append(value.id)
        return ".".join(reversed(parts))

    return ""


def _decorator_kwargs(dec: ast.AST) -> Dict[str, Any]:
    if not isinstance(dec, ast.Call):
        return {}

    out = {}
    for kw in dec.keywords:
        out[kw.arg] = _literal(kw.value)
    return out


def _decorator_args(dec: ast.AST) -> List[Any]:
    if not isinstance(dec, ast.Call):
        return []
    return [_literal(arg) for arg in dec.args]


def _is_mcp_tool_decorator(dec: ast.AST) -> bool:
    name = _decorator_name(dec)
    return name in MCP_PY_DECORATOR_PATTERNS or name.endswith(".tool")


def _extract_schema_from_function(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> Dict[str, Any]:
    props: Dict[str, Any] = {}
    required: List[str] = []

    for arg in fn.args.args:
        if arg.arg in {"self", "cls"}:
            continue

        required.append(arg.arg)
        type_name = "string"
        if arg.annotation:
            try:
                type_name = ast.unparse(arg.annotation)
            except Exception:
                type_name = "unknown"

        props[arg.arg] = {"type": str(type_name)}

    return {
        "type": "object",
        "properties": props,
        "required": required,
    }


def _extract_code_snippet(source: str, node: ast.AST, max_lines: int = 60) -> str:
    lines = source.splitlines()
    start = max(getattr(node, "lineno", 1) - 1, 0)
    end = min(getattr(node, "end_lineno", start + max_lines), start + max_lines, len(lines))
    return "\n".join(lines[start:end])


def _guess_server_name(path: Path) -> str:
    parts = [p.lower() for p in path.parts]
    for candidate in ["payments", "payment", "crm", "slack", "github", "gmail", "email", "database", "db", "files", "storage"]:
        if candidate in parts or any(candidate in p for p in parts):
            return f"{candidate}-mcp"
    return "mcp-server"


def extract_python_tools(path: Path, repo_root: Path, repo_name: str) -> List[ToolRecord]:
    source = _safe_read(path)
    if not source.strip():
        return []

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    tools: List[ToolRecord] = []
    rel = str(path.relative_to(repo_root))

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        matching_decorators = [dec for dec in node.decorator_list if _is_mcp_tool_decorator(dec)]
        if not matching_decorators:
            continue

        dec = matching_decorators[0]
        args = _decorator_args(dec)
        kwargs = _decorator_kwargs(dec)

        tool_name = kwargs.get("name") or (args[0] if args and isinstance(args[0], str) else node.name)
        description = kwargs.get("description") or ast.get_docstring(node) or ""

        annotations = kwargs.get("annotations") or kwargs.get("metadata") or {}
        if not isinstance(annotations, dict):
            annotations = {}

        declared_permission = (
            annotations.get("permission")
            or annotations.get("required_permission")
            or annotations.get("scope")
            or kwargs.get("permission")
            or kwargs.get("required_permission")
            or kwargs.get("scope")
        )

        declared_action = annotations.get("action") or kwargs.get("action")
        declared_resource = annotations.get("resource") or kwargs.get("resource")
        declared_risk = annotations.get("risk") or kwargs.get("risk")

        tools.append(
            ToolRecord(
                repo_name=repo_name,
                file_path=rel,
                language="python",
                server_name=_guess_server_name(path),
                tool_name=str(tool_name),
                description=str(description),
                input_schema=_extract_schema_from_function(node),
                declared_permission=str(declared_permission) if declared_permission else None,
                declared_action=str(declared_action) if declared_action else None,
                declared_resource=str(declared_resource) if declared_resource else None,
                declared_risk=str(declared_risk).lower() if declared_risk else None,
                code_snippet=_extract_code_snippet(source, node),
                evidence=[f"decorator:{_decorator_name(dec)}"],
            )
        )

    return tools


def _extract_balanced_call(text: str, start_idx: int) -> str:
    depth = 0
    in_str: Optional[str] = None
    escape = False
    out = []

    for ch in text[start_idx:]:
        out.append(ch)

        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == in_str:
                in_str = None
            continue

        if ch in {"'", '"', "`"}:
            in_str = ch
            continue

        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                break

    return "".join(out)


def extract_js_ts_tools(path: Path, repo_root: Path, repo_name: str) -> List[ToolRecord]:
    source = _safe_read(path)
    if not source.strip():
        return []

    tools: List[ToolRecord] = []
    rel = str(path.relative_to(repo_root))

    patterns = [r"(?:server|mcp|app)\.tool\s*\(", r"registerTool\s*\("]

    for pattern in patterns:
        for match in re.finditer(pattern, source):
            call_start = source.find("(", match.start())
            call_text = _extract_balanced_call(source, call_start)

            name_match = re.search(r"\(\s*[\"'`]([^\"'`]+)[\"'`]", call_text)
            obj_name_match = re.search(r"\bname\s*:\s*[\"'`]([^\"'`]+)[\"'`]", call_text)

            tool_name = name_match.group(1) if name_match else obj_name_match.group(1) if obj_name_match else None
            if not tool_name:
                continue

            desc_match = re.search(r"\bdescription\s*:\s*[\"'`]([^\"'`]+)[\"'`]", call_text)
            description = desc_match.group(1) if desc_match else ""

            permission_match = re.search(
                r"\b(?:permission|requiredPermission|required_permission|scope)\s*:\s*[\"'`]([^\"'`]+)[\"'`]",
                call_text,
            )
            risk_match = re.search(r"\brisk\s*:\s*[\"'`]([^\"'`]+)[\"'`]", call_text)
            action_match = re.search(r"\baction\s*:\s*[\"'`]([^\"'`]+)[\"'`]", call_text)
            resource_match = re.search(r"\bresource\s*:\s*[\"'`]([^\"'`]+)[\"'`]", call_text)

            input_schema = {}
            for field_match in re.finditer(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*z\.(string|number|boolean|array|object)\s*\(", call_text):
                input_schema.setdefault("properties", {})[field_match.group(1)] = {"type": field_match.group(2)}
            if input_schema:
                input_schema["type"] = "object"

            tools.append(
                ToolRecord(
                    repo_name=repo_name,
                    file_path=rel,
                    language=path.suffix.lstrip("."),
                    server_name=_guess_server_name(path),
                    tool_name=tool_name,
                    description=description,
                    input_schema=input_schema,
                    declared_permission=permission_match.group(1) if permission_match else None,
                    declared_action=action_match.group(1) if action_match else None,
                    declared_resource=resource_match.group(1) if resource_match else None,
                    declared_risk=risk_match.group(1).lower() if risk_match else None,
                    code_snippet=call_text[:2500],
                    evidence=["pattern:server.tool/registerTool"],
                )
            )

    return tools


def _extract_tool_items_from_obj(obj: Any) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []

    if isinstance(obj, dict):
        if "tools" in obj and isinstance(obj["tools"], list):
            for item in obj["tools"]:
                if isinstance(item, dict):
                    items.append(item)

        for value in obj.values():
            items.extend(_extract_tool_items_from_obj(value))

    elif isinstance(obj, list):
        for value in obj:
            items.extend(_extract_tool_items_from_obj(value))

    return items


def extract_config_tools(path: Path, repo_root: Path, repo_name: str) -> List[ToolRecord]:
    source = _safe_read(path)
    if not source.strip():
        return []

    rel = str(path.relative_to(repo_root))
    data: Any = None

    try:
        if path.suffix.lower() == ".json":
            data = json.loads(source)
        else:
            data = yaml.safe_load(source)
    except Exception:
        return []

    if data is None:
        return []

    items = _extract_tool_items_from_obj(data)
    tools: List[ToolRecord] = []

    for item in items:
        name = item.get("name") or item.get("tool") or item.get("id")
        if not name:
            continue

        permission = item.get("permission") or item.get("required_permission") or item.get("scope")
        description = item.get("description") or item.get("desc") or ""

        tools.append(
            ToolRecord(
                repo_name=repo_name,
                file_path=rel,
                language=path.suffix.lstrip("."),
                server_name=item.get("server") or item.get("mcp_server") or _guess_server_name(path),
                tool_name=str(name),
                description=str(description),
                input_schema=item.get("input_schema") or item.get("inputSchema") or {},
                declared_permission=str(permission) if permission else None,
                declared_action=str(item.get("action")) if item.get("action") else None,
                declared_resource=str(item.get("resource")) if item.get("resource") else None,
                declared_risk=str(item.get("risk")).lower() if item.get("risk") else None,
                code_snippet=json.dumps(item, indent=2, default=str)[:2500],
                evidence=["config:tools[]"],
            )
        )

    return tools


def extract_tools_from_file(path: Path, repo_root: Path, repo_name: str) -> List[ToolRecord]:
    suffix = path.suffix.lower()

    if suffix == ".py":
        return extract_python_tools(path, repo_root, repo_name)

    if suffix in {".ts", ".tsx", ".js", ".jsx"}:
        return extract_js_ts_tools(path, repo_root, repo_name)

    if suffix in {".json", ".yaml", ".yml"}:
        return extract_config_tools(path, repo_root, repo_name)

    return []
