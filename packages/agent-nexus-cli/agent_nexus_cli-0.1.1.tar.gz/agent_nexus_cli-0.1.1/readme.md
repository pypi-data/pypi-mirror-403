# Nexus - AI Coding Agent

**Nexus is a modern, CLI-based AI coding agent that transforms natural language into efficient, production-ready code.**

Powered by **LangChain**, **LangGraph**, and **LangSmith**, Nexus provides a persistent, stateful coding assistant with advanced capabilities like human-in-the-loop approvals, full observability, and the **Model Context Protocol (MCP)** for extensible tooling.

<div align="center">
  <h3>⚡ Project Showcase ⚡</h3>
  <img src="https://raw.githubusercontent.com/DataRohit/Nexus/master/assets/images/Screenshot%202026-01-24%20210940.png" width="100%" alt="Nexus Hero">
  <br><br>
  <table>
    <tr>
      <td align="center"><img src="https://raw.githubusercontent.com/DataRohit/Nexus/master/assets/images/Screenshot%202026-01-24%20211722.png" width="400" alt="Showcase 2"></td>
      <td align="center"><img src="https://raw.githubusercontent.com/DataRohit/Nexus/master/assets/images/Screenshot%202026-01-24%20211827.png" width="400" alt="Showcase 3"></td>
    </tr>
    <tr>
      <td align="center"><img src="https://raw.githubusercontent.com/DataRohit/Nexus/master/assets/images/Screenshot%202026-01-24%20211835.png" width="400" alt="Showcase 4"></td>
      <td align="center"><img src="https://raw.githubusercontent.com/DataRohit/Nexus/master/assets/images/Screenshot%202026-01-24%20211901.png" width="400" alt="Showcase 5"></td>
    </tr>
     <tr>
      <td align="center"><img src="https://raw.githubusercontent.com/DataRohit/Nexus/master/assets/images/Screenshot%202026-01-24%20211912.png" width="400" alt="Showcase 6"></td>
      <td align="center"><img src="https://raw.githubusercontent.com/DataRohit/Nexus/master/assets/images/Screenshot%202026-01-24%20211923.png" width="400" alt="Showcase 7"></td>
    </tr>
  </table>
</div>

## ✨ Features

- 🔄 **Stateful Conversations** - Persistent conversation history with SQLite checkpointing.
- 🔌 **Model Context Protocol (MCP)** - Connect external tools using the open standard MCP.
- 🛠️ **Powerful Built-in Tools** - File operations, shell commands, and code analysis.
- 👤 **Human-in-the-Loop** - Secure approval workflows (`y/n/d`) for tool execution.
- 🛡️ **Operational Modes** - Security-focused CODE, ARCHITECT, and ASK modes.
- 📉 **Intelligent Guidance** - Context-aware mode switch suggestions and agent-initiated transitions.

- 🚀 **Production-Ready** - Built with modern best practices, type safety, and structured logging.

## 🏗️ Architecture

Nexus is built on a robust stack:

- **LangChain** - Orchestration and tool integration.
- **LangGraph** - State machine for reliable agent workflows.
- **LangSmith** - Observability, tracing, and evaluation.
- **MCP (Model Context Protocol)** - Standardized connection to external data and tools.
- **Rich-Click** - Modern, beautiful CLI interface.
- **Pydantic** - Strict configuration and validation.
- **SQLite** - Local persistence for conversation threads.

## 📋 Prerequisites

- Python 3.10+
- OpenAI API key
- (Optional) LangSmith API key for tracing
- (Optional) Docker/Node.js for specific MCP servers

## 🚀 Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/datarohit/nexus.git
   cd nexus
   ```

2. **Create and activate virtual environment:**

   ```bash
   # Using uv (recommended)
   uv venv
   source .venv/Scripts/activate  # Windows (Git Bash)
   
   # Or using standard venv
   python -m venv .venv
   source .venv/Scripts/activate
   ```

3. **Install dependencies:**

   ```bash
   # Using uv (fastest)
   uv pip install -e .
   
   # Or using pip
   pip install -e .
   ```

4. **Configure environment:**

   Copy the example environment file:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` with your keys:

   ```env
   OPENAI_API_KEY=sk-...
   LANGSMITH_API_KEY=ls__...  # Optional
   LANGSMITH_PROJECT=nexus
   LANGSMITH_TRACING=true
   ```

