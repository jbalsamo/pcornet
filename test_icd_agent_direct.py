#!/usr/bin/env python3

import logging
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.abspath('.'))

# Configure logging to see debug output
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s %(name)s:%(filename)s:%(lineno)d %(message)s')

def test_icd_agent_directly():
    print("=== Testing IcdAgent Directly ===")
    
    try:
        from modules.agents.icd_agent import IcdAgent
        
        # Initialize the ICD agent directly
        agent = IcdAgent()
        
        # Test direct call
        query = "What is ICD code I10?"
        print(f"Testing query: {query}")
        
        result = agent.process(query)
        
        print(f"✅ Result type: {type(result)}")
        print(f"✅ Result keys: {result.keys() if isinstance(result, dict) else 'N/A'}")
        
        if isinstance(result, dict) and 'processed_response' in result:
            processed_response = result['processed_response']
            print(f"✅ Processed response length: {len(processed_response)}")
            print(f"✅ Processed response:")
            print("=" * 80)
            print(processed_response)
            print("=" * 80)
            
            # Check for citations
            import re
            citations = re.findall(r'\[([^\]]+)\]', processed_response)
            if citations:
                print(f"✅ Found citations in processed_response: {citations}")
            else:
                print("⚠️  No citations found in processed_response")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_icd_agent_directly()
    sys.exit(0 if success else 1)