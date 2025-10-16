#!/usr/bin/env python3
"""
Test script to verify the SNOMED workflow:
1. Search for ICD codes first
2. Then add SNOMED mappings
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.master_agent import MasterAgent
from modules.interactive_session import interactive_session
import uuid

def test_snomed_workflow():
    """Test the proper workflow for SNOMED integration."""
    
    print("🔄 Testing SNOMED Workflow...")
    
    # Initialize agent
    agent = MasterAgent()
    session_id = str(uuid.uuid4())[:8]
    
    print(f"📋 Session ID: {session_id}")
    
    # Step 1: Search for ICD codes first
    print("\n🔍 Step 1: Searching for diabetes codes...")
    search_query = "Find diabetes codes"
    response1 = agent.chat(query=search_query, session_id=session_id)
    
    print("✅ Search Response (first 200 chars):")
    print(response1[:200] + "..." if len(response1) > 200 else response1)
    
    # Check session stats
    stats = interactive_session.get_session_stats(session_id)
    print(f"\n📊 Session Stats: {stats}")
    
    # Step 2: Now try to add SNOMED codes
    print("\n🏥 Step 2: Adding SNOMED codes...")
    snomed_query = "Add SNOMED codes"
    response2 = agent.chat(query=snomed_query, session_id=session_id)
    
    print("✅ SNOMED Response (first 200 chars):")
    print(response2[:200] + "..." if len(response2) > 200 else response2)
    
    # Final session stats
    final_stats = interactive_session.get_session_stats(session_id)
    print(f"\n📊 Final Session Stats: {final_stats}")
    
    print("\n✅ Workflow test completed!")

if __name__ == "__main__":
    test_snomed_workflow()