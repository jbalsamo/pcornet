# PCORnet Multi-Agent Chat System

A multi-agent chat system designed to interact with specialized AI agents. This implementation uses a Streamlit web interface, with a master agent that routes queries to either a general-purpose Chat Agent or a specialized ICD (International Classification of Diseases) Search Agent.

## Features

- **Dual-Agent System**: A `MasterAgent` orchestrates requests between a `ChatAgent` for conversation and an `IcdAgent` for specific medical code lookups.
- **ICD Code Search**: The `IcdAgent` connects to Azure AI Search to perform hybrid searches for ICD codes, returning structured JSON data.
- **Web UI**: A user-friendly Streamlit interface for interacting with the agents.
- **Conversation History**: Manages chat history, though it is not yet fully persistent across sessions in the UI.
- **Secure and Configurable**: Uses environment variables for configuration and includes basic security validation.

## Architecture

The system is structured with a clear separation between the main application, configuration, and the different agent modules.

```
pcornet/
├── main.py                     # Streamlit application entry point
├── modules/
│   ├── __init__.py
│   ├── config.py               # Configuration management for Azure OpenAI
│   ├── conversation_history.py # Manages chat message history
│   ├── master_agent.py         # Central agent that routes to sub-agents
│   ├── search_tool.py          # Helper for Azure AI Search (for future use)
│   ├── security.py             # Input validation and rate limiting
│   └── agents/
│       ├── __init__.py
│       ├── base_agent.py       # (Optional) Base class for agents
│       ├── chat_agent.py       # General conversational agent
│       └── icd_agent.py        # Agent for searching ICD codes
├── data/                       # Directory for session data
├── saved/                      # Directory for saved conversations/exports
├── tests/                      # Pytest test suite
├── requirements.txt            # Python dependencies
├── activate.sh                 # Helper script to activate virtual environment
├── run_streamlit.sh            # Helper script to run the Streamlit app
├── .env                        # Local environment variables (gitignored)
└── README.md                   # This file
```

## Setup

### 1. Clone the Repository

Clone this repository to your local machine.

### 2. Create and Activate a Virtual Environment

It's recommended to use a virtual environment to manage dependencies.

```bash
# Create the virtual environment
python3 -m venv .venv

# Activate it (macOS/Linux)
source .venv/bin/activate

# Or use the provided helper script
source activate.sh
```

### 3. Install Dependencies

Install the required Python packages from `requirements.txt`.

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the root of the project and add your Azure service credentials.

```
# .env file

# Azure OpenAI Credentials
AZURE_OPENAI_ENDPOINT="https://your-resource-name.openai.azure.com/"
AZURE_OPENAI_API_KEY="your-openai-api-key"
AZURE_OPENAI_API_VERSION="2024-05-01-preview"
AZURE_OPENAI_CHAT_DEPLOYMENT="your-chat-deployment-name" # e.g., gpt-4o

# Azure AI Search Credentials (for ICD Agent)
AZURE_AI_SEARCH_ENDPOINT="https://your-search-service-name.search.windows.net"
AZURE_AI_SEARCH_API_KEY="your-search-admin-or-query-key"
AZURE_AI_SEARCH_INDEX="pcornet-icd-index" # The name of your ICD search index
```

## Deployment Options

### Local Development (Default)

Follow the setup instructions above for local development.

### Ubuntu Server Production Deployment

For production deployment on Ubuntu 24 Server, use the automated installer:

```bash
# Transfer files to server
scp -r pcornet/ ubuntu@your-server-ip:/tmp/

# SSH into server and run installer
ssh ubuntu@your-server-ip
cd /tmp/pcornet
sudo ./install.sh
```

The installer sets up:
- ✅ Systemd service (auto-restart, starts on boot)
- ✅ Nginx reverse proxy
- ✅ UFW firewall configuration
- ✅ Dedicated user and secure permissions
- ✅ Service management commands

**Service Management:**
```bash
sudo ./manage.sh start|stop|restart|status|logs|tail
```

**Complete deployment guide:** See [docs/UBUNTU_DEPLOYMENT.md](docs/UBUNTU_DEPLOYMENT.md)

## Usage

The application is run as a Streamlit web app.

```bash
# Option 1: Use the helper script
./run_streamlit.sh

# Option 2: Run directly with Streamlit
streamlit run main.py --server.port 8888
```

After running the command, open your web browser to `http://localhost:8888`. The interface provides a dropdown to select which agent (`chat` or `icd`) you want to interact with.

## How It Works

1.  **User Interface**: The user selects an agent and enters a query in the Streamlit UI.
2.  **Routing**: `main.py` captures the input and the selected `agent_type`. It calls the `MasterAgent.chat()` method, passing both the query and the agent type.
3.  **Delegation**: The `MasterAgent` uses a simple `if/elif` block to determine which sub-agent to use.
    - If `agent_type` is `"chat"`, it calls the `ChatAgent`.
    - If `agent_type` is `"icd"`, it calls the `IcdAgent`.
4.  **Processing**:
    - The **ChatAgent** uses `langchain_openai` to generate a conversational response based on the user's query.
    - The **IcdAgent** sends a POST request to the Azure AI Search REST API to find matching ICD code documents. It then formats the JSON response into a structured dictionary.
5.  **Response**: The result from the agent is returned to the UI and displayed to the user. For the `IcdAgent`, this is typically a JSON object shown in an expandable container.

## Extending the System

Adding a new agent is straightforward and involves creating a new agent class and updating the master agent to route to it.

### 1. Create the New Agent Class

Create a new file in `modules/agents/`, for example, `modules/agents/new_agent.py`. The class should have a `process(query)` method.

```python
# modules/agents/new_agent.py
import logging

logger = logging.getLogger(__name__)

class NewAgent:
    """A new agent for a new purpose."""
    def __init__(self):
        logger.info("✅ NewAgent initialized")
        # Add any initialization logic here

    def process(self, query: str) -> str:
        """Process a query and return a string response."""
        # Your agent's logic here
        return f"NewAgent processed your query: {query}"
```

### 2. Integrate into MasterAgent

In `modules/master_agent.py`, import your new agent and add it to the routing logic.

```python
# modules/master_agent.py

# 1. Import the new agent
from modules.agents.chat_agent import ChatAgent
from modules.agents.icd_agent import IcdAgent
from modules.agents.new_agent import NewAgent # <-- Add this import

class MasterAgent:
    def __init__(self):
        # ... existing initializations ...
        # 2. Initialize your new agent
        self.new_agent = NewAgent()
        logger.info("✅ NewAgent initialized")

    def chat(self, query: str, agent_type: str = "chat"):
        agent_type = agent_type.lower()
        if agent_type == "chat":
            return self.chat_agent.process(query)
        elif agent_type == "icd":
            return self._chat_icd(query)
        # 3. Add a new route
        elif agent_type == "new_agent": # <-- Add this block
            return self.new_agent.process(query)
        else:
            return f"❌ Unknown agent type: {agent_type}"
    # ... rest of the file
```

### 3. Update the UI

Finally, add your new agent as an option in the Streamlit interface in `main.py`.

```python
# main.py
# ...
agent_options = ["chat", "icd", "new_agent"] # <-- Add your new agent type
agent_type = st.selectbox("Choose Agent:", options=agent_options)
# ...
```

## Testing

The project is configured with `pytest`. To run the test suite:

```bash
pytest
```

To run tests with code coverage:

```bash
pytest --cov=modules --cov-report=html
```

This will generate a coverage report in an `htmlcov/` directory.
