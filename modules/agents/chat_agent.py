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
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from ..config import get_config, CONCEPT_SET_FORMATTING_PROMPT

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
        using environment variables for the deployment name, endpoint, API version,
        and key. It sets a default temperature and token limit for the responses.

        Raises:
            Exception: If the language model fails to initialize, often due to
                       missing or incorrect environment variables.
        """
        try:
            config = get_config()
            self.llm = AzureChatOpenAI(
                deployment_name=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
                temperature=config.agent_temperature,
                max_tokens=1000,
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-05-01-preview"),
                openai_api_key=os.getenv("AZURE_OPENAI_API_KEY")
            )
            logger.info("✅ ChatAgent LLM initialized successfully")
        except Exception as e:
            logger.exception("Failed to initialize ChatAgent LLM")
            raise e

    def process(self, user_input: str) -> str:
        """
        Processes a user's chat message and returns the model's response.

        This method constructs a message list with a system prompt and the user's
        input, then invokes the language model to get a conversational response.

        Args:
            user_input (str): The message from the user.

        Returns:
            str: The AI-generated response as a string. Returns an error message
                 if the model invocation fails.
        """
        try:
            messages = [
                SystemMessage(content="You are a helpful AI assistant."),
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
