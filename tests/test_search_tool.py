"""Tests for the Search helper in modules/search_tool.py

This test mocks HTTP calls for embeddings (Azure OpenAI) and the Azure Cognitive
Search "search" API to validate the hybrid search flow. We import `Search` inside
the test after required env vars are set by the `mock_azure_openai_config` fixture.
"""
import os
import json

import pytest


def _mock_sdk_clients(monkeypatch):
    """Mock AzureOpenAI and SearchClient SDK classes used by Search."""

    class DummyEmbeddingData:
        def __init__(self, embedding):
            self.embedding = embedding

    class DummyEmbeddingResponse:
        def __init__(self, embedding):
            self.data = [DummyEmbeddingData(embedding)]

    class FakeAzureOpenAI:
        def __init__(self, **kwargs):
            pass

        class Embeddings:
            @staticmethod
            def create(model, input):
                return DummyEmbeddingResponse([0.1, 0.2, 0.3])
        
        embeddings = Embeddings()

    class FakeSearchResult(dict):
        pass

    class FakeSearchResults(list):
        def __iter__(self):
            return super().__iter__()

    class FakeSearchClient:
        def __init__(self, endpoint, index_name=None, credential=None):
            pass

        def search(self, search_text, vector_queries=None, **kwargs):
            # Return an iterable of fake results
            r = FakeSearchResult({"@search.score": 0.92, "id": "doc1", "title": "Heart Disease", "content": "Description of heart disease."})
            return FakeSearchResults([r])

    # Mock create_openai_client to return our fake client (at both locations for robustness)
    fake_client = FakeAzureOpenAI()
    monkeypatch.setattr("modules.config.create_openai_client", lambda: fake_client)
    monkeypatch.setattr("modules.search_tool.create_openai_client", lambda: fake_client)
    monkeypatch.setattr("modules.search_tool.SearchClient", FakeSearchClient)
    monkeypatch.setattr("modules.search_tool.AzureKeyCredential", lambda key: key)
    # Provide a simple VectorizedQuery factory
    monkeypatch.setattr("modules.search_tool.VectorizedQuery", lambda vector, fields, k_nearest_neighbors: {"vector": vector, "fields": fields, "k_nearest_neighbors": k_nearest_neighbors})


@pytest.mark.unit
def test_search_hybrid_returns_hits(mock_azure_openai_config, monkeypatch):
    """Test that Search.run returns hits for the pcornet_icd_index using hybrid search."""
    # Override/set additional search service env vars (mock values)
    # The fixture already sets some, but we need to ensure these specific ones
    monkeypatch.setenv("AZURE_AI_SEARCH_ENDPOINT", "https://test-search.search.windows.net")
    monkeypatch.setenv("AZURE_AI_SEARCH_API_KEY", "test-search-key")
    monkeypatch.setenv("AZURE_SEARCH_API_VERSION", "2023-07-01-Preview")
    monkeypatch.setenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "embedding-deploy")

    # Force reload of config to pick up new env vars
    import importlib
    import modules.config
    importlib.reload(modules.config)

    # Patch SDK clients for embeddings and search AFTER config reload
    _mock_sdk_clients(monkeypatch)

    # Import Search after env vars are set and config reloaded
    from modules.search_tool import Search

    s = Search(index="pcornet_icd_index", query="heart disease", top=3)
    results = s.run()

    assert isinstance(results, list)
    assert len(results) == 1

    hit = results[0]
    assert hit["score"] == 0.92
    assert hit["document"]["title"] == "Heart Disease"
    assert "Description of heart disease." in hit["document"]["content"]
