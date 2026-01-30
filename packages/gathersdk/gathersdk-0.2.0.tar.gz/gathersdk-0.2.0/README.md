# Gather SDK

Connect [Google ADK](https://github.com/google/adk-python) agents to [Gather.is](https://app.gather.is) workspaces.

> **Gather.is is the testing layer for AI agents.** Get your agents live, chatting with your team, as quickly as possible.

## Installation

```bash
pip install gathersdk google-adk
```

## Quick Start

### 1. Get Your Config

1. Sign up at [app.gather.is](https://app.gather.is)
2. Create a workspace
3. Click workspace dropdown → **SDK Settings**
4. Download `gather.config.json`
5. Place it in your agents folder

### 2. Create an Agent

```
my-agents/
├── gather.config.json    # Downloaded from Gather.is
└── hello_agent/
    ├── __init__.py       # from .agent import root_agent
    └── agent.py          # Define your agent here
```

**hello_agent/__init__.py:**

```python
from .agent import root_agent
```

**hello_agent/agent.py:**

```python
from google.adk import Agent

root_agent = Agent(
    name="hello_agent",
    model="gemini-2.5-flash",
    description="A friendly test agent",
    instruction="""You are a helpful assistant.
Keep responses short and friendly."""
)
```

### 3. Run the Stack (Two Terminals)

**Terminal 1** - ADK Web Server:
```bash
export GOOGLE_API_KEY=your_key_here
adk web --port 8000
```

**Terminal 2** - Gather SDK:
```bash
gathersdk serve
```

### 4. Chat with Your Agent

Go to [app.gather.is](https://app.gather.is), open your workspace, and type:

```
@hello_agent hello!
```

Your agent responds in real-time!

---

## How It Works

```
User → Gather.is → SDK → ADK → Gemini
                              ↓
User ← Gather.is ← SDK ← Response
```

1. User mentions `@hello_agent` in a channel
2. Gather.is sends the message to your running SDK
3. SDK routes it to Google ADK
4. ADK invokes Gemini with your agent's instructions
5. Response flows back through the same path

---

## Commands

```bash
# Start the SDK bridge (default ADK URL: http://localhost:8000)
gathersdk serve

# Custom ADK server URL
gathersdk serve --adk-url http://localhost:8002

# Use custom config/directory
gathersdk serve --config path/to/config.json --dir ./agents

# Discover agents without connecting
gathersdk discover

# Verbose logging
gathersdk -v serve
```

---

## Debugging

Run the ADK debug UI to see what's happening inside your agents:

```bash
adk web
```

Open [localhost:8000](http://localhost:8000) to see:

- All discovered agents
- Session history
- Message events
- Tool calls and responses

---

## Configuration

### gather.config.json

Downloaded from Gather.is SDK Settings:

```json
{
  "workspace_id": "your_workspace_id",
  "pocketnode_url": "https://app.gather.is",
  "auth_token": "your_session_token"
}
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `GOOGLE_API_KEY` | Your Google AI API key (required) |
| `GATHER_CONFIG_PATH` | Path to gather.config.json (default: current directory) |

---

## Agent Structure

Agents must follow Google ADK folder conventions:

```
agents_folder/           # Run gathersdk serve from here
├── gather.config.json   # Your Gather.is config
├── agent_one/           # Each agent is a sibling folder
│   ├── __init__.py      # Must export: root_agent
│   └── agent.py         # Must define: root_agent = Agent(...)
└── agent_two/           # Another agent at same level
    ├── __init__.py
    └── agent.py
```

**Important:** Agents must be siblings (same level), NOT nested inside each other.

---

## Troubleshooting

### "ADK server not reachable"
Start the ADK web server first:
```bash
adk web --port 8000
```

### "Authentication failed"
Your auth token expired. Download a fresh `gather.config.json` from the web UI.

### Agent not responding
1. Check the agent is discovered: `gathersdk discover`
2. Check ADK server logs for errors
3. Verify `GOOGLE_API_KEY` is set
4. Check ADK debug UI at http://localhost:8000

---

## Documentation

Full documentation at **[app.gather.is/docs](https://app.gather.is/docs)**

- [Quickstart](https://app.gather.is/docs/getting-started/quickstart/)
- [Agent Development](https://app.gather.is/docs/guides/agent-development/)
- [SDK Reference](https://app.gather.is/docs/sdk/configuration/)

---

## Links

- Website: [gather.is](https://gather.is)
- App: [app.gather.is](https://app.gather.is)
- Docs: [app.gather.is/docs](https://app.gather.is/docs)
- Google ADK: [github.com/google/adk-python](https://github.com/google/adk-python)
