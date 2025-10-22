# Interactive Chat Features Documentation

## Overview

The PCORnet Assistant provides a **ChatGPT-style conversational interface** where analysts can naturally request medical coding information and dynamically modify results through pure text conversations. No buttons or complex UI elements - just natural language interaction like talking to ChatGPT.

## ChatGPT-Style Interface

### 🗣️ **Pure Conversational Design**

- **No Buttons**: All interactions through natural text input
- **Clean Chat Interface**: Familiar ChatGPT-like message bubbles
- **Instant Responses**: Real-time conversation flow
- **Context Preservation**: Remembers your entire conversation

### 💬 **Natural Language Processing**

- **Ask Anything**: "Find diabetes codes", "Add SNOMED mappings", "Show as table"
- **Follow-up Questions**: Build on previous responses naturally
- **Smart Understanding**: Interprets intent from conversational language
- **Flexible Phrasing**: Multiple ways to ask for the same information

## Key Features

### 🔄 Interactive Session Management

- **Session Persistence**: Each conversation maintains a unique session ID
- **Data Context**: Keeps track of all information shown to the user
- **Modification History**: Tracks all changes made during the session
- **Multi-User Support**: Concurrent sessions with isolated data

### 📝 Dynamic Data Manipulation

- **Add Information**: Request additional data like SNOMED codes, parent/child relationships
- **Remove Information**: Filter out unwanted codes or data types
- **Format Data**: Change how information is displayed (table, JSON, list)
- **Filter Data**: Show only specific types of information

### 🎯 Intelligent Command Detection

- **Natural Language**: Use conversational commands like "add SNOMED codes"
- **Context Awareness**: System understands what data is currently available
- **Smart Routing**: Automatically determines the best way to handle requests

## Interactive Commands

### Adding Information

| Command                | Description                                   | Example                                     |
| ---------------------- | --------------------------------------------- | ------------------------------------------- |
| `Add SNOMED codes`     | Include SNOMED mappings for current ICD codes | "Add SNOMED codes for these diabetes codes" |
| `Include parent codes` | Add hierarchical parent relationships         | "Also include parent codes"                 |
| `Add descriptions`     | Include detailed descriptions                 | "Add more detailed descriptions"            |
| `Show relationships`   | Include code relationships                    | "Show parent-child relationships"           |

### Removing Information

| Command                | Description                        | Example                           |
| ---------------------- | ---------------------------------- | --------------------------------- |
| `Remove [code]`        | Remove specific ICD or SNOMED code | "Remove I10" or "Remove 59621000" |
| `Remove SNOMED codes`  | Remove all SNOMED data             | "Remove all SNOMED codes"         |
| `Without descriptions` | Remove description fields          | "Show without descriptions"       |
| `Remove duplicates`    | Clean up duplicate entries         | "Remove any duplicates"           |

### Formatting Data

| Command          | Description               | Example                 |
| ---------------- | ------------------------- | ----------------------- |
| `Show as table`  | Display as markdown table | "Show this as a table"  |
| `Format as JSON` | Export as structured JSON | "Format as JSON"        |
| `Show as list`   | Simple bulleted list      | "Show as a simple list" |
| `Export data`    | Prepare for download      | "Export this data"      |

### Filtering Data

| Command               | Description              | Example                    |
| --------------------- | ------------------------ | -------------------------- |
| `Only show ICD codes` | Filter to ICD codes only | "Just show the ICD codes"  |
| `Just SNOMED codes`   | Show SNOMED codes only   | "Only SNOMED codes please" |
| `Filter by type`      | Show specific data types | "Only show mappings"       |

## Usage Examples

### Example 1: Building a Concept Set Interactively

```
👤 User: "Search for diabetes ICD codes"
🤖 Assistant: [Shows diabetes ICD codes E10, E11, E12...]

👤 User: "Add SNOMED codes"
🤖 Assistant: [Adds corresponding SNOMED mappings]

👤 User: "Remove E12 and show as table"
🤖 Assistant: [Removes E12 and displays remaining data in table format]

👤 User: "Export as JSON"
🤖 Assistant: [Provides downloadable JSON format]
```

