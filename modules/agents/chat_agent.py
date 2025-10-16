# modules/agents/chat_agent.py
import os
import logging
from langchain.chat_models import AzureChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from ..config import config

logger = logging.getLogger(__name__)

class ChatAgent:
    """Specialized agent for general chat and conversation."""

    def __init__(self):
        try:
            self.llm = AzureChatOpenAI(
                deployment_name=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
                model="gpt-4.1",
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
        """Process a chat request."""
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
