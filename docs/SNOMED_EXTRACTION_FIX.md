# SNOMED Extraction Fix - Enhanced Instructions & Logging

## Problem

User asked "Show matching snomed codes" and the LLM responded:
```
❌ "Could you clarify what you would like to match SNOMED codes to?
    Do you have a list of ICD-10 codes...?"
```

Even though:
- OHDSI field contains SNOMED mappings
- Context should be passed from session
- Instructions say "SNOMED codes are in OHDSI field"

## Root Cause

The LLM instructions weren't explicit enough about SNOMED requests specifically. The system message said SNOMED was in OHDSI, but didn't emphasize that ANY SNOMED request should immediately use the data.

## Solutions Implemented

### 1. Explicit SNOMED Warning

**File**: `modules/agents/chat_agent.py` (Line 78)

```python
⚠️ IMPORTANT: If the user asks for SNOMED codes, they are ALREADY in the OHDSI field below - DO NOT ask what to match, just extract them!
```

**Purpose**: Immediately visible warning before the data that SNOMED is already there.

### 2. Mandatory Numbered Rules

**File**: `modules/agents/chat_agent.py` (Lines 94-102)

```python
MANDATORY RULES:
1. NEVER ask the user to provide data - you already have ALL the data above
2. For ANY SNOMED request: Immediately parse the OHDSI field above and extract SNOMED codes
3. For "show snomed codes" or "matching snomed": Look at OHDSI field, find vocabulary_id="SNOMED", extract concept_code
4. Format the data as requested (table, JSON, list, etc.)
5. Do not add any additional codes or information not in the list above
6. If asked about codes not in the list, state they are not in the current dataset
7. When asked to create a table, use the data above immediately - do not ask for clarification
8. You have ALL the context needed - the OHDSI field contains the SNOMED mappings
```

**Key Changes**:
- Numbered list (easier to follow)
- Rule #2: "For ANY SNOMED request: Immediately parse..."
- Rule #3: Specific examples "show snomed codes", "matching snomed"
- Rule #8: Reinforces completeness

### 3. Enhanced Logging for Debugging

**File**: `modules/master_agent.py`

**Added logging points**:

```python
# Line 140: Classification logging
logger.info(f"📋 Agent classification: '{query}' → agent_type='{agent_type}'")

# Line 167: Follow-up check logging
logger.info(f"📋 Checking follow-up: is_explicit_new_search={is_explicit_new_search}, is_concept_set={is_concept_set}")

# Line 170: Follow-up confirmed
logger.info(f"📋 ✅ Follow-up confirmed: Using chat agent with RAG context from session")

# Line 199: Standard routing (NOT follow-up)
logger.info(f"📋 Routing to '{agent_type}' agent (standard query path - NOT follow-up)")

# Line 207: Context passed with code count
logger.info(f"📋 State: Passing {num_codes} codes ({context_lines} lines) as context to chat agent")

# Line 211: Response WITH/WITHOUT context indicator
logger.info(f"📋 State: Chat response generated ({len(response)} chars) {'WITH' if context_str else 'WITHOUT'} context")
```

**Benefits**:
- See exactly which path the query took
- Know if follow-up was detected
- Confirm context was passed
- See code count being passed

## Expected Log Flow

### Scenario: "Show matching snomed codes" (Follow-up)

```
INFO - 📋 Agent classification: 'Show matching snomed codes' → agent_type='chat'
INFO - 📋 Session check: has_session_data=True, session_id=streamlit_abc123
INFO - 📋 Checking follow-up: is_explicit_new_search=False, is_concept_set=False
INFO - 📋 ✅ Follow-up confirmed: Using chat agent with RAG context from session
INFO - 📋 State: Retrieved 3 codes (18 lines) from session
INFO - 📋 State: Response generated (245 chars) using session context with 3 codes
```

### Scenario: Falls to Standard Routing (Still gets context!)

```
INFO - 📋 Agent classification: 'Show matching snomed codes' → agent_type='chat'
INFO - 📋 Session check: has_session_data=True, session_id=streamlit_abc123
INFO - 📋 Checking follow-up: is_explicit_new_search=False, is_concept_set=True
INFO - 📋 State initialized: agent_type='chat', user_input='Show matching snomed codes'
INFO - 📋 Routing to 'chat' agent (standard query path - NOT follow-up)
INFO - 📋 State: Passing 3 codes (18 lines) as context to chat agent
INFO - 📋 State: Chat response generated (245 chars) WITH context
```

### Scenario: No Context (BUG - shouldn't happen!)

```
INFO - 📋 Agent classification: 'Show matching snomed codes' → agent_type='chat'
INFO - 📋 Session check: has_session_data=False, session_id=streamlit_abc123
INFO - 📋 State initialized: agent_type='chat', user_input='Show matching snomed codes'
INFO - 📋 Routing to 'chat' agent (standard query path - NOT follow-up)
INFO - 📋 State: ⚠️ No session context available, using chat agent without RAG context
INFO - 📋 State: Chat response generated (180 chars) WITHOUT context
```

