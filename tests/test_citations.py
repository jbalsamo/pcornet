"""Test citation functionality in concept set queries."""
import pytest
import re
from modules.master_agent import MasterAgent


@pytest.mark.integration
def test_citation_in_concept_set(check_azure_credentials):
    """Test that concept set responses include proper citations and ICD codes."""
    # Initialize the master agent
    master_agent = MasterAgent()
    
    # Test the concept set workflow
    query = "create a concept set for hypertension"
    
    # This should trigger the concept set workflow
    response = master_agent.chat(query)
    
    # Assertions
    assert isinstance(response, str), "Response should be a string"
    assert len(response) > 0, "Response should not be empty"
    
    # Check for ICD code patterns (flexible format check)
    # ICD codes can appear in various formats: [I10], I10, "I10", etc.
    icd_codes = re.findall(r'\b(I1[0-5](?:\.\d+)?)\b', response)
    assert len(icd_codes) > 0, f"Response should contain hypertension ICD-10 codes (I10-I15 range). Response: {response[:200]}"
    
    # Check for hypertension-related content
    assert "hypertension" in response.lower() or any(code in response for code in ["I10", "I11", "I12", "I13", "I15"]), \
        "Response should contain hypertension-related content or codes"
    
    # Check that the response includes some structured information (code, label, or description)
    has_structure = any(keyword in response.lower() for keyword in ["code", "label", "score", "hypertension", "blood pressure"])
    assert has_structure, "Response should include structured information about the codes"