#!/usr/bin/env python3
"""
Test script to examine Azure AI Search index structure and identify available fields.
This will help us understand if REL segment data is already indexed.
"""

import logging
import sys
import os
import json

# Add the project root to Python path
sys.path.insert(0, os.path.abspath('.'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

def examine_search_index():
    """Examine the structure of documents in the Azure AI Search index."""
    print("=== Examining Azure AI Search Index Structure ===")
    
    try:
        from modules.search_tool import Search
        
        # Perform a broad search to get sample documents
        search = Search(
            index="pcornet-icd-index",
            query="hypertension",  # Common term likely to return results
            top=5
        )
        
        results = search.run()
        
        if not results:
            print("❌ No results returned from search")
            return False
        
        print(f"✅ Found {len(results)} sample documents")
        
        # Examine the structure of the first few documents
        for i, result in enumerate(results[:3]):
            print(f"\n--- Document {i+1} ---")
            document = result.get('document', {})
            score = result.get('score', 'N/A')
            
            print(f"Score: {score}")
            print("Available fields:")
            
            # List all fields in the document
            for field, value in document.items():
                if isinstance(value, str):
                    value_preview = value[:100] + "..." if len(value) > 100 else value
                else:
                    value_preview = str(value)
                print(f"  {field}: {value_preview}")
        
        # Look for REL segment or relationship-related fields
        print("\n=== Looking for REL segment or relationship data ===")
        rel_fields_found = []
        
        for result in results:
            document = result.get('document', {})
            for field in document.keys():
                if any(keyword in field.lower() for keyword in ['rel', 'relationship', 'parent', 'child', 'snomed']):
                    if field not in rel_fields_found:
                        rel_fields_found.append(field)
        
        if rel_fields_found:
            print(f"✅ Found potential REL segment fields: {rel_fields_found}")
            
            # Show sample data from REL fields
            for field in rel_fields_found:
                print(f"\n--- Sample data from field '{field}' ---")
                for i, result in enumerate(results[:2]):
                    document = result.get('document', {})
                    if field in document:
                        value = document[field]
                        print(f"Document {i+1}: {value}")
        else:
            print("⚠️  No obvious REL segment fields found in field names")
            
        # Look for SNOMED-related content in text fields
        print("\n=== Searching for SNOMED relationship patterns in content ===")
        snomed_patterns = ['parent', 'child', 'is a', 'SNOMED', 'relationship']
        
        for result in results:
            document = result.get('document', {})
            doc_id = document.get('id', 'Unknown')
            
            # Check all text fields for SNOMED relationship patterns
            for field, value in document.items():
                if isinstance(value, str):
                    for pattern in snomed_patterns:
                        if pattern.lower() in value.lower():
                            print(f"Found '{pattern}' in {doc_id}.{field}: {value[:200]}...")
                            break
        
        return True
        
    except Exception as e:
        print(f"❌ Error examining index: {e}")
        import traceback
        traceback.print_exc()
        return False

def search_for_rel_segment():
    """Specifically search for documents that might contain REL segment data."""
    print("\n=== Searching for REL segment data ===")
    
    try:
        from modules.search_tool import Search
        
        # Search for terms related to relationships
        rel_queries = [
            "REL segment",
            "SNOMED relationship",
            "parent code",
            "child code", 
            "is a relationship"
        ]
        
        for query in rel_queries:
            print(f"\nSearching for: '{query}'")
            
            search = Search(
                index="pcornet-icd-index",
                query=query,
                top=3
            )
            
            results = search.run()
            
            if results:
                print(f"✅ Found {len(results)} results for '{query}'")
                
                # Show first result
                first_doc = results[0].get('document', {})
                doc_id = first_doc.get('id', 'Unknown')
                print(f"Example result ID: {doc_id}")
                
                # Look for interesting fields
                for field, value in first_doc.items():
                    if isinstance(value, str) and len(value) < 500:
                        print(f"  {field}: {value}")
            else:
                print(f"❌ No results for '{query}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Error searching for REL data: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success1 = examine_search_index()
    success2 = search_for_rel_segment()
    
    sys.exit(0 if (success1 and success2) else 1)