# Tests

This directory contains tests for the Chat Agent System.

## Running Tests

### Run all tests
```bash
pytest
```

### Run with verbose output
```bash
pytest -v
```

### Run specific test file
```bash
pytest tests/test_conversation_history.py
```

### Run with coverage
```bash
pytest --cov=modules --cov-report=html
```

## Test Structure

- **conftest.py** - Shared fixtures and test configuration
- **test_*.py** - All pytest test files (19 test modules)
- **manual_debug_*.py** - Standalone debug scripts (not run by pytest)

## Adding New Tests

When adding new modules, create corresponding test files:

1. Create `test_<module_name>.py` in this directory
2. Import the module to test
3. Write test functions starting with `test_`
4. Use fixtures from `conftest.py` as needed

Example:
```python
def test_my_feature(mock_azure_openai_config):
    # Your test here
    assert True
```
