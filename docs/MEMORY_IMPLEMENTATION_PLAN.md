# Agent Memory Implementation Plan

**Goal:** Enable the agent to remember previous conversation steps and use that data as context when necessary.

---

## Quick Implementation (Next Steps)

### Phase 1: Basic Semantic Memory (2-3 hours)

#### Step 1.1: Install Dependencies
```bash
pip install chromadb sentence-transformers tiktoken
```

Update `requirements.txt`:
```python
# Add to requirements.txt
chromadb>=0.4.18
sentence-transformers>=2.2.2
tiktoken>=0.5.1
```

#### Step 1.2: Create Memory Module Structure
```bash
mkdir -p modules/memory
touch modules/memory/__init__.py
touch modules/memory/embeddings.py
touch modules/memory/episodic_memory.py
touch modules/memory/memory_manager.py
```

#### Step 1.3: Implement Embedding Service

**Create:** `modules/memory/embeddings.py`

```python
"""Embedding service for semantic search."""
import logging
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        """Initialize with fast, efficient embedding model (384D)."""
        self.model = SentenceTransformer(model_name)
        logger.info(f"✅ Embedding model loaded: {model_name}")
    
    def embed_text(self, text: str) -> list:
        """Generate embedding for text."""
        return self.model.encode(text).tolist()
    
    def embed_batch(self, texts: list) -> list:
        """Generate embeddings for multiple texts."""
        return self.model.encode(texts).tolist()

embedding_service = EmbeddingService()
```

#### Step 1.4: Implement Episodic Memory (Vector Store)

**Create:** `modules/memory/episodic_memory.py`

```python
"""Episodic Memory: Semantic search over past conversations."""
import logging
import chromadb
from datetime import datetime
from .embeddings import embedding_service

logger = logging.getLogger(__name__)

class EpisodicMemory:
    def __init__(self, persist_dir="data/memory/episodic"):
        """Initialize vector store for past conversations."""
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(
            name="conversations",
            metadata={"description": "Past conversation episodes"}
        )
        logger.info(f"✅ Episodic memory: {self.collection.count()} episodes")
    
    def add_turn(self, turn_id: str, user_query: str, 
                 assistant_response: str, metadata: dict):
        """Store a conversation turn."""
        text = f"Q: {user_query}\nA: {assistant_response}"
        embedding = embedding_service.embed_text(text)
        
        self.collection.add(
            ids=[turn_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata]
        )
        logger.debug(f"Stored turn: {turn_id}")
    
    def search_similar(self, query: str, n_results=3):
        """Find similar past conversations."""
        query_embedding = embedding_service.embed_text(query)
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        similar = []
        if results['documents']:
            for i, doc in enumerate(results['documents'][0]):
                similar.append({
                    'text': doc,
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i]
                })
        
        return similar

episodic_memory = EpisodicMemory()
```

#### Step 1.5: Create Memory Manager

**Create:** `modules/memory/memory_manager.py`

```python
"""Memory Manager: Orchestrates memory operations."""
import logging
from datetime import datetime
from .episodic_memory import episodic_memory

logger = logging.getLogger(__name__)

class MemoryManager:
    """Coordinates all memory operations."""
    
    def store_conversation_turn(self, session_id: str, 
                                user_query: str, 
                                assistant_response: str):
        """Store a conversation turn in memory."""
        turn_id = f"{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        metadata = {
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'query_preview': user_query[:100]
        }
        
        episodic_memory.add_turn(
            turn_id=turn_id,
            user_query=user_query,
            assistant_response=assistant_response,
            metadata=metadata
        )
    
    def get_relevant_memory(self, query: str, n_results=3):
        """Retrieve relevant past conversations."""
        similar = episodic_memory.search_similar(query, n_results)
        
        if not similar:
            return ""
        
        # Format for context
        context_parts = ["**Relevant Past Conversations:**\n"]
        for i, item in enumerate(similar, 1):
            context_parts.append(f"{i}. {item['text'][:300]}...\n")
        
        return "\n".join(context_parts)

memory_manager = MemoryManager()
```

#### Step 1.6: Integrate with MasterAgent

**Edit:** `modules/master_agent.py`

Add at top:
```python
from modules.memory.memory_manager import memory_manager
```

Modify the `chat` method (around line 129):

```python
def chat(self, query: str, agent_type: str = "auto", session_id: str = "default"):
    """Enhanced with memory retrieval."""
    
    # Add user message to conversation history
    self.conversation_history.add_user_message(query)
    
    # NEW: Retrieve relevant past conversations
    memory_context = memory_manager.get_relevant_memory(query, n_results=2)
    
    # Auto-detect agent type
    if agent_type == "auto":
        agent_type = self._classify_agent_type(query)
    
    # Check session data (existing code)
    has_session_data = self._has_active_session(session_id)
    
    # Build context with memory
    if has_session_data:
        # Existing session context code...
        context_str = self._get_session_context_string(session_id)
        
        # NEW: Append memory context if relevant
        if memory_context:
            context_str = f"{memory_context}\n\n{context_str}"
        
        if context_str:
            response = self.chat_agent.process(query, context=context_str)
            self.conversation_history.add_assistant_message(response, agent_type="chat")
            
            # NEW: Store this turn in memory
            memory_manager.store_conversation_turn(session_id, query, response)
            
            return response
    
    # Continue with existing routing logic...
    # (rest of method unchanged)
```

