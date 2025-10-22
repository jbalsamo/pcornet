"""
Semantic Memory: Extracts and stores facts, preferences, and domain knowledge.

Maintains structured knowledge extracted from conversations, including
user preferences, medical coding facts, and domain-specific insights.
"""
import json
import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class SemanticMemory:
    """
    Manages semantic memory: facts, user preferences, domain knowledge.
    
    Extracts and stores structured information from conversations
    that can be retrieved and applied in future interactions.
    """
    
    def __init__(self, storage_file: str = "data/memory/semantic_facts.json"):
        """
        Initialize semantic memory.
        
        Args:
            storage_file: Path to JSON file for persistent storage
        """
        self.storage_file = storage_file
        self.facts: Dict[str, Dict[str, Any]] = {}
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(storage_file), exist_ok=True)
        
        # Load existing facts
        self.load()
        
        # Initialize Azure OpenAI for fact extraction
        try:
            from ..config import create_openai_client
            self.client = create_openai_client()
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI client for fact extraction: {e}")
            self.client = None
        
        logger.info(f"✅ Semantic memory initialized: {len(self.facts)} facts loaded")
    
    def extract_facts(self, conversation_text: str) -> List[Dict[str, Any]]:
        """
        Extract facts from conversation using LLM.
        
        Args:
            conversation_text: Recent conversation text to analyze
            
        Returns:
            List of extracted facts with metadata
        """
        if not self.client:
            logger.warning("OpenAI client not available for fact extraction")
            return []
        
        try:
            prompt = f"""Extract key facts, preferences, and domain knowledge from this medical coding conversation.

Conversation:
{conversation_text}

Extract facts in JSON format with these fields:
- fact_type: "user_preference" | "domain_knowledge" | "context" | "reference"
- content: The actual fact (concise, one sentence)
- confidence: "high" | "medium" | "low"
- entities: List of relevant entities (ICD codes, conditions, etc.)

Return ONLY valid JSON array, no other text.
Example:
[
  {{
    "fact_type": "user_preference",
    "content": "User prefers detailed ICD code descriptions with examples",
    "confidence": "high",
    "entities": ["ICD-10"]
  }},
  {{
    "fact_type": "domain_knowledge",
    "content": "Hypertension is coded as I10 in ICD-10",
    "confidence": "high",
    "entities": ["I10", "hypertension"]
  }}
]"""

            response = self.client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=500
            )
            
            facts_text = response.choices[0].message.content.strip()
            
            # Parse JSON
            if facts_text.startswith("[") and facts_text.endswith("]"):
                facts = json.loads(facts_text)
                logger.info(f"Extracted {len(facts)} facts from conversation")
                return facts
            else:
                logger.warning("LLM did not return valid JSON array for fact extraction")
                return []
                
        except Exception as e:
            logger.error(f"Failed to extract facts: {e}")
            return []
    
    def add_fact(self, fact: Dict[str, Any]) -> str:
        """
        Add a fact to semantic memory.
        
        Args:
            fact: Fact dictionary with type, content, confidence, entities
            
        Returns:
            Fact ID
        """
        try:
            fact_id = f"fact_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            # Add metadata
            fact['id'] = fact_id
            fact['created_at'] = datetime.now().isoformat()
            fact['access_count'] = 0
            fact['last_accessed'] = None
            
            self.facts[fact_id] = fact
            self.save()
            
            logger.debug(f"Added fact: {fact_id} - {fact.get('content', '')[:50]}")
            return fact_id
            
        except Exception as e:
            logger.error(f"Failed to add fact: {e}")
            return ""
    
    def search_facts(self, 
                     query: str = None,
                     fact_type: str = None,
                     entities: List[str] = None,
                     min_confidence: str = None) -> List[Dict[str, Any]]:
        """
        Search facts by query, type, or entities.
        
        Args:
            query: Text to search in fact content
            fact_type: Filter by fact type
            entities: Filter by entities
            min_confidence: Minimum confidence level (low/medium/high)
        
        Returns:
            Matching facts sorted by relevance
        """
        matching_facts = []
        confidence_order = {'high': 3, 'medium': 2, 'low': 1}
        min_conf_value = confidence_order.get(min_confidence, 0) if min_confidence else 0
        
        for fact in self.facts.values():
            # Filter by confidence
            if min_confidence:
                fact_conf = confidence_order.get(fact.get('confidence', 'low'), 0)
                if fact_conf < min_conf_value:
                    continue
            
            # Filter by type
            if fact_type and fact.get('fact_type') != fact_type:
                continue
            
            # Filter by entities
            if entities:
                fact_entities = [e.lower() for e in fact.get('entities', [])]
                if not any(e.lower() in fact_entities for e in entities):
                    continue
            
            # Filter by query
            if query:
                content = fact.get('content', '').lower()
                if query.lower() not in content:
                    continue
            
            # Update access tracking
            fact['access_count'] = fact.get('access_count', 0) + 1
            fact['last_accessed'] = datetime.now().isoformat()
            
            matching_facts.append(fact.copy())
        
        # Sort by confidence and access count
        matching_facts.sort(
            key=lambda f: (
                confidence_order.get(f.get('confidence', 'low'), 0),
                f.get('access_count', 0)
            ),
            reverse=True
        )
        
        if matching_facts:
            self.save()  # Save updated access counts
        
        return matching_facts
    
    def get_all_facts(self, fact_type: str = None) -> List[Dict[str, Any]]:
        """Get all facts, optionally filtered by type."""
        if fact_type:
            return [f for f in self.facts.values() if f.get('fact_type') == fact_type]
        return list(self.facts.values())
    
    def delete_fact(self, fact_id: str) -> bool:
        """Delete a fact from memory."""
        if fact_id in self.facts:
            del self.facts[fact_id]
            self.save()
            logger.debug(f"Deleted fact: {fact_id}")
            return True
        return False
    
    def save(self) -> bool:
        """Save facts to file."""
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.facts, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Failed to save facts: {e}")
            return False
    
    def load(self) -> bool:
        """Load facts from file."""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    self.facts = json.load(f)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to load facts: {e}")
            self.facts = {}
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about semantic memory."""
        type_counts = {}
        for fact in self.facts.values():
            fact_type = fact.get('fact_type', 'unknown')
            type_counts[fact_type] = type_counts.get(fact_type, 0) + 1
        
        return {
            'total_facts': len(self.facts),
            'by_type': type_counts,
            'storage_file': self.storage_file
        }

# Global instance
semantic_memory = SemanticMemory()
