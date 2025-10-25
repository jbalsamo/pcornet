"""
Main application entry point for the Azure OpenAI Chat Agent System.
"""
import os
import sys

# Set environment variables FIRST before any other imports
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['PYTHONWARNINGS'] = 'ignore'

import warnings

# Aggressively suppress ALL warnings
warnings.simplefilter('ignore')
warnings.filterwarnings('ignore')
warnings.filterwarnings('ignore', category=Warning)
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=DeprecationWarning)

import logging
import argparse
import streamlit as st
import json
import glob
from datetime import datetime

# Custom filter to block torch.classes warnings
class TorchWarningFilter(logging.Filter):
    def filter(self, record):
        message = record.getMessage()
        return not ('torch.classes' in message or '__path__._path' in message)

# Suppress logging from specific noisy modules
for logger_name in ['torch', 'sentence_transformers', 'transformers', 'chromadb', 'streamlit']:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.ERROR)
    logger.addFilter(TorchWarningFilter())

# Also add filter to root logger
logging.getLogger().addFilter(TorchWarningFilter())

# Configure langchain globals to suppress deprecation warnings
try:
    from langchain import globals as langchain_globals
    langchain_globals.set_verbose(False)
except ImportError:
    # Fallback for older versions of langchain
    pass

from modules.master_agent import MasterAgent
from modules.security import InputValidationException, RateLimitException
from modules.interactive_session import interactive_session

logger = logging.getLogger(__name__)

def setup_logging(verbose: bool = False):
    """Set up logging configuration based on verbose flag."""
    log_level = logging.INFO if verbose else logging.WARNING
    
    root_logger = logging.getLogger()
    if root_logger.handlers:
        for handler in root_logger.handlers:
            root_logger.removeHandler(handler)
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        force=True
    )

