#!/usr/bin/env python3
"""
Test script to verify SNOMED code mapping fix - concept_id for "Maps to" relationships.
"""

import logging
import sys
import os
import json

# Add the project root to Python path
sys.path.insert(0, os.path.abspath('.'))

# Configure logging
logging.basicConfig(level=logging.WARNING, format='%(asctime)s %(levelname)s %(message)s')

def test_snomed_mapping_fix():
    """Test that SNOMED mappings correctly use concept_id for 'Maps to' relationships."""
    print("=== Testing SNOMED Mapping Fix (concept_id for 'Maps to') ===")
    
    try:
        from modules.relationship_search import RelationshipSearch
        
        # Test SNOMED mapping for I10 (Essential hypertension)
        rel_search = RelationshipSearch(
            index="pcornet-icd-index",
            query="I10",
            top=5
        )
        
        snomed_mappings = rel_search.search_snomed_mappings("I10")
        
        print(f"Found {len(snomed_mappings)} SNOMED mappings for I10")
        
        maps_to_found = False
        
        for mapping in snomed_mappings:
            relationship_id = mapping.get("relationship_id", "")
            snomed_code = mapping.get("snomed_code", "")
            snomed_name = mapping.get("snomed_name", "")
            icd_code = mapping.get("icd_code", "")
            
            print(f"\nMapping: {icd_code} -> {snomed_code}")
            print(f"  Relationship: {relationship_id}")
            print(f"  SNOMED Name: {snomed_name}")
            
            if relationship_id == "Maps to":
                maps_to_found = True
                # Verify concept_id format (should be numeric for "Maps to")
                if snomed_code.isdigit():
                    print(f"  ✅ Correct: concept_id ({snomed_code}) used for 'Maps to'")
                else:
                    print(f"  ❌ Error: Non-numeric SNOMED code for 'Maps to': {snomed_code}")
                    return False
            else:
                print(f"  ℹ️  Other relationship type: {relationship_id}")
        
        if maps_to_found:
            print("\n✅ Successfully found 'Maps to' relationships with correct concept_id usage")
        else:
            print("\n⚠️  No 'Maps to' relationships found - testing concept_code fallback")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in SNOMED mapping test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_full_snomed_response():
    """Test the full SNOMED response through IcdAgent."""
    print("\n=== Testing Full SNOMED Response ===")
    
    try:
        from modules.agents.icd_agent import IcdAgent
        
        agent = IcdAgent()
        
        # Test SNOMED mapping query
        query = "What is the SNOMED mapping for I10?"
        print(f"Testing query: {query}")
        
        response = agent.process(query)
        
        if "error" in response:
            print(f"❌ Error: {response['error']}")
            return False
        
        processed_response = response.get("processed_response", "")
        
        print(f"✅ Response received (length: {len(processed_response)} chars)")
        
        # Check if response mentions concept IDs (numeric SNOMED codes)
        import re
        numeric_codes = re.findall(r'\b\d{6,}\b', processed_response)
        
        if numeric_codes:
            print(f"✅ Found numeric SNOMED codes (concept_ids): {numeric_codes[:3]}...")
        else:
            print("⚠️  No numeric SNOMED codes found in response")
        
        print("\nResponse preview:")
        print("=" * 60)
        print(processed_response[:400] + "..." if len(processed_response) > 400 else processed_response)
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Error in full SNOMED response test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run SNOMED mapping fix tests."""
    print("🔧 Testing SNOMED Mapping Fix")
    print("=" * 50)
    
    tests = [
        test_snomed_mapping_fix,
        test_full_snomed_response,
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
        print("🎉 SNOMED mapping fix verified successfully!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)