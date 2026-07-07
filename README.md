# MCP-XRay

> **Understand what your AI agents can actually do.**

MCP-XRay is an open-source, local-first security auditing tool that discovers, extracts, infers, and visualizes permissions used by AI agents and Model Context Protocol (MCP) servers.

Instead of manually inspecting source code, configuration files, or tool definitions, MCP-XRay automatically builds a permission graph, helping developers, security engineers, product owners, and auditors understand an AI application's effective capabilities.

---

## Why MCP-XRay?

As AI agents gain access to files, APIs, databases, cloud services, shell commands, and other sensitive resources, it becomes increasingly difficult to answer simple questions like:

* What permissions does this AI agent have?
* Which tools are exposed?
* What resources can they access?
* Which permissions are explicitly declared versus inferred?
* What is the overall security risk?

MCP-XRay provides a single, human-readable view of an AI application's permissions, making security reviews and governance significantly easier.

---

## Features

* Scan local folders or GitHub repositories
* Detect MCP servers and tool definitions
* Support Python, JavaScript, TypeScript, JSON, and YAML
* Extract explicitly declared permissions
* Infer permissions from tool names, descriptions, and implementation
* Visualize relationships as an interactive permission graph
* Export graph data as JSON
* Save scan snapshots
* Compare snapshots to detect permission drift
* Designed to support multiple MCP clients and permission sources

---

## Permission Graph

MCP-XRay visualizes permissions using the following hierarchy:

```text
Repository
    └── File
          └── MCP Server
                 └── Tool
                        └── Permission
                               └── Resource
                                      └── Risk
```

---

## Supported Discovery Sources

MCP-XRay discovers tools, permissions, and related metadata from multiple implementation patterns across the MCP ecosystem.

| Discovery Source | Status | Description |
|------------------|:------:|-------------|
| Python MCP Decorators | ✅ | Detects tools registered using `@mcp.tool`, `@server.tool`, `@app.tool`, and `@tool` decorators. |
| JavaScript / TypeScript Tool Registration | ✅ | Detects tools registered using `server.tool()`, `mcp.tool()`, `app.tool()`, and `registerTool()`. |
| JSON Tool Definitions | ✅ | Extracts tool definitions, permissions, and metadata from JSON configuration files. |
| YAML Tool Definitions | ✅ | Extracts tool definitions, permissions, and metadata from YAML configuration files. |
| MCP Agent Manifests | ✅ | Discovers external MCP server registrations from agent manifests (`spec.servers`). |
| MCP Client Tool Calls | ✅ | Detects remote MCP tool invocations using `call_tool()` patterns. |
| Plain AI Agent Tools | ✅ | Discovers agent tools implemented as standard Python functions without MCP decorators. |
| Automatic Input Schema Extraction | ✅ | Generates input schemas from Python function signatures and Zod-based TypeScript definitions. |
| Permission Metadata Extraction | ✅ | Extracts declared Permission, Scope, Action, Resource, and Risk metadata when available. |
| Permission Inference | ✅ | Infers permissions from tool names, descriptions, and implementation when explicit metadata is unavailable. |
| Detection Evidence | ✅ | Records how each tool was discovered (decorator, registration pattern, configuration, manifest, or client call). |
| Prompt Definitions | 🚧 | Planned |
| Resource Definitions | 🚧 | Planned |
| Runtime Discovery | 🚧 | Planned |
| Additional MCP Clients | 🚧 | Planned |

> **Note:** New discovery sources are continuously being added as the MCP ecosystem evolves. Contributions are welcome!
---

## Installation

```bash
git clone https://github.com/subhamku2020/MCP-XRay.git
cd MCP-XRay

python -m venv .venv

# macOS/Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate

pip install -r requirements.txt
```

---

## Run

```bash
streamlit run app.py
```

---

## Quick Demo

Open the Streamlit UI and select:

* **Scan Mode:** Local Folder
* **Path:** `samples/demo_repo`

Then click **Scan**.

---

## Scan a GitHub Repository

Provide any public GitHub repository URL.

```text
https://github.com/org/repo
```

Private repositories are supported if Git authentication is already configured locally.

---

## What MCP-XRay Detects

### Python

Detects MCP tools registered using common decorators.

```python
@mcp.tool(...)
@server.tool(...)
@app.tool(...)
@tool(...)
```

**Extracts:** Tool Name • Description • Input Schema • Permission • Action • Resource • Risk

---

### TypeScript / JavaScript

Detects common MCP tool registration patterns.

```typescript
server.tool(...)
mcp.tool(...)
app.tool(...)
registerTool(...)
```

**Extracts:** Tool Name • Description • Zod Schema • Permission • Action • Resource • Risk

---

### YAML / JSON

Parses configuration-based tool definitions.

```yaml
tools:
  - name: create_refund
    permission: payments.refund.create
    risk: high
```

**Extracts:** Tool Metadata • Permission • Action • Resource • Risk • Input Schema

---

### MCP Agent Manifests

Detects external MCP server registrations from agent manifests.

```yaml
spec:
  servers:
    - id: payments
      destination: https://...
```

**Extracts:** Server Name • Server ID • Destination • Enabled Status

---

### MCP Client Tool Calls

Detects remote MCP tool invocations.

```python
self._server("payments").call_tool("create_refund")
```

**Extracts:** Target Server • Tool Name • Source Location

---

### Plain AI Agent Tools

Discovers agent tools implemented as plain Python functions (without MCP decorators).

```python
async def create_refund(...):
    """Create refund"""
```

**Extracts:** Function Name • Parameters • Docstring • Generated Input Schema

---


## Permission Classification

| Type         | Description                                                               |
| ------------ | ------------------------------------------------------------------------- |
| **Declared** | Permission is explicitly defined in code or metadata.                     |
| **Inferred** | Permission is derived from the tool name, description, or implementation. |
| **Unknown**  | The scanner cannot confidently determine the permission.                  |

---

## Roadmap

* Support all major MCP clients
* Discover permissions from every available MCP source
* HTML reports
* SARIF export
* CI/CD integration
* GitHub Action
* VS Code extension
* Risk scoring engine
* Policy-as-Code support
* Enterprise reporting

---

## Contributing

Contributions are welcome!

Whether you're fixing bugs, adding support for new MCP clients, improving permission extractors, or enhancing documentation, we'd love your help.

Please read **CONTRIBUTING.md** before opening a Pull Request.

---

## License

Licensed under the Apache License 2.0.
