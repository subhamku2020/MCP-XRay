# MCP-XRay
Scan Agentic tools for permissions

MCP-XRay is a local-first audit tool that scans a GitHub repository or local folder, detects MCP-style tool definitions, extracts or infers tool permissions, and renders a visual graph:

```text
Repository → File → MCP Server → Tool → Permission → Resource → Risk
```

## Features

- Scan local folders or GitHub repos
- Detect MCP tools in Python, TypeScript, JavaScript, JSON, YAML
- Extract declared permission metadata if present
- Infer missing permissions from tool names, descriptions, and code behavior
- Render an interactive graph using Streamlit + PyVis
- Export graph JSON
- Save scan snapshots
- Compare two snapshots for permission drift

## Install

```bash
python -m venv mcp
source mcp/bin/activate      # macOS/Linux
# .venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

## Try demo

In the Streamlit UI, choose:

```text
Scan mode: Local folder
Local folder path: samples/demo_repo
```

Then click **Scan**.

## GitHub repo scan

Use a public GitHub URL:

```text
https://github.com/org/repo
```

Private repos will work only if your local `git` is already authenticated.

## What it detects

### Python

```python
@mcp.tool()
def create_refund(customer_id: str, amount: float):
    """Create refund for customer."""
    ...
```

### TypeScript / JavaScript

```ts
server.tool("create_refund", schema, async (args) => {
  ...
})
```

### YAML / JSON

```yaml
tools:
  - name: create_refund
    description: Create refund
    permission: payments.refund.create
    risk: high
```

## Permission source types

- `declared`: permission is explicitly present in code/config metadata
- `inferred`: permission is guessed from name/description/code behavior
- `unknown`: scanner could not infer confidently

