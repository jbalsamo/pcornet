"""Tests for the Search helper in modules/search_tool.py

This test mocks HTTP calls for embeddings (Azure OpenAI) and the Azure Cognitive
Search "search" API to validate the hybrid search flow. We import `Search` inside
the test after required env vars are set by the `mock_azure_openai_config` fixture.
"""
import os
import json

import pytest


def _mock_sdk_clients(monkeypatch):
    """Mock OpenAIClient and SearchClient SDK classes used by Search."""

    class DummyEmbedding:
        def __init__(self, embedding):
            self.data = [type("E", (), {"embedding": embedding})]

    class FakeOpenAIClient:
        def __init__(self, endpoint, credential=None):
            pass

        def get_embeddings(self, deployment_id, input):
            return DummyEmbedding([0.1, 0.2, 0.3])

    class FakeSearchResult(dict):
        pass

    class FakeSearchResults(list):
        def __iter__(self):
            return super().__iter__()

    class FakeSearchClient:
        def __init__(self, endpoint, index_name=None, credential=None):
            pass

        def search(self, search_text, vector=None, **kwargs):
            # Return an iterable of fake results
            r = FakeSearchResult({"@search.score": 0.92, "id": "doc1", "title": "Heart Disease", "content": "Description of heart disease."})
            return FakeSearchResults([r])

    monkeypatch.setattr("modules.search_tool.OpenAIClient", FakeOpenAIClient)
    monkeypatch.setattr("modules.search_tool.SearchClient", FakeSearchClient)
    monkeypatch.setattr("modules.search_tool.AzureKeyCredential", lambda key: key)
    # Provide a simple Vector factory if SDK is not installed
    monkeypatch.setattr("modules.search_tool.Vector", lambda value, fields, k: {"value": value, "fields": fields, "k": k})


def test_search_hybrid_returns_hits(mock_azure_openai_config, monkeypatch):
    """Test that Search.run returns hits for the pcornet_icd_index using hybrid search."""
    # Set search service env vars (mock values)
    os.environ["AZURE_SEARCH_ENDPOINT"] = "https://test-search.search.windows.net"
    os.environ["AZURE_SEARCH_API_KEY"] = "test-search-key"
    os.environ["AZURE_SEARCH_API_VERSION"] = "2023-07-01-Preview"
    os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"] = "embedding-deploy"

    # Patch SDK clients for embeddings and search
    _mock_sdk_clients(monkeypatch)

    # Import Search after env vars are set
    from modules.search_tool import Search

    s = Search(index="pcornet_icd_index", query="heart disease", top=3)
    results = s.run()

    assert isinstance(results, list)
    assert len(results) == 1

    hit = results[0]
    assert hit["score"] == 0.92
    assert hit["document"]["title"] == "Heart Disease"
    assert "Description of heart disease." in hit["document"]["content"]
