# Ainator

Ainator is a CLI/API framework for AI agents built on the [agno](https://github.com/agno/agno) framework. It provides interactive chat, persistent sessions, knowledge bases (RAG), and built-in tools for shell execution, file operations, and web search.

## Features

- **Interactive Chat**: Persistent sessions with compression and summarization
- **Knowledge Bases (RAG)**: Embed code repositories (AST-aware chunking), websites, and directories
- **Built-in Tools**: Shell execution (with safety controls), file operations, DuckDuckGo search
- **Session Management**: List, switch, show, and compress sessions
- **Learning & Memory**: User profile, memory, and session context
- **Cultural Knowledge**: Context-aware cultural knowledge integration
- **KeyboardInterrupt Handling**: Proper handling of interruption signals
- **Skills System**: Extensible via `.ainator/skills/` directory
- **Web Server**: FastAPI server with Swagger documentation
- **Model Support**: VLLM, DeepSeek, OpenAI, Anthropic...

## Installation

```bash
pip install ainator
```

## Quick Start

```bash
# Run a one-off prompt (creates new session)
ainator hi "What is the capital of France?"

# Continue in existing session
ainator but "Tell me more about that"

# Or start interactive chat
ainator chat

# Or Start the web server (localhost:7777/docs)
ainator server
# Then consume it through https://github.com/agno-agi/agent-ui
```

## Commands

### Chat & Prompt
- `ainator hi "your prompt"` - One-off prompt execution (creates new session)
- `ainator but "your prompt"` - Continue in existing session
- `ainator chat` - Interactive chat session

### Test-Driven Development & Fixing
- `ainator fix "python my_script.py or any command or pytest"` - Run until rc == 0

### Session Management
- `ainator sessions` - List all sessions
- `ainator switch <id>` - Switch to a session
- `ainator show` - Show messages in current session

### Skills Management
- `ainator skills` - List available skills

### RAG Management
- `ainator rag code add ./path/to/repo python` - Add code repository
- `ainator rag website add <url>` - Add website content
- `ainator rag search <knowledge-name> "query"` - Search knowledge base
- `ainator rag remove <knowledge-name>` - Remove knowledge base
- `ainator rag` - Show RAG status

### Server
- `ainator server` - Start FastAPI web server (port 7777)

## Configuration

Configuration file is auto-managed, but you can still hack it if you want to
tweak parameters: `.ainator/config.yml`

### Example Configuration
```yaml
agent:
    add_culture_to_context: true
    add_history_to_context: true
    compress_tool_results: true
    enable_session_summaries: true
    reasoning: true
    reasoning_max_steps: 5
    reasoning_min_steps: 2
    store_events: true
    update_cultural_knowledge: true
    update_memory_on_run: true
compression_manager: agno.compression.manager:CompressionManager compress_token_limit=60000 compress_tool_results=True
compression_model: agno.models.vllm:VLLM id=coder
db: ainator.db.sqlite:AsyncSqliteDb db_file=/home/jpic/src/ainator/.ainator/agno.db
extra_skills: []
knowledge:
    agno:
        path: /home/jpic/src/agno/libs/agno/agno
        plugin: code
learning_machine: agno.learn:LearningMachine user_profile=False user_memory=False session_context=True entity_memory=False learned_knowledge=True
model: agno.models.vllm:VLLM id=coder
session_id: bf51cd29-c374-4074-b0eb-faa54f2a6e70
session_name: Fixing Configuration Tests with Temporary Directories
tools:
- agno.tools.file:FileTools base_dir=/home/jpic/src/ainator
- agno.tools.shell:ShellTools
- agno.tools.duckduckgo:DuckDuckGoTools
```

### Model Configuration Examples
```yaml
# VLLM
model: agno.models.vllm:VLLM id=coder

# DeepSeek
model: agno.models.deepseek:DeepSeek id=deepseek-chat
```

### Environment Variables
- `AINATOR_MODEL` - Override the model configuration

## Architecture

### Core Framework
- **agno**: Core AI agent framework (agents, models, tools, SQLite database)
- **cli2**: Command-line interface framework

### Knowledge Plugins
- **code**: Repository embedding with AST-aware chunking
  - Uses llama-index CodeSplitter and HierarchicalNodeParser
  - BAAI/bge-small-en-v1.5 embeddings
  - LanceDB vector storage
- **site**: Website scraping with Parsel
- **generic**: Directory embedding **descriptive file names is required**

### Skills System
Extensible via `.ainator/skills/` directory, just create a skill in there or
clone a skills repo such as:

```py
git clone https://github.com/anthropics/skills .ainator/skills/anthropics
```

### Renderer
Streaming Markdown output

### Server
FastAPI server via AgentOS, consumable with
[AgentUI](https://github.com/agno-agi/agent-ui) or the AgentOS client, or plain
HTTP even.

### Tools
- Enhanced shell execution with chunked output
- File operations
- DuckDuckGo search
- Custom knowledge tools (RAGs)

### Compression
Automatic

### Learning
- User profile management
- Memory system
- Session context tracking

## Development

### Installation for Development
```bash
pip install -e '.'
```

### Testing
```bash
pytest tests/
```

### Version
Version 0.0.3 (defined in `src/ainator/__about__.py`)

## License

MIT © 2026-present jpic

## Links

- [PyPI](https://pypi.org/project/ainator/)
- [Source Code](https://yourlabs.io/oss/ainator)
- [Issues](https://yourlabs.io/oss/ainator/issues)
- [Agno Framework](https://github.com/agno-agi/agno)
- [cli2](https://yourlabs.io/oss/cli2)
