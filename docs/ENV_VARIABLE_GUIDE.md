# .env File Configuration Guide

## ✅ All Required Packages Installed

The following packages have been successfully installed in `.venv`:
- ✅ `openai` (v1.109.1)
- ✅ `azure-search-documents` (v11.6.0)
- ✅ `azure-core` (v1.36.0)
- ✅ All other dependencies from requirements.txt

## 🔧 Environment Variables Fix

Your `.env` file needs to use the **correct variable names**. The code expects these specific names:

### ❌ INCORRECT (from .env.template):
```bash
AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_SEARCH_API_KEY=your-search-api-key
```

### ✅ CORRECT (what the code expects):
```bash
AZURE_AI_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_AI_SEARCH_API_KEY=your-search-api-key
```

## 📋 Complete Required Environment Variables

Make sure your `.env` file includes these variables with the correct names:

```bash
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Azure OpenAI Deployment Names
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=your-embedding-deployment

# Azure AI Search Configuration (CORRECT NAMES)
AZURE_AI_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_AI_SEARCH_API_KEY=your-search-api-key

# Optional: Index configuration
PCORNET_ICD_INDEX_NAME=pcornet-icd-index
```

## 🔍 Variable Name Mapping

| .env.template (OLD)       | config.py (REQUIRED)        |
|---------------------------|----------------------------|
| `AZURE_SEARCH_ENDPOINT`   | `AZURE_AI_SEARCH_ENDPOINT` |
| `AZURE_SEARCH_API_KEY`    | `AZURE_AI_SEARCH_API_KEY`  |

## ✏️ How to Fix

1. Open your `.env` file
2. Find these lines:
   ```bash
   AZURE_SEARCH_ENDPOINT=...
   AZURE_SEARCH_API_KEY=...
   ```
3. Rename them to:
   ```bash
   AZURE_AI_SEARCH_ENDPOINT=...
   AZURE_AI_SEARCH_API_KEY=...
   ```
4. Save the file

## 🧪 Test After Fixing

Run the Streamlit app to verify:
```bash
source .venv/bin/activate
streamlit run main.py
```

The error "AZURE_AI_SEARCH_ENDPOINT is required" should be resolved.

## 📝 Note

The `.env.template` file has outdated variable names. The actual code (in `modules/config.py` line 44-45) expects:
- `AZURE_AI_SEARCH_ENDPOINT`
- `AZURE_AI_SEARCH_API_KEY`
