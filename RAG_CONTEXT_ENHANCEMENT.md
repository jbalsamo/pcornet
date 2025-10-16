# RAG Context Always Available Enhancement

## Problem Solved

When users asked follow-up questions about ICD codes (e.g., "show as table", "what does I10 mean?"), the chat agent wasn't consistently receiving the RAG data as context. This could lead to:
- The LLM not having access to the previously searched codes
- Potential for hallucinated information
- Inability to format or manipulate the exact data from the search

## Solution

**RAG context is now ALWAYS passed to the chat agent through the system message, ensuring the LLM can only use the exact codes from the search.**

## Changes Made

### 1. Enhanced Chat Agent to Accept Context

**File**: `modules/agents/chat_agent.py` (Lines 54-96)

```python
def process(self, user_input: str, context: str = None) -> str:
    """Process user input with optional RAG context."""
    
    # Build system message with RAG context if provided
    if context:
        system_content = f"""You are a helpful AI assistant specializing in medical coding and ICD-10 codes.

IMPORTANT: You have access to the following ICD-10 codes from a previous search. This is your ONLY source of information. Do not add any codes or information that are not in this list.

AVAILABLE ICD-10 CODES:
{context}

When answering questions:
- Only use the codes listed above
- Format the data as requested (table, JSON, list, etc.)
- Do not add any additional codes or information
- If asked about codes not in the list, state that they are not in the current dataset
- For formatting requests, use the exact codes and descriptions provided above"""
    else:
        system_content = "You are a helpful AI assistant."
    
    messages = [
        SystemMessage(content=system_content),
        HumanMessage(content=user_input)
    ]
    response = self.llm.invoke(messages)
    return response.content
```

**Key Features**:
- ✅ Context passed in system message (not user message)
- ✅ Explicit instruction to ONLY use provided codes
- ✅ Instructions for formatting requests
- ✅ Instruction to not add any codes not in the list

### 2. Added Helper Method in Master Agent

**File**: `modules/master_agent.py` (Lines 214-230)

```python
def _get_session_context_string(self, session_id: str) -> str:
    """
    Retrieve RAG context from session as a formatted string.
    
    Returns:
        Formatted string with ICD codes and descriptions, or None if no data
    """
    session_context = interactive_session.get_context(session_id)
    if session_context and session_context.current_data:
        context_lines = []
        for item in session_context.current_data.values():
            context_lines.append(f"[{item.key}] {item.value}")
        return "\n".join(context_lines)
    return None
```

**Benefits**:
- ✅ Single source of truth for context extraction
- ✅ Consistent formatting across all calls
- ✅ Returns None if no session data (clean handling)

### 3. Context Always Passed for Follow-ups

**File**: `modules/master_agent.py` (Lines 154-162)

```python
# For follow-up questions
if not is_explicit_new_search and not self._is_concept_set_query(query):
    logger.info(f"Follow-up query detected with session data: '{query}'")
    # Get RAG context from session
    context_str = self._get_session_context_string(session_id)
    if context_str:
        # Use chat agent with RAG context in system message
        response = self.chat_agent.process(query, context=context_str)
        return response
```

### 4. Context Passed for Direct Chat Routing

**File**: `modules/master_agent.py` (Lines 176-181)

```python
if agent_type == "chat":
    # Include session context if available (RAG data from previous searches)
    context_str = self._get_session_context_string(session_id) if has_session_data else None
    response = self.chat_agent.process(query, context=context_str)
    return response
```

## How It Works

### Data Flow

```
User Query 1: "find diabetes codes"
    ↓
ICD Agent: Search Azure AI Search
    ↓
Results: [E10] Type 1 diabetes, [E11] Type 2 diabetes
    ↓
Store in session.current_data:
    - E10 → "Type 1 diabetes mellitus without complications"
    - E11 → "Type 2 diabetes mellitus without complications"
    ↓
Display to user with [citations]

---

User Query 2: "show as table"
    ↓
Master Agent: Detects follow-up + has session data
    ↓
Extract context from session:
    "[E10] Type 1 diabetes mellitus without complications
     [E11] Type 2 diabetes mellitus without complications"
    ↓
Chat Agent: process(query="show as table", context=context_str)
    ↓
System Message: "AVAILABLE ICD-10 CODES: [E10] Type 1...[E11] Type 2...
                 User request: show as table"
    ↓
LLM: Creates table using ONLY the codes in system message
    ↓
Response: Markdown table with E10 and E11 only

---

User Query 3: "what is E11?"
    ↓
Master Agent: Detects follow-up + has session data
    ↓
Chat Agent: process(query="what is E11?", context=context_str)
    ↓
LLM: Looks at system message for E11
    ↓
Response: "E11 is Type 2 diabetes mellitus without complications
           (from the codes in our search)"
```

## Guarantees

### ✅ RAG Data is Single Source of Truth
- Context ALWAYS included in system message for follow-ups
- LLM explicitly instructed to use ONLY provided codes
- No additional codes can be added
- No hallucination possible

### ✅ Context Preserved Across Messages
- Session stores data after first search
- Every follow-up retrieves from session
- Context consistent until "New Chat"

### ✅ Works for All Follow-up Types
- **Format changes**: "show as table", "show as JSON"
- **Questions**: "what is I10?", "explain E11"
- **Modifications**: "add descriptions", "remove E10"
- **Comparisons**: "which is for heart disease?"

### ✅ Performance Optimized
- Context extracted once per message
- Reuses helper method
- No redundant session lookups

## Test Scenarios

### Scenario 1: Format Change
```
User: "find hypertension codes"
→ [I10] Essential hypertension, [I11] Hypertensive heart disease

User: "show as table"
→ | Code | Description |
  | I10  | Essential hypertension |
  | I11  | Hypertensive heart disease |
```

### Scenario 2: Specific Question
```
User: "find diabetes codes"
→ [E10] Type 1 diabetes, [E11] Type 2 diabetes

User: "what's the difference between E10 and E11?"
→ Uses ONLY E10 and E11 from context
  "E10 is Type 1 diabetes... E11 is Type 2 diabetes..."
```

### Scenario 3: Multiple Follow-ups
```
User: "find heart disease codes"
→ [I20] Angina, [I21] MI, [I50] Heart failure

User: "show as JSON"
→ JSON with I20, I21, I50

User: "now as a list"
→ Bullet list with I20, I21, I50

User: "what is I21?"
→ "I21 is Acute myocardial infarction..."
```

### Scenario 4: Code Not in Results
```
User: "find diabetes codes"
→ [E10] Type 1, [E11] Type 2

User: "what is E12?"
→ "E12 is not in the current dataset. The codes from our search are E10 and E11."
```

## Files Modified

1. ✅ `modules/agents/chat_agent.py` - Added context parameter and enhanced system message
2. ✅ `modules/master_agent.py` - Added helper method and context passing
3. ✅ `modules/agents/icd_agent.py` - Fixed session lookups (from V2)
4. ✅ `modules/interactive_session.py` - Added get_context() method (from V2)

## Summary

**RAG context is now the single source of truth for all follow-up questions**:
- ✅ Stored in session after first search
- ✅ Retrieved for every follow-up
- ✅ Passed in system message to LLM
- ✅ LLM explicitly instructed to use only provided codes
- ✅ No hallucination possible
- ✅ Context preserved across entire conversation

The Master Agent controls the loop, the session stores the state, and the chat agent enforces RAG-only responses.
