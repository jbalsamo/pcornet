"""Test Azure Search index connectivity and structure."""
import pytest
import os
import json

# Try to import azure packages, skip test if not available
try:
    from azure.core.credentials import AzureKeyCredential
    from azure.search.documents.indexes import SearchIndexClient
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False


@pytest.mark.integration
@pytest.mark.skipif(not AZURE_AVAILABLE, reason="Azure SDK not installed")
def test_search_index_connection():
    """Test that we can connect to and retrieve the Azure Search index."""
    endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    key = os.getenv("AZURE_SEARCH_API_KEY")
    index_name = os.getenv("AZURE_SEARCH_INDEX_NAME", "pcornet-icd-index")
    
    # Skip test if credentials not available
    if not endpoint or not key:
        pytest.skip("Azure Search credentials not configured")
    
    # Create client and get index
    client = SearchIndexClient(endpoint=endpoint, credential=AzureKeyCredential(key))
    index = client.get_index(index_name)
    
    # Assertions
    assert index is not None, "Index should exist"
    assert index.name == index_name, f"Index name should be {index_name}"
    
    # Verify index has fields
    index_dict = index.as_dict()
    assert "fields" in index_dict, "Index should have fields defined"
    assert len(index_dict["fields"]) > 0, "Index should have at least one field"
