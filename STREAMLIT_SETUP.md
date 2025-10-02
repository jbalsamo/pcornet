# Streamlit Setup Guide

## Changes Made

Your application now supports two modes:

### 1. **Streamlit Web UI** (Default)
- Modern chat interface
- Runs on port 8888
- Features:
  - Chat area with message history
  - Clear Chat button (clears display only)
  - Clear History button (clears persistent history)
  - Save History button
  - Copy Output button for each response
  - Sidebar with system info and stats

### 2. **CLI Mode** (Optional)
- Original command-line interface
- Activated with `--cli` flag
- All original functionality preserved

## Installation

Install the new dependencies:

```bash
pip install -r requirements.txt
```

This will install:
- `streamlit==1.28.0` - Web UI framework
- `pyperclip==1.8.2` - Clipboard functionality for copy button

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
- Messages displayed in chat format
- User messages on left, assistant on right
- Each assistant message has a Copy button

### Sidebar
- **System Info**: Endpoint, deployment, API version, agents
- **History Stats**: Message counts
- **Controls**:
  - Clear Chat - Clears UI display only
  - Clear History - Clears persistent conversation history
  - Save History - Manual save to disk

### Input
- Chat input at bottom of screen
- Type message and press Enter

## Notes

- Conversation history is shared between CLI and Streamlit modes
- History persists in `data/conversation_history.json`
- Streamlit automatically reloads when code changes
- Copy button uses clipboard (may require permissions on some systems)
