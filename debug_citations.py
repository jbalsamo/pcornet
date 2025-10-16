#!/usr/bin/env python3

import re

def test_citation_normalization():
    # Simulate the search results from FakeSearch
    search_results = [
        {
            "score": 0.95,
            "document": {
                "id": "I10",
                "title": "Essential (primary) hypertension",
                "content": "Elevated blood pressure... (ICD-10 I10)",
            },
        }
    ]
    
    # Simulate the LLM response
    response = "MOCK ICD ANSWER: Evidence suggests hypertension. I10 and [EXTERNAL]."
    
    # Extract valid IDs (same as in our method)
    valid_ids = set()
    for result in search_results:
        doc_id = result.get("document", {}).get("id")
        if doc_id:
            valid_ids.add(doc_id)
    
    print(f"Valid IDs: {valid_ids}")
    print(f"Original response: {response}")
    
    # Test the regex pattern
    icd_pattern = r'\b([A-Z]\d{2}(?:\.\d+)?)\b'
    matches = re.findall(icd_pattern, response)
    print(f"Regex matches: {matches}")
    
    # Apply normalization
    def normalize_icd_citation(match):
        code = match.group(1)
        print(f"Checking code: {code}, in valid_ids: {code in valid_ids}")
        if code in valid_ids:
            return f'[{code}]'
        return code
    
    response = re.sub(icd_pattern, normalize_icd_citation, response)
    print(f"After ICD normalization: {response}")
    
    # Replace unsupported citations
    response = re.sub(r'\[EXTERNAL\]', '[UNSUPPORTED_CITATION]', response)
    print(f"Final response: {response}")

if __name__ == "__main__":
    test_citation_normalization()