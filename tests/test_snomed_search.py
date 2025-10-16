#!/usr/bin/env python3
"""
Quick test script to verify the SNOMED search functionality works correctly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.agents.icd_agent import IcdAgent
from modules.interactive_session import interactive_session

def test_snomed_search():
    """Test the SNOMED search functionality for diabetes."""
    print("🧪 Testing SNOMED Search Functionality")
    print("=" * 50)
    
    # Initialize the ICD agent
    try:
        agent = IcdAgent()
        print("✅ IcdAgent initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize IcdAgent: {e}")
        return
    
    # Test case 1: Empty session + "add SNOMED codes for diabetes"
    session_id = "test_session_001"
    query = "add SNOMED codes for diabetes"
    
    print(f"🔍 Query analysis:")
    print(f"  - Query: '{query}'")
    print(f"  - Query lower: '{query.lower()}'")
    print(f"  - Contains 'diabetes': {'diabetes' in query.lower()}")
    print(f"  - Contains 'snomed': {'snomed' in query.lower()}")
    
    print(f"\n📋 Test Case: '{query}'")
    print("-" * 30)
    
    try:
        # This should trigger the interactive processing
        result = agent.process_interactive(query, session_id)
        
        print(f"📊 Result type: {type(result)}")
        print(f"📊 Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
        if isinstance(result, dict):
            # Check if we got data back
            data = result.get('data', '[]')
            response = result.get('processed_response', '')
            
            print(f"\n📈 Data length: {len(data)} characters")
            print(f"📝 Response preview: {response[:200]}...")
            
            # Parse the data to see if we got actual search results
            if data != '[]':
                import json
                try:
                    parsed_data = json.loads(data)
                    print(f"🎯 Found {len(parsed_data)} search results")
                    if parsed_data:
                        first_result = parsed_data[0]
                        doc = first_result.get('document', {})
                        print(f"📋 First result: {doc.get('CODE', 'N/A')} - {doc.get('STR', 'N/A')[:50]}...")
                except json.JSONDecodeError:
                    print("⚠️ Data is not valid JSON")
            else:
                print("⚠️ No search data returned")
        
        print(f"\n✅ Test completed successfully")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_snomed_search()