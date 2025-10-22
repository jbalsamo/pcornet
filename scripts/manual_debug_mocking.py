#!/usr/bin/env python3

import logging
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.abspath('.'))

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s %(name)s:%(filename)s:%(lineno)d %(message)s')

# Define FakeSearch and FakeLLM
class FakeSearch:
    def __init__(self, index, query, top=5, vector_field=None, **kwargs):
        print(f"🔧 FakeSearch initialized with query: {query}")
        self.index = index
        self.query = query
        self.top = top
        self.vector_field = vector_field

    def run(self):
        result = [
            {
                "score": 0.95,
                "document": {
                    "id": "I10",
                    "title": "Essential (primary) hypertension",
                    "content": "Elevated blood pressure... (ICD-10 I10)",
                },
            }
        ]
        print(f"🔧 FakeSearch returning: {result}")
        return result

class FakeLLM:
    def invoke(self, messages):
        response_content = "MOCK ICD ANSWER: Evidence suggests hypertension. I10 and [EXTERNAL]."
        print(f"🔧 FakeLLM returning: {response_content}")
        
        class MockResponse:
            def __init__(self, content):
                self.content = content
        
        return MockResponse(response_content)

def test_with_explicit_patching():
    print("=== Testing with explicit patching ===")
    
    # Import and patch
    import modules.search_tool as search_tool_mod
    import modules.agents.icd_agent as icd_agent_mod
    
    # Store original classes
    original_search = search_tool_mod.Search
    original_llm_factory = icd_agent_mod.IcdAgent._create_llm
    
    # Apply patches
    search_tool_mod.Search = FakeSearch
    icd_agent_mod.IcdAgent._create_llm = lambda self: FakeLLM()
    
    try:
        # Import and test
        from modules.agents.icd_agent import IcdAgent
        
        agent = IcdAgent(index="pcornet-icd-index")
        resp = agent.process("What is ICD code I10?")
        
        print(f"✅ Response type: {type(resp)}")
        print(f"✅ Response keys: {resp.keys() if isinstance(resp, dict) else 'N/A'}")
        if isinstance(resp, dict) and 'processed_response' in resp:
            print(f"✅ Processed response: {resp['processed_response']}")
        
    finally:
        # Restore original classes
        search_tool_mod.Search = original_search
        icd_agent_mod.IcdAgent._create_llm = original_llm_factory

if __name__ == "__main__":
    test_with_explicit_patching()