"""
Memory Module: Multi-tiered memory system for agent context and learning.

Provides:
- Episodic memory: Vector-based semantic search of past conversations
- Semantic memory: Extracted facts and domain knowledge
- Context building: Intelligent assembly of relevant context
- Memory management: Orchestration of all memory systems
"""

import warnings

# Suppress torch warnings before importing any memory components
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', message='.*torch.classes.*')
warnings.filterwarnings('ignore', message='.*Tried to instantiate class.*')

from .embeddings import embedding_service, EmbeddingService
from .episodic_memory import episodic_memory, EpisodicMemory
from .semantic_memory import semantic_memory, SemanticMemory
from .context_builder import context_builder, ContextBuilder
from .memory_manager import memory_manager, MemoryManager

__all__ = [
    'embedding_service',
    'EmbeddingService',
    'episodic_memory',
    'EpisodicMemory',
    'semantic_memory',
    'SemanticMemory',
    'context_builder',
    'ContextBuilder',
    'memory_manager',
    'MemoryManager',
]
