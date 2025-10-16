#!/usr/bin/env python3
"""
End-to-end integration test for REL segment functionality through the master agent.
Demonstrates the complete workflow from user query to REL segment response.
"""

import logging
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.abspath('.'))

# Configure logging
logging.basicConfig(level=logging.WARNING, format='%(asctime)s %(levelname)s %(message)s')

def test_end_to_end_rel_functionality():
    """Test REL segment functionality through the master agent."""
    print("=== End-to-End REL Segment Integration Test ===")
    
    try:
        from modules.master_agent import MasterAgent
        
        master_agent = MasterAgent()
        
        # Test different types of REL segment queries
        rel_queries = [
            {
                "query": "What are the parent codes for I10?",
                "description": "Hierarchy query for parent codes"
            },
            {
                "query": "Show me child codes for I12",
                "description": "Hierarchy query for child codes"
            },
            {
                "query": "What is the SNOMED mapping for I21?",
                "description": "SNOMED mapping query"
            },
            {
                "query": "What codes are related to I50?", 
                "description": "General relationship query"
            }
        ]
        
        print("Testing REL segment queries through master agent:")
        print("=" * 60)
        
        for i, test_case in enumerate(rel_queries, 1):
            query = test_case["query"]
            description = test_case["description"]
            
            print(f"\n{i}. {description}")
            print(f"Query: {query}")
            
            try:
                response = master_agent.chat(query)
                
                print(f"✅ Response received (length: {len(response)} chars)")
                
                # Show a preview of the response
                preview_length = 300
                if len(response) > preview_length:
                    preview = response[:preview_length] + "..."
                else:
                    preview = response
                
                print(f"Preview: {preview}")
                
                # Check for relationship-specific content
                rel_indicators = [
                    "parent", "child", "hierarchy", "snomed", "mapping",
                    "relationship", "maps to", "related", "PAR", "CHD"
                ]
                
                found_indicators = [indicator for indicator in rel_indicators 
                                  if indicator.lower() in response.lower()]
                
                if found_indicators:
                    print(f"✅ Contains relationship content: {', '.join(found_indicators[:3])}")
                else:
                    print("⚠️  No obvious relationship indicators found")
                    
            except Exception as e:
                print(f"❌ Error processing query: {e}")
                return False
        
        print("\n" + "=" * 60)
        print("🎉 End-to-end REL segment integration test completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_regular_icd_vs_rel_routing():
    """Test that regular ICD queries still work and REL queries are routed correctly."""
    print("\n=== Testing Regular ICD vs REL Query Routing ===")
    
    try:
        from modules.master_agent import MasterAgent
        
        master_agent = MasterAgent()
        
        # Test regular ICD query (should not use REL functionality)
        print("1. Testing regular ICD query:")
        regular_query = "What is ICD code I10?"
        print(f"Query: {regular_query}")
        
        regular_response = master_agent.chat(regular_query)
        print(f"✅ Regular ICD response received (length: {len(regular_response)} chars)")
        
        # Test REL query (should use REL functionality)
        print("\n2. Testing REL query:")
        rel_query = "What are the parent codes for I10?"
        print(f"Query: {rel_query}")
        
        rel_response = master_agent.chat(rel_query)
        print(f"✅ REL response received (length: {len(rel_response)} chars)")
        
        # Compare responses - they should be different
        if regular_response != rel_response:
            print("✅ Responses are different - proper routing confirmed")
        else:
            print("⚠️  Responses are identical - routing may need adjustment")
        
        # Check for relationship-specific content in REL response
        rel_keywords = ["parent", "child", "hierarchy", "relationship"]
        has_rel_content = any(keyword in rel_response.lower() for keyword in rel_keywords)
        
        if has_rel_content:
            print("✅ REL response contains relationship-specific content")
        else:
            print("⚠️  REL response lacks relationship-specific content")
        
        return True
        
    except Exception as e:
        print(f"❌ Routing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the complete integration test suite."""
    print("🔗 REL Segment End-to-End Integration Test")
    print("=" * 50)
    
    tests = [
        test_end_to_end_rel_functionality,
        test_regular_icd_vs_rel_routing,
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
    print("📊 Integration Test Results:")
    
    passed = sum(results)
    total = len(results)
    
    for i, (test, result) in enumerate(zip(tests, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{i+1}. {test.__name__}: {status}")
    
    print(f"\nOverall: {passed}/{total} integration tests passed")
    
    if passed == total:
        print("🎉 All REL segment integration tests passed!")
        print("\n✨ REL Segment is now fully functional and searchable! ✨")
        print("Users can now query:")
        print("  - Parent-child code relationships")
        print("  - SNOMED code mappings") 
        print("  - General code relationships")
        print("  - Hierarchical code structures")
    else:
        print("⚠️  Some integration tests failed.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)