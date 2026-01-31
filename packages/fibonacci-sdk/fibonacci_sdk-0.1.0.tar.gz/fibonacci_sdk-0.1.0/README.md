# Fibonacci SDK

<p align="center">
  <strong>Build and deploy AI-powered workflows programmatically</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/fibonacci-sdk/"><img src="https://img.shields.io/pypi/v/fibonacci-sdk.svg" alt="PyPI version"></a>
  <a href="https://pypi.org/project/fibonacci-sdk/"><img src="https://img.shields.io/pypi/pyversions/fibonacci-sdk.svg" alt="Python versions"></a>
  <a href="https://github.com/RohanBanerjee88/fibonacci-sdk/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-Proprietary-blue.svg" alt="License"></a>
</p>

<p align="center">
  <a href="https://docs.fibonacci.today">Documentation</a> •
  <a href="#installation">Installation</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#features">Features</a> •
  <a href="https://github.com/fibonacci-ai/fibonacci-sdk/issues">Issues</a>
</p>

---

## What is Fibonacci?

Fibonacci is a platform for building autonomous AI agents and workflows. The SDK allows developers to:

- 🤖 **Build AI Workflows** - Chain LLM calls, tools, and logic programmatically
- 🚀 **Deploy Instantly** - One command to deploy to production
- 🔧 **40+ Integrations** - Connect to Slack, Google Sheets, GitHub, and more
- 📊 **Monitor & Optimize** - Track costs, performance, and optimize automatically

---

## Installation

```bash
pip install fibonacci-sdk
```

### With Security Features (Recommended)

```bash
pip install fibonacci-sdk[security]
```

This includes secure keychain storage for API keys.

---

## Quick Start

### 1. Get Your API Key

