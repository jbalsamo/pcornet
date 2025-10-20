# Streamlit Setup Guide

## Application Modes

Your application now supports two modes:

### 1. **Streamlit Web UI** (Default)
- Modern chat interface with AI-powered conversation management
- Runs on port 8888
- Features:
  - Real-time chat interface with message history
  - **New Chat**: Automatically saves current conversation with AI-generated title
  - **Previous Chats**: Browse and load saved conversations
  - **Delete Conversations**: Remove saved chats with confirmation dialog
  - **System Info** (Collapsible): View endpoint, deployment, and agent information
  - **History Stats** (Collapsible): Track message counts and usage
  - **Dark Mode**: Toggle between dark and light themes
  - Compact UI with optimized spacing for maximum content visibility

### 2. **CLI Mode** (Optional)
- Original command-line interface
- Activated with `--cli` flag
- All original functionality preserved

## Installation

Install the dependencies:

```bash
pip install -r requirements.txt
```

This will install:
- `streamlit` - Web UI framework
- All other required dependencies (see requirements.txt)

## Running the Application

### Streamlit Mode (Default)

**Option 1: Using the helper script**
```bash
./run_streamlit.sh
```

**Option 2: Direct streamlit command**
```bash
streamlit run main.py --server.port 8888
```

**Option 3: Python command (will launch streamlit)**
```bash
python main.py
```

Then open your browser to: http://localhost:8888

### CLI Mode

```bash
# Quiet mode
python main.py --cli

# Verbose mode
python main.py --cli -v
```

## Files Modified

1. **requirements.txt** - Added streamlit and pyperclip dependencies
2. **main.py** - Refactored to support both modes:
   - Added `run_streamlit_mode()` function
   - Renamed original `main()` to `run_cli_mode()`
   - New `main()` routes to correct mode based on `--cli` flag
3. **README.md** - Updated with dual-mode documentation
4. **run_streamlit.sh** - New helper script to launch Streamlit on port 8888

## Streamlit UI Components

### Main Chat Area
- Messages displayed in chat format with user and assistant bubbles
- Optimized spacing for maximum content visibility
- Chat input at bottom of screen

### Sidebar Components

#### System Info (Collapsible)
- Collapsed by default to save space
- Shows: Endpoint, deployment, API version, specialized agents
- Toggle with ▶/▼ button

#### History Stats (Collapsible)
- Collapsed by default to save space
- Shows: Total messages, user messages, assistant messages
- Toggle with ▶/▼ button

#### Controls
- **🆕 New Chat**: Saves current conversation with AI-generated title, then clears for new chat
- Will only save if there are messages to save
- Generates short, meaningful titles (2-4 words)

#### Previous Chats
- Scrollable list of saved conversations (newest first)
- Each conversation shows:
  - 📄 Load button - Opens the saved conversation
  - 🗑️ Delete button - Removes the conversation (with confirmation)
- Conversations automatically named based on first user message
- Loaded conversations can be continued and updates save back to same file

### Conversation Management

#### Auto-Save Behavior
- When clicking "New Chat": Current conversation saved automatically
- When loading another chat: Current conversation saved first
- Conversations saved to `saved/` directory with AI-generated names
- No duplicate titles - continues existing conversation when loaded and modified

#### Delete Confirmation
- Clicking delete shows confirmation dialog in main area
- Options: "✅ Yes, Delete" or "❌ No, Cancel"
- If deleted conversation is currently loaded, it clears the current chat
- Action is permanent and cannot be undone

## File Storage

- **Current Session**: 
  - `data/conversation_history.json` - Agent's full conversation history
  - `data/chat_history.json` - UI chat messages
- **Saved Conversations**:
  - `saved/<ai_generated_title>.json` - Individual saved conversations

## Notes

- Conversation history is shared between CLI and Streamlit modes
- Streamlit automatically reloads when code changes
- AI generates concise titles (2-4 words, max 40 characters)
- Dark mode is enabled by default
- Compact UI maximizes space for chat content
