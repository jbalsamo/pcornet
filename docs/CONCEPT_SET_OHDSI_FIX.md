# Concept Set OHDSI/SNOMED Fix

## Problem

When creating a concept set with SNOMED codes using:
```
"Create a concept set for Heart Disease. Include SNOMED codes for data."
```

The response included ICD codes but said:
```
❌ "Note: Only ICD codes and descriptions are provided, as no SNOMED codes were included in your data."
```

**But the OHDSI field DOES contain SNOMED codes!**

## Root Causes

### 1. ConceptSetExtractorAgent Only Extracted CODE, STR, Score

**File**: `modules/agents/concept_set_extractor_agent.py`

```python
# OLD - Missing OHDSI and other fields
for item in data:
    document = item.get("document", {})
    code = document.get("CODE", "N/A")
    label = document.get("STR", "N/A")
    score = item.get("score", 0.0)
    formatted_lines.append(f"Code: {code}, Label: {label}, Score: {score:.4f}")
```

**Result**: OHDSI field never extracted, lost in the workflow

### 2. CONCEPT_SET_FORMATTING_PROMPT Didn't Mention OHDSI

**File**: `modules/config.py`

```python
# OLD - No mention of OHDSI or SNOMED
CONCEPT_SET_FORMATTING_PROMPT = """
You are a helpful AI assistant. Format the data...
Do not add any information that is not in the provided data.
"""
```

**Result**: LLM didn't know OHDSI field contained SNOMED codes

## Solutions Implemented

### 1. Extract ALL Document Fields (Including OHDSI)

**File**: `modules/agents/concept_set_extractor_agent.py` (Lines 52-71)

```python
# Log available fields for debugging
available_fields = list(document.keys())
logger.debug(f"📋 Extracting {code}: fields available = {available_fields}")

# Build line with code, label, and score
line = f"Code: {code}, Label: {label}, Score: {score:.4f}"

# Add ALL additional fields from document (OHDSI, SAB, etc.)
additional_fields = []
for field, value in document.items():
    if field not in ["CODE", "STR", "id"] and value:
        # Format field name nicely
        additional_fields.append(f"{field}: {value}")
        logger.debug(f"📋 Added field {field} for {code}")

if additional_fields:
    line += ", " + ", ".join(additional_fields)
    logger.info(f"📋 Extracted {code} with {len(additional_fields)} additional fields (including OHDSI if present)")
```

**Benefits**:
- ✅ Extracts OHDSI field
- ✅ Extracts SAB and any other fields
- ✅ Logs what fields are found
- ✅ Confirms OHDSI presence

### 2. Enhanced CONCEPT_SET_FORMATTING_PROMPT with OHDSI Instructions

**File**: `modules/config.py` (Lines 224-252)

```python
CONCEPT_SET_FORMATTING_PROMPT = """
You are a helpful AI assistant specializing in medical coding. Your task is to format the provided data into a clear and readable format based on the user's original request.

🔒 CRITICAL: The data you are given is the ONLY source of information. Do not add any codes or information not in the provided data.

⚠️ IMPORTANT OHDSI FIELD: If the data includes an OHDSI field, it contains mappings to other vocabularies in JSON format:
- The OHDSI field has a "maps" array
- Each map contains: vocabulary_id, concept_code, concept_name, relationship_id, domain_id
- When vocabulary_id="SNOMED", the concept_code is the SNOMED CT code and concept_name is its description
- If the user asks for SNOMED codes, extract them from the OHDSI field - they are already there!

User's original request: "{query}"
Data to format:
---
{context_data}
---

MANDATORY RULES:
1. Use ONLY the data provided above
2. For SNOMED requests: Parse the OHDSI field, find vocabulary_id="SNOMED", extract concept_code and concept_name
3. If user asks for SNOMED codes and OHDSI field exists, include a SNOMED column in your table
4. Format as requested (table, JSON, list, etc.)
5. If the user asks for a table, create a markdown table
6. If the user does not specify a format, default to a markdown table with appropriate columns
7. If OHDSI data is present and user mentions SNOMED, automatically include SNOMED codes
8. Do not say "no SNOMED codes provided" if OHDSI field exists - extract them!

Based on the user's request, present the data in the best possible format.
"""
```

**Key Changes**:
- 🔒 CRITICAL and ⚠️ IMPORTANT callouts
- Explicit explanation of OHDSI structure
- Rule #2: How to extract SNOMED
- Rule #3: Include SNOMED column when requested
- Rule #7: Automatically include if user mentions SNOMED
- Rule #8: Don't say "no SNOMED" if OHDSI exists

## How the Concept Set Workflow Works Now

