"""
Context Builder: Intelligently assembles context from multiple memory sources.

Combines working memory, episodic memory, and semantic memory to create
comprehensive context for the LLM while respecting token limits.
"""
import logging
from typing import List, Dict, Any, Optional
import tiktoken
from .episodic_memory import episodic_memory
from .semantic_memory import semantic_memory

logger = logging.getLogger(__name__)

class ContextBuilder:
    """
    Builds intelligent context by combining multiple memory sources.
    
    Priorities:
    1. Semantic Facts (small, specific, high value)
    2. Current Working Memory (immediate conversation)
    3. Episodic Memory (relevant past conversations)
    """
    
    def __init__(self, max_tokens: int = 2000, encoding_name: str = "cl100k_base"):
        """
        Initialize context builder.
        
        Args:
            max_tokens: Maximum tokens for assembled context
            encoding_name: Tokenizer encoding (cl100k_base for GPT-4)
        """
        self.max_tokens = max_tokens
        try:
            self.encoder = tiktoken.get_encoding(encoding_name)
        except:
            logger.warning(f"Failed to load tiktoken encoder, using character approximation")
            self.encoder = None
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        if self.encoder:
            return len(self.encoder.encode(text))
        else:
            # Approximate: 1 token ≈ 4 characters
            return len(text) // 4
    
    def build_context(self,
                     current_query: str,
                     working_memory: str = "",
                     session_context: str = "",
                     include_episodic: bool = True,
                     include_semantic: bool = True,
                     entities: List[str] = None) -> str:
        """
        Build comprehensive context for LLM.
        
        Args:
            current_query: User's current query
            working_memory: Recent conversation context
            session_context: Current session data (ICD codes, etc.)
            include_episodic: Include similar past conversations
            include_semantic: Include relevant facts
            entities: Entities to search for in memory
        
        Returns:
            Assembled context string within token limits
        """
        context_parts = []
        remaining_tokens = self.max_tokens
        
        # Extract entities from query if not provided
        if entities is None:
            entities = self._extract_entities(current_query)
        
        # 1. Semantic Facts (highest priority - small and specific)
        if include_semantic:
            facts = semantic_memory.search_facts(
                query=current_query,
                entities=entities,
                min_confidence="medium"
            )
            
            if facts:
                fact_text = self._format_facts(facts[:5])  # Top 5 facts
                fact_tokens = self.count_tokens(fact_text)
                
                if fact_tokens < remaining_tokens:
                    context_parts.append(("RELEVANT_FACTS", fact_text))
                    remaining_tokens -= fact_tokens
                    logger.debug(f"Added {len(facts[:5])} facts ({fact_tokens} tokens)")
        
        # 2. Session Context (current ICD codes, SNOMED, etc.)
        if session_context:
            session_tokens = self.count_tokens(session_context)
            if session_tokens < remaining_tokens * 0.5:  # Reserve 50% for session data
                context_parts.append(("CURRENT_SESSION_DATA", session_context))
                remaining_tokens -= session_tokens
                logger.debug(f"Added session context ({session_tokens} tokens)")
        
        # 3. Working Memory (recent conversation)
        if working_memory:
            working_tokens = self.count_tokens(working_memory)
            if working_tokens < remaining_tokens:
                context_parts.append(("RECENT_CONVERSATION", working_memory))
                remaining_tokens -= working_tokens
                logger.debug(f"Added working memory ({working_tokens} tokens)")
            else:
                # Truncate if too large
                truncated = self._truncate_to_tokens(working_memory, remaining_tokens)
                context_parts.append(("RECENT_CONVERSATION", truncated))
                remaining_tokens = 0
        
        # 4. Episodic Memory (relevant past conversations)
        if include_episodic and remaining_tokens > 200:  # Only if we have space
            episodes = episodic_memory.search_similar(
                query=current_query,
                n_results=3
            )
            
            if episodes:
                # Filter to high-similarity episodes
                relevant_episodes = [ep for ep in episodes if ep.get('similarity', 0) > 0.7]
                
                if relevant_episodes:
                    episode_text = self._format_episodes(relevant_episodes, remaining_tokens)
                    if episode_text:
                        context_parts.append(("SIMILAR_PAST_CONVERSATIONS", episode_text))
                        logger.debug(f"Added {len(relevant_episodes)} past episodes")
        
        # Assemble final context
        assembled = self._assemble_sections(context_parts)
        
        final_tokens = self.count_tokens(assembled)
        logger.info(f"Built context: {final_tokens}/{self.max_tokens} tokens from {len(context_parts)} sources")
        
        return assembled
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract potential entities from text (ICD codes, medical terms, etc.)."""
        import re
        entities = []
        
        # ICD code patterns
        icd_pattern = r'\b[A-Z]\d{2}(?:\.\d+)?\b'
        entities.extend(re.findall(icd_pattern, text.upper()))
        
        # Common medical terms
        medical_terms = ['hypertension', 'diabetes', 'icd', 'snomed', 'code', 'diagnosis']
        for term in medical_terms:
            if term.lower() in text.lower():
                entities.append(term)
        
        return list(set(entities))
    
    def _format_facts(self, facts: List[Dict[str, Any]]) -> str:
        """Format facts for context."""
        if not facts:
            return ""
        
        lines = []
        for fact in facts:
            confidence = fact.get('confidence', 'unknown')
            content = fact.get('content', '')
            fact_type = fact.get('fact_type', 'unknown')
            lines.append(f"[{fact_type}] {content} (confidence: {confidence})")
        
        return "\n".join(lines)
    
    def _format_episodes(self, episodes: List[Dict[str, Any]], max_tokens: int) -> str:
        """Format past episodes for context, respecting token limit."""
        if not episodes:
            return ""
        
        lines = []
        used_tokens = 0
        
        for i, ep in enumerate(episodes, 1):
            # Format episode with similarity score
            similarity = ep.get('similarity', 0)
            text = ep['text']
            
            # Truncate long episodes
            max_ep_length = 300
            if len(text) > max_ep_length:
                text = text[:max_ep_length] + "..."
            
            episode_line = f"\n[Similarity: {similarity:.2f}] {text}"
            episode_tokens = self.count_tokens(episode_line)
            
            if used_tokens + episode_tokens > max_tokens:
                break
            
            lines.append(episode_line)
            used_tokens += episode_tokens
        
        if not lines:
            return ""
        
        return "\n".join(lines)
    
    def _truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """Truncate text to fit within token limit."""
        if self.encoder:
            tokens = self.encoder.encode(text)
            if len(tokens) > max_tokens:
                truncated_tokens = tokens[:max_tokens]
                return self.encoder.decode(truncated_tokens) + "...[truncated]"
        else:
            # Approximate truncation
            max_chars = max_tokens * 4
            if len(text) > max_chars:
                return text[:max_chars] + "...[truncated]"
        
        return text
    
    def _assemble_sections(self, context_parts: List[tuple]) -> str:
        """Assemble context sections with clear delineation."""
        if not context_parts:
            return ""
        
        assembled_parts = []
        
        for label, text in context_parts:
            if text.strip():
                section = f"\n### {label.replace('_', ' ')}\n{text.strip()}\n"
                assembled_parts.append(section)
        
        return "\n".join(assembled_parts)

# Global instance
context_builder = ContextBuilder()
