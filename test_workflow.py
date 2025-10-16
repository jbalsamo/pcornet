#!/usr/bin/env python3

import logging
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.abspath('.'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

def test_concept_set_workflow():
    print("=== Testing Concept Set Workflow ===")
    
    try:
        from modules.master_agent import MasterAgent
        
        # Initialize the master agent
        master_agent = MasterAgent()
        
        # Test the concept set workflow
        query = "create a concept set for diabetes"
        print(f"Testing query: {query}")
        
        # This should trigger the concept set workflow
        response = master_agent.chat(query)
        
        print(f"✅ Success! Response length: {len(response)} characters")
        print(f"✅ Response preview: {response[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_concept_set_workflow()
    sys.exit(0 if success else 1)