"""
A specialized agent for querying the PCORnet ICD index in Azure AI Search.

This module defines the IcdAgent, which is responsible for searching an Azure
AI Search index containing International Classification of Diseases (ICD) codes.
It uses an LLM to process search results and generate responses with proper
citations referencing the document IDs where information was found.
"""

# modules/agents/icd_agent.py
import os
import json
import logging
import re
from modules.search_tool import Search, SearchError
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)

class IcdAgent:
    """
    An agent that queries an Azure AI Search index for ICD code information.

    This agent uses the `Search` helper to connect to a specified Azure AI
    Search endpoint and index to perform searches for ICD codes. It processes
    the results using an LLM and generates responses with proper citations
    referencing the document IDs where information was found.
    """

    def __init__(self, index="pcornet-icd-index"):
        """
        Initializes the IcdAgent.
        
        Args:
            index (str): The name of the search index to query.
        """
        self.index_name = index
        self.last_retrieved_documents = []
        
        # Initialize LLM client
        try:
            self.llm = self._create_llm()
            logger.info("✅ IcdAgent initialized with LLM")
        except Exception as e:
            logger.error(f"Failed to initialize IcdAgent LLM: {e}")
            raise e

    def _create_llm(self):
        """Creates and returns an LLM client for processing search results."""
        from modules.config import get_config
        config = get_config()
        
        return AzureChatOpenAI(
            deployment_name=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
            temperature=config.agent_temperature,
            max_tokens=1000,
            azure_endpoint=config.azure_openai_endpoint,
            api_version=config.azure_openai_api_version,
            openai_api_key=config.azure_openai_api_key
        )

    def process(self, query: str) -> str:
        """
        Performs a hybrid search in the ICD index and processes results with LLM.

        This method searches for ICD codes, processes the results with an LLM to
        generate a comprehensive response, and includes proper citations referencing
        the document IDs where information was found.

        Args:
            query (str): The search query from the user.

        Returns:
            str: A processed response with citations, or error message if search fails.
        """
        # Check for predefined concept sets first
        if "heart disease concept set" in query.lower():
            return self._get_heart_disease_concept_set()
            
        try:
            search = Search(
                index=self.index_name,
                query=query,
                top=10,
                semantic_config="defaultSemanticConfig"
            )
            results = search.run()
            self.last_retrieved_documents = results

            if not results:
                return "No ICD codes found for your query."

            # Generate LLM response with search context
            response = self._generate_llm_response(query, results)
            
            # Post-process to normalize citations
            response = self._normalize_citations(response, results)
            
            return response

        except SearchError as e:
            logger.exception("ICD search failed")
            return f"Search operation failed: {e}"
        except Exception as e:
            logger.exception("ICD processing failed")
            return f"An error occurred: {e}"

    def process_with_history(self, query: str, history) -> str:
        """
        Process a query with conversation history context.
        
        Args:
            query (str): The user's query.
            history: Conversation history object with get_langchain_messages() method.
            
        Returns:
            str: Processed response with citations.
        """
        # Check for predefined concept sets first
        if "heart disease concept set" in query.lower():
            return self._get_heart_disease_concept_set()
            
        try:
            search = Search(
                index=self.index_name,
                query=query,
                top=10,
                semantic_config="defaultSemanticConfig"
            )
            results = search.run()
            self.last_retrieved_documents = results

            if not results:
                return "No ICD codes found for your query."

            # Generate response with history context
            response = self._generate_llm_response_with_history(query, results, history)
            
            # Post-process to normalize citations
            response = self._normalize_citations(response, results)
            
            return response

        except SearchError as e:
            logger.exception("ICD search failed")
            return f"Search operation failed: {e}"
        except Exception as e:
            logger.exception("ICD processing failed")
            return f"An error occurred: {e}"