After generating response (around line 250), add:
```python
# Store conversation turn in memory
memory_manager.store_conversation_turn(session_id, query, response)
```

---

## Phase 2: Enhanced Memory Features (1 week)

### Feature 1: Automatic Fact Extraction

**Create:** `modules/memory/semantic_memory.py`

```python
"""Semantic Memory: Extract and store facts from conversations."""
import json
import logging
from openai import AzureOpenAI
import os

logger = logging.getLogger(__name__)

class SemanticMemory:
    def __init__(self, storage_file="data/memory/facts.json"):
        self.storage_file = storage_file
        self.facts = self._load_facts()
        
        self.client = AzureOpenAI(
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        )
    
    def extract_facts(self, conversation_text: str):
        """Extract facts using LLM."""
        prompt = f"""Extract key facts from this medical coding conversation.
        
Conversation:
{conversation_text}

Return facts as JSON array:
[{{"type": "preference|knowledge", "content": "fact", "confidence": "high|medium|low"}}]

Only return the JSON, nothing else."""

        response = self.client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        
        try:
            facts = json.loads(response.choices[0].message.content)
            for fact in facts:
                self._add_fact(fact)
            return len(facts)
        except:
            return 0
    
    def _add_fact(self, fact):
        """Add fact to storage."""
        fact_id = f"fact_{len(self.facts)}"
        self.facts[fact_id] = fact
        self._save_facts()
    
    def get_relevant_facts(self, query: str):
        """Get facts relevant to query."""
        # Simple keyword matching (can be enhanced with embeddings)
        relevant = []
        query_lower = query.lower()
        
        for fact in self.facts.values():
            if any(word in fact['content'].lower() for word in query_lower.split()):
                relevant.append(fact)
        
        return relevant[:5]
    
    def _load_facts(self):
        if os.path.exists(self.storage_file):
            with open(self.storage_file) as f:
                return json.load(f)
        return {}
    
    def _save_facts(self):
        os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
        with open(self.storage_file, 'w') as f:
            json.dump(self.facts, f, indent=2)

semantic_memory = SemanticMemory()
```

### Feature 2: Conversation Summarization

**Add to** `modules/memory/memory_manager.py`:

```python
def summarize_conversation(self, messages: list) -> str:
    """Summarize long conversation for context compression."""
    if len(messages) < 10:
        return ""
    
    # Build conversation text
    convo_text = "\n".join([
        f"{msg['role']}: {msg['content']}" 
        for msg in messages
    ])
    
    from openai import AzureOpenAI
    import os
    
    client = AzureOpenAI(
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    )
    
    prompt = f"""Summarize this conversation in 3-5 bullet points focusing on:
- Key medical codes discussed
- Important decisions made
- User preferences expressed

Conversation:
{convo_text}

Format as markdown bullets."""

    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=300
    )
    
    return response.choices[0].message.content
```

---

## Testing the Implementation

### Test 1: Basic Memory Retrieval

```python
# Test script: test_memory_basic.py
from modules.memory.memory_manager import memory_manager

# Store some conversations
memory_manager.store_conversation_turn(
    session_id="test_001",
    user_query="What is the ICD-10 code for hypertension?",
    assistant_response="The ICD-10 code for hypertension is I10."
)

memory_manager.store_conversation_turn(
    session_id="test_002",
    user_query="Tell me about diabetes codes",
    assistant_response="Diabetes codes start with E10-E14 in ICD-10."
)

# Retrieve relevant memory
context = memory_manager.get_relevant_memory("hypertension codes")
print("Retrieved context:")
print(context)
```

### Test 2: End-to-End with Agent

```bash
# Start the app
streamlit run main.py

# Test conversation:
# 1. "What is the ICD-10 code for hypertension?"
# 2. Start new chat
# 3. "I asked about a cardiovascular condition before, what was it?"
# Expected: Agent should reference the previous hypertension conversation
```

---

## Configuration

### Memory Settings

**Add to** `modules/config.py`:

```python
# Memory Configuration
MEMORY_CONFIG = {
    "episodic_memory": {
        "enabled": True,
        "max_results": 3,  # Number of similar conversations to retrieve
        "persist_directory": "data/memory/episodic"
    },
    "semantic_memory": {
        "enabled": True,
        "storage_file": "data/memory/facts.json",
        "auto_extract": True  # Automatically extract facts
    },
    "working_memory": {
        "max_messages": 20,
        "summarize_after": 50  # Summarize when conversation exceeds this
    }
}
```