### Example 2: Exploring Code Relationships

```
👤 User: "What are the codes for heart failure?"
🤖 Assistant: [Shows I50 heart failure codes]

👤 User: "Include parent codes and relationships"
🤖 Assistant: [Adds hierarchical structure and relationships]

👤 User: "Add SNOMED mappings"
🤖 Assistant: [Includes SNOMED equivalents]

👤 User: "Only show the main codes, not subcategories"
🤖 Assistant: [Filters to primary codes only]
```

### Example 3: Data Cleanup and Refinement

```
👤 User: "Find hypertension codes"
🤖 Assistant: [Shows various hypertension codes I10, I11, I12...]

👤 User: "Remove I15 and I16"
🤖 Assistant: [Removes specified codes]

👤 User: "Add SNOMED codes but only for essential hypertension"
🤖 Assistant: [Adds targeted SNOMED mappings]

👤 User: "Show as table for my report"
🤖 Assistant: [Formats as professional table]
```

## Technical Implementation

### Session Architecture

- **Session ID**: Unique identifier for each conversation
- **Data Store**: In-memory storage with optional persistence
- **Context Tracking**: Maintains current data state
- **Modification Log**: Records all changes for audit trail

### Data Structure

```python
DataItem:
  - item_type: 'icd_code', 'snomed_code', 'description', etc.
  - key: Unique identifier (e.g., 'I10', '59621000')
  - value: Display value
  - metadata: Additional information (relationships, mappings)
  - added_at: Timestamp
  - source_query: Original query that added this item
```

### Command Processing Flow

1. **Detection**: Natural language processing identifies modification requests
2. **Classification**: Determines modification type (add, remove, format, filter)
3. **Extraction**: Identifies data types and specific items involved
4. **Processing**: Executes the requested modification
5. **Response**: Provides updated data with context

## Benefits for Analysts

### 🎯 **Improved Workflow**

- **Iterative Exploration**: Refine searches step by step
- **Context Preservation**: Never lose track of current working set
- **Flexible Output**: Get data in the format you need

### 📊 **Enhanced Productivity**

- **Reduced Queries**: Modify existing results instead of new searches
- **Quick Adjustments**: Add or remove information with simple commands
- **Format Flexibility**: Switch between table, JSON, list views instantly

### 🔍 **Better Analysis**

- **Comprehensive Views**: Combine ICD codes, SNOMED mappings, relationships
- **Data Quality**: Remove duplicates and irrelevant information
- **Export Ready**: Generate reports in multiple formats

### 🤝 **User-Friendly Interface**

- **Natural Language**: No need to learn special syntax
- **Context Aware**: System remembers what you're working with
- **Helpful Prompts**: Suggestions for available actions

## Getting Started

### Just Start Typing!

The interface is designed to be as simple as ChatGPT:

1. **Open the app** - No setup required
2. **Type your question** - "Find ICD codes for heart failure"
3. **Get results** - See relevant codes immediately
4. **Continue the conversation** - "Add SNOMED codes", "Show as table", etc.
5. **Export if needed** - "Format as JSON" for download

### Example First Conversation

```
You: "Find diabetes ICD codes"
Assistant: [Shows E10, E11, E12 diabetes codes with descriptions]

You: "Add SNOMED codes"
Assistant: [Adds corresponding SNOMED mappings for each ICD code]

You: "Remove E12 and show as table"
Assistant: [Removes E12 and displays remaining data in table format]
```

No buttons, no menus, no complex interface - just natural conversation!

## Advanced Features

### Session Persistence

- Sessions maintain state across page refreshes
- Export session data for later use
- Clear sessions when starting new projects

### Multi-Format Export

- **JSON**: Structured data for programmatic use
- **Markdown Table**: Ready for documentation
- **CSV**: Compatible with Excel and other tools

### Audit Trail

- Track all modifications made during session
- See when each item was added or removed
- Maintain source query for each data item

---

_The interactive chat functionality transforms the PCORnet Assistant from a simple search tool into a dynamic workspace for medical coding analysis and concept set development._
