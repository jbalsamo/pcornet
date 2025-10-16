"""
ChatGPT-style conversational interface for PCORnet GPT application.

This script provides a clean, conversational chat interface similar to ChatGPT
where users can naturally ask for ICD codes, SNOMED mappings, and interact
with the data through pure text conversations without any buttons.

Features:
- Pure conversational interface (no buttons)
- Interactive session management
- Dynamic data modification through natural language
- Clean chat history display
- Minimal, focused design

To run the application:
    streamlit run main.py
"""

# main.py
import os
import uuid
import streamlit as st
from datetime import datetime
from modules.master_agent import MasterAgent
from modules.interactive_session import interactive_session

def display_message(role, content, timestamp=None):
    """Display a chat message with appropriate styling."""
    if role == "user":
        with st.chat_message("user"):
            st.markdown(content)
    else:
        with st.chat_message("assistant"):
            st.markdown(content)

def main():
    """
    ChatGPT-style conversational interface for PCORnet.
    """
    st.set_page_config(
        page_title="PCORnet Assistant", 
        layout="centered",
        initial_sidebar_state="expanded"
    )

    # Initialize session state
    if "agent" not in st.session_state:
        st.session_state.agent = MasterAgent()

    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())[:8]
        
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Header
    st.title("🏥 PCORnet Assistant")
    st.caption("Ask me about ICD codes, SNOMED mappings, medical coding, and more...")

    # Welcome message for new sessions
    if not st.session_state.messages:
        welcome_message = """
Hello! I'm your PCORnet medical coding assistant. I can help you with:

• **Search for ICD codes** - "Find diabetes codes" or "Show me heart failure codes"
• **Get SNOMED mappings** - "Add SNOMED codes" or "What's the SNOMED for I10?"
• **Explore relationships** - "Show parent codes" or "Find related codes"
• **Format data** - "Show as table" or "Export as JSON"
• **Modify results** - "Remove E11" or "Only show primary codes"

Just ask me anything in natural language!
        """
        
        with st.chat_message("assistant"):
            st.markdown(welcome_message.strip())

    # Display chat history
    for message in st.session_state.messages:
        display_message(message["role"], message["content"])

    # Chat input
    if prompt := st.chat_input("Ask about ICD codes, SNOMED mappings, or medical coding..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        display_message("user", prompt)

        # Get response from agent
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = st.session_state.agent.chat(
                        query=prompt, 
                        session_id=st.session_state.session_id
                    )
                    
                    st.markdown(response)
                    
                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                    # Also maintain the older chat history format for compatibility
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    st.session_state.chat_history.append((timestamp, prompt, response))
                    
                    # Limit history to prevent memory issues
                    if len(st.session_state.messages) > 20:
                        st.session_state.messages = st.session_state.messages[-20:]
                    
                    if len(st.session_state.chat_history) > 10:
                        st.session_state.chat_history = st.session_state.chat_history[-10:]
                        
                except Exception as e:
                    error_msg = f"I apologize, but I encountered an error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

    # Sidebar with conversation history
    with st.sidebar:
        st.header("Session")
        st.text(f"ID: {st.session_state.session_id}")
        
        # Get session stats if available
        session_stats = interactive_session.get_session_stats(st.session_state.session_id)
        if "error" not in session_stats and session_stats.get("total_items", 0) > 0:
            st.metric("Data Items", session_stats.get("total_items", 0))
        
        st.markdown("---")
        
        # Conversation History
        col_header, col_clear = st.columns([3, 1])
        with col_header:
            st.header("History")
        with col_clear:
            if st.session_state.chat_history and st.button("Clear All", key="clear_all_history", help="Remove all conversations"):
                st.session_state.chat_history = []
                st.rerun()
        
        if st.session_state.chat_history:
            for i, (timestamp, question, answer) in enumerate(reversed(st.session_state.chat_history)):
                # Calculate the actual index in the original list
                actual_index = len(st.session_state.chat_history) - 1 - i
                
                col1, col2 = st.columns([5, 1])
                
                with col1:
                    with st.expander(f"{timestamp} - {question[:40]}...", expanded=False):
                        st.markdown(f"**Q:** {question}")
                        st.markdown(f"**A:** {answer}")
                
                with col2:
                    if st.button("🗑️", key=f"delete_history_{actual_index}", help="Remove this conversation"):
                        # Remove the conversation at the actual index
                        st.session_state.chat_history.pop(actual_index)
                        st.rerun()
        else:
            st.markdown("*No conversations yet*")
        
        st.markdown("---")
        
        if st.button("New Session", use_container_width=True):
            st.session_state.session_id = str(uuid.uuid4())[:8]
            st.session_state.messages = []
            st.session_state.chat_history = []
            interactive_session.clear_session(st.session_state.session_id)
            st.rerun()
            
        # Export function (only show if there's data)
        if session_stats.get("total_items", 0) > 0:
            st.markdown("---")
            if st.button("Export Data", use_container_width=True):
                json_data = interactive_session.format_data_as_json(st.session_state.session_id)
                st.download_button(
                    label="Download JSON",
                    data=json_data,
                    file_name=f"pcornet_data_{st.session_state.session_id}.json",
                    mime="application/json",
                    use_container_width=True
                )

    # Example prompts (subtle, at bottom)
    if not st.session_state.messages:
        st.markdown("---")
        st.markdown("**Example questions to try:**")
        st.markdown("• *Find ICD codes for diabetes*")
        st.markdown("• *What is the SNOMED mapping for I10?*")
        st.markdown("• *Show me heart disease codes and add SNOMED codes*")
        st.markdown("• *Create a concept set for hypertension*")

if __name__ == "__main__":
    main()
