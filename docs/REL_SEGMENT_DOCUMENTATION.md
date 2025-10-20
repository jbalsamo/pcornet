# REL Segment Search Documentation

## Overview

The REL segment functionality has been successfully implemented in the PCORnet ICD system, enabling users to search for SNOMED code relationships including parent-child hierarchies and "is a" relationships. This functionality extends the existing ICD search capabilities with comprehensive relationship data.

## What is the REL Segment?

The REL segment contains relationship data that describes how medical codes relate to each other, including:

- **Parent-Child Relationships (PAR/CHD)**: Hierarchical code structures
- **SNOMED Mappings (RO)**: Connections between ICD and SNOMED codes
- **Synonyms (SY)**: Alternative representations of the same concept
- **Required/Associated Codes (RQ)**: Related or prerequisite codes

## Features Implemented

### 1. Relationship Query Detection

The system automatically detects when users are asking for relationship information based on keywords like:

- "parent codes", "child codes", "hierarchy"
- "SNOMED mapping", "maps to"
- "related to", "relationships"
- "is a", "part of", "belongs to"

### 2. Parent-Child Hierarchy Search

Users can query for hierarchical relationships:

```
Query: "What are the parent codes for I10?"
Response: Shows I10 belongs to "Hypertensive diseases (I10-I1A)" under "Diseases of the circulatory system (I00-I99)"

Query: "Show me child codes for I12"
Response: Lists I12.0 and I12.9 as specific subtypes of hypertensive chronic kidney disease
```

### 3. SNOMED Code Mappings

Users can find SNOMED equivalents for ICD codes:

```
Query: "What is the SNOMED mapping for I21?"
Response: Shows I21 "Acute myocardial infarction" maps to SNOMED code 57054005 with the same description
```

### 4. General Relationship Search

Users can explore broader relationships:

```
Query: "What codes are related to I50?"
Response: Shows all relationship types (parent, child, synonyms, etc.) for heart failure codes
```

## Technical Implementation

### Core Components

1. **RelationshipSearch Class** (`modules/relationship_search.py`)

   - Extends the base Search functionality
   - Provides specialized methods for relationship queries
   - Parses REL segment JSON data into structured format

2. **Enhanced IcdAgent** (`modules/agents/icd_agent.py`)

   - Detects relationship queries automatically
   - Routes to appropriate relationship search methods
   - Generates LLM responses with relationship context

3. **Master Agent Integration**
   - Seamlessly routes relationship queries to IcdAgent
   - Maintains backward compatibility with regular ICD queries

### Data Structure

The REL segment data in Azure AI Search contains JSON objects with:

- `REL`: Relationship type (PAR, CHD, RO, SY, RQ)
- `CODE`: Related code
- `STR`: Description/name of related code
- `SAB`: Source vocabulary (ICD10CM, SNOMEDCT_US, etc.)
- `RELA`: Relationship attribute (optional)

## Usage Examples

### Through Streamlit Interface

Users can ask natural language questions:

- "What are the parent codes for diabetes codes?"
- "Show me the SNOMED mapping for I10"
- "What codes are under hypertensive diseases?"
- "What is the hierarchy for heart failure codes?"

### Through API/Direct Integration

```python
from modules.agents.icd_agent import IcdAgent

agent = IcdAgent()
result = agent.process("What are the parent codes for I10?")
print(result["processed_response"])
```

## Response Format

Relationship queries return comprehensive responses including:

1. **Hierarchical Information**: Clear parent-child structures
2. **SNOMED Mappings**: Direct code equivalencies and relationships
3. **Citations**: Document IDs in square brackets [I10] for traceability
4. **Multiple Relationship Types**: PAR, CHD, RO, SY, RQ relationships
5. **Source Attribution**: Clear indication of data sources (ICD10CM, SNOMEDCT_US, etc.)

## Testing and Validation

The REL segment functionality has been thoroughly tested with:

✅ **Unit Tests**: Individual component validation  
✅ **Integration Tests**: End-to-end workflow testing  
✅ **Query Detection Tests**: Relationship vs. regular query classification  
✅ **Data Parsing Tests**: REL segment JSON parsing and formatting  
✅ **Master Agent Tests**: Complete routing and response validation

All tests pass successfully, confirming the system is production-ready.

## Benefits

1. **Enhanced Medical Coding**: Users can explore code relationships and hierarchies
2. **SNOMED Integration**: Seamless access to SNOMED mappings for interoperability
3. **Improved Search**: More comprehensive responses with relationship context
4. **Educational Value**: Users learn about code structures and relationships
5. **Backward Compatibility**: Existing ICD queries continue to work as before

## Future Enhancements

Potential areas for expansion:

- Visual hierarchy diagrams
- Bulk relationship exports
- Custom relationship filtering
- Cross-vocabulary relationship exploration
- Relationship-based concept set building

---

_The REL segment functionality is now fully operational and ready for production use. Users can explore the rich relationship data available in the PCORnet ICD index through natural language queries._
