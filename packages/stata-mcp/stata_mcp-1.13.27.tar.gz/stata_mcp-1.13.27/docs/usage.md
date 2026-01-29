# Usage Guide

> **Hope no [Star War](https://www.aeaweb.org/articles?id=10.1257/app.20150044) future.** - Let's evolve from reg monkeys to causal thinkers.

This guide covers how to integrate and use Stata-MCP across different environments and agents.

## Prerequisites

Before using Stata-MCP, ensure you have:
- **Stata** 17+ installed with a valid license
- **uv** package manager or Python 3.11+
- **Stata-MCP** installed or available via `uvx`

Verify your setup:
```bash
uvx stata-mcp --usable
```

## Usage in Python

### Using OpenAI Agents SDK

Stata-MCP can be integrated with Python agents using the OpenAI Agents SDK.

#### Method 1: Direct MCP Server Integration

```python
# !uv pip install openai-agents
from agents import Agent, Runner
from agents.mcp import MCPServerStdio, MCPServerStdioParams

# Create MCP server connection
stata_mcp_server = MCPServerStdio(
    name="Stata-MCP",
    params=MCPServerStdioParams(
        command="uvx",
        args=["stata-mcp"]
    )
)

# Initialize agent with MCP server
agent = Agent(
    name="Research Assistant",
    instructions="You are a helpful economics research assistant.",
    mcp_servers=[stata_mcp_server]
)

# Run analysis
result = await Runner.run(
    agent,
    input="Run a regression: log(wage) ~ age, educ, exper with nlsw88 data and report coefficients."
)

print(f"Result: \n> {result.final_output}")
```

#### Method 2: Pre-configured StataAgent

```python
# !uv pip install stata-mcp
from agents import Runner
from stata_mcp.agent_as import StataAgent

# Use pre-configured Stata agent
agent = StataAgent()
result = await Runner.run(
    agent,
    input="Help me run a regression -> log(wage) ~ age, educ, exper with `nlsw88` data and report me the coefficients."
)
print(f"Result: \n> {result.final_output}")
```

### Agent as Tool

Embed Stata-MCP as a tool within larger agent workflows:

```python
# !uv pip install openai-agents stata-mcp
from agents import Agent, Runner
from stata_mcp.agent_as import StataAgent

# Create Stata agent and convert to tool
stata_agent = StataAgent(max_turns=100)
stata_tool = stata_agent.as_tool

# Embed in a larger research workflow
researcher = Agent(
    name="Scientific Researcher",
    instructions="You are a helpful scientist conducting empirical research.",
    tools=[stata_tool]
)

# Run the composed agent
result = await Runner.run(
    researcher,
    input="Analyze the relationship between education and wages using standard datasets."
)
```

## Usage in Coding Agents

Stata-MCP is designed for seamless integration with modern AI coding agents. Below are tested configurations for popular platforms.

### Claude Code (Recommended)

Claude Code is our recommended solution for AI-assisted empirical research.

#### Global Installation

```bash
claude mcp add stata-mcp -- uvx stata-mcp
```

#### Project-based Configuration

For research projects, use project-scoped configuration:

```bash
cd ~/Documents/MyResearchProject
claude mcp add stata-mcp --env STATA_MCP_CWD=$(pwd) --scope project -- uvx --directory $(pwd) stata-mcp
```

#### Specify Version

To use a specific version:

```bash
claude mcp add stata-mcp --env STATA_MCP_CWD=$(pwd) --scope project -- uvx --directory $(pwd) stata-mcp==1.13.0
```

**Verify installation:**
```bash
claude mcp list
```

**Benefits of project-based configuration:**
- Isolates Stata-MCP environment per research project
- Automatic path management within project directory
- No global configuration conflicts

### Codex (VS Code Extension)

For VS Code users with the Codex extension, edit `~/.codex/config.toml`:

```toml
[mcp_servers.stata-mcp]
command = "uvx"
args = ["stata-mcp"]
```

### Cline

For Cline users, edit the MCP configuration file at `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/setting/cline_mcp_settings.json`:

```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": [
        "stata-mcp"
      ]
    }
  }
}
```

### Cursor

**Note:** Cursor has limited file system access. MCP servers may not access `Documents` directory by default. If you encounter issues, try this configuration:

```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": [
        "stata-mcp"
      ],
      "env": {
        "STATA_MCP_CWD": "/path/to/your/project"
      }
    }
  }
}
```

Replace `/path/to/your/project` with your actual research directory.

## Usage in AI Clients

Most AI clients follow the standard MCP server configuration format. Below is the universal configuration pattern:

### Standard Configuration (Claude Desktop, Cherry Studio, etc.)

```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": [
        "stata-mcp"
      ]
    }
  }
}
```

### Configuration with Custom Working Directory

```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": [
        "stata-mcp"
      ],
      "env": {
        "STATA_MCP_CWD": "/path/to/working/directory"
      }
    }
  }
}
```

### Configuration with Environment Variables

```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": [
        "stata-mcp"
      ],
      "env": {
        "STATA_MCP_CWD": "/path/to/working/directory",
        "STATA_MCP_MODEL": "gpt-4",
        "STATA_MCP_API_KEY": "your-api-key",
        "STATA_MCP_API_BASE_URL": "https://api.openai.com/v1"
      }
    }
  }
}
```

## Environment Variables

Stata-MCP supports several environment variables for customization:

| Variable | Description | Default |
|----------|-------------|---------|
| `STATA_MCP_CWD` | Current working directory for Stata operations | `./` |
| `STATA_MCP_MODEL` | LLM model for agent mode | `gpt-3.5-turbo` |
| `STATA_MCP_API_KEY` | API key for LLM provider | `OPENAI_API_KEY` |
| `STATA_MCP_API_BASE_URL` | Base URL for API requests | `https://api.openai.com/v1` |
| `STATA_MCP_CLIENT` | Client type identifier | - |

## Terminal REPL Mode

For interactive sessions, use the built-in REPL agent:

```bash
# Start with current directory
uvx stata-mcp --agent

# Start with custom working directory
uvx stata-mcp --agent ~/Documents/MyResearch
```

**Usage:**
- Type your research questions in natural language
- Agent maintains conversation context
- Type `/exit` or `bye` to quit

## Advanced Usage

### Custom Agent Instructions

Create a custom StataAgent with specific instructions:

```python
from stata_mcp.agent_as import StataAgent

agent = StataAgent(
    instructions="""
    You are a labor economics specialist.
    Focus on causal inference methods like DID, RDD, and IV.
    Always robustness checks and placebo tests.
    """,
    max_turns=50
)
```

### Session Management

REPLAgent supports SQLite-based session persistence:

```python
from stata_mcp.agent_as import REPLAgent

agent = REPLAgent(
    work_dir="~/research",
    session_id="my_experiment_1"  # Optional custom session ID
)
```

Sessions are stored in `<work_dir>/.stata_sessions.db` for conversation history.

## Troubleshooting

### Common Issues

**"Stata not found"**
- Verify Stata installation: `which stata` (macOS/Linux) or check PATH
- Use `StataFinder` configuration guide for custom paths

**"Module not found" errors**
- Ensure dependencies: `uv pip install openai-agents stata-mcp`
- Check Python version: 3.11+ required

**MCP server not connecting**
- Verify `uvx stata-mcp --usable` passes all checks
- Check client's MCP server logs
- Test with stdio transport (default)

### Debug Mode

Enable verbose logging:
```bash
export STATA_MCP_DEBUG=1
uvx stata-mcp --agent
```

## Best Practices

1. **Project Structure**: Use project-scoped MCP configuration for better isolation
2. **Version Pinning**: Specify exact versions in production: `stata-mcp==1.13.0`
3. **Data Management**: Keep raw data immutable; use processing/ directories
4. **Session Cleanup**: Regularly archive or cleanup old SQLite session databases
5. **API Keys**: Use environment variables, never hardcode credentials

## Additional Resources

- [Overview](overview.md) - Architecture and design
- [Tools Documentation](tools.md) - Available MCP tools
- [Agents Guide](agents/index.md) - Agent-specific documentation
- [GitHub Repository](https://github.com/sepinetam/stata-mcp) - Source code and issues

## Contributing

Found a bug or have a feature request? Please [open an issue](https://github.com/sepinetam/stata-mcp/issues/new) or submit a pull request.
