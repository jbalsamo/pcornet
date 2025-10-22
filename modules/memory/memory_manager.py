"""
Memory Manager: Orchestrates all memory systems.

Coordinates working memory, episodic memory, semantic memory, and context building
to provide comprehensive memory capabilities to the agent.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from .episodic_memory import episodic_memory
from .semantic_memory import semantic_memory
from .context_builder import context_builder

logger = logging.getLogger(__name__)

class MemoryManager:
    """
    Central manager for all memory systems.
    
    Coordinates:
    - Working memory (current conversation via ConversationHistory)
    - Episodic memory (past conversations via vector search)
    - Semantic memory (extracted facts and knowledge)
    - Context building (intelligent assembly of all sources)
    """
    
    def __init__(self):
        """Initialize memory manager."""
        self.auto_extract_facts = True  # Auto-extract facts after conversations
        self.fact_extraction_threshold = 5  # Extract facts every N turns
        self.turn_counter = 0
        
        logger.info("✅ Memory Manager initialized")
    
    def process_conversation_turn(self,
                                  session_id: str,
                                  user_query: str,
                                  assistant_response: str,
                                  metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Process a conversation turn and update all memory systems.
        
        This should be called after each user-assistant exchange.
        
        Args:
            session_id: Current session identifier
            user_query: User's query
            assistant_response: Assistant's response
            metadata: Additional metadata to store
        """
        try:
            self.turn_counter += 1
            
            # Build turn ID
            turn_id = f"{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Prepare metadata
            turn_metadata = {
                'session_id': session_id,
                'timestamp': datetime.now().isoformat(),
                'user_query_preview': user_query[:100],
                'turn_number': self.turn_counter
            }
            if metadata:
                turn_metadata.update(metadata)
            
            # Add to episodic memory
            success = episodic_memory.add_turn(
                turn_id=turn_id,
                user_query=user_query,
                assistant_response=assistant_response,
                metadata=turn_metadata
            )
            
            if success:
                logger.debug(f"Stored conversation turn in episodic memory: {turn_id}")
            
            # Periodically extract facts
            if self.auto_extract_facts and self.turn_counter % self.fact_extraction_threshold == 0:
                self._extract_facts_from_turn(user_query, assistant_response)
            
        except Exception as e:
            logger.error(f"Failed to process conversation turn: {e}")
    
    def _extract_facts_from_turn(self, user_query: str, assistant_response: str) -> int:
        """Extract and store facts from a conversation turn."""
        try:
            conversation_text = f"User: {user_query}\nAssistant: {assistant_response}"
            facts = semantic_memory.extract_facts(conversation_text)
            
            count = 0
            for fact in facts:
                fact_id = semantic_memory.add_fact(fact)
                if fact_id:
                    count += 1
            
            if count > 0:
                logger.info(f"Extracted and stored {count} facts from conversation")
            
            return count
            
        except Exception as e:
            logger.error(f"Failed to extract facts from turn: {e}")
            return 0
    
    def get_relevant_context(self,
                            current_query: str,
                            working_memory: str = "",
                            session_context: str = "",
                            max_tokens: int = 2000,
                            include_episodic: bool = True,
                            include_semantic: bool = True) -> str:
        """
        Get relevant context from all memory sources.
        
        Args:
            current_query: User's current query
            working_memory: Recent conversation context
            session_context: Current session data (ICD codes, etc.)
            max_tokens: Maximum tokens for context
            include_episodic: Include past conversations
            include_semantic: Include facts
            
        Returns:
            Assembled context string
        """
        try:
            # Update context builder token limit if needed
            if max_tokens != context_builder.max_tokens:
                context_builder.max_tokens = max_tokens
            
            # Build comprehensive context
            context = context_builder.build_context(
                current_query=current_query,
                working_memory=working_memory,
                session_context=session_context,
                include_episodic=include_episodic,
                include_semantic=include_semantic
            )
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to get relevant context: {e}")
            return ""
    
    def search_past_conversations(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search past conversations for similar content.
        
        Args:
            query: Search query
            n_results: Number of results to return
            
        Returns:
            List of similar past conversations
        """
        try:
            return episodic_memory.search_similar(query, n_results)
        except Exception as e:
            logger.error(f"Failed to search past conversations: {e}")
            return []
    
    def get_facts_for_query(self, query: str, entities: List[str] = None) -> List[Dict[str, Any]]:
        """
        Get relevant facts for a query.
        
        Args:
            query: Query to search facts for
            entities: Optional entities to filter by
            
        Returns:
            List of relevant facts
        """
        try:
            return semantic_memory.search_facts(
                query=query,
                entities=entities,
                min_confidence="medium"
            )
        except Exception as e:
            logger.error(f"Failed to get facts for query: {e}")
            return []
    
    def extract_facts_from_conversation(self, conversation_text: str) -> int:
        """
        Manually trigger fact extraction from conversation.
        
        Args:
            conversation_text: Conversation to extract facts from
            
        Returns:
            Number of facts extracted
        """
        try:
            facts = semantic_memory.extract_facts(conversation_text)
            
            count = 0
            for fact in facts:
                fact_id = semantic_memory.add_fact(fact)
                if fact_id:
                    count += 1
            
            return count
            
        except Exception as e:
            logger.error(f"Failed to extract facts: {e}")
            return 0
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get statistics about all memory systems.
        
        Returns:
            Dictionary with stats from all memory components
        """
        try:
            stats = {
                'episodic_memory': episodic_memory.get_stats(),
                'semantic_memory': semantic_memory.get_stats(),
                'auto_fact_extraction': self.auto_extract_facts,
                'total_turns_processed': self.turn_counter
            }
            return stats
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {}
    
    def clear_all_memory(self, confirm: bool = False) -> bool:
        """
        Clear all memory (use with caution!).
        
        Args:
            confirm: Must be True to actually clear
            
        Returns:
            True if successful
        """
        if not confirm:
            logger.warning("Clear all memory called without confirmation")
            return False
        
        try:
            episodic_cleared = episodic_memory.clear_all()
            
            # Clear semantic memory
            semantic_memory.facts = {}
            semantic_cleared = semantic_memory.save()
            
            logger.warning("🗑️ All memory cleared (episodic and semantic)")
            return episodic_cleared and semantic_cleared
            
        except Exception as e:
            logger.error(f"Failed to clear memory: {e}")
            return False
    
    def set_auto_fact_extraction(self, enabled: bool, threshold: int = 5) -> None:
        """
        Configure automatic fact extraction.
        
        Args:
            enabled: Enable/disable auto extraction
            threshold: Extract facts every N turns
        """
        self.auto_extract_facts = enabled
        self.fact_extraction_threshold = threshold
        logger.info(f"Auto fact extraction: {'enabled' if enabled else 'disabled'} (threshold: {threshold})")

# Global instance
memory_manager = MemoryManager()
