"""
The MasterAgent orchestrates interactions between different specialized agents.

This module defines the MasterAgent class, which acts as a router to delegate
user queries to the appropriate agent, such as the ChatAgent for general
conversation or the IcdAgent for specific ICD code lookups. It initializes
all available agents and provides a unified entry point for processing chat
requests.
"""

import os
import logging
import json
from typing import TypedDict
from modules.agents.chat_agent import ChatAgent
from modules.agents.icd_agent import IcdAgent
from modules.agents.concept_set_extractor_agent import ConceptSetExtractorAgent
from modules.interactive_session import interactive_session
from openai import AzureOpenAI
from modules.config import CONCEPT_SET_CLASSIFICATION_PROMPT

logger = logging.getLogger(__name__)


class MasterAgentState(TypedDict):
    """State definition for the master agent."""
    user_input: str
    agent_type: str
    context: str
    response: str
    error: str

class MasterAgent:
    """
    A central agent that routes user queries to specialized sub-agents.

    The MasterAgent initializes and manages a collection of agents (e.g.,
    ChatAgent, IcdAgent). It determines the appropriate agent to handle a
    given query based on the `agent_type` parameter and formats the response
    accordingly.
    """

    def __init__(self):
        """
        Initializes the MasterAgent and all its sub-agents.

        This constructor sets up the ChatAgent and IcdAgent, logging the
        successful initialization of each. It also performs a quick validation
        of the Azure OpenAI client configuration to ensure connectivity.

        Raises:
            Exception: If any of the agents fail to initialize.
        """
        try:
            # Initialize Agents
            self.chat_agent = ChatAgent()
            self.icd_agent = IcdAgent()
            self.concept_set_extractor_agent = ConceptSetExtractorAgent()
            logger.info("✅ All agents initialized successfully")

        except Exception as e:
            logger.exception("Failed to initialize agents")
            raise e

        # Quick validation of Azure OpenAI deployment
        try:
            self.client = AzureOpenAI(
                api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            )
            logger.info("✅ AzureOpenAI client initialized for MasterAgent")
        except Exception as e:
            logger.exception("Failed to initialize AzureOpenAI client")
            raise e

    def _is_concept_set_query(self, query: str) -> bool:
        """
        Uses an LLM to classify if the user's query is about a concept set.
        """
        try:
            prompt = CONCEPT_SET_CLASSIFICATION_PROMPT.format(query=query)
            response = self.client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=5,
                temperature=0.0,
            )
            is_concept_set = response.choices[0].message.content.strip().lower()
            logger.info(f"Concept set classification for '{query}': {is_concept_set}")
            return "true" in is_concept_set
        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
            return False

    def _classify_agent_type(self, query: str) -> str:
        """
        Classifies the query to determine the appropriate agent type.
        """
        query_lower = query.lower()
        
        # Check for ICD-related keywords
        icd_keywords = [
            "icd", "icd-10", "icd10", "i10", "i11", "i20", "i21", "i50",
            "code i", "diagnosis code", "medical code", "billing code"
        ]
        
        # Check if query contains specific ICD patterns
        import re
        icd_pattern = r'\b[a-z]\d{2}(?:\.\d+)?\b'  # Matches ICD patterns like I10, E11.9, etc.
        
        if any(keyword in query_lower for keyword in icd_keywords) or re.search(icd_pattern, query_lower):
            logger.info(f"ICD query detected: '{query}' -> routing to 'icd' agent")
            return "icd"
        
        # Default to chat agent
        logger.info(f"General query detected: '{query}' -> routing to 'chat' agent")
        return "chat"

    def chat(self, query: str, agent_type: str = "auto", session_id: str = "default"):
        """
        Processes a chat query by routing it to the specified agent or workflow.
        Enhanced with interactive session support.
        """
        # Auto-detect agent type if not specified
        if agent_type == "auto":
            agent_type = self._classify_agent_type(query)
        
        # Check if this is an interactive modification request
        if interactive_session.is_modification_request(query):
            logger.info(f"Interactive modification request detected: '{query}'")
            if agent_type == "icd" or self._has_active_session(session_id):
                return self.icd_agent.process_interactive(query, session_id)
            else:
                return "No active session found. Please start with a search query first, then I can help you modify the results."
        
        # Initialize state
        state = MasterAgentState(user_input=query, agent_type=agent_type, context="", response="", error="")

        # Step 1: Classify user intent
        if self._is_concept_set_query(query):
            logger.info("Concept set query detected. Starting concept set workflow.")
            return self._concept_set_workflow(state)

        # Enhanced routing with session support
        logger.info(f"Standard query detected. Routing to '{agent_type}' agent.")
        if agent_type == "chat":
            return self.chat_agent.process(query)
        elif agent_type == "icd":
            # Use interactive processing for ICD queries
            return self._chat_icd_interactive(query, session_id)
        else:
            return f"❌ Unknown agent type: {agent_type}"
    
    def _has_active_session(self, session_id: str) -> bool:
        """Check if there's an active session with data."""
        context = interactive_session.get_current_context()
        return context is not None and len(context.current_data) > 0
    
    def _chat_icd_interactive(self, query: str, session_id: str):
        """
        Enhanced ICD query handling with interactive session support.
        """
        try:
            # Use interactive processing
            result = self.icd_agent.process_interactive(query, session_id)
            
            if "error" in result:
                return result["error"]

            # Return the processed response with session context
            processed_response = result.get("processed_response", "")
            if processed_response:
                return processed_response
            
            # Fallback to regular processing if no interactive response
            return self._chat_icd(query)
            
        except Exception as e:
            logger.exception("Interactive ICD chat failed")
            return f"An error occurred: {e}"

    def _concept_set_workflow(self, state: MasterAgentState) -> str:
        """
        Executes the multi-step workflow for creating a concept set.
        """
        # Step 1: Call IcdAgent to get data
        logger.info("Workflow Step 1: Calling IcdAgent")
        icd_result = self.icd_agent.process(state["user_input"])
        if "error" in icd_result:
            return f"Error during ICD search: {icd_result['error']}"
        
        # Step 2: Update context in state
        # ConceptSetExtractorAgent expects raw JSON data, not processed response
        state["context"] = icd_result.get("data", "")
        logger.info("Workflow Step 2: Context updated with ICD data.")

        # Step 3: Call ConceptSetExtractorAgent to process the context
        logger.info("Workflow Step 3: Calling ConceptSetExtractorAgent")
        extracted_data = self.concept_set_extractor_agent.process(state["context"])
        if "error" in extracted_data:
             return f"Error during data extraction: {extracted_data['error']}"

        # Step 4: Call ChatAgent to format the final response
        logger.info("Workflow Step 4: Calling ChatAgent for final formatting.")
        final_response = self.chat_agent.format_concept_set(
            original_query=state["user_input"],
            context_data=extracted_data
        )
        
        return final_response

    def _chat_icd(self, query: str):
        """
        Handles a simple, direct ICD query using the IcdAgent.
        """
        try:
            data = self.icd_agent.process(query)
            if "error" in data:
                return data["error"]

            # For direct ICD queries, return the processed response with citations
            processed_response = data.get("processed_response", "")
            if processed_response:
                return processed_response
            
            # Fallback to formatted raw data if no processed response
            raw_results = json.loads(data.get("data", "[]"))
            
            output_lines = ["ICD Search Results:"]
            for r in raw_results:
                label = r.get("document", {}).get("STR", "N/A")
                code = r.get("document", {}).get("CODE", "N/A")
                score = r.get("score", 0.0)
                output_lines.append(f"Code: {code}, Label: {label}, Score: {score:.4f}")

            return "\n".join(output_lines)
        except Exception as e:
            logger.exception("Direct ICD chat failed")
            return f"An error occurred: {e}"
