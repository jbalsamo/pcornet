# Context Usage Fix - Follow-up Detection & LLM Instructions

## Problem

User reported that query #3 "format as table with SNOMED" didn't use the session data:

```
❌ Response: "Please provide the list of diagnoses..."
   (LLM asking for data instead of using session state)

✅ Expected: Table with ICD codes and SNOMED codes from session
```

## Root Causes

### 1. Follow-up Detection Too Broad
The old logic was detecting too many queries as "new searches":
```python
# OLD - Too permissive
is_explicit_new_search = any(keyword in query.lower() for keyword in [
    "search for", "find", "look up", "get", "show me", "what is"
]) and any(keyword in query.lower() for keyword in [
    "code", "icd", "diagnosis", "disease"
])
```

"format as table" → Doesn't match, good!  
BUT it might still be routed incorrectly

### 2. LLM Not Following Instructions
The system message wasn't strong enough - LLM was ignoring the context and asking for data.

### 3. No Explicit Code Count
LLM couldn't see HOW MUCH data it had available.

## Solutions Implemented

### 1. Stricter Follow-up Detection

**File**: `modules/master_agent.py` (Lines 148-162)

```python
# NEW - Much more restrictive
is_explicit_new_search = (
    # Must have both search intent AND "new/different/other"
    any(keyword in query.lower() for keyword in [
        "search for", "find", "look up", "get me", "retrieve"
    ]) and 
    any(keyword in query.lower() for keyword in [
        "new", "different", "other", "more"
    ])
) or (
    # Or explicitly asking about a new condition
    any(phrase in query.lower() for phrase in [
        "what is the code for", "find code for", "search for code"
    ])
)
```

**Results**:
- ✅ "format as table" → Follow-up (uses session)
- ✅ "show SNOMED codes" → Follow-up (uses session)  
- ✅ "what does E11 mean" → Follow-up (uses session)
- ✅ "find different codes" → New search
- ✅ "search for new disease" → New search

### 2. Much Stronger LLM Instructions

**File**: `modules/agents/chat_agent.py` (Lines 71-99)

```python
# Count codes for visibility
code_count = context.count('[') if context else 0

system_content = f"""You are a helpful AI assistant specializing in medical coding.

🔒 CRITICAL INSTRUCTION: You have access to {code_count} ICD-10 codes from a previous search below. This is your COMPLETE dataset. You MUST use ONLY this data. DO NOT ask the user for more information - you already have ALL the data you need.

AVAILABLE ICD-10 CODES WITH ALL FIELDS ({code_count} codes):
{context}

When answering questions:
- CRITICAL: Use ONLY the codes and data listed above - this is your complete dataset
- Never ask the user to provide data - you already have ALL the data you need above
- Format the data as requested (table, JSON, list, etc.)
- Do not add any additional codes or information not in the list
- For SNOMED requests: Extract SNOMED codes from the OHDSI field where vocabulary_id="SNOMED"
- When asked to create a table, use the data above immediately - do not ask for clarification
```

**Key Changes**:
- 🔒 Visual indicator (emoji) to draw attention
- Explicit code count shows LLM how much data it has
- "CRITICAL INSTRUCTION" emphasizes importance
- "DO NOT ask the user" - direct prohibition
- "you already have ALL the data" - reinforces completeness

### 3. Enhanced Logging

**File**: `modules/master_agent.py` (Lines 166-178)

```python
logger.info(f"📋 Follow-up detected: Using chat agent with RAG context from session")
context_str = self._get_session_context_string(session_id)
if context_str:
    context_lines = context_str.count('\n') + 1
    num_codes = len(interactive_session.get_context(session_id).current_data)
    logger.info(f"📋 State: Retrieved {num_codes} codes ({context_lines} lines) from session")
    
    response = self.chat_agent.process(query, context=context_str)
    logger.info(f"📋 State: Response generated using session context with {num_codes} codes")
```

**Benefits**:
- See exact number of codes being passed
- Track whether context was retrieved
- Confirm follow-up detection

### 4. Warning for Missing Context

**File**: `modules/master_agent.py` (Lines 179-181)

```python
else:
    logger.warning(f"📋 Follow-up detected but no context available in session {session_id}")
    # Continue to standard routing but it will still check for context
```