def save_chat_history_to_file(messages):
    """Save UI chat messages to data/chat_history.json"""
    try:
        os.makedirs("data", exist_ok=True)
        chat_data = {
            "saved_at": datetime.now().isoformat(),
            "messages": messages
        }
        with open("data/chat_history.json", 'w', encoding='utf-8') as f:
            json.dump(chat_data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error saving chat history: {e}")
        return False

def load_chat_history_from_file():
    """Load UI chat messages from data/chat_history.json"""
    try:
        if os.path.exists("data/chat_history.json"):
            with open("data/chat_history.json", 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("messages", [])
        return []
    except Exception as e:
        logger.error(f"Error loading chat history: {e}")
        return []

def get_saved_conversations():
    """Get list of all saved conversations in reverse chronological order."""
    try:
        if not os.path.exists("saved"):
            return []
        
        files = glob.glob("saved/*.json")
        file_info = []
        for filepath in files:
            filename = os.path.basename(filepath)
            name_without_ext = os.path.splitext(filename)[0]
            mod_time = os.path.getmtime(filepath)
            file_info.append((name_without_ext, filepath, mod_time))
        
        file_info.sort(key=lambda x: x[2], reverse=True)
        return file_info
    except Exception as e:
        logger.error(f"Error getting saved conversations: {e}")
        return []

def load_saved_conversation(filepath: str, agent):
    """Load a saved conversation and restore it to the current session."""
    try:
        logger.info(f"Loading conversation from {filepath}")
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        agent.conversation_history.messages.clear()
        messages = data.get("messages", [])
        logger.info(f"Found {len(messages)} messages in file")
        
        if messages and "timestamp" in messages[0]:
            from modules.conversation_history import ChatMessage
            for msg_dict in messages:
                message = ChatMessage(
                    role=msg_dict["role"],
                    content=msg_dict["content"],
                    timestamp=datetime.fromisoformat(msg_dict["timestamp"]),
                    agent_type=msg_dict.get("agent_type"),
                    metadata=msg_dict.get("metadata")
                )
                agent.conversation_history.messages.append(message)
        else:
            from modules.conversation_history import ChatMessage
            for msg_dict in messages:
                message = ChatMessage(
                    role=msg_dict["role"],
                    content=msg_dict["content"],
                    timestamp=datetime.now(),
                    agent_type=msg_dict.get("agent_type"),
                    metadata=msg_dict.get("metadata")
                )
                agent.conversation_history.messages.append(message)
        
        ui_messages = []
        for message in agent.conversation_history.messages:
            if message.role in ["user", "assistant"]:
                ui_messages.append({
                    "role": message.role,
                    "content": message.content
                })
        
        logger.info(f"Built {len(ui_messages)} UI messages for display")
        return ui_messages
        
    except Exception as e:
        logger.error(f"Error loading saved conversation from {filepath}: {e}", exc_info=True)
        return []

def generate_chat_title(first_user_message: str, agent) -> str:
    """Generate a short, meaningful title for the chat using AI."""
    try:
        prompt = f"""Create a SHORT title (2-4 words ONLY) that captures the main topic of this question:

"{first_user_message}"

Requirements:
- EXACTLY 2-4 words
- Maximum 40 characters total
- Capture the core topic/subject
- Use simple, clear words
- No quotes, punctuation, or special characters

Examples:
- "How do I deploy to Azure?" → "Azure Deployment"
- "What's the best way to handle errors in Python?" → "Python Error Handling"
- "Can you help me debug this code?" → "Code Debugging"

Return ONLY the title (2-4 words), nothing else."""

        title = agent.chat_agent.llm.invoke([{"role": "user", "content": prompt}]).content.strip()
        
        import re
        title = title.strip('"\'')
        title = re.sub(r'[^\w\s-]', '', title)
        title = re.sub(r'\s+', ' ', title)
        title = title[:40]
        title = title.replace(' ', '_')
        
        return title if title else "untitled_conversation"
        
    except Exception as e:
        logger.error(f"Error generating chat title: {e}")
        return f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

def main():
    """
    PCORnet Assistant with full sidebar functionality.
    """
    setup_logging(verbose=False)
    
    st.set_page_config(
        page_title="PCORNET Concept Set Tool",
        page_icon="🤖",
        layout="wide"
    )
    
    # Initialize session state
    if 'agent' not in st.session_state:
        try:
            st.session_state.agent = MasterAgent()
            st.session_state.initialized = True
        except Exception as e:
            st.error(f"❌ Failed to initialize agent: {e}")
            st.session_state.initialized = False
            return
    
    if 'messages' not in st.session_state:
        st.session_state.messages = load_chat_history_from_file()
        logger.info(f"Initialized session with {len(st.session_state.messages)} messages from chat_history.json")
    
    if 'current_conversation_name' not in st.session_state:
        st.session_state.current_conversation_name = None
    
    if 'delete_confirm_chat' not in st.session_state:
        st.session_state.delete_confirm_chat = None
    
    if 'theme' not in st.session_state:
        st.session_state.theme = 'light'
    
    # Initialize session_id for interactive sessions (persistent per Streamlit session)
    if 'interactive_session_id' not in st.session_state:
        import uuid
        st.session_state.interactive_session_id = f"streamlit_{uuid.uuid4().hex[:8]}"
        logger.info(f"Created new interactive session ID: {st.session_state.interactive_session_id}")
    
    # Apply custom CSS for theme styling (colors only, no layout changes)
    if st.session_state.theme == 'dark':
        theme_css = """
        <style>
        /* Dark mode */
        .stApp {
            background-color: #0e1117 !important;
            color: #fafafa !important;
        }
        [data-testid="stSidebar"] {
            background-color: #1a1d29 !important;
        }
        /* Sidebar collapse/expand button - dark mode */
        [data-testid="collapsedControl"] {
            background-color: #4a5568 !important;
            color: #fafafa !important;
        }
        [data-testid="collapsedControl"]:hover {
            background-color: #5a6578 !important;
        }
        /* Chat input - dark mode (colors only) - HIGH SPECIFICITY */
        [data-testid="stBottom"] [data-testid="stChatInput"] textarea,
        [data-testid="stChatInputContainer"] textarea,
        .stChatFloatingInputContainer textarea,
        [data-testid="stChatInput"] textarea {
            background-color: #1e2130 !important;
            color: #fafafa !important;
            caret-color: #fafafa !important;
            border-radius: 8px !important;
            border: 1px solid #4a5568 !important;
        }
        [data-testid="stBottom"] [data-testid="stChatInput"] textarea::placeholder,
        [data-testid="stChatInputContainer"] textarea::placeholder,
        .stChatFloatingInputContainer textarea::placeholder,
        [data-testid="stChatInput"] textarea::placeholder {
            color: #9ca3af !important;
        }
        /* Chat input container - dark mode - stable selector */
        [data-testid="stChatInput"] {
            background-color: transparent !important;
        }
        /* Fixed chat input area - stable selectors for dark mode */
        [data-testid="stBottom"],
        [data-testid="stChatInputContainer"],
        .stChatFloatingInputContainer {
            background-color: #0e1117 !important;
            color: #fafafa !important;
        }
        /* Ensure text elements in bottom area are light colored */
        [data-testid="stBottom"] p,
        [data-testid="stBottom"] span,
        [data-testid="stBottom"] label,
        [data-testid="stChatInputContainer"] p,
        [data-testid="stChatInputContainer"] span,
        [data-testid="stChatInputContainer"] label,
        .stChatFloatingInputContainer p,
        .stChatFloatingInputContainer span,
        .stChatFloatingInputContainer label {
            color: #fafafa !important;
        }
        /* Buttons */
        .stButton > button {
            background-color: #262730 !important;
            color: #fafafa !important;
            border: 2px solid #404050 !important;
        }
        .stButton > button:hover {
            background-color: #363740 !important;
            border-color: #606070 !important;
        }
        .stButton > button[kind="primary"] {
            background-color: #4a5568 !important;
            border-color: #5a6578 !important;
        }
        .stButton > button[kind="primary"]:hover {
            background-color: #5a6578 !important;
            border-color: #6a7588 !important;
        }
        /* Text inputs */
        .stTextInput > div > div > input {
            background-color: #1e2130 !important;
            color: #fafafa !important;
            caret-color: #fafafa !important;
            border: 2px solid #4a5568 !important;
        }
        /* Sidebar text visibility */
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] label {
            color: #e5e7eb !important;
        }
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] h2 {
            color: #fafafa !important;
        }
        /* Theme toggle buttons */
        .stButton button[key="light_mode"],
        .stButton button[key="dark_mode"] {
            width: 45px !important;
            min-width: 45px !important;
            height: 45px !important;
            padding: 0.2em !important;
            font-size: 20px !important;
        }
        .stButton button[key="light_mode"] {
            background: #e5e7eb !important;
            color: #1a202c !important;
            border: 2px solid #d1d5db !important;
        }
        .stButton button[key="dark_mode"] {
            background: #1a1d29 !important;
            color: #fafafa !important;
            border: 2px solid #2d3142 !important;
        }
        .stButton button[key="light_mode"][kind="primary"] {
            background: #e5e7eb !important;
            color: #1a202c !important;
            border: 4px solid #3b82f6 !important;
        }
        .stButton button[key="dark_mode"][kind="primary"] {
            background: #1a1d29 !important;
            color: #fafafa !important;
            border: 4px solid #3b82f6 !important;
        }
        /* Delete buttons */
        button[key^="delete_"],
        button[key*="delete"] {
            background: #374151 !important;
            color: #ef4444 !important;
            border: 2px solid #4b5563 !important;
        }
        button[key^="delete_"]:hover,
        button[key*="delete"]:hover {
            background: #4b5563 !important;
            color: #f87171 !important;
        }
        /* Previous chat buttons */
        button[key^="load_"] {
            background-color: #262730 !important;
            color: #fafafa !important;
            border: 2px solid #4a5568 !important;
            text-align: left !important;
        }
        button[key^="load_"]:hover {
            background-color: #363740 !important;
        }
        /* Info/Alert boxes */
        .stAlert p,
        [data-testid="stAlert"] p,
        [data-testid="stNotification"] p,
        div[data-baseweb="notification"] p {
            color: #fafafa !important;
            font-weight: 500 !important;
        }
        /* Chat messages - dark mode */
        .stChatMessage {
            background-color: #1e2130 !important;
            border: 2px solid #4a5568 !important;
            border-radius: 16px !important;
            padding: 1em !important;
        }
        .stChatMessage ul,
        .stChatMessage ol,
        .stChatMessage li,
        .stChatMessage p {
            color: #e5e7eb !important;
        }
        /* Code blocks - dark mode */
        .stChatMessage code {
            background-color: #262730 !important;
            color: #f0f2f6 !important;
            padding: 2px 6px !important;
            border-radius: 4px !important;
        }
        /* Top bar area - dark mode */
        [data-testid="stHeader"] {
            background-color: #0e1117 !important;
        }
        [data-testid="stToolbar"] {
            background-color: #0e1117 !important;
        }
        /* Title area */
        section.main > div:first-child {
            background-color: #0e1117 !important;
        }
        /* Main content area background */
        section.main {
            background-color: #0e1117 !important;
        }
        /* Headers */
        h1, h2, h3 {
            color: #fafafa !important;
        }
        /* Main content area padding - dark mode */
        section.main > div.block-container {
            padding-top: 0.5em !important;
            padding-left: 2em !important;
            padding-right: 2em !important;
            margin: 0 !important;
        }
        /* Table text visibility */
        table,
        table thead,
        table tbody,
        table tr,
        table td,
        table th {
            color: #e5e7eb !important;
        }
        table,
        table td,
        table th {
            border-color: #e5e7eb !important;
        }
        </style>
        """
    else:
        theme_css = """
        <style>
        /* Light mode */
        .stApp {
            background-color: #ffffff !important;
            color: #262730 !important;
        }
        [data-testid="stSidebar"] {
            background-color: #f8f9fa !important;
        }
        /* Sidebar collapse/expand button - light mode */
        [data-testid="collapsedControl"] {
            background-color: #4b5563 !important;
            color: #ffffff !important;
        }
        [data-testid="collapsedControl"]:hover {
            background-color: #374151 !important;
        }
        /* Chat input - light mode (colors only) - HIGH SPECIFICITY */
        [data-testid="stBottom"] [data-testid="stChatInput"] textarea,
        [data-testid="stChatInputContainer"] textarea,
        .stChatFloatingInputContainer textarea,
        [data-testid="stChatInput"] textarea {
            background-color: #f8f9fa !important;
            color: #262730 !important;
            caret-color: #262730 !important;
            border-radius: 8px !important;
            border: 1px solid #9ca3af !important;
        }
        [data-testid="stBottom"] [data-testid="stChatInput"] textarea::placeholder,
        [data-testid="stChatInputContainer"] textarea::placeholder,
        .stChatFloatingInputContainer textarea::placeholder,
        [data-testid="stChatInput"] textarea::placeholder {
            color: #6b7280 !important;
        }
        /* Chat input container - light mode - stable selector */
        [data-testid="stChatInput"] {
            background-color: transparent !important;
        }
        /* Fixed chat input area - stable selectors for light mode */
        [data-testid="stBottom"],
        [data-testid="stChatInputContainer"],
        .stChatFloatingInputContainer {
            background-color: #ffffff !important;
            color: #262730 !important;
        }
        /* Ensure text elements in bottom area are dark colored */
        [data-testid="stBottom"] p,
        [data-testid="stBottom"] span,
        [data-testid="stBottom"] label,
        [data-testid="stChatInputContainer"] p,
        [data-testid="stChatInputContainer"] span,
        [data-testid="stChatInputContainer"] label,
        .stChatFloatingInputContainer p,
        .stChatFloatingInputContainer span,
        .stChatFloatingInputContainer label {
            color: #262730 !important;
        }
        /* Buttons */
        .stButton > button {
            background-color: #ffffff !important;
            color: #262730 !important;
            border: 2px solid #d0d5db !important;
        }
        .stButton > button:hover {
            background-color: #f0f2f6 !important;
            border-color: #b0b5bb !important;
        }
        .stButton > button[kind="primary"] {
            background-color: #4299e1 !important;
            color: #ffffff !important;
            border-color: #3182ce !important;
        }
        .stButton > button[kind="primary"]:hover {
            background-color: #3182ce !important;
            border-color: #2c5aa0 !important;
        }
        /* Text inputs */
        .stTextInput > div > div > input {
            background-color: #ffffff !important;
            color: #262730 !important;
            caret-color: #262730 !important;
            border: 2px solid #9ca3af !important;
        }
        /* Sidebar text visibility */
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] label {
            color: #374151 !important;
        }
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] h2 {
            color: #1a202c !important;
        }
        /* Theme toggle buttons */
        .stButton button[key="light_mode"],
        .stButton button[key="dark_mode"] {
            width: 45px !important;
            min-width: 45px !important;
            height: 45px !important;
            padding: 0.2em !important;
            font-size: 20px !important;
        }
        .stButton button[key="light_mode"] {
            background: #e5e7eb !important;
            color: #1a202c !important;
            border: 2px solid #d1d5db !important;
        }
        .stButton button[key="dark_mode"] {
            background: #1a1d29 !important;
            color: #fafafa !important;
            border: 2px solid #2d3142 !important;
        }
        .stButton button[key="light_mode"][kind="primary"] {
            background: #e5e7eb !important;
            color: #1a202c !important;
            border: 4px solid #3b82f6 !important;
        }
        .stButton button[key="dark_mode"][kind="primary"] {
            background: #1a1d29 !important;
            color: #fafafa !important;
            border: 4px solid #3b82f6 !important;
        }
        /* Delete buttons */
        button[key^="delete_"],
        button[key*="delete"] {
            background: #ffffff !important;
            color: #dc2626 !important;
            border: 2px solid #fca5a5 !important;
        }
        button[key^="delete_"]:hover,
        button[key*="delete"]:hover {
            background: #f3f4f6 !important;
            color: #b91c1c !important;
        }
        /* Previous chat buttons */
        button[key^="load_"] {
            background-color: #ffffff !important;
            color: #262730 !important;
            border: 2px solid #9ca3af !important;
            text-align: left !important;
        }
        button[key^="load_"]:hover {
            background-color: #f0f2f6 !important;
        }
        /* Info/Alert boxes */
        .stAlert p,
        [data-testid="stAlert"] p,
        [data-testid="stNotification"] p,
        div[data-baseweb="notification"] p {
            color: #1a1a1a !important;
            font-weight: 500 !important;
        }
        /* Chat messages - light mode */
        .stChatMessage {
            background-color: #ffffff !important;
            border: 2px solid #9ca3af !important;
            border-radius: 16px !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            padding: 1em !important;
        }
        .stChatMessage ul,
        .stChatMessage ol,
        .stChatMessage li,
        .stChatMessage p {
            color: #1a1a1a !important;
        }
        /* Code blocks - light mode */
        .stChatMessage code {
            background-color: #f3f4f6 !important;
            color: #1f2937 !important;
            padding: 2px 6px !important;
            border-radius: 4px !important;
            border: 1px solid #d1d5db !important;
        }
        /* Top bar area - light mode */
        [data-testid="stHeader"] {
            background-color: #ffffff !important;
        }
        [data-testid="stToolbar"] {
            background-color: #ffffff !important;
        }
        /* Title area */
        section.main > div:first-child {
            background-color: #ffffff !important;
        }
        /* Main content area background */
        section.main {
            background-color: #ffffff !important;
        }
        /* Headers */
        h1, h2, h3 {
            color: #262730 !important;
        }
        /* Main content area padding - light mode */
        section.main > div.block-container {
            padding-top: 0.5em !important;
            padding-left: 2em !important;
            padding-right: 2em !important;
            margin: 0 !important;
        }
        /* Table text visibility */
        table,
        table thead,
        table tbody,
        table tr,
        table td,
        table th {
            color: #1a1a1a !important;
        }
        table,
        table td,
        table th {
            border-color: #1a1a1a !important;
        }
        </style>
        """
    
    st.markdown(theme_css, unsafe_allow_html=True)
    
    # Additional CSS for layout
    st.markdown("""
    <style>
    /* Title with minimal padding and margins */
    [data-testid="stAppViewContainer"] > div:first-child {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    h1 {
        margin-top: 0 !important;
        margin-bottom: 0 !important;
        padding-top: 0.25em !important;
        padding-bottom: 0.25em !important;
    }
    /* Main block container - reduce top padding */
    .block-container {
        padding-top: 0.25em !important;
        margin-top: 0 !important;
    }
    /* Reduce divider margins */
    hr {
        margin-top: 0.25em !important;
        margin-bottom: 0.25em !important;
    }
    /* Reduce element container spacing */
    .element-container {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    /* Reduce chat message spacing and ensure proper width */
    .stChatMessage {
        margin-top: 0.25em !important;
        margin-bottom: 0.25em !important;
        padding-bottom: 0.5em !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
    }
    /* Reduce vertical block spacing */
    [data-testid="stVerticalBlock"] > div {
        gap: 0.25em !important;
    }
    /* Sidebar flex column layout with spacing */
    [data-testid="stSidebar"] {
        padding: 0 !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 2em !important;
        padding-left: 1em !important;
        padding-right: 1em !important;
        padding-bottom: 1em !important;
        display: flex !important;
        flex-direction: column !important;
        height: 100vh !important;
        box-sizing: border-box !important;
    }
    /* Override auto-generated emotion cache classes in sidebar */
    [data-testid="stSidebar"] [class*="st-emotion-cache"] {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    [data-testid="stSidebar"] > div > [class*="st-emotion-cache"]:first-child {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    /* Sidebar content padding - stable selector */
    [data-testid="stSidebarContent"] {
        padding-top: 0 !important;
        padding-bottom: 0.5em !important;
        padding-left: 0.25em !important;
        padding-right: 0.25em !important;
        margin-top: 0 !important;
        margin-bottom: 0.25em !important;
        height: 100% !important;
    }
    /* Main area element container padding - stable selector */
    section.main div.element-container > div {
        padding: 0px !important;
    }
    /* Block container bottom padding - stable selector */
    section.main > div.block-container {
        padding-bottom: 170px !important;
    }
    /* Chat input container styling - stable selector */
    [data-testid="stChatInput"] {
        max-width: 100% !important;
        box-sizing: border-box !important;
        width: 100% !important;
    }
    /* Ensure textarea and file input stay within bounds */
    [data-testid="stChatInput"] textarea {
        max-width: 100% !important;
        box-sizing: border-box !important;
        width: 100% !important;
    }
    [data-testid="stChatInput"] input[type="file"] {
        max-width: 100% !important;
        box-sizing: border-box !important;
    }
    /* Limit file uploader container */
    [data-testid="stChatInput"] [data-testid="stFileUploader"] {
        max-width: 100% !important;
        box-sizing: border-box !important;
        overflow: hidden !important;
    }
    /* Hide duplicate file uploaders - keep only first one */
    [data-testid="stChatInput"] [data-testid="stFileUploader"]:not(:first-of-type) {
        display: none !important;
    }
    /* Ensure all nested divs don't overflow */
    [data-testid="stChatInput"] > div,
    [data-testid="stChatInput"] > div > div {
        max-width: 100% !important;
        box-sizing: border-box !important;
    }
    /* Fixed chat input container - stable selectors - centered at 80% */
    [data-testid="stBottom"],
    [data-testid="stChatInputContainer"],
    .stChatFloatingInputContainer {
        position: fixed !important;
        bottom: 0px !important;
        left: var(--sidebar-width, 21rem) !important;
        right: 0 !important;
        width: auto !important;
        max-width: 100% !important;
        padding-bottom: 1rem !important;
        padding-top: 1rem !important;
        padding-left: 5% !important;
        padding-right: 5% !important;
        box-sizing: border-box !important;
        overflow-x: hidden !important;
        z-index: 99 !important;
    }
    /* Chat input when sidebar is collapsed */
    [data-testid="collapsedControl"] ~ * [data-testid="stBottom"],
    [data-testid="collapsedControl"] ~ * [data-testid="stChatInputContainer"],
    [data-testid="collapsedControl"] ~ * .stChatFloatingInputContainer {
        left: 0 !important;
        padding-left: 10% !important;
        padding-right: 10% !important;
    }
    [data-testid="stSidebar"] .block-container {
        padding: 0 !important;
        flex: 1 !important;
        display: flex !important;
        flex-direction: column !important;
    }
    section[data-testid="stSidebar"] > div {
        padding: 0 !important;
    }
    /* Minimize vertical spacing in sidebar */
    [data-testid="stSidebar"] p {
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1.2 !important;
    }
    [data-testid="stSidebar"] .element-container {
        margin: 0 !important;
        padding: 0 !important;
    }
    [data-testid="stSidebar"] .stMarkdown {
        margin: 0 !important;
        padding: 0 !important;
    }
    [data-testid="stSidebar"] .row-widget {
        margin: 0 !important;
        padding: 0 !important;
    }
    [data-testid="stSidebar"] hr {
        margin: 0.5em 0 !important;
    }
    /* Hide empty elements in sidebar */
    [data-testid="stSidebar"] .element-container:empty {
        display: none !important;
    }
    [data-testid="stSidebar"] div:empty {
        display: none !important;
    }
    /* Reduce spacing between sidebar buttons */
    [data-testid="stSidebar"] .stButton {
        margin-top: 0.25em !important;
        margin-bottom: 0.25em !important;
    }
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        margin-top: 0.5em !important;
        margin-bottom: 0.25em !important;
        padding: 0 !important;
    }
    /* Center info boxes vertically in sidebar */
    [data-testid="stSidebar"] .stAlert,
    [data-testid="stSidebar"] [data-testid="stAlert"],
    [data-testid="stSidebar"] [data-testid="stNotification"] {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
        min-height: 100px !important;
        height: 100% !important;
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    [data-testid="stSidebar"] .element-container:has(.stAlert),
    [data-testid="stSidebar"] .element-container:has([data-testid="stAlert"]) {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    /* Theme section - center buttons and reduce height */
    [class*="st-emotion"][class*="cache"] [data-testid="column"] {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        min-height: auto !important;
        padding: 0.1em !important;
        padding-bottom: 0 !important;
    }
    /* Center theme buttons in their cells */
    [data-testid="stSidebar"] button[key="light_mode"],
    [data-testid="stSidebar"] button[key="dark_mode"] {
        margin: 0 auto !important;
        display: block !important;
    }
    [data-testid="stSidebar"] .stButton {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
    }
    [class*="st-emotion"][class*="cache"].row-widget.stHorizontal {
        min-height: auto !important;
        height: auto !important;
        padding: 0.1em 0 !important;
        padding-bottom: 0 !important;
        margin: 0 !important;
    }
    [data-testid="stSidebar"] [class*="st-emotion"][class*="cache"] {
        min-height: auto !important;
        padding-bottom: 0 !important;
    }
    /* Add bottom padding to prevent messages being hidden */
    section.main > div.block-container {
        padding-bottom: 150px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    
    # Check for delete confirmation BEFORE rendering sidebar to prevent recursion
    if st.session_state.delete_confirm_chat:
        name, filepath, display_name = st.session_state.delete_confirm_chat
        
        st.warning("⚠️ Confirmation Required")
        st.markdown(f"### Delete '{display_name}'?")
        st.write("This action cannot be undone.")
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Yes, Delete", use_container_width=True, type="primary", key="confirm_delete"):
                try:
                    os.remove(filepath)
                    logger.info(f"Deleted conversation: {filepath}")
                    
                    if st.session_state.current_conversation_name == name:
                        st.session_state.current_conversation_name = None
                        st.session_state.messages = []
                        st.session_state.agent.clear_conversation_history()
                        save_chat_history_to_file(st.session_state.messages)
                    
                    st.session_state.delete_confirm_chat = None
                    st.success(f"Deleted {display_name}")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Failed to delete: {e}")
                    st.session_state.delete_confirm_chat = None
                    st.rerun()
        
        with col2:
            if st.button("❌ No, Cancel", use_container_width=True, key="cancel_delete"):
                st.session_state.delete_confirm_chat = None
                st.rerun()
        
        st.stop()  # Stop execution here to prevent sidebar from rendering
    
    # ============================================================================
    # SIDEBAR - Theme Toggle, Controls, and Previous Chats
    # ============================================================================
    with st.sidebar:
        st.markdown("### ⚙️ PCORNET Assistant")
        st.divider()
        
        # Theme Toggle Section
        st.markdown("**Theme**")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("☀️", key="light_mode", help="Light Mode",
                        type="primary" if st.session_state.theme == 'light' else "secondary"):
                st.session_state.theme = 'light'
                st.rerun()
        with col2:
            if st.button("🌙", key="dark_mode", help="Dark Mode",
                        type="primary" if st.session_state.theme == 'dark' else "secondary"):
                st.session_state.theme = 'dark'
                st.rerun()
        
        st.divider()
        
        # Controls Section
        st.markdown("**Controls**")
        
        if st.button("🆕 New Chat", use_container_width=True, key="new_chat_btn", type="primary"):
            has_messages = len(st.session_state.messages) > 0
            has_history = len(st.session_state.agent.conversation_history.messages) > 0
            
            if has_messages or has_history:
                if st.session_state.messages:
                    first_user_msg = None
                    for msg in st.session_state.messages:
                        if msg["role"] == "user":
                            first_user_msg = msg["content"]
                            break
                    
                    if first_user_msg:
                        with st.spinner("Saving current chat..."):
                            if st.session_state.current_conversation_name:
                                title = st.session_state.current_conversation_name
                                logger.info(f"Saving back to existing conversation: {title}")
                            else:
                                title = generate_chat_title(first_user_msg, st.session_state.agent)
                                logger.info(f"Generated new conversation title: {title}")
                        
                        st.session_state.agent.conversation_history.save_to_custom_file(title)
                
                st.session_state.agent.clear_conversation_history()
                st.session_state.messages = []
                st.session_state.current_conversation_name = None
                
                # Clear interactive session and create new one
                from modules.interactive_session import interactive_session
                if st.session_state.interactive_session_id:
                    interactive_session.clear_session(st.session_state.interactive_session_id)
                import uuid
                st.session_state.interactive_session_id = f"streamlit_{uuid.uuid4().hex[:8]}"
                logger.info(f"Cleared interactive session and created new ID: {st.session_state.interactive_session_id}")
                
                save_chat_history_to_file(st.session_state.messages)
                st.rerun()
        
        st.divider()
        
        # Previous Chats Section
        st.markdown("**💬 Previous Chats**")
        
        saved_convos = get_saved_conversations()
        
        if saved_convos:
            # Create scrollable container for chat list
            for name, filepath, _ in saved_convos:
                display_name = name.replace('_', ' ')
                
                col1, col2 = st.columns([5, 1])
                
                with col1:
                    chat_clicked = st.button(f"📄 {display_name}", use_container_width=True, key=f"load_{name}")
                
                with col2:
                    if st.button("🗑️", key=f"delete_{name}", help="Delete this conversation"):
                        st.session_state.delete_confirm_chat = (name, filepath, display_name)
                        st.rerun()
                
                if chat_clicked:
                    if st.session_state.current_conversation_name != name:
                        if st.session_state.messages:
                            first_user_msg = None
                            for msg in st.session_state.messages:
                                if msg["role"] == "user":
                                    first_user_msg = msg["content"]
                                    break
                            
                            if first_user_msg:
                                with st.spinner("💾 Saving current chat..."):
                                    if st.session_state.current_conversation_name:
                                        title = st.session_state.current_conversation_name
                                    else:
                                        title = generate_chat_title(first_user_msg, st.session_state.agent)
                                    
                                    st.session_state.agent.conversation_history.save_to_custom_file(title)
                        
                        with st.spinner(f"📂 Loading {display_name}..."):
                            ui_messages = load_saved_conversation(filepath, st.session_state.agent)
                            
                            if ui_messages:
                                st.session_state.messages = ui_messages
                                st.session_state.current_conversation_name = name
                                save_chat_history_to_file(st.session_state.messages)
                                st.session_state.agent.save_conversation_history()
                                logger.info(f"Loaded {len(ui_messages)} messages from {filepath}")
                            else:
                                st.error("Failed to load conversation")
                        
                        st.rerun()
        else:
            st.info("No saved conversations yet. Start chatting to create one!")
        
        # Add padding at bottom of sidebar
        st.markdown("<br>" * 3, unsafe_allow_html=True)
    
    # ============================================================================
    # MAIN CHAT AREA - Title, Conversation Display, and Input
    # ============================================================================
    
    if not st.session_state.initialized:
        return
    
    # Title in main area
    st.title("🤖 PCORNET Concept Set Tool")
    
    # Show current conversation name if loaded
    if st.session_state.current_conversation_name:
        current_display = st.session_state.current_conversation_name.replace('_', ' ')
        st.caption(f"📂 Current conversation: **{current_display}**")
    
    st.divider()
    
    # Chat messages container (scrollable area at top)
    chat_container = st.container()
    with chat_container:
        if st.session_state.messages:
            logger.info(f"Displaying {len(st.session_state.messages)} messages")
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
        else:
            st.info("👋 Welcome! Start a conversation by typing a message below.")
    
    # Chat input at the bottom
    if prompt := st.chat_input("Type your message here..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("🤔 Processing..."):
                try:
                    # Pass session_id to maintain interactive context
                    response = st.session_state.agent.chat(
                        prompt, 
                        session_id=st.session_state.interactive_session_id
                    )
                    st.markdown(response)
                    
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                    st.session_state.agent.save_conversation_history()
                    save_chat_history_to_file(st.session_state.messages)
                    
                except InputValidationException as e:
                    error_msg = f"⚠️ Input validation error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                except RateLimitException as e:
                    error_msg = f"⏳ Rate limit exceeded: {str(e)}"
                    st.warning(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                except Exception as e:
                    error_msg = f"❌ Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

if __name__ == "__main__":
    main()
