# Azure OpenAI Chat Agent System

A stripped-down multi-agent chat system with conversation history that persists across agents. Built using Azure OpenAI, LangChain, and LangGraph.

## Features

- **Master Agent**: Orchestrates and routes requests to specialized agents using LLM-based classification
- **Chat Agent**: Handles general conversation with context awareness
- **Conversation History**: Persistent chat history that spans across agents
- **Security & Rate Limiting**: Input validation and rate limiting to prevent abuse
- **Interactive CLI**: Command-line interface with multiple commands
- **Auto-save**: Automatically saves conversation history on shutdown
- **Verbose Mode**: Optional detailed logging for debugging

## Architecture

```
pcornet/
├── main.py                 # Application entry point
├── modules/
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── conversation_history.py  # Chat history with persistence
│   ├── master_agent.py    # Master agent controller with LLM classification
│   ├── security.py        # Input validation and rate limiting
│   └── agents/
│       ├── __init__.py
│       └── chat_agent.py  # Chat specialist agent
├── data/                  # Conversation history storage
├── tests/                 # Test files
├── requirements.txt       # Python dependencies
├── .env.template         # Environment variables template
└── .gitignore

```

## Setup

### 1. Clone or download this repository

### 2. Create a virtual environment (Python 3.11)

```bash
python3.11 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Or use the helper script:
source activate.sh
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Azure OpenAI

Copy `.env.template` to `.env` and fill in your Azure OpenAI credentials:

```bash
cp .env.template .env
```

Edit `.env` with your values:
```
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o
```

## Usage

### Run in quiet mode (default)
```bash
python main.py
```

### Run with verbose logging
```bash
python main.py -v
# or
python main.py --verbose
```

## Available Commands

During the interactive chat session, you can use these commands:

- **status** - Show system status and agent information
- **history** - Show conversation history statistics and recent messages
- **clear-history** - Clear all conversation history
- **save** - Manually save conversation history to disk
- **help** - Display available commands
- **quit/exit/bye** - Exit the system (auto-saves history)

## How It Works

### Conversation Flow

1. **User Input** → Master Agent receives the message
2. **Validation** → Input is validated and sanitized for security
3. **Rate Limiting** → Request is checked against rate limits
4. **Classification** → Task is classified using LLM (currently routes to "chat")
5. **Routing** → Request is routed to the Chat Agent
6. **Processing** → Chat Agent processes with full conversation history
7. **Response** → Response is returned and added to history
8. **Persistence** → History is auto-saved on shutdown

### Conversation History

- **Rolling Window**: Keeps last N messages (default: 20, configurable)
- **Cross-Agent**: History spans all agents for context continuity
- **Persistence**: Auto-loads on startup, auto-saves on shutdown
- **Storage**: JSON format in `data/conversation_history.json`

## Configuration Options

Edit `.env` to customize:

```bash
# Agent behavior
AGENT_TEMPERATURE=1.0          # Response creativity (0.0-2.0)
REQUEST_TIMEOUT=30             # API timeout in seconds
MAX_RETRIES=3                  # Retry failed requests

# Conversation history
MAX_CONVERSATION_MESSAGES=20   # Rolling window size
CONVERSATION_HISTORY_FILE=data/conversation_history.json

# Security settings
RATE_LIMIT_ENABLED=true        # Enable/disable rate limiting
RATE_LIMIT_CALLS=10           # Max calls per time window
RATE_LIMIT_PERIOD=60          # Time window in seconds
MAX_INPUT_LENGTH=10000        # Max input characters
```

## Testing

Run tests with pytest:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=modules --cov-report=html
```

## Extending the System

### Adding New Agents

1. Create a new agent file in `modules/agents/`
2. Implement the agent class with `process()` and `process_with_history()` methods
3. Import and initialize the agent in `master_agent.py`
4. Update classification logic if needed

Example:
```python
# modules/agents/new_agent.py
class NewAgent:
    def __init__(self):
        self.llm = self._create_llm()
        self.agent_type = "new_agent"
    
    def process_with_history(self, user_input, conversation_history):
        # Your implementation here
        pass
```

## Project Structure Details

### Master Agent (`master_agent.py`)
- Manages agent lifecycle
- Routes requests using LangGraph workflow
- Maintains conversation history
- Handles persistence

### Chat Agent (`chat_agent.py`)
- Specialized for general conversation
- Uses conversation history for context
- Built on Azure OpenAI

### Conversation History (`conversation_history.py`)
- Manages chat message storage
- Rolling window implementation
- JSON persistence
- Statistics and context retrieval

### Configuration (`config.py`)
- Environment variable management
- Validation of required settings
- Azure OpenAI connection parameters

## Troubleshooting

### "Failed to initialize agent"
- Check your `.env` file exists and has correct values
- Verify Azure OpenAI endpoint and API key
- Ensure deployment name matches your Azure setup

### "Could not restore previous conversation"
- Normal on first run (no history file exists yet)
- Check `data/` directory has write permissions
- Verify `CONVERSATION_HISTORY_FILE` path in `.env`

### Connection timeouts
- Increase `REQUEST_TIMEOUT` in `.env`
- Check network connectivity to Azure
- Verify Azure OpenAI service is running

## License

This project is provided as-is for educational and development purposes.

## Based On

This is a stripped-down version inspired by the grading-agent architecture, focusing on core chat functionality with conversation history.
