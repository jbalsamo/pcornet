"""Test citation functionality in concept set queries."""
import pytest
import re
from modules.master_agent import MasterAgent


@pytest.mark.integration
def test_citation_in_concept_set(check_azure_credentials):
    """Test that concept set responses include proper citations."""
    # Initialize the master agent
    master_agent = MasterAgent()
    
    # Test the concept set workflow
    query = "create a concept set for hypertension"
    
    # This should trigger the concept set workflow
    response = master_agent.chat(query)
    
    # Assertions
    assert isinstance(response, str), "Response should be a string"
    assert len(response) > 0, "Response should not be empty"
    
    # Check for citations in brackets
    citations = re.findall(r'\[([^\]]+)\]', response)
    assert len(citations) > 0, "Response should contain citations in brackets [CODE]"
    
    # Check for hypertension-related content
    assert "hypertension" in response.lower() or "I10" in response or "I11" in response, \
        "Response should contain hypertension-related codes"