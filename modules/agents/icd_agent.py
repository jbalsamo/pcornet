# modules/agents/icd_agent.py
import os
import logging
import requests

logger = logging.getLogger(__name__)

class IcdAgent:
    """
    ICD Agent to query the PCORnet ICD index in Azure Search and return JSON results.
    """

    def __init__(self):
        self.endpoint = os.getenv("AZURE_AI_SEARCH_ENDPOINT")
        self.index_name = os.getenv("AZURE_AI_SEARCH_INDEX", "pcornet-icd-index")
        self.api_key = os.getenv("AZURE_AI_SEARCH_API_KEY")
        self.api_version = os.getenv("AZURE_SEARCH_API_VERSION", "2023-07-01-Preview")

        if not all([self.endpoint, self.api_key]):
            raise ValueError("AZURE_AI_SEARCH_ENDPOINT and AZURE_AI_SEARCH_API_KEY must be set in .env")

        self.search_url = f"{self.endpoint}/indexes/{self.index_name}/docs/search?api-version={self.api_version}"

    def process(self, query: str) -> dict:
        """
        Perform a hybrid search in the ICD index for the query.

        Returns:
            dict: {
                "results": [ { "label": ..., "code": ..., "caption": ..., "REL": ... }, ... ],
                "answers": [ semantic answers if any ],
                "error": optional error message
            }
        """
        try:
            headers = {
                "Content-Type": "application/json",
                "api-key": self.api_key
            }

            payload = {
                "search": query,
                "queryType": "semantic",      # semantic + vector search
                "queryLanguage": "en-us",
                "semanticConfiguration": "defaultSemanticConfig",
                "top": 50                     # limit results
            }

            response = requests.post(self.search_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()

            results = []
            for doc in data.get("value", []):
                results.append({
                    "label": doc.get("STR"),
                    "code": doc.get("CODE"),
                    "caption": doc.get("DEF"),
                    "REL": doc.get("REL", [])
                })

            semantic_answers = data.get("@search.answers", [])

            return {
                "results": results,
                "answers": semantic_answers
            }

        except requests.exceptions.RequestException as e:
            logger.exception("ICD search request failed")
            return {"error": f"Network error: {e}"}
        except Exception as e:
            logger.exception("ICD processing failed")
            return {"error": str(e)}
