# modules/master_agent.py
import os
import logging
from modules.agents.chat_agent import ChatAgent
from modules.agents.icd_agent import IcdAgent  # Make sure icd_agent.py exists
from openai import OpenAI

logger = logging.getLogger(__name__)

class MasterAgent:
    """
    MasterAgent routes between chat and ICD search.
    """

    def __init__(self):
        try:
            # Initialize ChatAgent
            self.chat_agent = ChatAgent()
            logger.info("✅ ChatAgent initialized")

            # Initialize ICD Agent
            self.icd_agent = IcdAgent()
            logger.info("✅ IcdAgent initialized")
        except Exception as e:
            logger.exception("Failed to initialize agents")
            raise e

        # Quick validation of Azure OpenAI deployment
        try:
            self.client = OpenAI(api_key=os.getenv("AZURE_OPENAI_API_KEY"))
            logger.info("✅ AzureOpenAI client initialized for deployment check")
        except Exception as e:
            logger.exception("Failed to initialize AzureOpenAI client")
            raise e

    def chat(self, query: str, agent_type: str = "chat"):
        agent_type = agent_type.lower()
        if agent_type == "chat":
            return self.chat_agent.process(query)
        elif agent_type == "icd":
            return self._chat_icd(query)
        else:
            return f"❌ Unknown agent type: {agent_type}"

    def _chat_icd(self, query: str):
        """Use ICD agent to return results as JSON"""
        try:
            data = self.icd_agent.process(query)
            if "error" in data:
                return {"error": data["error"]}

            results = data.get("results", [])
            answers = data.get("answers", [])

            output = {
                "results": [
                    {
                        "label": r.get("label", "N/A"),
                        "code": r.get("code", "N/A"),
                        "caption": r.get("caption", ""),
                        "REL": r.get("REL", [])
                    }
                    for r in results
                ],
                "semantic_answers": answers
            }

            return output
        except Exception as e:
            logger.exception("ICD chat failed")
            return {"error": str(e)}
