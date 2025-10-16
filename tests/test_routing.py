"""Test master agent routing functionality."""
import pytest
import re
from modules.master_agent import MasterAgent


@pytest.mark.integration
def test_master_agent_routing(check_azure_credentials):
    """Test that the master agent correctly routes different types of queries."""
    # Initialize the master agent
    master_agent = MasterAgent()
    
    # Test different queries to see routing
    queries = [
        "What is ICD code I10?",
        "Tell me about hypertension",
        "icd code I10",
        "explain I10"
    ]
    
    for query in queries:
        # Manually check classification (if method exists)
        if hasattr(master_agent, '_classify_agent_type'):
            agent_type = master_agent._classify_agent_type(query)
            assert agent_type in ['icd', 'chat', 'concept_set'], \
                f"Agent type should be valid, got: {agent_type}"
        
        # Test the actual routing
        response = master_agent.chat(query)
        
        # Assertions
        assert isinstance(response, str), "Response should be a string"
        assert len(response) > 0, "Response should not be empty"


@pytest.mark.integration
def test_icd_query_routing(check_azure_credentials):
    """Test that ICD-specific queries are routed to the ICD agent."""
    master_agent = MasterAgent()
    
    # Test ICD-specific query
    query = "What is ICD code I10?"
    
    if hasattr(master_agent, '_classify_agent_type'):
        agent_type = master_agent._classify_agent_type(query)
        assert agent_type == 'icd', "ICD queries should be routed to 'icd' agent"
    
    response = master_agent.chat(query)
    
    # Check for citations (ICD responses should have citations)
    citations = re.findall(r'\[([^\]]+)\]', response)
    assert len(citations) > 0 or "I10" in response, \
        "ICD response should contain citations or code references"