"""
Main application entry point for the Azure OpenAI Chat Agent System.
"""
import logging
import argparse
import streamlit as st
import pyperclip
from modules.master_agent import MasterAgent
from modules.security import InputValidationException, RateLimitException

logger = logging.getLogger(__name__)

def setup_logging(verbose: bool = False):
    """Set up logging configuration based on verbose flag.
    
    Args:
        verbose: If True, show INFO level logs. If False, show WARNING and above only.
    """
    log_level = logging.INFO if verbose else logging.WARNING
    
    # Get root logger and clear existing handlers to prevent duplicates
    root_logger = logging.getLogger()
    if root_logger.handlers:
        for handler in root_logger.handlers:
            root_logger.removeHandler(handler)
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        force=True
    )
    
    if verbose:
        print("📝 Verbose logging enabled (INFO level)")
    else:
        print("🔇 Quiet mode (WARNING level and above)")

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Azure OpenAI Chat Agent System - Multi-agent chat with conversation history',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s              # Run Streamlit UI on port 8888
  %(prog)s --cli        # Run in CLI mode
  %(prog)s --cli -v     # Run in CLI mode with verbose logging

Available commands during chat (CLI mode):
  status         - Show system status
  history        - Show conversation history stats
  clear-history  - Clear conversation history
  help           - Show help message
  quit/exit/bye  - Exit the system
        """
    )
    parser.add_argument(
        '--cli',
        action='store_true',
        help='Run in CLI mode instead of Streamlit UI'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging (show INFO level logs)'
    )
    return parser.parse_args()

def run_cli_mode(verbose: bool = False):
    """Run the application in CLI mode."""
    setup_logging(verbose=verbose)
    
    print("🚀 Starting Azure OpenAI Chat Agent System...")
    print("=" * 60)
    
    try:
        # Initialize the master agent
        print("📡 Initializing Master Agent System...")
        agent = MasterAgent()
        
        # Display configuration info
        info = agent.get_info()
        status = agent.get_agent_status()
        
        print(f"✅ Master Agent System initialized successfully!")
        print(f"🔗 Endpoint: {info['endpoint']}")
        print(f"🤖 Deployment: {info['deployment']}")
        print(f"📋 API Version: {info['api_version']}")
        print(f"🎯 Specialized Agents: {', '.join(info['specialized_agents']) if info['specialized_agents'] else 'None'}")
        print("=" * 60)
        
        # Interactive chat loop
        print("💡 You can now chat with the Chat Agent System!")
        print("💡 Type 'quit', 'exit', 'bye' to exit, or 'help' for available commands.")
        print("=" * 60)
        
        while True:
            try:
                user_input = input("\n👤 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    agent.shutdown()
                    print("👋 Goodbye! Thanks for using the Chat Agent System!")
                    break
                
                if user_input.lower() == 'status':
                    status = agent.get_agent_status()
                    print("\n📊 System Status:")
                    print(f"   Master Agent: {status['master_agent']}")
                    if status['specialized_agents']:
                        print("   Specialized Agents:")
                        for agent_name, agent_status in status['specialized_agents'].items():
                            print(f"     - {agent_name}: {agent_status}")
                    continue
                
                if user_input.lower() == 'help':
                    print("\n🆘 Available Commands:")
                    print("   • status - Show system status")
                    print("   • history - Show conversation history stats")
                    print("   • clear-history - Clear conversation history")
                    print("   • save - Manually save conversation history")
                    print("   • help - Show this help message")
                    print("   • quit/exit/bye - Exit the system (auto-saves)")
                    print("   • Any other input - Chat with the system")
                    continue
                
                if user_input.lower() == 'history':
                    history_info = agent.get_conversation_history()
                    print("\n💬 Conversation History:")
                    stats = history_info['stats']
                    print(f"   Total Messages: {stats['total_messages']}")
                    print(f"   User Messages: {stats['user_messages']}")
                    print(f"   Assistant Messages: {stats['assistant_messages']}")
                    if stats['agent_usage']:
                        print("   Agent Usage:")
                        for agent_name, count in stats['agent_usage'].items():
                            print(f"     - {agent_name}: {count} responses")
                    if stats['total_messages'] > 0:
                        print(f"\n📝 Recent Context (last 5 messages):")
                        recent_context = agent.conversation_history.get_recent_context(5)
                        print(recent_context)
                    continue
                
                if user_input.lower() == 'clear-history':
                    agent.clear_conversation_history()
                    # Also delete the saved file
                    agent.conversation_history.delete_saved_history()
                    print("🗑️  Conversation history cleared!")
                    continue
                
                if user_input.lower() == 'save':
                    print("💾 Saving conversation history...")
                    if agent.save_conversation_history():
                        print(f"✅ Saved {len(agent.conversation_history)} messages to disk")
                    else:
                        print("⚠️  Failed to save conversation history")
                    continue
                
                if not user_input:
                    print("⚠️  Please enter a message.")
                    continue
                
                print("🤔 Processing...")
                try:
                    response = agent.chat(user_input)
                    print(f"🤖 Assistant: {response}")
                except InputValidationException as e:
                    print(f"⚠️  Input validation error: {e}")
                except RateLimitException as e:
                    print(f"⏱️  {e}")
                
            except KeyboardInterrupt:
                print("\n")
                agent.shutdown()
                print("\n👋 Goodbye! Thanks for using the Chat Agent System!")
                break
            except Exception as e:
                print(f"❌ Error during chat: {e}")
                logger.error(f"Chat error: {e}")
    
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        logger.error(f"Initialization error: {e}")
        print("\n🔧 Please check your .env file configuration:")
        print("   - AZURE_OPENAI_ENDPOINT")
        print("   - AZURE_OPENAI_API_KEY") 
        print("   - AZURE_OPENAI_CHAT_DEPLOYMENT")
        return 1
    
    return 0

def save_chat_history_to_file(messages):
    """Save UI chat messages to data/chat_history.json"""
    import json
    from datetime import datetime
    import os
    
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

def save_chat_history_to_custom_file(messages, filename):
    """Save UI chat messages to saved/ directory with custom filename.
    
    DEPRECATED: This function is no longer used. The conversation history save method
    is now used exclusively for saving conversations to the saved/ directory.
    
    Args:
        messages: List of UI messages to save
        filename: Filename (without extension) to save as
        
    Returns:
        True if successful, False otherwise
    """
    import json
    from datetime import datetime
    import os
    
    try:
        os.makedirs("saved", exist_ok=True)
        
        # Add .json extension if not present
        if not filename.endswith('.json'):
            filename = f"{filename}.json"
        
        chat_data = {
            "saved_at": datetime.now().isoformat(),
            "messages": messages
        }
        
        filepath = os.path.join("saved", filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(chat_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved UI chat history to {filepath}")
        return True
    except Exception as e:
        logger.error(f"Error saving chat history to custom file: {e}")
        return False

def load_chat_history_from_file():
    """Load UI chat messages from data/chat_history.json"""
    import json
    import os
    
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
    """Get list of all saved conversations in reverse chronological order.
    
    Returns:
        List of tuples (filename_without_ext, full_path, modified_time)
    """
    import os
    import glob
    
    try:
        if not os.path.exists("saved"):
            return []
        
        # Get all json files in saved directory
        files = glob.glob("saved/*.json")
        
        # Get file info with modification time
        file_info = []
        for filepath in files:
            filename = os.path.basename(filepath)
            name_without_ext = os.path.splitext(filename)[0]
            mod_time = os.path.getmtime(filepath)
            file_info.append((name_without_ext, filepath, mod_time))
        
        # Sort by modification time, newest first
        file_info.sort(key=lambda x: x[2], reverse=True)
        
        return file_info
    except Exception as e:
        logger.error(f"Error getting saved conversations: {e}")
        return []

def load_saved_conversation(filepath: str, agent):
    """Load a saved conversation and restore it to the current session.
    
    Args:
        filepath: Path to the saved conversation JSON file
        agent: MasterAgent instance
    """
    import json
    
    try:
        logger.info(f"Loading conversation from {filepath}")
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Clear current history
        agent.conversation_history.messages.clear()
        
        messages = data.get("messages", [])
        logger.info(f"Found {len(messages)} messages in file")
        
        # Check if this is the UI chat format (simple role/content) or conversation history format (with timestamp)
        if messages and "timestamp" in messages[0]:
            # This is the full conversation history format
            logger.info("Loading full conversation history format (with timestamps)")
            from datetime import datetime
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
            # This is the simple UI chat format, rebuild conversation history
            logger.info("Loading simple UI chat format (no timestamps)")
            from datetime import datetime
            from modules.conversation_history import ChatMessage
            
            for msg_dict in messages:
                message = ChatMessage(
                    role=msg_dict["role"],
                    content=msg_dict["content"],
                    timestamp=datetime.now(),  # Use current time since we don't have the original
                    agent_type=msg_dict.get("agent_type"),
                    metadata=msg_dict.get("metadata")
                )
                agent.conversation_history.messages.append(message)
        
        # Build UI messages from conversation history
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
    """Generate a short, meaningful title for the chat using AI.
    
    Args:
        first_user_message: The first user message in the conversation
        agent: The MasterAgent instance to use for generation
        
    Returns:
        A short filename-safe title (2-4 words, max 40 chars)
    """
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

        title = agent.llm.invoke(prompt).content.strip()
        
        # Clean the title to be filename-safe
        import re
        # Remove quotes if present
        title = title.strip('"\'')
        # Remove special chars except spaces and hyphens
        title = re.sub(r'[^\w\s-]', '', title)
        # Replace multiple spaces with single space
        title = re.sub(r'\s+', ' ', title)
        # Limit to 40 chars
        title = title[:40]
        # Replace spaces with underscores for filename
        title = title.replace(' ', '_')
        
        return title if title else "untitled_conversation"
        
    except Exception as e:
        logger.error(f"Error generating chat title: {e}")
        from datetime import datetime
        return f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

def run_streamlit_mode():
    """Run the application in Streamlit UI mode."""
    # Check if we're actually running in Streamlit context
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        if get_script_run_ctx() is None:
            print("\n❌ Error: Streamlit mode requires running with 'streamlit run'")
            print("\n📝 To run in Streamlit mode, use one of these commands:")
            print("   ./run_streamlit.sh")
            print("   streamlit run main.py --server.port 8888")
            print("\n💡 Or use CLI mode instead:")
            print("   python main.py --cli")
            return
    except Exception:
        print("\n❌ Error: Cannot detect Streamlit runtime")
        print("\n📝 To run in Streamlit mode, use:")
        print("   streamlit run main.py --server.port 8888")
        print("\n💡 Or use CLI mode instead:")
        print("   python main.py --cli")
        return
    
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
            st.error("Please check your .env file configuration:")
            st.error("- AZURE_OPENAI_ENDPOINT")
            st.error("- AZURE_OPENAI_API_KEY")
            st.error("- AZURE_OPENAI_CHAT_DEPLOYMENT")
            st.session_state.initialized = False
            return
    
    if 'messages' not in st.session_state:
        # Load chat history from file if it exists
        st.session_state.messages = load_chat_history_from_file()
        logger.info(f"Initialized session with {len(st.session_state.messages)} messages from chat_history.json")
    
    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = True  # Start in dark mode
    
    if 'current_conversation_name' not in st.session_state:
        st.session_state.current_conversation_name = None  # Track currently loaded conversation
    
    if 'delete_confirm_chat' not in st.session_state:
        st.session_state.delete_confirm_chat = None  # Track chat pending deletion
    
    
    # Get theme background color
    bg_color = "#1e1e1e" if st.session_state.dark_mode else "#ffffff"
    text_color = "#ffffff" if st.session_state.dark_mode else "#000000"
    
    # Simple CSS for pills and sidebar spacing
    st.markdown("""
    <style>
        /* Minimize top padding in sidebar */
        section[data-testid="stSidebar"] > div:first-child {
            padding-top: 0.25rem !important;
        }
        
        /* Reduce sidebar padding and margins */
        section[data-testid="stSidebar"] > div {
            padding-top: 0.25rem !important;
            padding-bottom: 0.25rem !important;
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }
        
        /* Reduce spacing between sidebar elements */
        section[data-testid="stSidebar"] .element-container {
            margin-bottom: 0.1rem !important;
        }
        
        /* Reduce header spacing */
        section[data-testid="stSidebar"] h1, 
        section[data-testid="stSidebar"] h2, 
        section[data-testid="stSidebar"] h3 {
            margin-top: 0.25rem !important;
            margin-bottom: 0.25rem !important;
            padding-top: 0 !important;
        }
        
        /* Reduce button spacing in sidebar */
        section[data-testid="stSidebar"] button {
            margin-top: 0.1rem !important;
            margin-bottom: 0.1rem !important;
            padding: 0.25rem 0.5rem !important;
        }
        
        /* Reduce divider spacing */
        section[data-testid="stSidebar"] hr {
            margin-top: 0.25rem !important;
            margin-bottom: 0.25rem !important;
        }
        
        /* Reduce text element spacing */
        section[data-testid="stSidebar"] .stText {
            margin-bottom: 0.1rem !important;
            line-height: 1.3 !important;
        }
        
        /* Reduce block container spacing */
        section[data-testid="stSidebar"] .block-container {
            padding-top: 0.5rem !important;
        }
        
        /* Reduce main content title area padding and position */
        .main .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 1rem !important;
        }
        
        /* Reduce title/header spacing in main content */
        .main h1 {
            margin-top: 0 !important;
            margin-bottom: 0.25rem !important;
            padding-top: 0 !important;
            padding-bottom: 0 !important;
        }
        
        /* Reduce spacing after title */
        .main > div:first-child {
            margin-bottom: 0.25rem !important;
        }
        
        /* Reduce divider spacing in main content */
        .main hr {
            margin-top: 0.25rem !important;
            margin-bottom: 0.5rem !important;
        }
        
        /* Reduce element container spacing in main */
        .main .element-container {
            margin-bottom: 0.25rem !important;
        }
        
        /* Reduce padding and margins in chat message containers */
        .st-emotion-cache-16txtl3 {
            padding-top: 0.25rem !important;
            padding-bottom: 0.25rem !important;
            margin-top: 0.25rem !important;
            margin-bottom: 0.25rem !important;
            height: 100% !important;
        }
        
        /* Minimal pill button styling */
        div[data-testid="column"] button {
            border-radius: 14px !important;
            font-size: 14px !important;
            padding: 2px 8px !important;
            min-width: 40px !important;
            border: 2px solid transparent !important;
            transition: all 0.3s ease !important;
        }
        
        /* Primary (selected) pill */
        div[data-testid="column"] button[kind="primary"] {
            background-color: #0078d4 !important;
            color: white !important;
            box-shadow: 0 2px 6px rgba(0, 120, 212, 0.3) !important;
        }
        
        /* Secondary (unselected) pill */
        div[data-testid="column"] button[kind="secondary"] {
            background-color: rgba(128, 128, 128, 0.1) !important;
            color: rgba(128, 128, 128, 0.6) !important;
        }
        
        div[data-testid="column"] button[kind="secondary"]:hover {
            background-color: rgba(128, 128, 128, 0.2) !important;
            color: rgba(128, 128, 128, 0.8) !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Title and pills - simple layout, no sticky
    col1, col2, col3, col4 = st.columns([8, 1, 1, 2])
    with col1:
        st.markdown(f'<h2 style="margin: 0; padding: 0.5rem 0; font-size: 1.5rem; font-weight: 600; color: {text_color};">🤖 PCORNET Concept Set Tool</h2>', unsafe_allow_html=True)
    with col2:
        if st.button("☀️", key="light_pill", type="primary" if not st.session_state.dark_mode else "secondary"):
            st.session_state.dark_mode = False
            st.rerun()
    with col3:
        if st.button("🌙", key="dark_pill", type="primary" if not st.session_state.dark_mode else "secondary"):
            st.session_state.dark_mode = True
            st.rerun()
    with col4:
        st.write("")
    
    st.divider()
    
    # Sidebar with info and controls
    with st.sidebar:
        st.divider()
    
    # Apply theme based on dark_mode state (after toggle to get immediate update)
    if st.session_state.dark_mode:
        # Dark Mode Color Palette (based on VS Code Dark+)
        st.markdown("""
        <style>
            /* Dark mode - comprehensive styling */
            .stApp, [data-testid="stAppViewContainer"], 
            [data-testid="stHeader"], [data-testid="stToolbar"],
            main, .main {
                background-color: #1e1e1e !important;
                color: #d4d4d4 !important;
            }
            .stSidebar, [data-testid="stSidebar"],
            [data-testid="stSidebarNav"], section[data-testid="stSidebar"] > div {
                background-color: #252526 !important;
            }
            /* All background elements */
            div[data-testid="stVerticalBlock"],
            div[data-testid="stHorizontalBlock"] {
                background-color: transparent !important;
            }
            /* Text colors */
            .stMarkdown, .stText, p, span, div, label {
                color: #d4d4d4 !important;
            }
            /* Headers */
            h1, h2, h3, h4, h5, h6 {
                color: #ffffff !important;
            }
            /* Input fields */
            .stTextInput > div > div > input,
            .stTextArea textarea {
                background-color: #3c3c3c !important;
                color: #d4d4d4 !important;
                border: 1px solid #454545 !important;
            }
            .stTextInput > div > div > input:focus,
            .stTextArea textarea:focus {
                border-color: #007acc !important;
            }
            /* Chat input - comprehensive with unified container */
            .stChatInput, [data-testid="stChatInput"],
            .stChatInput > div, [data-testid="stChatInput"] > div,
            .stChatFloatingInputContainer {
                background-color: #3a3a3a !important;
            }
            /* Chat input floating container */
            .stChatInput, .stChatFloatingInputContainer {
                background-color: #3a3a3a !important;
                border-top: 2px solid #454545 !important;
                padding-top: 0.75rem !important;
                padding-bottom: 0.75rem !important;
                padding-left: 1rem !important;
                padding-right: 1rem !important;
            }
            .stChatInput > div > div > input,
            [data-testid="stChatInput"] input,
            .stChatInput textarea,
            [data-testid="stChatInput"] textarea {
                background-color: #3c3c3c !important;
                color: #d4d4d4 !important;
                border: 2px solid #ffffff !important;
            }
            .stChatInput > div > div > input::placeholder,
            [data-testid="stChatInput"] input::placeholder {
                color: #858585 !important;
            }
            /* Buttons */
            .stButton > button {
                background-color: #0e639c !important;
                color: #ffffff !important;
                border: 1px solid #007acc !important;
            }
            .stButton > button:hover {
                background-color: #1177bb !important;
                border-color: #1177bb !important;
            }
            /* Chat messages */
            .stChatMessage, [data-testid="stChatMessage"] {
                background-color: #2d2d30 !important;
                color: #d4d4d4 !important;
            }
            .stChatMessage p {
                color: #d4d4d4 !important;
            }
            /* Toggle switch */
            .stCheckbox, .stRadio, .stToggle {
                color: #d4d4d4 !important;
            }
            /* Dividers */
            hr {
                border-color: #454545 !important;
            }
            /* Success/Error messages */
            .stSuccess {
                background-color: #1e3a1e !important;
                color: #4ec9b0 !important;
            }
            .stError {
                background-color: #3a1e1e !important;
                color: #f48771 !important;
            }
            /* Tooltips - dark mode */
            [data-baseweb="tooltip"] {
                background-color: #3c3c3c !important;
                color: #d4d4d4 !important;
                border: 1px solid #454545 !important;
            }
        </style>
        """, unsafe_allow_html=True)
    else:
        # Light Mode Color Palette (based on VS Code Light+)
        st.markdown("""
        <style>
            /* Light mode - comprehensive styling */
            .stApp, [data-testid="stAppViewContainer"],
            [data-testid="stHeader"], [data-testid="stToolbar"],
            main, .main {
                background-color: #ffffff !important;
                color: #1e1e1e !important;
            }
            .stSidebar, [data-testid="stSidebar"],
            [data-testid="stSidebarNav"], section[data-testid="stSidebar"] > div {
                background-color: #f3f3f3 !important;
            }
            /* All background elements */
            div[data-testid="stVerticalBlock"],
            div[data-testid="stHorizontalBlock"] {
                background-color: transparent !important;
            }
            /* Text colors */
            .stMarkdown, .stText, p, span, div, label {
                color: #1e1e1e !important;
            }
            /* Headers */
            h1, h2, h3, h4, h5, h6 {
                color: #000000 !important;
            }
            /* Input fields */
            .stTextInput > div > div > input,
            .stTextArea textarea {
                background-color: #ffffff !important;
                color: #1e1e1e !important;
                border: 1px solid #e0e0e0 !important;
            }
            .stTextInput > div > div > input:focus,
            .stTextArea textarea:focus {
                border-color: #0078d4 !important;
            }
            /* Chat input - comprehensive with unified container */
            .stChatInput, [data-testid="stChatInput"],
            .stChatInput > div, [data-testid="stChatInput"] > div,
            .stChatFloatingInputContainer {
                background-color: #e8e8e8 !important;
            }
            /* Chat input floating container */
            .stChatInput, .stChatFloatingInputContainer {
                background-color: #e8e8e8 !important;
                border-top: 2px solid #e0e0e0 !important;
                padding-top: 0.75rem !important;
                padding-bottom: 0.75rem !important;
                padding-left: 1rem !important;
                padding-right: 1rem !important;
            }
            .stChatInput > div > div > input,
            [data-testid="stChatInput"] input,
            .stChatInput textarea,
            [data-testid="stChatInput"] textarea {
                background-color: #ffffff !important;
                color: #000000 !important;
                border: 2px solid #000000 !important;
            }
            .stChatInput > div > div > input::placeholder,
            [data-testid="stChatInput"] input::placeholder {
                color: #6c6c6c !important;
            }
            /* Ensure text input shows black text */
            input[type="text"], textarea {
                color: #000000 !important;
            }
            /* Buttons */
            .stButton > button {
                background-color: #0078d4 !important;
                color: #ffffff !important;
                border: 1px solid #0078d4 !important;
            }
            .stButton > button:hover {
                background-color: #106ebe !important;
                border-color: #106ebe !important;
            }
            /* Chat messages */
            .stChatMessage, [data-testid="stChatMessage"] {
                background-color: #f8f8f8 !important;
                color: #1e1e1e !important;
            }
            .stChatMessage p {
                color: #1e1e1e !important;
            }
            /* Toggle switch */
            .stCheckbox, .stRadio, .stToggle {
                color: #1e1e1e !important;
            }
            /* Dividers */
            hr {
                border-color: #e0e0e0 !important;
            }
            /* Success/Error messages */
            .stSuccess {
                background-color: #dff6dd !important;
                color: #0e6027 !important;
            }
            .stError {
                background-color: #fde7e9 !important;
                color: #a80000 !important;
            }
            /* Tooltips - light mode */
            [data-baseweb="tooltip"] {
                background-color: #ffffff !important;
                color: #000000 !important;
                border: 2px solid #000000 !important;
            }
        </style>
        """, unsafe_allow_html=True)
    
    # Initialize collapse state for system info and history stats
    if 'show_system_info' not in st.session_state:
        st.session_state.show_system_info = False  # Collapsed by default
    
    if 'show_history_stats' not in st.session_state:
        st.session_state.show_history_stats = False  # Collapsed by default
    
    # Continue with rest of sidebar content
    with st.sidebar:
        # System Info with collapse button
        col1, col2 = st.columns([4, 1])
        with col1:
            st.header("📊 System Info")
        with col2:
            if st.button("▼" if st.session_state.show_system_info else "▶", key="toggle_system_info"):
                st.session_state.show_system_info = not st.session_state.show_system_info
        
        if st.session_state.initialized and st.session_state.show_system_info:
            info = st.session_state.agent.get_info()
            st.text(f"🔗 Endpoint: {info['endpoint']}")
            st.text(f"🤖 Deployment: {info['deployment']}")
            st.text(f"📋 API Version: {info['api_version']}")
            
            if info['specialized_agents']:
                st.text(f"🎯 Agents: {', '.join(info['specialized_agents'])}")
        
        st.divider()
        
        # History stats with collapse button
        col1, col2 = st.columns([4, 1])
        with col1:
            st.header("💬 History Stats")
        with col2:
            if st.button("▼" if st.session_state.show_history_stats else "▶", key="toggle_history_stats"):
                st.session_state.show_history_stats = not st.session_state.show_history_stats
        
        if st.session_state.show_history_stats:
            history_info = st.session_state.agent.get_conversation_history()
            stats = history_info['stats']
            st.text(f"Total Messages: {stats['total_messages']}")
            st.text(f"User Messages: {stats['user_messages']}")
            st.text(f"Assistant Messages: {stats['assistant_messages']}")
        
        st.divider()
        
        # Control buttons
        st.header("🏛️ Controls")
        
        if st.button("🆕 New Chat", use_container_width=True, key="new_chat_btn", type="primary"):
            # Only process if we actually need to clear something
            has_messages = len(st.session_state.messages) > 0
            has_history = len(st.session_state.agent.conversation_history.messages) > 0
            
            if has_messages or has_history:
                # Save current conversation if there are messages
                if st.session_state.messages:
                    # Find the first user message
                    first_user_msg = None
                    for msg in st.session_state.messages:
                        if msg["role"] == "user":
                            first_user_msg = msg["content"]
                            break
                    
                    if first_user_msg:
                        # Use existing conversation name if available, otherwise generate new title
                        with st.spinner("Saving current chat..."):
                            if st.session_state.current_conversation_name:
                                # Reuse the existing conversation name
                                title = st.session_state.current_conversation_name
                                logger.info(f"Saving back to existing conversation: {title}")
                            else:
                                # Generate new title using AI
                                title = generate_chat_title(first_user_msg, st.session_state.agent)
                                logger.info(f"Generated new conversation title: {title}")
                        
                        # Save conversation history to saved/ directory with the title
                        # (This contains all message data including timestamps and metadata)
                        st.session_state.agent.conversation_history.save_to_custom_file(title)
                
                # Clear the agent's conversation history
                st.session_state.agent.clear_conversation_history()
                # Clear the UI messages
                st.session_state.messages = []
                st.session_state.current_conversation_name = None
                # Clear current session history file (data/chat_history.json)
                save_chat_history_to_file(st.session_state.messages)
                # Refresh the page to update stats
                st.rerun()
        
        st.divider()
        
        # Previous Chats Section
        st.header("💬 Previous Chats")
        
        # Get all saved conversations
        saved_convos = get_saved_conversations()
        
        if saved_convos:
            # Create a scrollable container
            st.markdown("""
            <style>
                .chat-list {
                    max-height: 400px;
                    overflow-y: auto;
                }
            </style>
            """, unsafe_allow_html=True)
            
            # Display each saved conversation as a button with delete option
            for name, filepath, _ in saved_convos:
                # Replace underscores with spaces for display
                display_name = name.replace('_', ' ')
                
                # Create columns for chat button and delete button
                col1, col2 = st.columns([5, 1])
                
                with col1:
                    chat_clicked = st.button(f"📄 {display_name}", use_container_width=True, key=f"load_{name}")
                
                with col2:
                    delete_clicked = st.button("🗑️", key=f"delete_{name}", help="Delete this conversation")
                
                # Handle delete button
                if delete_clicked:
                    st.session_state.delete_confirm_chat = (name, filepath, display_name)
                
                # Handle chat button
                if chat_clicked:
                    # Check if we're clicking the same conversation that's already loaded
                    if st.session_state.current_conversation_name != name:
                        # Save current chat before loading new one
                        if st.session_state.messages:
                            first_user_msg = None
                            for msg in st.session_state.messages:
                                if msg["role"] == "user":
                                    first_user_msg = msg["content"]
                                    break
                            
                            if first_user_msg:
                                with st.spinner("💾 Saving current chat..."):
                                    # Use existing conversation name if available, otherwise generate new title
                                    if st.session_state.current_conversation_name:
                                        # Reuse the existing conversation name
                                        title = st.session_state.current_conversation_name
                                        logger.info(f"Saving back to existing conversation: {title}")
                                    else:
                                        # Generate new title using AI
                                        title = generate_chat_title(first_user_msg, st.session_state.agent)
                                        logger.info(f"Generated new conversation title: {title}")
                                    
                                    # Save conversation history with the title
                                    # (This contains all message data including timestamps and metadata)
                                    st.session_state.agent.conversation_history.save_to_custom_file(title)
                        
                        # Load the selected conversation
                        with st.spinner(f"📂 Loading {display_name}..."):
                            ui_messages = load_saved_conversation(filepath, st.session_state.agent)
                            
                            if ui_messages:
                                st.session_state.messages = ui_messages
                                st.session_state.current_conversation_name = name  # Track what we loaded
                                # Save loaded chat to current history files
                                save_chat_history_to_file(st.session_state.messages)
                                st.session_state.agent.save_conversation_history()
                                logger.info(f"Loaded {len(ui_messages)} messages from {filepath}")
                            else:
                                st.error("Failed to load conversation")
                                logger.error(f"No messages loaded from {filepath}")
                        
                        st.rerun()
        else:
            st.info("No saved conversations yet. Start chatting to create one!")
    
    # Show delete confirmation dialog if a chat is pending deletion
    if st.session_state.delete_confirm_chat:
        name, filepath, display_name = st.session_state.delete_confirm_chat
        
        st.divider()
        st.markdown("### ⚠️ Confirm Deletion")
        st.write(f"Are you sure you want to delete **{display_name}**?")
        st.write("This action cannot be undone.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Yes, Delete", use_container_width=True, type="primary", key="confirm_delete"):
                import os
                try:
                    # Delete the file
                    os.remove(filepath)
                    logger.info(f"Deleted conversation: {filepath}")
                    
                    # If this was the currently loaded conversation, clear it
                    if st.session_state.current_conversation_name == name:
                        st.session_state.current_conversation_name = None
                        st.session_state.messages = []
                        st.session_state.agent.clear_conversation_history()
                        save_chat_history_to_file(st.session_state.messages)
                    
                    # Clear the delete confirmation
                    st.session_state.delete_confirm_chat = None
                except Exception as e:
                    st.error(f"❌ Failed to delete: {e}")
                    logger.error(f"Error deleting {filepath}: {e}")
                    st.session_state.delete_confirm_chat = None
        
        with col2:
            if st.button("❌ No, Cancel", use_container_width=True, key="cancel_delete"):
                st.session_state.delete_confirm_chat = None
        
        st.divider()
        # Stop rendering the rest while showing confirmation
        return
    
    # Main chat area
    if not st.session_state.initialized:
        return
    
    # Display chat messages
    logger.info(f"Displaying {len(st.session_state.messages)} messages")
    for idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Keep current_conversation_name to save back to the same conversation
        
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("🤔 Processing..."):
                try:
                    response = st.session_state.agent.chat(prompt)
                    st.markdown(response)
                    
                    # Add assistant message to chat
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                    # Auto-save conversation history to data/conversation_history.json
                    st.session_state.agent.save_conversation_history()
                    
                    # Auto-save chat history to data/chat_history.json
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

def main():
    """Main function to run the Azure OpenAI Chat Agent System."""
    # Parse command-line arguments
    args = parse_arguments()
    
    if args.cli:
        # Run in CLI mode
        return run_cli_mode(verbose=args.verbose)
    else:
        # Run in Streamlit mode
        run_streamlit_mode()
        return 0

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
