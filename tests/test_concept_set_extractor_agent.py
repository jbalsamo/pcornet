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
    input_data = json.dumps([
        {
            "document": {
                "code": "E11.9",
                "label": "Type 2 diabetes mellitus without complications"
            },
            "@search.score": 0.95
        },
        {
            "document": {
                "code": "E10.9",
                "label": "Type 1 diabetes mellitus without complications"
            },
            "@search.score": 0.92
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
    assert "search.score" not in result  # Should not include search score

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
    Tests robustness against missing 'document', 'code', or 'label' keys.
    """
    input_data = json.dumps([
        {
            "document": {
                "code": "E11.9"
                # Missing 'label'
            }
        },
        {
            # Missing 'document'
            "code": "E10.9",
            "label": "Type 1 diabetes"
        }
    ])

    result = agent.process(input_data)
    assert isinstance(result, str)
    assert "Code: E11.9, Label: N/A" in result
    # The second entry should be gracefully ignored or handled
    assert "E10.9" not in result # Or assert it's handled as N/A depending on implementation
