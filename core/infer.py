from __future__ import annotations

import re

from core.models import PermissionRecord, ToolRecord


READ_WORDS = ["get", "read", "search", "list", "lookup", "fetch", "query", "find"]
WRITE_WORDS = ["create", "add", "update", "write", "send", "post", "publish", "insert", "process", "issue"]
DELETE_WORDS = ["delete", "remove", "drop", "destroy", "revoke", "cancel"]
EXEC_WORDS = ["exec", "execute", "shell", "command", "bash", "subprocess", "run_command"]

RESOURCE_HINTS = [
    ("refund", "refund", "payments.refund"),
    ("payment", "payment", "payments.payment"),
    ("invoice", "invoice", "billing.invoice"),
    ("customer", "customer_profile", "crm.customer"),
    ("user", "user", "user"),
    ("email", "email", "email"),
    ("gmail", "email", "gmail.message"),
    ("slack", "slack_message", "slack.message"),
    ("message", "message", "message"),
    ("file", "file", "file"),
    ("s3", "s3_bucket", "s3.object"),
    ("secret", "secret", "secret"),
    ("database", "database", "database"),
    ("db", "database", "database"),
    ("sql", "database", "database"),
    ("order", "order", "commerce.order"),
    ("ticket", "ticket", "support.ticket"),
]


def normalize_action(text: str) -> str:
    text = text.lower()

    if any(word in text for word in DELETE_WORDS):
        return "delete"

    if any(word in text for word in EXEC_WORDS):
        return "execute"

    if re.search(r"\b(post|put|patch)\b", text):
        return "write"

    if re.search(r"\b(delete)\b", text):
        return "delete"

    if re.search(r"\b(select|get)\b", text):
        return "read"

    if any(word in text for word in WRITE_WORDS):
        if "send" in text or "publish" in text or "post" in text:
            return "send"
        if "update" in text:
            return "update"
        return "create"

    if any(word in text for word in READ_WORDS):
        return "read"

    return "unknown"


def infer_resource(text: str) -> tuple[str, str]:
    text = text.lower()

    for hint, resource, namespace in RESOURCE_HINTS:
        if hint in text:
            return resource, namespace

    m = re.search(r"/([a-zA-Z0-9_-]+)", text)
    if m:
        raw = m.group(1).strip("_-")
        if raw:
            singular = raw[:-1] if raw.endswith("s") else raw
            return singular, singular

    return "unknown", "unknown"


def risk_for(action: str, resource: str, text: str) -> str:
    if action in {"delete", "execute"}:
        return "critical"

    if resource in {"secret", "database"} and action != "read":
        return "critical"

    if resource in {"refund", "payment", "s3_bucket", "customer_profile", "email", "user"}:
        if action in {"create", "update", "write", "send"}:
            return "high"
        return "medium"

    if action in {"create", "update", "write", "send"}:
        return "medium"

    if action == "read":
        return "low"

    return "unknown"


def build_permission(namespace: str, resource: str, action: str) -> str:
    if namespace == "unknown" and resource == "unknown":
        return f"unknown.{action}" if action != "unknown" else "unknown"

    if namespace.endswith(f".{resource}"):
        return f"{namespace}.{action}"

    if namespace != "unknown":
        return f"{namespace}.{action}"

    return f"{resource}.{action}"


def infer_permission(tool: ToolRecord) -> PermissionRecord:
    if tool.declared_permission:
        action = tool.declared_action or normalize_action(tool.declared_permission)
        resource = tool.declared_resource or infer_resource(tool.declared_permission)[0]
        risk = tool.declared_risk or risk_for(action, resource, tool.declared_permission)
        return PermissionRecord(
            permission=tool.declared_permission,
            action=action,
            resource=resource,
            risk=risk,
            source="declared",
            reason="Permission metadata was declared in code/config.",
        )

    text = " ".join([
        tool.tool_name or "",
        tool.description or "",
        tool.code_snippet or "",
        " ".join(tool.evidence or []),
    ])

    action = normalize_action(text)
    resource, namespace = infer_resource(text)
    permission = build_permission(namespace, resource, action)
    risk = risk_for(action, resource, text)

    reason = "Inferred from tool name/description/code behavior."
    if permission == "unknown" or action == "unknown":
        reason = "No explicit metadata found and inference was weak."

    return PermissionRecord(
        permission=permission,
        action=action,
        resource=resource,
        risk=risk,
        source="inferred" if permission != "unknown" else "unknown",
        reason=reason,
    )
