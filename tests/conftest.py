"""
Pytest configuration and shared fixtures.
"""
import pytest
import os
from unittest.mock import Mock, MagicMock


def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests that don't require external services")
    config.addinivalue_line("markers", "integration: Integration tests that require Azure services")
    config.addinivalue_line("markers", "requires_azure: Tests that require Azure credentials")


@pytest.fixture
def mock_azure_openai_config():
    """Mock Azure OpenAI configuration for testing."""
    os.environ['AZURE_OPENAI_ENDPOINT'] = 'https://test.openai.azure.com/'
    os.environ['AZURE_OPENAI_API_KEY'] = 'test-api-key'
    os.environ['AZURE_OPENAI_CHAT_DEPLOYMENT'] = 'gpt-4o'
    os.environ['AZURE_OPENAI_API_VERSION'] = '2024-02-15-preview'
    os.environ['AZURE_AI_SEARCH_ENDPOINT'] = 'https://test.search.windows.net'
    os.environ['AZURE_AI_SEARCH_API_KEY'] = 'test-search-key'
    os.environ['AZURE_SEARCH_INDEX_NAME'] = 'test-index'
    yield
    # Cleanup
    for key in ['AZURE_OPENAI_ENDPOINT', 'AZURE_OPENAI_API_KEY', 
                'AZURE_OPENAI_CHAT_DEPLOYMENT', 'AZURE_OPENAI_API_VERSION',
                'AZURE_AI_SEARCH_ENDPOINT', 'AZURE_AI_SEARCH_API_KEY', 'AZURE_SEARCH_INDEX_NAME']:
        os.environ.pop(key, None)


@pytest.fixture
def check_azure_credentials():
    """Check if Azure credentials are configured."""
    required_vars = [
        'AZURE_OPENAI_ENDPOINT',
        'AZURE_OPENAI_API_KEY',
        'AZURE_AI_SEARCH_ENDPOINT',
        'AZURE_AI_SEARCH_KEY'
    ]
    
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        pytest.skip(f"Azure credentials not configured. Missing: {', '.join(missing)}")
    
    return True


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing."""
    mock_response = Mock()
    mock_response.content = "This is a test response from the AI assistant."
    return mock_response


@pytest.fixture
def sample_conversation_messages():
    """Sample conversation messages for testing."""
    return [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there! How can I help you?"},
        {"role": "user", "content": "What's the weather like?"},
        {"role": "assistant", "content": "I don't have access to weather data."}
    ]


@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary data directory for testing."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir
