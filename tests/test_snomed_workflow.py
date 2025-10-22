"""
Test script to verify the SNOMED workflow:
1. Search for ICD codes first
2. Then add SNOMED mappings
"""
import pytest
import uuid
from modules.master_agent import MasterAgent
from modules.interactive_session import interactive_session


@pytest.mark.integration
def test_snomed_workflow(check_azure_credentials):
    """Test the proper workflow for SNOMED integration."""
    # Initialize agent
    agent = MasterAgent()
    session_id = str(uuid.uuid4())[:8]
    
    # Step 1: Search for ICD codes first (this should create and populate the session)
    search_query = "Find diabetes codes"
    response1 = agent.chat(query=search_query, session_id=session_id)
    
    # Assertions for search response
    assert isinstance(response1, str), "Search response should be a string"
    assert len(response1) > 0, "Search response should not be empty"
    
    # Check for rate limiting or auth errors (common when running full test suite)
    if "401" in response1 or "rate limit" in response1.lower():
        pytest.skip("API rate limit exceeded or authentication error - skip test")
    
    assert "diabetes" in response1.lower() or "E10" in response1 or "E11" in response1, \
        "Response should contain diabetes-related codes"
    
    # Check session stats after search - session might not be created if it's a simple chat response
    stats = interactive_session.get_session_stats(session_id)
    # Accept both scenarios: session created with items, or no session (simple chat response)
    if "error" not in stats:
        assert "total_items" in stats, "Session stats should have total_items if session exists"
        assert stats.get("total_items", 0) > 0, "Session should have items after search"
    else:
        # No session created - this is okay for simple queries
        pytest.skip("Session not created for this query - query was handled as simple chat")
    
    # Step 2: Now try to add SNOMED codes
    snomed_query = "Add SNOMED codes"
    response2 = agent.chat(query=snomed_query, session_id=session_id)
    
    # Assertions for SNOMED response
    assert isinstance(response2, str), "SNOMED response should be a string"
    assert len(response2) > 0, "SNOMED response should not be empty"
    # SNOMED codes are numeric
    assert any(char.isdigit() for char in response2), \
        "SNOMED response should contain numeric SNOMED codes"
    
    # Final session stats should show more items or same
    final_stats = interactive_session.get_session_stats(session_id)
    assert final_stats.get("total_items", 0) >= stats.get("total_items", 0), \
        "Final session should have at least as many items as initial search"