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
    
    # Header
    st.title("🤖 PCORNET Concept Set Tool")
    
    # Sidebar with info and controls
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
            st.header("🎛️ Controls")
            
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
    chat_container = st.container()
    with chat_container:
        for idx, message in enumerate(st.session_state.messages):
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                # Add copy button for assistant messages
                if message["role"] == "assistant":
                    # Use a unique key based on message index
                    if st.button(f"📋 Copy", key=f"copy_msg_{idx}"):
                        pyperclip.copy(message["content"])
                        st.success("Copied to clipboard!", icon="✅")
    
    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get assistant response
        with st.chat_message("assistant"):
            with st.spinner("🤔 Processing..."):
                try:
                    response = st.session_state.agent.chat(prompt)
                    st.markdown(response)
                    
                    # Add assistant message to chat
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                except InputValidationException as e:
                    error_msg = f"⚠️ Input validation error: {e}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                    
                except RateLimitException as e:
                    error_msg = f"⏱️ {e}"
                    st.warning(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                    
                except Exception as e:
                    error_msg = f"❌ Error: {e}"
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
