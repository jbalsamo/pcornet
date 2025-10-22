"""Test direct ICD code searches."""
import pytest
import re
from modules.master_agent import MasterAgent

@pytest.mark.integration
def test_direct_icd_search(check_azure_credentials):
    """Test that direct ICD code queries work correctly."""
    # Initialize the master agent
    master_agent = MasterAgent()
    
    # Test direct ICD query
    query = "What is ICD code I10?"
    
    # This should go directly to ICD agent
    response = master_agent.chat(query)
    
    # Assertions
    assert isinstance(response, str), "Response should be a string"
    assert len(response) > 0, "Response should not be empty"
    assert "I10" in response or "hypertension" in response.lower(), \
        "Response should mention I10 or hypertension"
    
    # Check for citations in brackets
    citations = re.findall(r'\[([^\]]+)\]', response)
    # ICD responses should have citations
    assert len(citations) > 0 or "No ICD codes found" in response, \
        "Response should contain citations or indicate no codes found"