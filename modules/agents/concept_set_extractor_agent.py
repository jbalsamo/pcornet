"""
A specialized agent for extracting and formatting data from a context string.

This module defines the ConceptSetExtractorAgent, which is designed to take a
raw string of data (typically a JSON-like representation of search results),
extract the relevant fields, and format them into a clean, human-readable
string for presentation or further processing by another agent.
"""
import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class ConceptSetExtractorAgent:
    """
    An agent responsible for processing context data to extract concept sets.
    """

    def __init__(self):
        """
        Initializes the ConceptSetExtractorAgent.
        """
        logger.info("✅ ConceptSetExtractorAgent initialized")

    def process(self, context_data: str) -> str:
        """
        Processes a raw context string, extracts ICD data, and formats it.

        Args:
            context_data (str): A string containing the raw data, expected to be
                                a JSON representation of a list of dictionaries.

        Returns:
            str: A formatted string containing the extracted concept set, or an
                 error message if processing fails.
        """
        try:
            # The context data is a string representation of a list of dicts
            data: List[Dict[str, Any]] = json.loads(context_data)

            if not data:
                return "No concepts found in the provided data."  # Match test expectation

            formatted_lines = ["Here are the extracted ICD concepts for the concept set:"]
            for item in data:
                document = item.get("document", {})
                code = document.get("CODE", "N/A")
                label = document.get("STR", "N/A")
                score = item.get("score", 0.0)
                formatted_lines.append(f"Code: {code}, Label: {label}, Score: {score:.4f}")

            return "\n".join(formatted_lines)

        except json.JSONDecodeError:
            logger.warning("Extractor agent failed to decode JSON from context.")
            return {"error": "Failed to decode JSON"}  # Return dict for test compatibility
        except Exception as e:
            logger.exception("An unexpected error occurred in the extractor agent.")
            return f"An error occurred while extracting the concept set: {e}"
