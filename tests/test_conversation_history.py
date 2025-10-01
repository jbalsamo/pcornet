"""
Tests for the ConversationHistory module.
"""
import pytest
import os
from datetime import datetime
from modules.conversation_history import ConversationHistory, ChatMessage

def test_conversation_history_initialization(temp_data_dir):
    """Test conversation history initialization."""
    storage_file = temp_data_dir / "test_history.json"
    history = ConversationHistory(max_messages=10, storage_file=str(storage_file))
    
    assert history.max_messages == 10
    assert len(history) == 0
    assert history.storage_file == str(storage_file)

def test_add_user_message(temp_data_dir):
    """Test adding user messages."""
    storage_file = temp_data_dir / "test_history.json"
    history = ConversationHistory(storage_file=str(storage_file))
    
    history.add_user_message("Hello, assistant!")
    
    assert len(history) == 1
    assert history.messages[0].role == "user"
    assert history.messages[0].content == "Hello, assistant!"

def test_add_assistant_message(temp_data_dir):
    """Test adding assistant messages."""
    storage_file = temp_data_dir / "test_history.json"
    history = ConversationHistory(storage_file=str(storage_file))
    
    history.add_assistant_message("Hello, user!", agent_type="chat")
    
    assert len(history) == 1
    assert history.messages[0].role == "assistant"
    assert history.messages[0].agent_type == "chat"

def test_rolling_window(temp_data_dir):
    """Test rolling window behavior."""
    storage_file = temp_data_dir / "test_history.json"
    history = ConversationHistory(max_messages=3, storage_file=str(storage_file))
    
    # Add more messages than max
    for i in range(5):
        history.add_user_message(f"Message {i}")
    
    # Should only keep last 3
    assert len(history) == 3
    assert history.messages[0].content == "Message 2"
    assert history.messages[-1].content == "Message 4"

def test_get_stats(temp_data_dir):
    """Test statistics generation."""
    storage_file = temp_data_dir / "test_history.json"
    history = ConversationHistory(storage_file=str(storage_file))
    
    history.add_user_message("Hello")
    history.add_assistant_message("Hi", agent_type="chat")
    history.add_user_message("How are you?")
    
    stats = history.get_stats()
    
    assert stats['total_messages'] == 3
    assert stats['user_messages'] == 2
    assert stats['assistant_messages'] == 1
    assert 'chat' in stats['agent_usage']

def test_clear_history(temp_data_dir):
    """Test clearing history."""
    storage_file = temp_data_dir / "test_history.json"
    history = ConversationHistory(storage_file=str(storage_file))
    
    history.add_user_message("Test message")
    assert len(history) == 1
    
    history.clear_history()
    assert len(history) == 0

def test_save_and_load(temp_data_dir):
    """Test saving and loading conversation history."""
    storage_file = temp_data_dir / "test_history.json"
    
    # Create and populate history
    history1 = ConversationHistory(storage_file=str(storage_file))
    history1.add_user_message("Hello")
    history1.add_assistant_message("Hi there", agent_type="chat")
    
    # Save to disk
    assert history1.save_to_disk() == True
    
    # Load in new instance
    history2 = ConversationHistory(storage_file=str(storage_file))
    assert history2.load_from_disk() == True
    
    # Verify loaded data
    assert len(history2) == 2
    assert history2.messages[0].content == "Hello"
    assert history2.messages[1].content == "Hi there"
    assert history2.messages[1].agent_type == "chat"

def test_get_recent_context(temp_data_dir):
    """Test getting recent conversation context."""
    storage_file = temp_data_dir / "test_history.json"
    history = ConversationHistory(storage_file=str(storage_file))
    
    history.add_user_message("First message")
    history.add_assistant_message("First response", agent_type="chat")
    
    context = history.get_recent_context(num_messages=2)
    
    assert "First message" in context
    assert "First response" in context
    assert "User:" in context
    assert "Assistant" in context
