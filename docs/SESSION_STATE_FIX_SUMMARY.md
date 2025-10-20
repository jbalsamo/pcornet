# Session State & RAG Context Fix

## Problem

When users tried to continue a conversation to modify or reformat RAG data (e.g., "show as table", "add SNOMED codes"), they received:
> "No active session found. Please start with a search query first, then I can help you modify the results."

The system was not retaining the RAG data and conversation state between messages.

## Root Causes

1. **Missing Session ID**: `main.py` wasn't initializing or passing a `session_id` to the `agent.chat()` call
2. **Session Not Persisted**: Each Streamlit interaction had no way to maintain state across messages
3. **Session Check Failing**: `_has_active_session()` was checking the wrong context
4. **Follow-up Detection**: The system only detected explicit modification keywords, not general follow-up questions

## Changes Made

### 1. Added Session ID Management in `main.py`

**Lines 202-206:**
```python
# Initialize session_id for interactive sessions (persistent per Streamlit session)
if 'interactive_session_id' not in st.session_state:
    import uuid
    st.session_state.interactive_session_id = f"streamlit_{uuid.uuid4().hex[:8]}"
    logger.info(f"Created new interactive session ID: {st.session_state.interactive_session_id}")
```

**Lines 393-397:**
```python
# Pass session_id to maintain interactive context
response = st.session_state.agent.chat(
    prompt, 
    session_id=st.session_state.interactive_session_id
)
```

### 2. Clear Session on New Chat in `main.py`

**Lines 280-286:**
```python
# Clear interactive session and create new one
from modules.interactive_session import interactive_session
if st.session_state.interactive_session_id:
    interactive_session.clear_session(st.session_state.interactive_session_id)
import uuid
st.session_state.interactive_session_id = f"streamlit_{uuid.uuid4().hex[:8]}"
logger.info(f"Cleared interactive session and created new ID: {st.session_state.interactive_session_id}")
```

### 3. Fixed Session Check in `modules/master_agent.py`

**Lines 180-186:**
```python
def _has_active_session(self, session_id: str) -> bool:
    """Check if there's an active session with data."""
    # Check if session exists in contexts
    if session_id in interactive_session.contexts:
        context = interactive_session.contexts[session_id]
        return len(context.current_data) > 0
    return False
```

### 4. Enhanced Follow-up Detection in `modules/master_agent.py`

**Lines 141-166:**
```python
# Check if there's an active session with previous ICD data
has_session_data = self._has_active_session(session_id)

# Check if this is an interactive modification request OR if we have session data and it's a follow-up
is_followup_with_context = (
    has_session_data and 
    len(self.conversation_history.messages) > 0 and
    not self._is_concept_set_query(query)
)

if interactive_session.is_modification_request(query) or is_followup_with_context:
    logger.info(f"Interactive request detected: query='{query}', has_session_data={has_session_data}")
    if agent_type == "icd" or has_session_data:
        response = self.icd_agent.process_interactive(query, session_id)
        # Handle dict or string response
        if isinstance(response, dict):
            final_response = response.get("processed_response", str(response))
        else:
            final_response = response
        # Add assistant response to history
        self.conversation_history.add_assistant_message(final_response, agent_type="icd")
        return final_response
```

## How It Works Now

### Session Flow

1. **User starts Streamlit** → Unique `interactive_session_id` created (e.g., `streamlit_a1b2c3d4`)
2. **First query** (e.g., "find diabetes codes") → ICD search performed → Results stored in session
3. **Follow-up query** (e.g., "show as table") → System detects session has data → Routes to `process_interactive()`
4. **Chat agent formats data** → Uses stored RAG data → No new search needed
5. **New Chat button** → Session cleared → New ID generated

### RAG Data Flow

```
User Query 1: "find hypertension codes"
    ↓
ICD Search → RAG retrieves documents
    ↓
Store in session: interactive_session.contexts[session_id]
    ↓
Display results to user
    ↓
User Query 2: "show as table"
    ↓
Detect: has_session_data=True + is_followup=True
    ↓
Route to: process_interactive(query, session_id)
    ↓
Retrieve stored data from session
    ↓
Use ChatAgent to format as table (NO NEW SEARCH)
    ↓
Display formatted results (RAG data only, no LLM filler)
```

## Key Principles Maintained

✅ **RAG Data as Single Source of Truth**
- Session stores original RAG documents
- Follow-up queries manipulate stored data
- No new LLM-generated content added
- Chat agent only formats/visualizes existing data

✅ **Conversation Context Preserved**
- Session persists across multiple messages
- Conversation history maintained in `master_agent`
- Session cleared only when user starts new chat

✅ **Interactive Capabilities**
- "show as table" → Formats stored data
- "add SNOMED codes" → Searches and adds to session
- "remove X" → Removes from session
- All operations use stored RAG data

## Testing

Test the fix with this sequence:

1. **Start conversation**:
   - User: "find hypertension codes"
   - Expected: ICD codes displayed with [citations]

2. **Follow-up without explicit keywords**:
   - User: "show that as a table"
   - Expected: Same data formatted as markdown table

3. **Modification request**:
   - User: "add SNOMED codes"
   - Expected: SNOMED mappings added (from RAG only)

4. **Format change**:
   - User: "show as JSON"
   - Expected: Same data in JSON format

5. **New chat**:
   - Click "New Chat" button
   - User: "any query"
   - Expected: Fresh start, previous data cleared

## Files Modified

1. ✅ `main.py` - Added session_id initialization and passing
2. ✅ `modules/master_agent.py` - Fixed session checking and follow-up detection
3. ✅ `modules/agents/icd_agent.py` - Already has `process_interactive()` method
4. ✅ `modules/interactive_session.py` - Already has full session management

No changes needed to:
- `conversation_history.py` - Already tracks messages correctly
- `chat_agent.py` - Already formats data without adding content
- `search_tool.py` - Already returns only RAG data

## Summary

The fix ensures that:
- Each Streamlit session gets a unique `interactive_session_id`
- This ID is passed to every `agent.chat()` call
- RAG data from first query is stored in session
- Follow-up queries detect session has data
- Chat agent manipulates stored data without new searches
- **RAG data remains the only source of truth**
- Conversation state persists until user starts new chat
