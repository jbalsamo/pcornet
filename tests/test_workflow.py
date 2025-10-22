"""Test concept set workflow functionality."""
import pytest
from modules.master_agent import MasterAgent


@pytest.mark.integration
def test_concept_set_workflow(check_azure_credentials):
    """Test that the master agent can process concept set queries."""
    # Initialize the master agent
    master_agent = MasterAgent()
    
    # Test the concept set workflow
    query = "create a concept set for diabetes"
    
    # This should trigger the concept set workflow
    response = master_agent.chat(query)
    
    # Assertions
    assert isinstance(response, str), "Response should be a string"
    assert len(response) > 0, "Response should not be empty"
    
    # Check for rate limiting or auth errors (common when running full test suite)
    if "401" in response or "rate limit" in response.lower():
        pytest.skip("API rate limit exceeded or authentication error - skip test")
    
    assert "diabetes" in response.lower() or "E11" in response or "E10" in response, \
        "Response should contain diabetes-related content"