Sign up at [fibonacci.today](https://fibonacci.today) to get your API key.

### 2. Set Up Authentication

```bash
# Option 1: Environment variable
export FIBONACCI_API_KEY="fib_live_your_api_key"

# Option 2: Secure keychain storage (recommended)
fibonacci security save
# Then enter your API key when prompted
```

### 3. Create Your First Workflow

```python
from fibonacci import Workflow, LLMNode, ToolNode

# Create a workflow
wf = Workflow(
    name="Customer Support Bot",
    description="AI-powered customer support assistant"
)

# Add an LLM node
respond = LLMNode(
    id="respond",
    name="Generate Response",
    instruction="""
    You are a helpful customer support assistant.
    
    Customer message: {{input.message}}
    
    Provide a friendly, helpful response.
    """
)

wf.add_node(respond)

# Deploy to Fibonacci platform
workflow_id = wf.deploy()
print(f"Deployed! Workflow ID: {workflow_id}")

# Execute the workflow
result = wf.run(input_data={"message": "How do I reset my password?"})
print(result.output_data)
```

---

## Features

### 🔗 Node Types

| Node | Description | Example Use Case |
|------|-------------|------------------|
| **LLMNode** | Call Claude AI models | Text generation, analysis, summarization |
| **ToolNode** | Execute platform tools | Read Google Sheets, send Slack messages |
| **CriticNode** | Evaluate outputs | Quality scoring, validation |
| **ConditionalNode** | Branch logic | Route based on sentiment, conditions |

### 📦 Example: Multi-Step Workflow

```python
from fibonacci import Workflow, LLMNode, ToolNode, ConditionalNode

wf = Workflow(name="Sales Report Pipeline")

# Step 1: Read data from Google Sheets
read_data = ToolNode(
    id="read_data",
    name="Read Sales Data",
    tool="google_sheets_read",
    params={"spreadsheet_id": "{{input.sheet_id}}"}
)

# Step 2: Analyze with AI
analyze = LLMNode(
    id="analyze",
    name="Analyze Sales",
    instruction="Analyze this sales data and identify trends: {{read_data}}",
    dependencies=["read_data"]
)

# Step 3: Check if urgent
check_urgent = ConditionalNode(
    id="check_urgent",
    name="Check Urgency",
    left_value="{{analyze}}",
    operator="contains",
    right_value="urgent",
    true_branch=["send_alert"],
    false_branch=["send_report"],
    dependencies=["analyze"]
)

# Step 4a: Send alert if urgent
send_alert = ToolNode(
    id="send_alert",
    name="Send Urgent Alert",
    tool="slack_send_message",
    params={
        "channel": "#sales-alerts",
        "message": "🚨 URGENT: {{analyze}}"
    },
    dependencies=["check_urgent"]
)

# Step 4b: Send regular report
send_report = ToolNode(
    id="send_report",
    name="Send Report",
    tool="slack_send_message",
    params={
        "channel": "#sales-reports",
        "message": "📊 Daily Report: {{analyze}}"
    },
    dependencies=["check_urgent"]
)

wf.add_nodes([read_data, analyze, check_urgent, send_alert, send_report])

# Deploy and run
wf.deploy()
result = wf.run(input_data={"sheet_id": "abc123"})
```

### 💾 Memory & State

Persist data across workflow runs:

```python
from fibonacci import Memory

# Store data
memory = Memory(scope="workflow", workflow_id="your-workflow-id")
memory.set("user_preferences", {"theme": "dark", "language": "en"})

# Retrieve later
prefs = memory.get("user_preferences")
print(prefs)  # {"theme": "dark", "language": "en"}
```

### 📄 YAML Support

Define workflows in YAML:

```yaml
# workflow.yaml
name: Email Summarizer
description: Summarize incoming emails

nodes:
  - id: summarize
    type: llm
    name: Summarize Email
    instruction: "Summarize this email: {{input.email_body}}"
    config:
      model: claude-haiku-4-5
      max_tokens: 500
```

```python
from fibonacci import Workflow

# Load from YAML
wf = Workflow.from_yaml("workflow.yaml")
wf.deploy()

# Export to YAML
wf.to_yaml("exported.yaml")
```

---

## CLI Commands

```bash
# Initialize a new workflow project
fibonacci init "My Workflow"

# List your workflows
fibonacci list

# Execute a workflow
fibonacci run <workflow-id> '{"message": "hello"}'

# Check run status
fibonacci status <run-id>

# Security commands
fibonacci security status    # Check API key security
fibonacci security save      # Save API key to secure keychain
fibonacci security migrate   # Migrate from .env to keychain

# Audit logs
fibonacci audit view         # View recent audit events
```

---

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FIBONACCI_API_KEY` | Your API key | Required |
| `FIBONACCI_BASE_URL` | API base URL | `http://api.fibonacci.today` |
| `FIBONACCI_TIMEOUT` | Request timeout (seconds) | `300` |
| `FIBONACCI_DEBUG` | Enable debug logging | `false` |

### Configuration File

Create `~/.fibonacci/config.yaml`:

```yaml
api_key: fib_live_your_key
base_url: http://api.fibonacci.today
timeout: 300
debug: false
```

### Secure Storage (Recommended)

Store your API key in the system keychain:

```bash
fibonacci security save
```

This uses:
- **macOS**: Keychain
- **Windows**: Credential Manager
- **Linux**: Secret Service

---

## Tool Discovery

Find available tools programmatically:

```python
from fibonacci import list_tools, get_tool_schema, search_tools

# List all tools
tools = list_tools()
for tool in tools:
    print(f"{tool['name']}: {tool['description']}")

# Get detailed schema
schema = get_tool_schema("google_sheets_read")
print(schema)

# Search for tools
results = search_tools("slack")
print(results)
```

---

## Error Handling

```python
from fibonacci import (
    Workflow,
    FibonacciError,
    AuthenticationError,
    ValidationError,
    ExecutionError
)

try:
    wf = Workflow(name="My Workflow")
    wf.deploy()
except AuthenticationError:
    print("Invalid API key")
except ValidationError as e:
    print(f"Workflow validation failed: {e.errors}")
except ExecutionError as e:
    print(f"Execution failed: {e.message}")
except FibonacciError as e:
    print(f"General error: {e.message}")
```

---

## Requirements

- Python 3.11 or higher
- Valid Fibonacci API key

### Dependencies

- `httpx` - HTTP client
- `pydantic` - Data validation
- `typer` - CLI framework
- `rich` - Terminal formatting
- `pyyaml` - YAML support
- `keyring` (optional) - Secure credential storage

---

## Documentation

- 📖 **Full Documentation**: [docs.fibonacci.today](https://docs.fibonacci.today)
- 🔧 **API Reference**: [docs.fibonacci.today/api](https://docs.fibonacci.today/api)

---

## License

This SDK is proprietary software. See [LICENSE](LICENSE) for terms.

**TL;DR**: You can use this SDK with a valid Fibonacci API key. You cannot modify, redistribute, or create competing products.

---

## Contributing

We welcome bug reports and feature suggestions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

<p align="center">
  <strong>Built with ❤️ by Fibonacci, Inc.</strong>
</p>

<p align="center">
  <a href="https://fibonacci.today">Website</a> •
  <a href="https://docs.fibonacci.today">Docs</a> •
</p>