## 🔌 Model Context Protocol (MCP)

Nexus supports the Model Context Protocol, allowing you to easily extend its capabilities with external servers.

### Configuration

Create or edit `.nexus/mcp_config.json` in your project root to define servers.

**Example Configuration:**

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "C:/Projects"]
    }
  }
}
```

Nexus automatically loads these servers, counts their tools, and injects their descriptions into the agent's system prompt so it knows exactly how to use them.

## 🎭 Multi-Mode System

Nexus supports three operational modes to provide structure and safety during complex tasks:

| Mode | Allowed Tools | File Access | Description |
| :--- | :--- | :--- | :--- |
| **CODE** | All tools | Unrestricted | Full access for implementation and debugging. |
| **ARCHITECT** | All tools | `.nexus/plans/` | Restricted mode for project planning and design. |
| **ASK** | MCP Tools | None | Conversation-only mode for questions and research. |

Nexus defaults to **CODE** mode. When a restricted action is attempted, Nexus will intelligently suggest a mode switch. The agent can also programmatically request a mode change via the `switch_mode` tool when it recognizes a shift in task requirements.

## 💻 Usage

### Interactive Chat

Start the agent in interactive mode:

```bash
nexus chat
```

You will see a dashboard showing the active session, loaded prompts, rules, and connected MCP servers.

**Slash Commands:**
While in chat mode, you can use the following slash commands:

- `/help` - Show all available commands.
- `/mode <name>` - Switch between `code`, `architect`, and `ask`.
- `/config` - View configuration and the active operational mode.

- `/mcps` - List active MCP servers and their tools.
- `/about` - Show application information.

### Command Line Mode

Send a single instruction without entering interactive mode:

```bash
nexus chat "Refactor main.py to use async/await"
```

### Thread Management

Maintain context across sessions using thread IDs:

```bash
nexus chat --thread-id feature-auth "Add login endpoint"
nexus chat --thread-id feature-auth "Now add logout"
```

### View History

Review past conversations:

```bash
nexus history --thread-id feature-auth
```

### Configuration Check

Verify your settings and loaded components:

```bash
nexus config
```

## 🏗️ Project Structure

```text
nexus/
├── nexus/
│   ├── agent/          # Core agent logic
│   │   ├── graph.py    # LangGraph definition & tool loading
│   │   ├── nodes.py    # Agent reasoning & approval nodes
│   │   ├── state.py    # State schema
│   │   ├── modes.py    # Mode definitions & configs
│   │   ├── restrictions.py # Tool restriction logic
│   │   └── approval.py # Interactive approval workflow
│   │
│   ├── tools/          # Tool definitions
│   │   ├── mcp.py      # MCP client & configuration handler
│   │   ├── file_ops.py # Built-in file tools
│   │   ├── shell.py    # Built-in shell tools
│   │   └── mode.py     # Mode management tools

│   │
│   ├── config/         # Configuration
│   │   ├── settings.py # Pydantic settings
│   │   └── prompts.py  # System prompts
│   │
│   ├── ui/             # Terminal Interface
│   │   ├── cli.py      # CLI entry point & UI components
│   │   └── console.py  # Rich console instance
│   │
│   └── main.py         # App entry point
│
├── .nexus/             # Local config directory
│   ├── mcp_config.json # MCP server definitions
│   └── prompts/        # Custom user prompts
│
└── readme.md           # Documentation
```

## ⚙️ Configuration Variables

| Variable | Description | Default |
| :--- | :--- | :--- |
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `OPENAI_BASE_URL` | OpenAI base URL | None |
| `LANGSMITH_TRACING` | Enable tracing | true |
| `LOG_LEVEL` | Logging verbosity | INFO |
| `CHECKPOINT_DB` | SQLite DB path | checkpoints.db |

## 🤝 Contributing

Contributions are welcome! Please follow the code style guidelines:

1. Use **Ruff** for linting.
2. Use **MyPy/Ty** for type checking.
3. Ensure all functions have docstrings.

```bash
ruff check .
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **LangChain & LangGraph** for the agent framework.
- **Anthropic & MCP Team** for the Model Context Protocol standard.
- **Rich** for the terminal UI.

---

### Made with ❤️ by Rohit Vilas Ingole
