"""
Main application entry point for the Azure OpenAI Chat Agent System.
"""
import logging
import argparse
import streamlit as st
import json
import os
import glob
from datetime import datetime
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
    
    if 'show_system_info' not in st.session_state:
        st.session_state.show_system_info = False
    
    if 'show_history_stats' not in st.session_state:
        st.session_state.show_history_stats = False
    
    if 'show_memory_stats' not in st.session_state:
        st.session_state.show_memory_stats = False
    
    # Initialize session_id for interactive sessions (persistent per Streamlit session)
    if 'interactive_session_id' not in st.session_state:
        import uuid
        st.session_state.interactive_session_id = f"streamlit_{uuid.uuid4().hex[:8]}"
        logger.info(f"Created new interactive session ID: {st.session_state.interactive_session_id}")
    
    # Title
    st.title("🤖 PCORNET Concept Set Tool")
    st.divider()
    
    # Sidebar with full functionality
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
        
        # Memory stats with collapse button
        col1, col2 = st.columns([4, 1])
        with col1:
            st.header("🧠 Memory Stats")
        with col2:
            if st.button("▼" if st.session_state.show_memory_stats else "▶", key="toggle_memory_stats"):
                st.session_state.show_memory_stats = not st.session_state.show_memory_stats
        
        if st.session_state.show_memory_stats:
            try:
                memory_stats = st.session_state.agent.get_memory_stats()
                
                episodic = memory_stats.get('episodic_memory', {})
                st.text(f"Past Conversations: {episodic.get('total_episodes', 0)}")
                
                semantic = memory_stats.get('semantic_memory', {})
                st.text(f"Facts Learned: {semantic.get('total_facts', 0)}")
                
                st.text(f"Auto-Extract: {'✓' if memory_stats.get('auto_fact_extraction', False) else '✗'}")
            except Exception as e:
                st.warning("Memory stats unavailable (first run)")
        
        st.divider()
        
        # Control buttons
        st.header("🏛️ Controls")
        
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
        st.header("💬 Previous Chats")
        
        saved_convos = get_saved_conversations()
        
        if saved_convos:
            for name, filepath, _ in saved_convos:
                display_name = name.replace('_', ' ')
                
                col1, col2 = st.columns([5, 1])
                
                with col1:
                    chat_clicked = st.button(f"📄 {display_name}", use_container_width=True, key=f"load_{name}")
                
                with col2:
                    delete_clicked = st.button("🗑️", key=f"delete_{name}", help="Delete this conversation")
                
                if delete_clicked:
                    st.session_state.delete_confirm_chat = (name, filepath, display_name)
                
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
                try:
                    os.remove(filepath)
                    logger.info(f"Deleted conversation: {filepath}")
                    
                    if st.session_state.current_conversation_name == name:
                        st.session_state.current_conversation_name = None
                        st.session_state.messages = []
                        st.session_state.agent.clear_conversation_history()
                        save_chat_history_to_file(st.session_state.messages)
                    
                    st.session_state.delete_confirm_chat = None
                except Exception as e:
                    st.error(f"❌ Failed to delete: {e}")
                    st.session_state.delete_confirm_chat = None
        
        with col2:
            if st.button("❌ No, Cancel", use_container_width=True, key="cancel_delete"):
                st.session_state.delete_confirm_chat = None
        
        st.divider()
        return
    
    # Main chat area
    if not st.session_state.initialized:
        return
    
    # Display chat messages
    logger.info(f"Displaying {len(st.session_state.messages)} messages")
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
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
