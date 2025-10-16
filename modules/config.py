# modules/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class AzureOpenAIConfig:
    def __init__(self):
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION")
        self.chat_deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")
        self.agent_temperature = float(os.getenv("AGENT_TEMPERATURE", "1.0"))

    def get_azure_openai_kwargs(self) -> dict:
        """Return kwargs suitable for initializing AzureChatOpenAI"""
        return {
            "azure_endpoint": self.endpoint,
            "api_key": self.api_key,
            "api_version": self.api_version,
            "deployment_name": self.chat_deployment
        }

# global instance
config = AzureOpenAIConfig()
