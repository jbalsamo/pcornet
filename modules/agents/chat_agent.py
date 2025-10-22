"""
A specialized agent for handling general conversational chat.

This module defines the ChatAgent, which uses the AzureChatOpenAI model from
the LangChain library to engage in conversations. It is responsible for
processing user input and generating helpful, context-aware responses for
non-specialized queries.
"""

# modules/agents/chat_agent.py
import os
import logging
from langchain_core.messages import HumanMessage, SystemMessage
from ..config import get_config, create_chat_llm, CONCEPT_SET_FORMATTING_PROMPT

logger = logging.getLogger(__name__)

class ChatAgent:
    """
    A conversational agent powered by Azure OpenAI's GPT models.

    This agent is designed for general-purpose chat. It initializes a connection
    to an Azure OpenAI deployment and uses it to respond to user messages.
    """

    def __init__(self):
        """
        Initializes the ChatAgent and its underlying language model.

        This constructor configures and instantiates the AzureChatOpenAI model
        using centralized configuration. It sets a default temperature and 
        token limit for the responses.

        Raises:
            Exception: If the language model fails to initialize, often due to
                       missing or incorrect environment variables.
        """
        try:
            self.llm = create_chat_llm(max_tokens=1000)
            logger.info("✅ ChatAgent LLM initialized successfully")
        except Exception as e:
            logger.exception("Failed to initialize ChatAgent LLM")
            raise e

    def process(self, user_input: str, context: str = None) -> str:
        """
        Processes a user's chat message and returns the model's response.

        This method constructs a message list with a system prompt and the user's
        input, then invokes the language model to get a conversational response.

        Args:
            user_input (str): The message from the user.
            context (str): Optional RAG context from previous searches to include.

        Returns:
            str: The AI-generated response as a string. Returns an error message
                 if the model invocation fails.
        """
        try:
            # Build system message with RAG context if provided
            if context:
                # Count how many codes we have
                code_count = context.count('[') if context else 0
                system_content = f"""You are a helpful AI assistant specializing in medical coding and ICD-10 codes.

🔒 CRITICAL INSTRUCTION: You have access to {code_count} ICD-10 codes from a previous search below. This is your COMPLETE dataset. You MUST use ONLY this data. DO NOT ask the user for more information - you already have ALL the data you need.

⚠️ IMPORTANT: If the user asks for SNOMED codes, they are ALREADY in the OHDSI field below - DO NOT ask what to match, just extract them!

AVAILABLE ICD-10 CODES WITH ALL FIELDS ({code_count} codes):
{context}

UNDERSTANDING THE DATA:
- Each code entry includes [CODE] Description
- OHDSI field contains mappings to other vocabularies (JSON format)
  - When OHDSI is present, it contains a "maps" array
  - Each map has: vocabulary_id, concept_code, concept_name, relationship_id, domain_id
  - vocabulary_id "SNOMED" indicates SNOMED CT codes
  - concept_code is the actual SNOMED code
  - concept_name is the SNOMED description
- SAB field indicates the source abbreviation
- All other fields are additional metadata

MANDATORY RULES:
1. NEVER ask the user to provide data - you already have ALL the data above
2. For ANY SNOMED request: Immediately parse the OHDSI field above and extract SNOMED codes
3. For "show snomed codes" or "matching snomed": Look at OHDSI field, find vocabulary_id="SNOMED", extract concept_code
4. Format the data as requested (table, JSON, list, etc.)
5. Do not add any additional codes or information not in the list above
6. If asked about codes not in the list, state they are not in the current dataset
7. When asked to create a table, use the data above immediately - do not ask for clarification
8. You have ALL the context needed - the OHDSI field contains the SNOMED mappings"""
            else:
                system_content = "You are a helpful AI assistant."
            
            messages = [
                SystemMessage(content=system_content),
                HumanMessage(content=user_input)
            ]
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"Error in ChatAgent: {e}")
            return f"⚠️ Error: {e}"

    def format_concept_set(self, original_query: str, context_data: str) -> str:
        """
        Uses the LLM to format the extracted concept set data.

        Args:
            original_query (str): The user's original query.
            context_data (str): The extracted data from the ConceptSetExtractorAgent.

        Returns:
            str: A formatted, conversational response for the user.
        """
        try:
            prompt = CONCEPT_SET_FORMATTING_PROMPT.format(
                query=original_query,
                context_data=context_data
            )
            messages = [HumanMessage(content=prompt)]
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"Error in ChatAgent formatting concept set: {e}")
            return f"⚠️ Error formatting the concept set: {e}"
