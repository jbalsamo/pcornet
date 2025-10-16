# Test Files Conversion Status

## Completed ✅
- test_workflow.py - Converted to pytest format
- test_citations.py - Converted to pytest format  
- test_routing.py - Converted to pytest format
- test_direct_icd.py - Converted to pytest format

## Already Pytest Format ✅
- test_concept_set_extractor_agent.py
- test_config.py
- test_conversation_history.py
- test_icd_agent.py
- test_search_tool.py
- test_security.py

## Needs Conversion 🔄
- test_icd_agent_direct.py
- test_import_request.py
- test_index_structure.py
- test_rel_integration.py
- test_rel_segment.py
- test_sidebar_history.py
- test_snomed_fix.py
- test_snomed_search.py
- test_snomed_workflow.py

## Debug Files (Moved to tests/)
- debug_citations.py - Keep as-is for debugging
- debug_mocking.py - Keep as-is for debugging

## Conversion Rules Applied

1. **Removed**:
   - `#!/usr/bin/env python3` shebang
   - `sys.path.insert()` path manipulation
   - `logging.basicConfig()` calls
   - `if __name__ == "__main__"` blocks
   - `sys.exit()` calls
   - Print statements used for debugging

2. **Added**:
   - Module docstrings
   - `import pytest`
   - Proper assertions instead of print/return True/False
   - Function docstrings
   - Meaningful assertion messages

3. **Structure**:
   - Follow pytest discovery conventions
   - Use `test_*` function names
   - Use proper assert statements
   - Leverage conftest.py fixtures where applicable
