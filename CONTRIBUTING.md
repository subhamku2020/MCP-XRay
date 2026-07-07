# Contributing to MCP-XRay

Thank you for your interest in contributing to MCP-XRay! 🚀

MCP-XRay aims to become a comprehensive permission discovery and auditing framework for AI agents and Model Context Protocol (MCP) servers.

Whether you're fixing bugs, improving documentation, or adding support for new frameworks, every contribution is appreciated.

---

## Ways to Contribute

There are many ways to contribute:

- 🐛 Report bugs
- 💡 Suggest new features
- 📚 Improve documentation
- 🔍 Add support for new MCP frameworks
- ⚙️ Implement new extractors
- 🛡️ Improve permission inference
- 🧪 Add test cases
- 📊 Improve visualizations
- 🚀 Improve performance

---

## Getting Started

Clone the repository.

```bash
git clone https://github.com/subhamku2020/MCP-XRay.git
cd MCP-XRay
```

Create a virtual environment.

```bash
python -m venv .venv
```

Activate it.

**Linux / macOS**

```bash
source .venv/bin/activate
```

**Windows**

```powershell
.venv\Scripts\activate
```

Install dependencies.

```bash
pip install -r requirements.txt
```

Run the application.

```bash
streamlit run app.py
```

---

## Areas Where We Need Help

Some high-impact contribution areas include:

### New Extractors

Support additional frameworks and tool registration patterns.

Examples:

- LangGraph
- PydanticAI
- OpenAI Agents SDK
- CrewAI
- AutoGen
- Semantic Kernel
- LlamaIndex
- Custom MCP implementations

---

### Permission Sources

Improve extraction from:

- Tool metadata
- Configuration files
- Agent manifests
- Client tool calls
- Prompt definitions
- Resource definitions
- Runtime discovery

---

### Permission Inference

Improve detection of:

- Actions
- Resources
- Risk levels
- Missing permissions
- Dangerous operations

---

### Reporting

Help add support for:

- HTML reports
- Markdown reports
- CSV export
- SARIF export

---

### Testing

Help create sample repositories and test cases covering different MCP implementations.

---

## Pull Requests

Please keep pull requests focused on a single feature or bug.

Before submitting:

- Ensure the project runs successfully.
- Update documentation if needed.
- Include sample inputs when adding a new extractor.
- Add tests whenever possible.
---

Thank you for helping improve MCP-XRay!
