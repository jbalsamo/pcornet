#!/usr/bin/env python3

import logging
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.abspath('.'))

# Configure logging to be less verbose
logging.basicConfig(level=logging.WARNING, format='%(asctime)s %(levelname)s %(message)s')

def test_citation_in_concept_set():
    print("=== Testing Citation Functionality in Concept Set ===")
    
    try:
        from modules.master_agent import MasterAgent
        
        # Initialize the master agent
        master_agent = MasterAgent()
        
        # Test the concept set workflow
        query = "create a concept set for hypertension"
        print(f"Testing query: {query}")
        
        # This should trigger the concept set workflow
        response = master_agent.chat(query)
        
        print(f"✅ Success! Response length: {len(response)} characters")
        print(f"✅ Full response:")
        print("=" * 80)
        print(response)
        print("=" * 80)
        
        # Check for citations in brackets
        import re
        citations = re.findall(r'\[([^\]]+)\]', response)
        if citations:
            print(f"✅ Found citations: {citations}")
        else:
            print("⚠️  No bracketed citations found in response")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_citation_in_concept_set()
    sys.exit(0 if success else 1)