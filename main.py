"""
Main application entry point for the Azure OpenAI Chat Agent System.
"""
import logging
import argparse
from modules.master_agent import MasterAgent
from modules.security import InputValidationException, RateLimitException

logger = logging.getLogger(__name__)

def setup_logging(verbose: bool = False):
    """Set up logging configuration based on verbose flag.
    
    Args:
        verbose: If True, show INFO level logs. If False, show WARNING and above only.
    """
    log_level = logging.INFO if verbose else logging.WARNING
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        force=True  # Force reconfiguration if already configured
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
  %(prog)s              # Run in quiet mode
  %(prog)s -v           # Run with verbose logging
  %(prog)s --verbose    # Run with verbose logging (long form)

Available commands during chat:
  status         - Show system status
  history        - Show conversation history stats
  clear-history  - Clear conversation history
  help           - Show help message
  quit/exit/bye  - Exit the system
        """
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging (show INFO level logs)'
    )
    return parser.parse_args()

def main():
    """Main function to run the Azure OpenAI Chat Agent System."""
    # Parse command-line arguments
    args = parse_arguments()
    
    # Set up logging based on verbose flag
    setup_logging(verbose=args.verbose)
    
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

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
