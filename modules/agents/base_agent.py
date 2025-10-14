"""
Base Agent - common parent class for specialized agents.
"""
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

class BaseAgent:
    """Base class for specialized agents like ChatAgent or IcdAgent."""

    def __init__(self, name: str):
        self.name = name
        self.agent_type = name.lower().replace(" ", "_")
        logger.info(f"{self.name} initialized")

    def process_with_history(self, user_input: str, history: Any) -> str:
        raise NotImplementedError("Subclasses must implement process_with_history()")

    def get_status(self) -> str:
        return "active"

    def get_capabilities(self) -> Dict[str, Any]:
        return {"agent_type": self.agent_type, "capabilities": []}
