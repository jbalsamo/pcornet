#!/usr/bin/env python3
"""
Test script for REL segment functionality in the ICD Agent.
Tests parent-child relationships, SNOMED mappings, and general relationship queries.
"""

import logging
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.abspath('.'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

def test_relationship_query_detection():
    """Test if the IcdAgent correctly identifies relationship queries."""
    print("=== Testing Relationship Query Detection ===")
    
    try:
        from modules.agents.icd_agent import IcdAgent
        
        agent = IcdAgent()
        
        # Test various relationship query types
        relationship_queries = [
            "What are the parent codes of I10?",
            "Show me child codes for I12",
            "What is the SNOMED mapping for I21?",
            "What codes are related to I50?",
            "Show me the hierarchy for hypertension codes",
        ]
        
        non_relationship_queries = [
            "What is ICD code I10?",
            "Tell me about hypertension",
            "Find diabetes codes",
        ]
        
        print("Testing relationship queries:")
        for query in relationship_queries:
            is_rel_query = agent._is_relationship_query(query)
            status = "✅" if is_rel_query else "❌"
            print(f"{status} '{query}' -> {is_rel_query}")
        
        print("\nTesting non-relationship queries:")
        for query in non_relationship_queries:
            is_rel_query = agent._is_relationship_query(query)
            status = "❌" if is_rel_query else "✅"
            print(f"{status} '{query}' -> {is_rel_query}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in relationship query detection: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_hierarchy_search():
    """Test parent-child hierarchy search for specific codes."""
    print("\n=== Testing Hierarchy Search ===")
    
    try:
        from modules.agents.icd_agent import IcdAgent
        
        agent = IcdAgent()
        
        # Test hierarchy for a hypertension code
        query = "What are the parent and child codes for I12?"
        print(f"Testing hierarchy query: {query}")
        
        response = agent.process(query)
        
        if "error" in response:
            print(f"❌ Error: {response['error']}")
            return False
        
        print(f"✅ Response received (length: {len(response['processed_response'])} chars)")
        print("Response preview:")
        print("=" * 60)
        print(response['processed_response'][:500] + "..." if len(response['processed_response']) > 500 else response['processed_response'])
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Error in hierarchy search: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_snomed_mapping_search():
    """Test SNOMED mapping search for ICD codes."""
    print("\n=== Testing SNOMED Mapping Search ===")
    
    try:
        from modules.agents.icd_agent import IcdAgent
        
        agent = IcdAgent()
        
        # Test SNOMED mapping for a specific code
        query = "What is the SNOMED mapping for I10?"
        print(f"Testing SNOMED mapping query: {query}")
        
        response = agent.process(query)
        
        if "error" in response:
            print(f"❌ Error: {response['error']}")
            return False
        
        print(f"✅ Response received (length: {len(response['processed_response'])} chars)")
        print("Response preview:")
        print("=" * 60)
        print(response['processed_response'][:500] + "..." if len(response['processed_response']) > 500 else response['processed_response'])
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Error in SNOMED mapping search: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_general_relationship_search():
    """Test general relationship search."""
    print("\n=== Testing General Relationship Search ===")
    
    try:
        from modules.agents.icd_agent import IcdAgent
        
        agent = IcdAgent()
        
        # Test general relationship query
        query = "Show me relationships for hypertension codes"
        print(f"Testing general relationship query: {query}")
        
        response = agent.process(query)
        
        if "error" in response:
            print(f"❌ Error: {response['error']}")
            return False
        
        print(f"✅ Response received (length: {len(response['processed_response'])} chars)")
        print("Response preview:")
        print("=" * 60)
        print(response['processed_response'][:500] + "..." if len(response['processed_response']) > 500 else response['processed_response'])
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Error in general relationship search: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_direct_relationship_search():
    """Test the RelationshipSearch class directly."""
    print("\n=== Testing Direct RelationshipSearch ===")
    
    try:
        from modules.relationship_search import RelationshipSearch
        
        # Test hierarchy search
        print("Testing hierarchy search for I10...")
        rel_search = RelationshipSearch(
            index="pcornet-icd-index",
            query="I10",
            top=10
        )
        
        hierarchy_data = rel_search.search_parent_child_hierarchy("I10")
        
        print(f"✅ Found {len(hierarchy_data['parents'])} parents and {len(hierarchy_data['children'])} children")
        
        if hierarchy_data['parents']:
            print("Sample parent:")
            print(f"  {hierarchy_data['parents'][0]['parent_code']}: {hierarchy_data['parents'][0]['parent_name']}")
        
        if hierarchy_data['children']:
            print("Sample child:")
            print(f"  {hierarchy_data['children'][0]['child_code']}: {hierarchy_data['children'][0]['child_name']}")
        
        # Test SNOMED mapping search
        print("\nTesting SNOMED mapping search for I10...")
        snomed_mappings = rel_search.search_snomed_mappings("I10")
        
        print(f"✅ Found {len(snomed_mappings)} SNOMED mappings")
        
        if snomed_mappings:
            print("Sample SNOMED mapping:")
            mapping = snomed_mappings[0]
            print(f"  ICD: {mapping.get('icd_code')} -> SNOMED: {mapping.get('snomed_code')}")
            print(f"  Names: {mapping.get('icd_name')} -> {mapping.get('snomed_name')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in direct relationship search: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all REL segment functionality tests."""
    print("🔍 Testing REL Segment Functionality")
    print("=" * 50)
    
    tests = [
        test_relationship_query_detection,
        test_direct_relationship_search,
        test_hierarchy_search,
        test_snomed_mapping_search,
        test_general_relationship_search,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = sum(results)
    total = len(results)
    
    for i, (test, result) in enumerate(zip(tests, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{i+1}. {test.__name__}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All REL segment functionality tests passed!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)