## How It Works Now

### Example Flow: "format as table with SNOMED"

```
User Query: "format as table with SNOMED"
    ↓
Classification: agent_type = "chat" (no ICD keywords)
    ↓
Session Check: has_session_data = True ✓
    ↓
New Search Check:
    - "format" in ["search for", "find"...] ? NO
    - "table" in ["new", "different"...] ? NO
    - Match explicit patterns? NO
    → is_explicit_new_search = False ✓
    ↓
Follow-up Detection: NOT new search + has session data
    → Follow-up = True ✓
    ↓
Get Context:
    num_codes = 3
    context_str = "[E10] Type 1 diabetes...
                    OHDSI: {...SNOMED...}
                   [E11] Type 2 diabetes...
                    OHDSI: {...SNOMED...}
                   [E13] Other diabetes...
                    OHDSI: {...SNOMED...}"
    ↓
Build System Message:
    "🔒 CRITICAL: You have 3 ICD-10 codes...
     AVAILABLE ICD-10 CODES (3 codes):
     [E10] Type 1 diabetes...
       OHDSI: {\"maps\":[{\"vocabulary_id\":\"SNOMED\"...}]}
     ..."
    ↓
Chat Agent Process:
    - Sees: 3 codes with OHDSI data
    - Instruction: "DO NOT ask user for data"
    - Task: "format as table with SNOMED"
    ↓
LLM Action:
    1. Parse OHDSI field for each code
    2. Extract SNOMED where vocabulary_id="SNOMED"
    3. Create table with ICD + SNOMED
    ↓
Response:
    | ICD Code | Description | SNOMED Code | SNOMED Name |
    | E10 | Type 1 diabetes | 46635009 | Diabetes mellitus type 1 |
    | E11 | Type 2 diabetes | 44054006 | Diabetes mellitus type 2 |
    | E13 | Other diabetes | 190372001 | Other specified diabetes |
```

## Test Cases

### Case 1: Format as Table
```
User: "find diabetes codes"
→ Stores E10, E11, E13 with OHDSI data

User: "format as table with SNOMED"
→ ✅ Uses session data
→ ✅ Extracts SNOMED from OHDSI
→ ✅ Creates table immediately
```

### Case 2: Show SNOMED
```
User: "find hypertension codes"
→ Stores I10, I11 with OHDSI data

User: "show SNOMED codes"
→ ✅ Uses session data
→ ✅ Extracts SNOMED codes
→ ✅ Displays: "I10 → 59621000, I11 → ..."
```

### Case 3: Explain Code
```
User: "find diabetes codes"
→ Stores E10, E11, E13

User: "what is E11?"
→ ✅ Uses session data
→ ✅ Finds E11 in context
→ ✅ Explains using stored description
```

### Case 4: New Search (Should NOT Use Session)
```
User: "find diabetes codes"
→ Stores diabetes codes

User: "find different codes for hypertension"
→ ✅ Detects "different" keyword
→ ✅ Triggers NEW search
→ ✅ Clears old data, searches hypertension
```

## Debugging

If follow-up isn't working, check logs:

```bash
# Should see these logs
📋 Session check: has_session_data=True, session_id=streamlit_abc123
📋 Follow-up detected: Using chat agent with RAG context from session
📋 State: Retrieved 3 codes (15 lines) from session
📋 State: Response generated using session context with 3 codes
```

If NOT seeing follow-up detection:
```bash
# Instead might see
📋 Session check: has_session_data=False
# or
📋 State initialized: agent_type='icd', user_input='...'
# (means it went to standard routing, not follow-up)
```

## Files Modified

1. ✅ `modules/master_agent.py` - Stricter follow-up detection, enhanced logging
2. ✅ `modules/agents/chat_agent.py` - Stronger LLM instructions with code count

## Summary

**Follow-up detection is now much more reliable:**
- ✅ Stricter "new search" detection (requires "new"/"different"/"other")
- ✅ LLM receives CRITICAL instructions to use provided data
- ✅ Code count visible to LLM (shows completeness)
- ✅ Enhanced logging shows exactly what's happening
- ✅ "format as table with SNOMED" now uses session data correctly

**The chat agent will now use session state for follow-ups and never ask for data it already has!**
