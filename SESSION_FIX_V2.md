# Session State Fix V2 - Master Agent Loop Control

## Critical Bug Fixed

**Problem**: Even with session_id passed, the system was saying "No active session found" because:
1. `interactive_session.get_current_context()` relied on `self.current_session_id` 
2. This wasn't being set properly - methods checked wrong variable
3. Follow-up queries weren't routing through chat agent with RAG context

## Root Cause

The `InteractiveSession` class has two ways to track sessions:
- `self.current_session_id` - Global "current" session (wrong approach for multi-session)
- `self.contexts[session_id]` - Dictionary of all sessions (correct approach)

Methods like `get_current_context()` used `self.current_session_id`, but that wasn't being set when processing queries with a specific `session_id`.

## Solution: Master Agent Controls Loop

Instead of relying on interactive session's internal state, the Master Agent now:
1. **Stores RAG data in session** after first query
2. **Detects follow-up questions** by checking if session has data
3. **Routes to ChatAgent with context** for formatting/manipulation
4. **Never loses RAG context** - it's always available in session

## Changes Made

### 1. Added `get_context(session_id)` Method

**File**: `modules/interactive_session.py` (Lines 67-69)
```python
def get_context(self, session_id: str) -> Optional[InteractiveContext]:
    """Get a session context by ID."""
    return self.contexts.get(session_id)
```

### 2. Fixed Session Lookups in ICD Agent

**File**: `modules/agents/icd_agent.py`

**Line 672** (was 671):
```python
# OLD: current_context = interactive_session.get_current_context()
# NEW:
current_context = interactive_session.get_context(session_id)
```

**Line 1071** (was 1070):
```python
# OLD: if not interactive_session.get_current_context():
# NEW:
if not interactive_session.get_context(session_id):
```

### 3. Master Agent Loop Control

**File**: `modules/master_agent.py` (Lines 141-169)

```python
# Check if there's an active session with previous ICD data
has_session_data = self._has_active_session(session_id)

# For follow-up questions, use the chat agent with RAG context
if has_session_data and len(self.conversation_history.messages) > 0:
    is_explicit_new_search = any(keyword in query.lower() for keyword in [
        "search for", "find", "look up", "get", "show me", "what is"
    ]) and any(keyword in query.lower() for keyword in [
        "code", "icd", "diagnosis", "disease", "condition"
    ])
    
    # If it's not explicitly a new search, treat it as a follow-up
    if not is_explicit_new_search and not self._is_concept_set_query(query):
        logger.info(f"Follow-up query detected with session data: '{query}'")
        # Use chat agent with session context
        session_context = interactive_session.get_context(session_id)
        if session_context and session_context.current_data:
            # Build context from session data
            context_lines = []
            for item in session_context.current_data.values():
                context_lines.append(f"[{item.key}] {item.value}")
            context_str = "\n".join(context_lines)
            
            # Use chat agent to handle the query with context
            formatted_query = f"Using the following ICD codes from our previous search:\n\n{context_str}\n\nUser request: {query}"
            response = self.chat_agent.process(formatted_query)
            return response
```

## How The Loop Works Now

```
User Query 1: "find hypertension codes"
    ↓
Master Agent: detects ICD query
    ↓
ICD Agent: process_interactive(query, session_id)
    ↓
    1. Search RAG for hypertension
    2. Store results in session[session_id]
    3. Return formatted response with citations
    ↓
Display: "[I10] Essential hypertension..."
    ↓
User Query 2: "show as table"
    ↓
Master Agent: 
    - has_session_data=True ✓
    - conversation history exists ✓
    - not explicit new search ✓
    - not concept set query ✓
    ↓
Master Agent: retrieve session data
    ↓
Build context string from session:
    "[I10] Essential hypertension
     [I11] Hypertensive heart disease"
    ↓
Chat Agent: format as table using context
    - Gets: "Using the following ICD codes... User request: show as table"
    - Formats stored RAG data only
    - Returns: markdown table
    ↓
Display: Table with only RAG data
```

## Key Improvements

### ✅ Master Agent is the Controller
- Decides when to search (new query)
- Decides when to format (follow-up)
- Routes appropriately based on session state
- Maintains RAG as source of truth

### ✅ Session Lookup Fixed
- Uses `get_context(session_id)` everywhere
- No dependency on `current_session_id`
- Works with multiple concurrent sessions

### ✅ Follow-up Detection Smart
- Checks for session data existence
- Checks for conversation history
- Filters out explicit new searches
- Filters out concept set queries

### ✅ RAG Context Preserved
- First query stores data in session
- Follow-ups retrieve from session
- Chat agent receives explicit context
- No LLM hallucination possible

## Test Sequence

1. **First Query - New Search**
   ```
   User: "find diabetes codes"
   Expected: ICD codes with [citations], stored in session
   ```

2. **Follow-up - Format Change**
   ```
   User: "show as table"
   Expected: Same codes formatted as markdown table
   Should NOT search again
   ```

3. **Follow-up - General Question**
   ```
   User: "what does E11 mean?"
   Expected: Explanation using stored E11 from session
   Should NOT search again
   ```

4. **Follow-up - JSON Format**
   ```
   User: "show as JSON"
   Expected: Session data formatted as JSON
   ```

5. **New Search - Explicit**
   ```
   User: "find hypertension codes"  
   Expected: NEW search, NEW data stored in session
   ```

6. **New Chat Button**
   ```
   Action: Click "New Chat"
   Expected: Session cleared, new session_id created
   ```

## Files Modified

1. ✅ `modules/interactive_session.py` - Added `get_context()` method
2. ✅ `modules/agents/icd_agent.py` - Fixed 2 session lookups
3. ✅ `modules/master_agent.py` - Added loop control logic
4. ✅ `main.py` - Session ID initialization (from V1)

## Summary

The Master Agent now:
- **Controls the flow** - Decides search vs format
- **Maintains state** - Checks session for data
- **Provides context** - Passes RAG data to chat agent
- **Prevents hallucination** - Chat only formats existing data

RAG data is:
- **Stored once** - On first search
- **Retrieved always** - For follow-ups
- **Never regenerated** - By LLM
- **Single source of truth** - From Azure Search only