```
User: "Create a concept set for Heart Disease. Include SNOMED codes."
  ↓
Master Agent: Detects concept set query
  ↓
Step 1: ICD Agent searches for "Heart Disease"
  → Returns: I51.9, I11, I51, etc. with OHDSI fields
  → OHDSI contains: {"maps":[{"vocabulary_id":"SNOMED","concept_code":"123456"...}]}
  ↓
Step 2: Store in state.context (raw JSON with OHDSI)
  📋 Log: "State updated: context set (12453 chars) with ICD data"
  ↓
Step 3: ConceptSetExtractorAgent.process(state.context)
  → Extracts: CODE, STR, score, OHDSI, SAB, etc.
  📋 Log: "Extracting I51.9: fields available = ['CODE', 'STR', 'OHDSI', 'SAB', ...]"
  📋 Log: "Extracted I51.9 with 3 additional fields (including OHDSI if present)"
  → Output: "Code: I51.9, Label: Heart disease, Score: 0.9234, OHDSI: {...}, SAB: ICD10CM"
  ↓
Step 4: ChatAgent.format_concept_set(original_query, extracted_data)
  → Receives prompt with OHDSI field instructions
  → System message: "⚠️ IMPORTANT OHDSI FIELD: ... SNOMED codes in vocabulary_id='SNOMED'"
  → Data includes: "OHDSI: {\"maps\":[{\"vocabulary_id\":\"SNOMED\",\"concept_code\":\"56265001\"...}]}"
  ↓
LLM Processing:
  1. Sees: User asked for SNOMED codes
  2. Sees: OHDSI field present in data
  3. Rule #2: Parse OHDSI, find vocabulary_id="SNOMED"
  4. Extract: concept_code and concept_name
  5. Create table with ICD + SNOMED columns
  ↓
Response:
  | Code | Description | SNOMED Code | SNOMED Description |
  |------|-------------|-------------|-------------------|
  | I51.9 | Heart disease, unspecified | 56265001 | Heart disease |
  | I11 | Hypertensive heart disease | 48194001 | Hypertensive heart disease |
  | ... | ... | ... | ... |
```

## Expected Log Output

```
INFO - Concept set query detected. Starting concept set workflow.
INFO - Workflow Step 1: Calling IcdAgent
INFO - 📋 State updated: context set (12453 chars) with ICD data from search
INFO - Workflow Step 3: Calling ConceptSetExtractorAgent
DEBUG - 📋 Extracting I51.9: fields available = ['CODE', 'STR', 'id', 'OHDSI', 'SAB', 'CCS']
DEBUG - 📋 Added field OHDSI for I51.9
DEBUG - 📋 Added field SAB for I51.9
DEBUG - 📋 Added field CCS for I51.9
INFO - 📋 Extracted I51.9 with 3 additional fields (including OHDSI if present)
DEBUG - 📋 Extracting I11: fields available = ['CODE', 'STR', 'id', 'OHDSI', 'SAB']
INFO - 📋 Extracted I11 with 2 additional fields (including OHDSI if present)
...
INFO - Workflow Step 4: Calling ChatAgent for final formatting.
```

## Debugging

### If SNOMED Codes Still Not Showing

**Step 1: Check ConceptSetExtractorAgent Logs**
```bash
grep "📋 Extracting" | head -5
```

Look for:
- ✅ "fields available = ['CODE', 'STR', 'OHDSI', ...]" → OHDSI present
- ❌ "fields available = ['CODE', 'STR', 'id']" → OHDSI missing (BUG in search)

**Step 2: Check Additional Fields**
```bash
grep "📋 Extracted.*additional fields"
```

Look for:
- ✅ "Extracted I51.9 with 3 additional fields" → Fields extracted
- ❌ "Extracted I51.9 with 0 additional fields" → No OHDSI (search problem)

**Step 3: Check Raw Context Data**
Add debug logging in master_agent.py after line 312:
```python
logger.debug(f"Raw ICD data sample: {state['context'][:500]}")
```

Look for OHDSI field in the JSON.

**Step 4: Check Formatted Data Sent to LLM**
Add debug logging in chat_agent.py in format_concept_set method:
```python
logger.debug(f"Context data sent to LLM: {context_data[:500]}")
```

Should see: "OHDSI: {...}"

## Test Scenario

```bash
source .venv/bin/activate
streamlit run main.py
```

Try:
```
"Create a concept set for Heart Disease. Include SNOMED codes for data."
```

Expected Response:
```
Here is a concept set for Heart Disease with SNOMED codes:

| Code | Description | SNOMED Code | SNOMED Description |
|------|-------------|-------------|-------------------|
| I51.9 | Heart disease, unspecified | 56265001 | Heart disease |
| I11 | Hypertensive heart disease | 48194001 | Hypertensive heart disease |
| I51 | Complications and ill-defined descriptions of heart disease | 368009 | Heart valve disorder |
| ...  | ... | ... | ... |
```

NOT:
```
❌ "Note: Only ICD codes provided, no SNOMED codes were included in your data."
```

## Files Modified

1. ✅ `modules/agents/concept_set_extractor_agent.py` - Extract ALL fields including OHDSI
2. ✅ `modules/config.py` - Enhanced CONCEPT_SET_FORMATTING_PROMPT with OHDSI instructions

## Summary

**Concept set workflow now includes OHDSI field:**
- ✅ ConceptSetExtractorAgent extracts ALL fields (OHDSI, SAB, etc.)
- ✅ CONCEPT_SET_FORMATTING_PROMPT explains OHDSI structure
- ✅ LLM instructed to parse OHDSI for SNOMED codes
- ✅ Logging shows what fields are extracted
- ✅ SNOMED codes now available in concept sets

**The concept set workflow now properly handles SNOMED codes from the OHDSI field!** 🎉
