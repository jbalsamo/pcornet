"""
Tests for the configuration module.
"""
import pytest
import os
from modules.config import AzureOpenAIConfig

def test_config_initialization(mock_azure_openai_config):
    """Test configuration initialization with valid environment variables."""
    config = AzureOpenAIConfig()
    
    assert config.endpoint == 'https://test.openai.azure.com/'
    assert config.api_key == 'test-api-key'
    assert config.chat_deployment == 'gpt-4o'
    assert config.api_version == '2024-02-15-preview'

def test_config_validation_missing_endpoint():
    """Test configuration validation when endpoint is missing."""
    # Clear the endpoint
    os.environ.pop('AZURE_OPENAI_ENDPOINT', None)
    os.environ['AZURE_OPENAI_API_KEY'] = 'test-key'
    os.environ['AZURE_OPENAI_CHAT_DEPLOYMENT'] = 'gpt-4o'
    
    with pytest.raises(ValueError, match="AZURE_OPENAI_ENDPOINT is required"):
        AzureOpenAIConfig()
    
    # Cleanup
    os.environ.pop('AZURE_OPENAI_API_KEY', None)
    os.environ.pop('AZURE_OPENAI_CHAT_DEPLOYMENT', None)

def test_get_azure_openai_kwargs(mock_azure_openai_config):
    """Test getting Azure OpenAI kwargs."""
    config = AzureOpenAIConfig()
    kwargs = config.get_azure_openai_kwargs()
    
    assert 'azure_endpoint' in kwargs
    assert 'api_key' in kwargs
    assert 'api_version' in kwargs
    assert 'azure_deployment' in kwargs
    assert kwargs['azure_endpoint'] == 'https://test.openai.azure.com/'

def test_config_defaults(mock_azure_openai_config):
    """Test configuration defaults when no custom values are set."""
    # Ensure no custom values are set
    os.environ.pop('AGENT_TEMPERATURE', None)
    os.environ.pop('REQUEST_TIMEOUT', None)
    os.environ.pop('MAX_RETRIES', None)
    os.environ.pop('MAX_CONVERSATION_MESSAGES', None)
    
    config = AzureOpenAIConfig()
    
    assert config.agent_temperature == 1.0
    assert config.request_timeout == 30
    assert config.max_retries == 3
    assert config.max_conversation_messages == 20

def test_config_custom_values():
    """Test configuration with custom values."""
    os.environ['AZURE_OPENAI_ENDPOINT'] = 'https://test.openai.azure.com/'
    os.environ['AZURE_OPENAI_API_KEY'] = 'test-key'
    os.environ['AZURE_OPENAI_CHAT_DEPLOYMENT'] = 'gpt-4o'
    os.environ['AGENT_TEMPERATURE'] = '0.5'
    os.environ['MAX_CONVERSATION_MESSAGES'] = '50'
    
    config = AzureOpenAIConfig()
    
    assert config.agent_temperature == 0.5
    assert config.max_conversation_messages == 50
    
    # Cleanup
    for key in ['AZURE_OPENAI_ENDPOINT', 'AZURE_OPENAI_API_KEY', 
                'AZURE_OPENAI_CHAT_DEPLOYMENT', 'AGENT_TEMPERATURE', 
                'MAX_CONVERSATION_MESSAGES']:
        os.environ.pop(key, None)
