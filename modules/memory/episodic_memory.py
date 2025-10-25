"""
Episodic Memory: Stores and retrieves past conversations using semantic search.

Maintains a vector database of conversation episodes that can be searched
by semantic similarity, enabling the agent to recall relevant past interactions.
"""
import logging
import os
import warnings
from typing import List, Dict, Any, Optional
from datetime import datetime

# Suppress torch warnings before importing chromadb
warnings.filterwarnings('ignore', message='.*torch.classes.*')
warnings.filterwarnings('ignore', message='.*Tried to instantiate class.*')

import chromadb
from chromadb.config import Settings
from .embeddings import embedding_service

logger = logging.getLogger(__name__)

class EpisodicMemory:
    """
    Manages episodic memory using vector similarity search.
    
    Stores past conversation snippets and enables semantic search
    to find relevant past interactions when processing new queries.
    """
    
    def __init__(self, persist_directory: str = "data/memory/episodic"):
        """
        Initialize episodic memory with ChromaDB vector store.
        
        Args:
            persist_directory: Directory to persist the vector database
        """
        try:
            # Ensure directory exists
            os.makedirs(persist_directory, exist_ok=True)
            
            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(path=persist_directory)
            
            # Create or get collection
            self.collection = self.client.get_or_create_collection(
                name="conversation_episodes",
                metadata={"description": "Past conversation episodes for semantic search"}
            )
            
            logger.info(f"✅ Episodic memory initialized: {self.collection.count()} episodes stored")
            
        except Exception as e:
            logger.exception(f"Failed to initialize episodic memory: {e}")
            raise e
    
    def add_turn(self, 
                 turn_id: str,
                 user_query: str, 
                 assistant_response: str, 
                 metadata: Dict[str, Any]) -> bool:
        """
        Store a conversation turn in episodic memory.
        
        Args:
            turn_id: Unique identifier for this turn
            user_query: User's query
            assistant_response: Assistant's response
            metadata: Additional context (session_id, timestamp, etc.)
        
        Returns:
            True if successful
        """
        try:
            # Format as Q&A pair for better semantic matching
            text = f"User: {user_query}\nAssistant: {assistant_response}"
            
            # Generate embedding
            embedding = embedding_service.embed_text(text)
            
            if not embedding:
                logger.error(f"Failed to generate embedding for turn {turn_id}")
                return False
            
            # Add to collection
            self.collection.add(
                ids=[turn_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[metadata]
            )
            
            logger.debug(f"Stored conversation turn: {turn_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add turn to episodic memory: {e}")
            return False
    
    def search_similar(self, 
                       query: str, 
                       n_results: int = 3,
                       filter_metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for similar past conversations.
        
        Args:
            query: Search query
            n_results: Number of results to return
            filter_metadata: Optional metadata filters
        
        Returns:
            List of similar episodes with text, metadata, and similarity scores
        """
        try:
            # Generate query embedding
            query_embedding = embedding_service.embed_text(query)
            
            if not query_embedding:
                logger.warning("Failed to generate query embedding")
                return []
            
            # Search collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=filter_metadata
            )
            
            # Format results
            episodes = []
            if results and results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    episodes.append({
                        'id': results['ids'][0][i],
                        'text': doc,
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i] if results['distances'] else None,
                        'similarity': 1.0 - (results['distances'][0][i] if results['distances'] else 0)
                    })
            
            logger.debug(f"Found {len(episodes)} similar episodes for query: {query[:50]}...")
            return episodes
            
        except Exception as e:
            logger.error(f"Failed to search episodic memory: {e}")
            return []
    
    def get_recent_episodes(self, n_results: int = 10) -> List[Dict[str, Any]]:
        """
        Get most recent episodes.
        
        Args:
            n_results: Number of episodes to return
            
        Returns:
            List of recent episodes
        """
        try:
            # Get episodes (limited by n_results)
            results = self.collection.get(limit=n_results)
            
            episodes = []
            if results and results['documents']:
                for i, doc in enumerate(results['documents']):
                    episodes.append({
                        'id': results['ids'][i],
                        'text': doc,
                        'metadata': results['metadatas'][i]
                    })
            
            # Sort by timestamp if available
            episodes.sort(
                key=lambda x: x['metadata'].get('timestamp', ''),
                reverse=True
            )
            
            return episodes[:n_results]
            
        except Exception as e:
            logger.error(f"Failed to get recent episodes: {e}")
            return []
    
    def delete_episode(self, episode_id: str) -> bool:
        """Delete an episode from memory."""
        try:
            self.collection.delete(ids=[episode_id])
            logger.debug(f"Deleted episode: {episode_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete episode: {e}")
            return False
    
    def clear_all(self) -> bool:
        """Clear all episodic memory."""
        try:
            self.client.delete_collection(name="conversation_episodes")
            self.collection = self.client.create_collection(
                name="conversation_episodes",
                metadata={"description": "Past conversation episodes for semantic search"}
            )
            logger.info("✅ Cleared all episodic memory")
            return True
        except Exception as e:
            logger.error(f"Failed to clear episodic memory: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about episodic memory."""
        try:
            return {
                'total_episodes': self.collection.count(),
                'collection_name': self.collection.name
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {'total_episodes': 0, 'collection_name': 'unknown'}

# Global instance
episodic_memory = EpisodicMemory()