## How It Should Work Now

```
User: "find diabetes codes"
  → Stores: E10, E11, E13 with OHDSI field
  → OHDSI contains: {"maps":[{"vocabulary_id":"SNOMED"...}]}

User: "Show matching snomed codes"
  ↓
Agent Classification: "chat" (no ICD keywords)
  ↓
Session Check: has_session_data = True ✓
  ↓
Follow-up Detection:
  - is_explicit_new_search = False (no "new"/"different")
  - is_concept_set = False
  → Follow-up = True ✓
  ↓
Get Context with 3 codes and OHDSI fields
  ↓
System Message includes:
  "⚠️ IMPORTANT: If user asks for SNOMED, they are ALREADY in OHDSI field - DO NOT ask, just extract!
   
   MANDATORY RULES:
   2. For ANY SNOMED request: Immediately parse OHDSI field...
   3. For 'show snomed codes': Look at OHDSI, find vocabulary_id='SNOMED'...
   
   AVAILABLE ICD-10 CODES (3 codes):
   [E10] Type 1 diabetes...
     OHDSI: {\"maps\":[{\"vocabulary_id\":\"SNOMED\",\"concept_code\":\"46635009\"...}]}
   [E11] Type 2 diabetes...
     OHDSI: {\"maps\":[{\"vocabulary_id\":\"SNOMED\",\"concept_code\":\"44054006\"...}]}
   [E13] Other diabetes...
     OHDSI: {\"maps\":[{\"vocabulary_id\":\"SNOMED\",\"concept_code\":\"190372001\"...}]}"
  ↓
LLM Sees:
  - Warning: SNOMED already in OHDSI
  - Rule #2: For ANY SNOMED request → parse immediately
  - Data: 3 codes with OHDSI fields
  ↓
LLM Action:
  1. Parse OHDSI field for each code
  2. Find vocabulary_id="SNOMED"
  3. Extract concept_code
  4. Display results
  ↓
Response:
  "SNOMED Codes:
   - E10 → 46635009 (Diabetes mellitus type 1)
   - E11 → 44054006 (Diabetes mellitus type 2)
   - E13 → 190372001 (Other specified diabetes mellitus)"
```

## Debugging Steps

If "Show matching snomed codes" still asks for clarification:

### Step 1: Check Logs - Was it Follow-up?
```bash
grep "📋" | grep "Show matching snomed"
```

Look for:
- ✅ "Follow-up confirmed" → Good path
- ❌ "standard query path - NOT follow-up" → Still should get context, but check next

### Step 2: Check Context Was Passed
```bash
grep "📋 State: Passing" | tail -1
```

Look for:
- ✅ "Passing 3 codes (18 lines)" → Context passed
- ❌ "No session context available" → BUG - session lost

### Step 3: Check Response Generation
```bash
grep "📋 State: Chat response generated" | tail -1
```

Look for:
- ✅ "generated (245 chars) WITH context" → Context used
- ❌ "generated (180 chars) WITHOUT context" → No context passed

### Step 4: If Context WAS Passed but LLM Still Asked
This means LLM is ignoring instructions. Try:
1. Increase temperature to 0.0 in chat_agent config
2. Try different model (GPT-4 vs GPT-3.5)
3. Check if context string is actually populated (print it)

## Test Sequence

```bash
source .venv/bin/activate
streamlit run main.py
```

Try:
1. "find diabetes codes" → Should store E10, E11, E13
2. Check logs: `grep "Stored.*codes with OHDSI"`
3. "show matching snomed codes" → Should extract immediately
4. Check logs: Look for "Follow-up confirmed" and "Passing 3 codes"

Expected response:
```
SNOMED Codes from the ICD-10 codes in our dataset:

- **E10** (Type 1 diabetes mellitus without complications)
  → SNOMED: 46635009 - Diabetes mellitus type 1

- **E11** (Type 2 diabetes mellitus without complications)  
  → SNOMED: 44054006 - Diabetes mellitus type 2

- **E13** (Other specified diabetes mellitus without complications)
  → SNOMED: 190372001 - Other specified diabetes mellitus
```

## Files Modified

1. ✅ `modules/agents/chat_agent.py` - Added explicit SNOMED warning + numbered rules
2. ✅ `modules/master_agent.py` - Enhanced logging at all decision points

## Summary

**Enhanced LLM instructions with explicit SNOMED handling:**
- ⚠️ Warning: SNOMED already in OHDSI field
- Rule #2: ANY SNOMED request → parse immediately
- Rule #3: Specific examples of SNOMED requests
- Rule #8: Reinforces completeness

**Comprehensive logging added:**
- 📋 Agent classification
- 📋 Follow-up detection with boolean values
- 📋 Context passing with code counts
- 📋 Response generation WITH/WITHOUT indicator

**The LLM should now immediately extract SNOMED codes from OHDSI field without asking for clarification!**
