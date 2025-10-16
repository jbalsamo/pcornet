from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
import os, json

endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
key = os.getenv("AZURE_SEARCH_API_KEY")
index_name = os.getenv("AZURE_SEARCH_INDEX_NAME", "pcornet-icd-index")

client = SearchIndexClient(endpoint=endpoint, credential=AzureKeyCredential(key))
index = client.get_index(index_name)
print(json.dumps(index.as_dict(), indent=2))
