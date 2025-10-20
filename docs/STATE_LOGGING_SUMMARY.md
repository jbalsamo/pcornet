# State Logging Enhancement

## Overview

Added comprehensive logging throughout the Master Agent to track state changes and flow decisions. All state-related logs are prefixed with 📋 for easy filtering.

## Logging Points Added

### 1. Session State Check (Line 143)
```python
logger.info(f"📋 Session check: has_session_data={has_session_data}, session_id={session_id}")
```
**When**: At the start of every chat() call  
**Purpose**: Track whether previous RAG data exists in session

### 2. Follow-up Detection (Line 156)
```python
logger.info(f"📋 Follow-up detected: Using chat agent with RAG context from session")
```
**When**: When a follow-up query is detected  
**Purpose**: Confirm we're using the follow-up path (not new search)

### 3. Context Retrieval from Session (Line 161)
```python
context_lines = context_str.count('\n') + 1
logger.info(f"📋 State: Retrieved {context_lines} ICD codes from session as context")
```
**When**: When RAG context is retrieved from session  
**Purpose**: Show how many codes are being passed as context

### 4. Response Generation with Context (Line 164)
```python
logger.info(f"📋 State: Response generated ({len(response)} chars) using session context")
```
**When**: After chat agent generates response with RAG context  
**Purpose**: Confirm response was generated using session data

### 5. State Initialization (Line 170)
```python
logger.info(f"📋 State initialized: agent_type='{agent_type}', user_input='{query[:50]}...'")
```
**When**: MasterAgentState object is created  
**Purpose**: Track initial state values

### 6. Routing Decision (Line 180)
```python
logger.info(f"📋 Routing to '{agent_type}' agent (standard query path)")
```
**When**: Routing to chat or ICD agent  
**Purpose**: Show which agent path is being taken

### 7. Context Passing to Chat Agent (Lines 184-188)
```python
if context_str:
    context_lines = context_str.count('\n') + 1
    logger.info(f"📋 State: Passing {context_lines} ICD codes as context to chat agent")
else:
    logger.info(f"📋 State: No session context available, using chat agent without RAG context")
```
**When**: Before calling chat agent  
**Purpose**: Show whether RAG context is being passed

### 8. Chat Response Generated (Line 190)
```python
logger.info(f"📋 State: Chat response generated ({len(response)} chars)")
```
**When**: After chat agent returns response  
**Purpose**: Confirm response generation and size

### 9. ICD Agent Routing (Line 195)
```python
logger.info(f"📋 State: Routing to ICD agent with interactive session support")
```
**When**: Routing to ICD agent  
**Purpose**: Confirm ICD path with session support

### 10. ICD Response with Session Storage (Line 197)
```python
logger.info(f"📋 State: ICD response generated ({len(response)} chars), stored in session")
```
**When**: After ICD agent returns response  
**Purpose**: Confirm response generation and session storage

### 11. Context Updated in Workflow (Line 256)
```python
state["context"] = icd_result.get("data", "")
context_size = len(state["context"]) if state["context"] else 0
logger.info(f"📋 State updated: context set ({context_size} chars) with ICD data from search")
```
**When**: In concept set workflow, after ICD search  
**Purpose**: Track when state context is populated with RAG data

### 12. Helper Method - Context Retrieval (Lines 229-232)
```python
logger.debug(f"📋 Retrieved {len(session_context.current_data)} codes from session {session_id}")
# or
logger.debug(f"📋 No context data found in session {session_id}")
```
**When**: In _get_session_context_string() helper  
**Purpose**: Debug-level tracking of context retrieval

## Log Levels Used

- **INFO**: Primary flow and state changes
- **DEBUG**: Helper method details and context retrieval

## Example Log Output

### Scenario: First Query (New Search)
```
INFO - 📋 Session check: has_session_data=False, session_id=streamlit_a1b2c3d4
INFO - 📋 State initialized: agent_type='icd', user_input='find diabetes codes...'
INFO - 📋 Routing to 'icd' agent (standard query path)
INFO - 📋 State: Routing to ICD agent with interactive session support
INFO - 📋 State: ICD response generated (342 chars), stored in session
```

### Scenario: Follow-up Query (Using Session Context)
```
INFO - 📋 Session check: has_session_data=True, session_id=streamlit_a1b2c3d4
INFO - 📋 Follow-up detected: Using chat agent with RAG context from session
DEBUG - 📋 Retrieved 3 codes from session streamlit_a1b2c3d4
INFO - 📋 State: Retrieved 3 ICD codes from session as context
INFO - 📋 State: Response generated (215 chars) using session context
```

### Scenario: Chat with Context
```
INFO - 📋 Session check: has_session_data=True, session_id=streamlit_a1b2c3d4
INFO - 📋 State initialized: agent_type='chat', user_input='explain these codes...'
INFO - 📋 Routing to 'chat' agent (standard query path)
DEBUG - 📋 Retrieved 3 codes from session streamlit_a1b2c3d4
INFO - 📋 State: Passing 3 ICD codes as context to chat agent
INFO - 📋 State: Chat response generated (412 chars)
```

### Scenario: Concept Set Workflow
```
INFO - 📋 Session check: has_session_data=False, session_id=streamlit_a1b2c3d4
INFO - 📋 State initialized: agent_type='auto', user_input='create concept set for heart disease...'
INFO - Concept set query detected. Starting concept set workflow.
INFO - Workflow Step 1: Calling IcdAgent
INFO - 📋 State updated: context set (1247 chars) with ICD data from search
INFO - Workflow Step 3: Calling ConceptSetExtractorAgent
INFO - Workflow Step 4: Calling ChatAgent for final formatting.
```

## Benefits

### ✅ Complete Flow Visibility
- See every decision point
- Track state changes
- Understand routing logic

### ✅ Easy Debugging
- Prefix 📋 for filtering: `grep "📋" app.log`
- Shows data sizes (char counts, code counts)
- Clear indication of session usage

### ✅ Session Tracking
- Know when session data exists
- See when context is retrieved
- Track when data is stored

### ✅ Performance Insights
- Response sizes logged
- Context sizes logged
- Can identify large payloads

## Filtering Logs

To see only state-related logs:
```bash
# In terminal running streamlit
grep "📋" | tail -f

# If logs are written to file
tail -f app.log | grep "📋"
```

To see only INFO level state logs:
```bash
grep "INFO.*📋"
```

To see only DEBUG level state logs:
```bash
grep "DEBUG.*📋"
```

## Summary

State logging now provides:
- ✅ Session state tracking
- ✅ RAG context flow visibility
- ✅ Routing decision tracking
- ✅ Response generation confirmation
- ✅ Data size metrics
- ✅ Easy filtering with 📋 prefix

All critical state changes and flow decisions are now logged for debugging and monitoring.