---

## Monitoring & Debugging

### Add Memory Stats to UI

**Edit:** `main.py` (in sidebar)

```python
# Add to sidebar after "History Stats"
st.divider()

col1, col2 = st.columns([4, 1])
with col1:
    st.header("🧠 Memory Stats")
with col2:
    if st.button("▼" if st.session_state.get('show_memory', False) else "▶", 
                 key="toggle_memory"):
        st.session_state.show_memory = not st.session_state.get('show_memory', False)

if st.session_state.get('show_memory', False):
    from modules.memory.episodic_memory import episodic_memory
    count = episodic_memory.collection.count()
    st.text(f"Stored Episodes: {count}")
```

### Logging

Memory operations are automatically logged. View with:
```bash
# Check memory operations in logs
sudo journalctl -u pcornet-chat | grep "Memory"
```

---

## Performance Considerations

### 1. Embedding Model
- Uses `all-MiniLM-L6-v2` (fast, 384 dimensions)
- First load downloads ~80MB model
- Subsequent embeds are very fast (<100ms)

### 2. Vector Store
- ChromaDB is lightweight and efficient
- Persists to disk automatically
- Memory usage scales with conversation count

### 3. Token Usage
- Fact extraction uses ~500 tokens per extraction
- Summarization uses ~300 tokens per summary
- Monitor Azure OpenAI usage

---

## Rollout Plan

### Stage 1: Development (This Week)
1. ✅ Implement basic episodic memory
2. ✅ Integrate with MasterAgent
3. ✅ Test with sample conversations

### Stage 2: Testing (Next Week)
1. Test with real users
2. Monitor memory quality
3. Tune retrieval thresholds
4. Add semantic facts extraction

### Stage 3: Production (Week 3)
1. Deploy with patch installer
2. Monitor performance
3. Gather feedback
4. Iterate on relevance scoring

---

## Migration Guide

### For Existing Installations

```bash
# 1. Update dependencies
pip install chromadb sentence-transformers tiktoken

# 2. Pull new code
cd /opt/pcornet
sudo -u pcornet git pull

# 3. Run patch installer
sudo ./install.sh --patch

# 4. Restart service
sudo systemctl restart pcornet-chat

# 5. Verify memory initialization
sudo journalctl -u pcornet-chat -n 20 | grep "Memory"
```

### Data Migration

Existing conversations will not be retroactively added to memory. To import:

```python
# Optional: Import existing conversations
from modules.memory.memory_manager import memory_manager
import json
import glob

for file in glob.glob("saved/*.json"):
    with open(file) as f:
        data = json.load(f)
        messages = data.get('messages', [])
        
        # Store pairs
        for i in range(0, len(messages)-1, 2):
            if messages[i]['role'] == 'user' and messages[i+1]['role'] == 'assistant':
                memory_manager.store_conversation_turn(
                    session_id=f"imported_{i}",
                    user_query=messages[i]['content'],
                    assistant_response=messages[i+1]['content']
                )
```

---

## Expected Improvements

### Before Memory:
- Agent has no context beyond current conversation
- Must re-explain preferences each time
- Cannot reference previous discussions

### After Memory:
- ✅ Agent remembers past conversations
- ✅ Can reference "what we discussed before"
- ✅ Learns user preferences over time
- ✅ Provides more contextual responses

### Example Scenario:

**Conversation 1:**
- User: "I need ICD-10 codes for hypertension"
- Agent: [provides codes]

**Conversation 2 (different session):**
- User: "Remember that cardiovascular condition we looked at?"
- Agent: "Yes, we discussed hypertension (I10) previously. Would you like more details?"

---

## Troubleshooting

### Issue: Memory not retrieving results
**Check:**
```python
from modules.memory.episodic_memory import episodic_memory
print(f"Episodes stored: {episodic_memory.collection.count()}")
```

### Issue: Embedding model download fails
**Solution:**
```bash
# Pre-download model
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

### Issue: ChromaDB permission errors
**Solution:**
```bash
sudo chown -R pcornet:pcornet /opt/pcornet/data/memory
```

---

## Next Steps - Quick Start

**To implement memory RIGHT NOW:**

1. **Install dependencies** (5 min)
   ```bash
   pip install chromadb sentence-transformers tiktoken
   ```

2. **Create memory modules** (10 min)
   - Copy code from sections 1.3, 1.4, 1.5 above

3. **Integrate with MasterAgent** (10 min)
   - Add imports and modify `chat()` method

4. **Test** (10 min)
   - Run test script
   - Try example conversations

**Total time: ~35 minutes for basic memory**

---

**Questions? Check:**
- `docs/CODE_REVIEW_SUMMARY.md` - Overall assessment
- Logs: `sudo journalctl -u pcornet-chat -f`
- Memory stats in UI sidebar (after implementation)
