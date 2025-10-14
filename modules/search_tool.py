"""Azure Cognitive Search hybrid search helper.

This module provides a Search class that performs a hybrid search (vector + semantic +
keyword) against an Azure Cognitive Search index. It reads necessary configuration from
environment variables (via `modules/config.py`) and will call Azure OpenAI to produce an
embedding for the query if an embedding vector is not supplied.

Environment variables used (set in .env):
- AZURE_SEARCH_ENDPOINT: your search service endpoint (required)
- AZURE_SEARCH_API_KEY: admin or query API key for the search service (required)
- AZURE_SEARCH_API_VERSION: API version for search (optional, default: 2023-07-01-Preview)
- AZURE_SEARCH_VECTOR_FIELD: name of the vector field in your index (optional, default: 'vector')
- AZURE_SEARCH_SEARCH_FIELDS: comma-separated search fields for keyword search (optional)
- AZURE_OPENAI_EMBEDDING_DEPLOYMENT: deployment name for embeddings (optional)

Usage:
    from modules.search_tool import Search
    s = Search(index=AZURE_SEARCH_INDEX, query="find documents about X")
    results = s.run()

The returned value is a list of hits with `score`, `document`, and optional `highlights`.
"""

from __future__ import annotations

import os
import json
import logging
from typing import Any, Dict, List, Optional

from .config import config as openai_config

logger = logging.getLogger(__name__)

try:
    from azure.core.credentials import AzureKeyCredential
    from azure.search.documents import SearchClient
    from azure.search.documents.models import Vector
    from azure.ai.openai import OpenAIClient
except Exception as e:  # pragma: no cover - import errors are surfaced at runtime
    # Defer the import error to runtime usage to keep module import time flexible in tests
    AzureKeyCredential = None
    SearchClient = None
    Vector = None
    OpenAIClient = None


class SearchError(Exception):
    pass


