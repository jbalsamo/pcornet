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
        st.session_state.messages = []
    
    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = True  # Start in dark mode
    
    # Get theme background color
    bg_color = "#1e1e1e" if st.session_state.dark_mode else "#ffffff"
    text_color = "#ffffff" if st.session_state.dark_mode else "#000000"
    
    # Simple CSS for pills
    st.markdown("""
    <style>
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
    
    # Continue with rest of sidebar content
    with st.sidebar:
        st.header("📊 System Info")
        
        if st.session_state.initialized:
            info = st.session_state.agent.get_info()
            st.text(f"🔗 Endpoint: {info['endpoint']}")
            st.text(f"🤖 Deployment: {info['deployment']}")
            st.text(f"📋 API Version: {info['api_version']}")
            
            if info['specialized_agents']:
                st.text(f"🎯 Agents: {', '.join(info['specialized_agents'])}")
            
            st.divider()
            
            # History stats
            st.header("💬 History Stats")
            history_info = st.session_state.agent.get_conversation_history()
            stats = history_info['stats']
            st.text(f"Total Messages: {stats['total_messages']}")
            st.text(f"User Messages: {stats['user_messages']}")
            st.text(f"Assistant Messages: {stats['assistant_messages']}")
            
            st.divider()
            
            # Control buttons
            st.header("🏛️ Controls")
            
            if st.button("🗑️ Clear Chat", use_container_width=True, key="clear_chat_btn"):
                # Reset messages to empty list (fresh state)
                st.session_state.messages = []
            
            if st.button("💾 Save History", use_container_width=True, key="save_history_btn"):
                if st.session_state.agent.save_conversation_history():
                    st.success(f"Saved {len(st.session_state.agent.conversation_history)} messages")
                else:
                    st.error("Failed to save history")
    
    # Main chat area
    if not st.session_state.initialized:
        return
    
    # Display chat messages
    for idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Type your message here..."):
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
