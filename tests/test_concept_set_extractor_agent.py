"""
Tests for the ConceptSetExtractorAgent.
"""
import json
import pytest
from modules.agents.concept_set_extractor_agent import ConceptSetExtractorAgent

@pytest.fixture
def agent():
    """Fixture to create a ConceptSetExtractorAgent instance."""
    return ConceptSetExtractorAgent()

def test_process_valid_json(agent):
    """
    Tests if the agent can correctly process a valid JSON string
    and extract the relevant information.
    """
    # Sample JSON input mimicking the output from IcdAgent
    # Note: Azure Search uses uppercase field names CODE and STR
    input_data = json.dumps([
        {
            "document": {
                "CODE": "E11.9",
                "STR": "Type 2 diabetes mellitus without complications"
            },
            "score": 0.95
        },
        {
            "document": {
                "CODE": "E10.9",
                "STR": "Type 1 diabetes mellitus without complications"
            },
            "score": 0.92
        }
    ])

    # Process the data
    result = agent.process(input_data)

    # Assertions
    assert isinstance(result, str)
    assert "E11.9" in result
    assert "Type 2 diabetes mellitus without complications" in result
    assert "E10.9" in result
    assert "Type 1 diabetes mellitus without complications" in result

def test_process_invalid_json(agent):
    """
    Tests the agent's behavior when provided with an invalid JSON string.
    It should return an error dictionary.
    """
    input_data = "this is not a valid json string"

    # Process the data
    result = agent.process(input_data)

    # Assertions
    assert isinstance(result, dict)
    assert "error" in result
    assert "Failed to decode JSON" in result["error"]

def test_process_empty_json_array(agent):
    """
    Tests the agent's behavior with an empty JSON array.
    It should indicate that no concepts were found.
    """
    input_data = "[]"

    # Process the data
    result = agent.process(input_data)

    # Assertions
    assert isinstance(result, str)
    assert "No concepts found" in result

def test_process_json_with_missing_keys(agent):
    """
    Tests robustness against missing 'document', 'CODE', or 'STR' keys.
    """
    input_data = json.dumps([
        {
            "document": {
                "CODE": "E11.9"
                # Missing 'STR' (label)
            }
        },
        {
            # Missing 'document' - should show as N/A
            "CODE": "E10.9",
            "STR": "Type 1 diabetes"
        }
    ])

    result = agent.process(input_data)
    assert isinstance(result, str)
    assert "Code: E11.9, Label: N/A" in result
    # The second entry should be gracefully handled with N/A since document is missing
    assert "Code: N/A, Label: N/A" in result