class Search:
    """Perform a hybrid search (vector + semantic + keyword) on an Azure Cognitive Search index.

    Inputs/outputs (contract):
    - input: index (str), query (str)
    - optional inputs: top (int), embedding (List[float])
    - output: List[Dict] where each dict contains at least `score` and `document` keys.

    Error modes: raises SearchError for configuration or HTTP errors.
    """

    def __init__(
        self,
        index: str,
        query: str,
        *,
        top: int = 20,
        embedding: Optional[List[float]] = None,
        semantic_config: Optional[str] = None,
        search_fields: Optional[List[str]] = None,
        vector_field: Optional[str] = None,
    ) -> None:
        self.index = index
        self.query = query
        self.top = int(top)
        self._embedding = embedding
        self.semantic_config = semantic_config

        # Load Azure Cognitive Search config from environment
        self.search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        self.search_api_key = os.getenv("AZURE_SEARCH_API_KEY")
        self.search_api_version = os.getenv("AZURE_SEARCH_API_VERSION", "2023-07-01-Preview")
        self.vector_field = vector_field or os.getenv("AZURE_SEARCH_VECTOR_FIELD", "vector")

        # Optionally override search fields passed directly or from env
        env_search_fields = os.getenv("AZURE_SEARCH_SEARCH_FIELDS")
        if search_fields:
            self.search_fields = search_fields
        elif env_search_fields:
            self.search_fields = [f.strip() for f in env_search_fields.split(",") if f.strip()]
        else:
            self.search_fields = None

        # OpenAI embedding deployment (optional) - will use Azure OpenAI config if set
        self.embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")

        self._validate_config()

    def _validate_config(self) -> None:
        if not self.search_endpoint:
            raise SearchError("AZURE_SEARCH_ENDPOINT is required in environment or .env")
        if not self.search_api_key:
            raise SearchError("AZURE_SEARCH_API_KEY is required in environment or .env")

    def _get_embedding(self, text: str) -> List[float]:
        """Obtain embedding vector for `text` using Azure OpenAI embeddings endpoint.

        Requires `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` to be set in env, and `modules/config.config`
        to provide Azure OpenAI endpoint and api key. Raises SearchError if embeddings cannot be
        produced.
        """
        deployment = self.embedding_deployment or os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
        if not deployment:
            raise SearchError(
                "Embedding deployment not configured. Set AZURE_OPENAI_EMBEDDING_DEPLOYMENT in .env "
                "or provide an `embedding` directly to Search()."
            )

        # Use openai_config for endpoint and key
        aoai_endpoint = getattr(openai_config, "endpoint", None)
        aoai_key = getattr(openai_config, "api_key", None)

        if not aoai_endpoint or not aoai_key:
            raise SearchError("Azure OpenAI endpoint and api key must be present to create embeddings")

        if OpenAIClient is None:
            raise SearchError("azure-ai-openai SDK is not installed; cannot create embeddings")

        try:
            client = OpenAIClient(aoai_endpoint, credential=aoai_key)
            resp = client.get_embeddings(deployment_id=deployment, input=text)
            embedding = resp.data[0].embedding
            return embedding
        except Exception as e:
            logger.exception("Failed to create embedding via SDK")
            raise SearchError(f"Failed to create embedding via SDK: {e}") from e

    def _build_search_body(self, embedding: List[float]) -> Dict[str, Any]:
        """Construct the request body for the hybrid search call."""
        body: Dict[str, Any] = {}

        # Vector (k nearest neighbors)
        if embedding is not None:
            body["vector"] = {"value": embedding, "fields": self.vector_field, "k": self.top}

        # Query text (keyword/semantic)
        # When using semantic ranking, set queryType to 'semantic' and provide semantic config
        if self.semantic_config:
            body["queryType"] = "semantic"
            body["semantic"] = {"configuration": self.semantic_config}

        # Provide the query string - used for keyword match and semantic ranking
        body["query"] = self.query
        body["top"] = self.top

        if self.search_fields:
            body["searchFields"] = ",".join(self.search_fields)

        return body

    def run(self) -> List[Dict[str, Any]]:
        """Execute the hybrid search and return a list of hits.

        Each hit is a dict with keys: `score`, `document` (dict), and optionally `highlights`.
        """
        embedding = self._embedding

    # Skip embedding generation if your index already contains vectors
    # and we only need keyword + semantic search
    if embedding is None:
        logger.info("Skipping embedding generation (using built-in semantic + keyword search only)")
        embedding = []  # Empty list signals no vector needed

        if SearchClient is None or AzureKeyCredential is None:
            raise SearchError("azure-search-documents SDK is not installed; cannot run search")

        try:
            credential = AzureKeyCredential(self.search_api_key)
            client = SearchClient(endpoint=self.search_endpoint, index_name=self.index, credential=credential)

            # Use vector search via 'vector' parameter if supported
            vect = Vector(value=embedding, fields=self.vector_field, k=self.top)

            # Build search parameters
            search_text = self.query
            search_kwargs = {"top": self.top}
            if self.search_fields:
                search_kwargs["search_fields"] = self.search_fields
            if self.semantic_config:
                search_kwargs["query_type"] = "semantic"
                search_kwargs["semantic_configuration_name"] = self.semantic_config

            results = client.search(search_text, vector=vect, **search_kwargs)

            hits: List[Dict[str, Any]] = []
            for r in results:
                # results items may be dict-like or objects; try dict access first
                score = None
                if isinstance(r, dict):
                    score = r.get("@search.score") or r.get("@search_score") or r.get("score")
                else:
                    score = getattr(r, "@search_score", None) or getattr(r, "score", None) or getattr(r, "@search.score", None)

                # Document content is available via mapping or object interface
                try:
                    document = dict(r)
                except Exception:
                    # fallback: try to build dict from attributes
                    document = {k: getattr(r, k) for k in dir(r) if not k.startswith("_")}
                hit = {"score": score, "document": document}
                # Highlights may be provided in r['@search.highlights'] depending on SDK
                if "@search.highlights" in r:
                    hit["highlights"] = r["@search.highlights"]
                hits.append(hit)

            return hits
        except Exception as e:
            logger.exception("Search SDK call failed: %s", e)
            raise SearchError(f"Search SDK call failed: {e}") from e


__all__ = ["Search", "SearchError"]
