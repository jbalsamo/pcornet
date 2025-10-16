#!/usr/bin/env python3

import logging
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.abspath('.'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')

def test_master_agent_routing():
    print("=== Testing Master Agent Routing ===")
    
    try:
        from modules.master_agent import MasterAgent
        
        # Initialize the master agent
        master_agent = MasterAgent()
        
        # Test different queries to see routing
        queries = [
            "What is ICD code I10?",
            "Tell me about hypertension",
            "icd code I10",
            "explain I10"
        ]
        
        for query in queries:
            print(f"\n--- Testing query: '{query}' ---")
            
            # Manually check classification (if method exists)
            if hasattr(master_agent, '_classify_agent_type'):
                agent_type = master_agent._classify_agent_type(query)
                print(f"Agent type classification: {agent_type}")
            
            if hasattr(master_agent, '_is_concept_set_query'):
                is_concept_set = master_agent._is_concept_set_query(query)
                print(f"Is concept set query: {is_concept_set}")
            
            # Test the actual routing
            response = master_agent.chat(query)
            print(f"Response length: {len(response)}")
            
            # Check for citations
            import re
            citations = re.findall(r'\[([^\]]+)\]', response)
            print(f"Citations found: {citations}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_master_agent_routing()
    sys.exit(0 if success else 1)