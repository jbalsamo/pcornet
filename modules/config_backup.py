"""
Configuration loader for application settings.

This module defines a configuration class that loads service
settings from environment variables using `dotenv`. It provides a centralized
and consistent way to access configuration details like API keys, endpoints,
and deployment names throughout the application. It also includes a
health check to verify connections to external services on startup.
"""

import os
import logging
from dotenv import load_dotenv

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AppConfig:
    """
    A container for all application configuration parameters.

    This class reads environment variables related to Azure services,
    and stores them as instance attributes. It also provides health checks
    to validate service connections at startup.
    """
    def __init__(self):
        """
        Initializes the configuration object by loading environment variables.
        """
        # Load environment variables from .env file
        load_dotenv()
        
        # General settings
        self.agent_temperature = float(os.getenv("AGENT_TEMPERATURE", 0.7))

        # Azure OpenAI settings
        self.azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.azure_openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.azure_openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION")
        self.azure_openai_chat_deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")
        self.azure_openai_embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")

        # Azure AI Search settings
        self.azure_ai_search_endpoint = os.getenv("AZURE_AI_SEARCH_ENDPOINT")
        self.azure_ai_search_api_key = os.getenv("AZURE_AI_SEARCH_API_KEY")
        self.pcornet_icd_index = os.getenv("PCORNET_ICD_INDEX_NAME")

        # Log loaded variables for verification
        self._log_loaded_variables()

    def _log_loaded_variables(self):
        """Logs the loaded configuration variables for verification."""
        logging.info("--- Configuration Variables Loaded ---")
        logging.info(f"AGENT_TEMPERATURE: {self.agent_temperature}")
        logging.info(f"AZURE_OPENAI_ENDPOINT: {self.azure_openai_endpoint}")
        logging.info(f"AZURE_OPENAI_API_KEY: {'*' * 8 if self.azure_openai_api_key else 'Not Set'}")
        logging.info(f"AZURE_OPENAI_API_VERSION: {self.azure_openai_api_version}")
        logging.info(f"AZURE_OPENAI_CHAT_DEPLOYMENT: {self.azure_openai_chat_deployment}")
        logging.info(f"AZURE_OPENAI_EMBEDDING_DEPLOYMENT: {self.azure_openai_embedding_deployment}")
        logging.info(f"AZURE_AI_SEARCH_ENDPOINT: {self.azure_ai_search_endpoint}")
        logging.info(f"AZURE_AI_SEARCH_API_KEY: {'*' * 8 if self.azure_ai_search_api_key else 'Not Set'}")
        logging.info(f"PCORNET_ICD_INDEX_NAME: {self.pcornet_icd_index}")
        logging.info("------------------------------------")

    def health_check(self):
        """
        Performs a health check on the configured Azure services.
        Returns True if all checks pass, False otherwise.
        """
        logging.info("--- Performing Health Checks ---")
        services_ok = True

        # Check Azure OpenAI connection
        if not all([self.azure_openai_endpoint, self.azure_openai_api_key, self.azure_openai_api_version]):
            logging.error("Azure OpenAI environment variables are not fully set.")
            services_ok = False
        else:
            try:
                from openai import AzureOpenAI
                client = AzureOpenAI(
                    azure_endpoint=self.azure_openai_endpoint,
                    api_key=self.azure_openai_api_key,
                    api_version=self.azure_openai_api_version,
                    timeout=10.0,
                )
                client.models.list()
                logging.info("✅ Azure OpenAI connection successful.")
            except ImportError:
                logging.error("❌ 'openai' SDK is not installed. Please run 'pip install openai'.")
                services_ok = False
            except Exception as e:
                logging.error(f"❌ Azure OpenAI connection failed: {e}")
                services_ok = False

        # Check Azure AI Search connection
        if not all([self.azure_ai_search_endpoint, self.azure_ai_search_api_key, self.pcornet_icd_index]):
            logging.error("Azure AI Search environment variables are not fully set.")
            services_ok = False
        else:
            try:
                from azure.core.credentials import AzureKeyCredential
                from azure.search.documents import SearchClient
                credential = AzureKeyCredential(self.azure_ai_search_api_key)
                search_client = SearchClient(
                    endpoint=self.azure_ai_search_endpoint,
                    index_name=self.pcornet_icd_index,
                    credential=credential
                )
                search_client.get_document_count()
                logging.info("✅ Azure AI Search connection successful.")
            except ImportError:
                logging.error("❌ 'azure-search-documents' SDK is not installed. Please run 'pip install azure-search-documents'.")
                services_ok = False
            except Exception as e:
                logging.error(f"❌ Azure AI Search connection failed: {e}")
                services_ok = False
        
        logging.info("--- Health Checks Complete ---")
        if not services_ok:
            logging.critical("🚨 One or more health checks failed. The application may not function correctly. Please check your .env file and service status.")
        
        return services_ok

# Create a single, global instance of the configuration
config = AppConfig()

# Prompt Templates
CONCEPT_SET_CLASSIFICATION_PROMPT = """
You are an expert at classifying user intent. Your task is to determine if the user's query is asking to create, generate, or find a "concept set".
A "concept set" is a group of medical codes (like ICD-10) related to a specific clinical idea, such as "Diabetes" or "Heart Failure".

Respond with "True" if the query is about creating a concept set.
Respond with "False" if the query is about anything else.

User Query: "{query}"
"""

CONCEPT_SET_FORMATTING_PROMPT = """
You are a helpful AI assistant. Your task is to format the provided data into a clear and readable format based on the user's original request.
The data you are given is the only source of information you should use for ICD codes and their descriptions. Do not add any information that is not in the provided data.

User's original request: "{query}"
Data to format:
---
{context_data}
---

Based on the user's request, present the data in the best possible format.
If the user asks for a table, create a markdown table.
If the user does not specify a format, default to a markdown table with "Code" and "Description" columns.
"""

import os
import logging
from dotenv import load_dotenv

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AppConfig:
    """
    A container for all application configuration parameters.

    This class reads environment variables related to Azure services,
    and stores them as instance attributes. It also provides health checks
    to validate service connections at startup.
    """
    def __init__(self):
        """
        Initializes the configuration object by loading environment variables.
        """
        # Load environment variables from .env file
        load_dotenv()
        
        # General settings
        self.agent_temperature = float(os.getenv("AGENT_TEMPERATURE", 0.7))

        # Azure OpenAI settings
        self.azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.azure_openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.azure_openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION")
        self.azure_openai_chat_deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")
        self.azure_openai_embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")

        # Azure AI Search settings
        self.azure_ai_search_endpoint = os.getenv("AZURE_AI_SEARCH_ENDPOINT")
        self.azure_ai_search_api_key = os.getenv("AZURE_AI_SEARCH_API_KEY")
        self.pcornet_icd_index = os.getenv("PCORNET_ICD_INDEX_NAME")

        # Log loaded variables for verification
        self._log_loaded_variables()

    def _log_loaded_variables(self):
        """Logs the loaded configuration variables for verification."""
        logging.info("--- Configuration Variables Loaded ---")
        logging.info(f"AGENT_TEMPERATURE: {self.agent_temperature}")
        logging.info(f"AZURE_OPENAI_ENDPOINT: {self.azure_openai_endpoint}")
        logging.info(f"AZURE_OPENAI_API_KEY: {'*' * 8 if self.azure_openai_api_key else 'Not Set'}")
        logging.info(f"AZURE_OPENAI_API_VERSION: {self.azure_openai_api_version}")
        logging.info(f"AZURE_OPENAI_CHAT_DEPLOYMENT: {self.azure_openai_chat_deployment}")
        logging.info(f"AZURE_OPENAI_EMBEDDING_DEPLOYMENT: {self.azure_openai_embedding_deployment}")
        logging.info(f"AZURE_AI_SEARCH_ENDPOINT: {self.azure_ai_search_endpoint}")
        logging.info(f"AZURE_AI_SEARCH_API_KEY: {'*' * 8 if self.azure_ai_search_api_key else 'Not Set'}")
        logging.info(f"PCORNET_ICD_INDEX_NAME: {self.pcornet_icd_index}")
        logging.info("------------------------------------")

    def health_check(self):
        """
        Performs a health check on the configured Azure services.
        Returns True if all checks pass, False otherwise.
        """
        logging.info("--- Performing Health Checks ---")
        services_ok = True

        # Check Azure OpenAI connection
        if not all([self.azure_openai_endpoint, self.azure_openai_api_key, self.azure_openai_api_version]):
            logging.error("Azure OpenAI environment variables are not fully set.")
            services_ok = False
        else:
            try:
                from openai import AzureOpenAI
                client = AzureOpenAI(
                    azure_endpoint=self.azure_openai_endpoint,
                    api_key=self.azure_openai_api_key,
                    api_version=self.azure_openai_api_version,
                    timeout=10.0,
                )
                client.models.list()
                logging.info("✅ Azure OpenAI connection successful.")
            except ImportError:
                logging.error("❌ 'openai' SDK is not installed. Please run 'pip install openai'.")
                services_ok = False
            except Exception as e:
                logging.error(f"❌ Azure OpenAI connection failed: {e}")
                services_ok = False

        # Check Azure AI Search connection
        if not all([self.azure_ai_search_endpoint, self.azure_ai_search_api_key, self.pcornet_icd_index]):
            logging.error("Azure AI Search environment variables are not fully set.")
            services_ok = False
        else:
            try:
                from azure.core.credentials import AzureKeyCredential
                from azure.search.documents import SearchClient
                credential = AzureKeyCredential(self.azure_ai_search_api_key)
                search_client = SearchClient(
                    endpoint=self.azure_ai_search_endpoint,
                    index_name=self.pcornet_icd_index,
                    credential=credential
                )
                search_client.get_document_count()
                logging.info("✅ Azure AI Search connection successful.")
            except ImportError:
                logging.error("❌ 'azure-search-documents' SDK is not installed. Please run 'pip install azure-search-documents'.")
                services_ok = False
            except Exception as e:
                logging.error(f"❌ Azure AI Search connection failed: {e}")
                services_ok = False
        
        logging.info("--- Health Checks Complete ---")
        if not services_ok:
            logging.critical("🚨 One or more health checks failed. The application may not function correctly. Please check your .env file and service status.")
        
        return services_ok

# Create a single, global instance of the configuration
config = AppConfig()

# Prompt Templates
CONCEPT_SET_CLASSIFICATION_PROMPT = """
You are an expert at classifying user intent. Your task is to determine if the user's query is asking to create, generate, or find a "concept set".
A "concept set" is a group of medical codes (like ICD-10) related to a specific clinical idea, such as "Diabetes" or "Heart Failure".

Respond with "True" if the query is about creating a concept set.
Respond with "False" if the query is about anything else.

User Query: "{query}"
"""

CONCEPT_SET_FORMATTING_PROMPT = """
You are a helpful AI assistant. Your task is to format the provided data into a clear and readable format based on the user's original request.
The data you are given is the only source of information you should use for ICD codes and their descriptions. Do not add any information that is not in the provided data.

User's original request: "{query}"
Data to format:
---
{context_data}
---

Based on the user's request, present the data in the best possible format.
If the user asks for a table, create a markdown table.
If the user does not specify a format, default to a markdown table with "Code" and "Description" columns.
"""

# modules/config.py
import os
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AppConfig:
    """
    A container for all application configuration parameters.

    This class reads environment variables related to Azure services,
    and stores them as instance attributes. It also provides health checks
    to validate service connections at startup.
    """
    def __init__(self):
        """
        Initializes the configuration object by loading environment variables.
        """
        # Load environment variables from .env file
        load_dotenv()
        
        # General settings
        self.agent_temperature = float(os.getenv("AGENT_TEMPERATURE", 0.7))

        # Azure OpenAI settings
        self.azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.azure_openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.azure_openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION")
        self.azure_openai_chat_deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")
        self.azure_openai_embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")

        # Azure AI Search settings
        self.azure_ai_search_endpoint = os.getenv("AZURE_AI_SEARCH_ENDPOINT")
        self.azure_ai_search_api_key = os.getenv("AZURE_AI_SEARCH_API_KEY")
        self.pcornet_icd_index = os.getenv("PCORNET_ICD_INDEX_NAME")

        # Log loaded variables for verification
        self._log_loaded_variables()

    def _log_loaded_variables(self):
        """Logs the loaded configuration variables for verification."""
        logging.info("--- Configuration Variables Loaded ---")
        logging.info(f"AGENT_TEMPERATURE: {self.agent_temperature}")
        logging.info(f"AZURE_OPENAI_ENDPOINT: {self.azure_openai_endpoint}")
        logging.info(f"AZURE_OPENAI_API_KEY: {'*' * 8 if self.azure_openai_api_key else 'Not Set'}")
        logging.info(f"AZURE_OPENAI_API_VERSION: {self.azure_openai_api_version}")
        logging.info(f"AZURE_OPENAI_CHAT_DEPLOYMENT: {self.azure_openai_chat_deployment}")
        logging.info(f"AZURE_OPENAI_EMBEDDING_DEPLOYMENT: {self.azure_openai_embedding_deployment}")
        logging.info(f"AZURE_AI_SEARCH_ENDPOINT: {self.azure_ai_search_endpoint}")
        logging.info(f"AZURE_AI_SEARCH_API_KEY: {'*' * 8 if self.azure_ai_search_api_key else 'Not Set'}")
        logging.info(f"PCORNET_ICD_INDEX_NAME: {self.pcornet_icd_index}")
        logging.info("------------------------------------")

    def health_check(self):
        """
        Performs a health check on the configured Azure services.
        Returns True if all checks pass, False otherwise.
        """
        logging.info("--- Performing Health Checks ---")
        services_ok = True

        # Check Azure OpenAI connection
        if not all([self.azure_openai_endpoint, self.azure_openai_api_key, self.azure_openai_api_version]):
            logging.error("Azure OpenAI environment variables are not fully set.")
            services_ok = False
        else:
            try:
                from openai import AzureOpenAI
                client = AzureOpenAI(
                    azure_endpoint=self.azure_openai_endpoint,
                    api_key=self.azure_openai_api_key,
                    api_version=self.azure_openai_api_version,
                    timeout=10.0,
                )
                client.models.list()
                logging.info("✅ Azure OpenAI connection successful.")
            except ImportError:
                logging.error("❌ 'openai' SDK is not installed. Please run 'pip install openai'.")
                services_ok = False
            except Exception as e:
                logging.error(f"❌ Azure OpenAI connection failed: {e}")
                services_ok = False

        # Check Azure AI Search connection
        if not all([self.azure_ai_search_endpoint, self.azure_ai_search_api_key, self.pcornet_icd_index]):
            logging.error("Azure AI Search environment variables are not fully set.")
            services_ok = False
        else:
            try:
                from azure.core.credentials import AzureKeyCredential
                from azure.search.documents import SearchClient
                credential = AzureKeyCredential(self.azure_ai_search_api_key)
                search_client = SearchClient(
                    endpoint=self.azure_ai_search_endpoint,
                    index_name=self.pcornet_icd_index,
                    credential=credential
                )
                search_client.get_document_count()
                logging.info("✅ Azure AI Search connection successful.")
            except ImportError:
                logging.error("❌ 'azure-search-documents' SDK is not installed. Please run 'pip install azure-search-documents'.")
                services_ok = False
            except Exception as e:
                logging.error(f"❌ Azure AI Search connection failed: {e}")
                services_ok = False
        
        logging.info("--- Health Checks Complete ---")
        if not services_ok:
            logging.critical("🚨 One or more health checks failed. The application may not function correctly. Please check your .env file and service status.")
        
        return services_ok

# Create a single, global instance of the configuration
config = AppConfig()

# Prompt Templates
CONCEPT_SET_CLASSIFICATION_PROMPT = """
You are an expert at classifying user intent. Your task is to determine if the user's query is asking to create, generate, or find a "concept set".
A "concept set" is a group of medical codes (like ICD-10) related to a specific clinical idea, such as "Diabetes" or "Heart Failure".

Respond with "True" if the query is about creating a concept set.
Respond with "False" if the query is about anything else.

User Query: "{query}"
"""

CONCEPT_SET_FORMATTING_PROMPT = """
You are a helpful AI assistant. Your task is to format the provided data into a clear and readable format based on the user's original request.
The data you are given is the only source of information you should use for ICD codes and their descriptions. Do not add any information that is not in the provided data.

User's original request: "{query}"
Data to format:
---
{context_data}
---

Based on the user's request, present the data in the best possible format.
If the user asks for a table, create a markdown table.
If the user does not specify a format, default to a markdown table with "Code" and "Description" columns.
"""

# modules/config.py
import os
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AppConfig:
    """
    A container for all application configuration parameters.

    This class reads environment variables related to Azure services,
    and stores them as instance attributes. It also provides health checks
    to validate service connections at startup.
    """
    def __init__(self):
        """
        Initializes the configuration object by loading environment variables.
        """
        # Load environment variables from .env file
        load_dotenv()
        
        # General settings
        self.agent_temperature = float(os.getenv("AGENT_TEMPERATURE", 0.7))

        # Azure OpenAI settings
        self.azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.azure_openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.azure_openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION")
        self.azure_openai_chat_deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")
        self.azure_openai_embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")

        # Azure AI Search settings
        self.azure_ai_search_endpoint = os.getenv("AZURE_AI_SEARCH_ENDPOINT")
        self.azure_ai_search_api_key = os.getenv("AZURE_AI_SEARCH_API_KEY")
        self.pcornet_icd_index = os.getenv("PCORNET_ICD_INDEX_NAME")

        # Log loaded variables for verification
        self._log_loaded_variables()

    def _log_loaded_variables(self):
        """Logs the loaded configuration variables for verification."""
        logging.info("--- Configuration Variables Loaded ---")
        logging.info(f"AGENT_TEMPERATURE: {self.agent_temperature}")
        logging.info(f"AZURE_OPENAI_ENDPOINT: {self.azure_openai_endpoint}")
        logging.info(f"AZURE_OPENAI_API_KEY: {'*' * 8 if self.azure_openai_api_key else 'Not Set'}")
        logging.info(f"AZURE_OPENAI_API_VERSION: {self.azure_openai_api_version}")
        logging.info(f"AZURE_OPENAI_CHAT_DEPLOYMENT: {self.azure_openai_chat_deployment}")
        logging.info(f"AZURE_OPENAI_EMBEDDING_DEPLOYMENT: {self.azure_openai_embedding_deployment}")
        logging.info(f"AZURE_AI_SEARCH_ENDPOINT: {self.azure_ai_search_endpoint}")
        logging.info(f"AZURE_AI_SEARCH_API_KEY: {'*' * 8 if self.azure_ai_search_api_key else 'Not Set'}")
        logging.info(f"PCORNET_ICD_INDEX_NAME: {self.pcornet_icd_index}")
        logging.info("------------------------------------")

    def health_check(self):
        """
        Performs a health check on the configured Azure services.
        Returns True if all checks pass, False otherwise.
        """
        logging.info("--- Performing Health Checks ---")
        services_ok = True

        # Check Azure OpenAI connection
        if not all([self.azure_openai_endpoint, self.azure_openai_api_key, self.azure_openai_api_version]):
            logging.error("Azure OpenAI environment variables are not fully set.")
            services_ok = False
        else:
            try:
                from openai import AzureOpenAI
                client = AzureOpenAI(
                    azure_endpoint=self.azure_openai_endpoint,
                    api_key=self.azure_openai_api_key,
                    api_version=self.azure_openai_api_version,
                    timeout=10.0,
                )
                client.models.list()
                logging.info("✅ Azure OpenAI connection successful.")
            except ImportError:
                logging.error("❌ 'openai' SDK is not installed. Please run 'pip install openai'.")
                services_ok = False
            except Exception as e:
                logging.error(f"❌ Azure OpenAI connection failed: {e}")
                services_ok = False

        # Check Azure AI Search connection
        if not all([self.azure_ai_search_endpoint, self.azure_ai_search_api_key, self.pcornet_icd_index]):
            logging.error("Azure AI Search environment variables are not fully set.")
            services_ok = False
        else:
            try:
                from azure.core.credentials import AzureKeyCredential
                from azure.search.documents import SearchClient
                credential = AzureKeyCredential(self.azure_ai_search_api_key)
                search_client = SearchClient(
                    endpoint=self.azure_ai_search_endpoint,
                    index_name=self.pcornet_icd_index,
                    credential=credential
                )
                search_client.get_document_count()
                logging.info("✅ Azure AI Search connection successful.")
            except ImportError:
                logging.error("❌ 'azure-search-documents' SDK is not installed. Please run 'pip install azure-search-documents'.")
                services_ok = False
            except Exception as e:
                logging.error(f"❌ Azure AI Search connection failed: {e}")
                services_ok = False
        
        logging.info("--- Health Checks Complete ---")
        if not services_ok:
            logging.critical("🚨 One or more health checks failed. The application may not function correctly. Please check your .env file and service status.")
        
        return services_ok

# Create a single, global instance of the configuration
config = AppConfig()

# Prompt Templates
CONCEPT_SET_CLASSIFICATION_PROMPT = """
You are an expert at classifying user intent. Your task is to determine if the user's query is asking to create, generate, or find a "concept set".
A "concept set" is a group of medical codes (like ICD-10) related to a specific clinical idea, such as "Diabetes" or "Heart Failure".

Respond with "True" if the query is about creating a concept set.
Respond with "False" if the query is about anything else.

User Query: "{query}"
"""

CONCEPT_SET_FORMATTING_PROMPT = """
You are a helpful AI assistant. Your task is to format the provided data into a clear and readable format based on the user's original request.
The data you are given is the only source of information you should use for ICD codes and their descriptions. Do not add any information that is not in the provided data.

User's original request: "{query}"
Data to format:
---
{context_data}
---

Based on the user's request, present the data in the best possible format.
If the user asks for a table, create a markdown table.
If the user does not specify a format, default to a markdown table with "Code" and "Description" columns.
"""

# modules/config.py
import os
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AppConfig:
    """
    A container for all application configuration parameters.

    This class reads environment variables related to Azure services,
    and stores them as instance attributes. It also provides health checks
    to validate service connections at startup.
    """
    def __init__(self):
        """
        Initializes the configuration object by loading environment variables.
        """
        # Load environment variables from .env file
        load_dotenv()
        
        # General settings
        self.agent_temperature = float(os.getenv("AGENT_TEMPERATURE", 0.7))

        # Azure OpenAI settings
        self.azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.azure_openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.azure_openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION")
        self.azure_openai_chat_deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")
        self.azure_openai_embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")

        # Azure AI Search settings
        self.azure_ai_search_endpoint = os.getenv("AZURE_AI_SEARCH_ENDPOINT")
        self.azure_ai_search_api_key = os.getenv("AZURE_AI_SEARCH_API_KEY")
        self.pcornet_icd_index = os.getenv("PCORNET_ICD_INDEX_NAME")

        # Log loaded variables for verification
        self._log_loaded_variables()

    def _log_loaded_variables(self):
        """Logs the loaded configuration variables for verification."""
        logging.info("--- Configuration Variables Loaded ---")
        logging.info(f"AGENT_TEMPERATURE: {self.agent_temperature}")
        logging.info(f"AZURE_OPENAI_ENDPOINT: {self.azure_openai_endpoint}")
        logging.info(f"AZURE_OPENAI_API_KEY: {'*' * 8 if self.azure_openai_api_key else 'Not Set'}")
        logging.info(f"AZURE_OPENAI_API_VERSION: {self.azure_openai_api_version}")
        logging.info(f"AZURE_OPENAI_CHAT_DEPLOYMENT: {self.azure_openai_chat_deployment}")
        logging.info(f"AZURE_OPENAI_EMBEDDING_DEPLOYMENT: {self.azure_openai_embedding_deployment}")
        logging.info(f"AZURE_AI_SEARCH_ENDPOINT: {self.azure_ai_search_endpoint}")
        logging.info(f"AZURE_AI_SEARCH_API_KEY: {'*' * 8 if self.azure_ai_search_api_key else 'Not Set'}")
        logging.info(f"PCORNET_ICD_INDEX_NAME: {self.pcornet_icd_index}")
        logging.info("------------------------------------")

    def health_check(self):
        """
        Performs a health check on the configured Azure services.
        Returns True if all checks pass, False otherwise.
        """
        logging.info("--- Performing Health Checks ---")
        services_ok = True

        # Check Azure OpenAI connection
        if not all([self.azure_openai_endpoint, self.azure_openai_api_key, self.azure_openai_api_version]):
            logging.error("Azure OpenAI environment variables are not fully set.")
            services_ok = False
        else:
            try:
                from openai import AzureOpenAI
                client = AzureOpenAI(
                    azure_endpoint=self.azure_openai_endpoint,
                    api_key=self.azure_openai_api_key,
                    api_version=self.azure_openai_api_version,
                    timeout=10.0,
                )
                client.models.list()
                logging.info("✅ Azure OpenAI connection successful.")
            except ImportError:
                logging.error("❌ 'openai' SDK is not installed. Please run 'pip install openai'.")
                services_ok = False
            except Exception as e:
                logging.error(f"❌ Azure OpenAI connection failed: {e}")
                services_ok = False

        # Check Azure AI Search connection
        if not all([self.azure_ai_search_endpoint, self.azure_ai_search_api_key, self.pcornet_icd_index]):
            logging.error("Azure AI Search environment variables are not fully set.")
            services_ok = False
        else:
            try:
                from azure.core.credentials import AzureKeyCredential
                from azure.search.documents import SearchClient
                credential = AzureKeyCredential(self.azure_ai_search_api_key)
                search_client = SearchClient(
                    endpoint=self.azure_ai_search_endpoint,
                    index_name=self.pcornet_icd_index,
                    credential=credential
                )
                search_client.get_document_count()
                logging.info("✅ Azure AI Search connection successful.")
            except ImportError:
                logging.error("❌ 'azure-search-documents' SDK is not installed. Please run 'pip install azure-search-documents'.")
                services_ok = False
            except Exception as e:
                logging.error(f"❌ Azure AI Search connection failed: {e}")
                services_ok = False
        
        logging.info("--- Health Checks Complete ---")
        if not services_ok:
            logging.critical("🚨 One or more health checks failed. The application may not function correctly. Please check your .env file and service status.")
        
        return services_ok

# Create a single, global instance of the configuration
config = AppConfig()

# Prompt Templates
CONCEPT_SET_CLASSIFICATION_PROMPT = """
You are an expert at classifying user intent. Your task is to determine if the user's query is asking to create, generate, or find a "concept set".
A "concept set" is a group of medical codes (like ICD-10) related to a specific clinical idea, such as "Diabetes" or "Heart Failure".

Respond with "True" if the query is about creating a concept set.
Respond with "False" if the query is about anything else.

User Query: "{query}"
"""

CONCEPT_SET_FORMATTING_PROMPT = """
You are a helpful AI assistant. Your task is to format the provided data into a clear and readable format based on the user's original request.
The data you are given is the only source of information you should use for ICD codes and their descriptions. Do not add any information that is not in the provided data.

User's original request: "{query}"
Data to format:
---
{context_data}
---

Based on the user's request, present the data in the best possible format.
If the user asks for a table, create a markdown table.
If the user does not specify a format, default to a markdown table with "Code" and "Description" columns.
"""

# modules/config.py
import os
from dotenv import load_dotenv

load_dotenv()


class AppConfig:
    """
    A container for Azure OpenAI configuration parameters.

    This class reads environment variables related to the Azure OpenAI service
    and stores them as instance attributes. It also provides a helper method
    to return these settings as a dictionary suitable for use with LangChain's
    AzureChatOpenAI client.
    """
    def __init__(self):
        """
        Initializes the configuration object by loading environment variables.
        """
        # Load environment variables
        load_dotenv()
        
        # General settings
        self.agent_temperature = float(os.getenv("AGENT_TEMPERATURE", 0.7))

        # Azure OpenAI settings
        self.azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.azure_openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.azure_openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION")
        self.azure_openai_chat_deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")
        self.azure_openai_embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")

        # Azure AI Search settings
        self.azure_ai_search_endpoint = os.getenv("AZURE_AI_SEARCH_ENDPOINT")
        self.azure_ai_search_api_key = os.getenv("AZURE_AI_SEARCH_API_KEY")
        self.pcornet_icd_index = os.getenv("PCORNET_ICD_INDEX_NAME")

        # Log loaded variables for verification
        self._log_loaded_variables()

    def _log_loaded_variables(self):
        """Logs the loaded configuration variables to the console."""
        print("--- Configuration Variables Loaded ---")
        print(f"AGENT_TEMPERATURE: {self.agent_temperature}")
        print(f"AZURE_OPENAI_ENDPOINT: {self.azure_openai_endpoint}")
        print(f"AZURE_OPENAI_API_KEY: {'*' * 8 if self.azure_openai_api_key else 'Not Set'}")
        print(f"AZURE_OPENAI_API_VERSION: {self.azure_openai_api_version}")
        print(f"AZURE_OPENAI_CHAT_DEPLOYMENT: {self.azure_openai_chat_deployment}")
        print(f"AZURE_OPENAI_EMBEDDING_DEPLOYMENT: {self.azure_openai_embedding_deployment}")
        print(f"AZURE_AI_SEARCH_ENDPOINT: {self.azure_ai_search_endpoint}")
        print(f"AZURE_AI_SEARCH_API_KEY: {'*' * 8 if self.azure_ai_search_api_key else 'Not Set'}")
        print(f"PCORNET_ICD_INDEX_NAME: {self.pcornet_icd_index}")
        print("------------------------------------")

    def get_azure_openai_kwargs(self) -> dict:
        """
        Returns a dictionary of keyword arguments for AzureChatOpenAI.
        """
        return {
            "azure_endpoint": self.azure_openai_endpoint,
            "api_key": self.azure_openai_api_key,
            "api_version": self.azure_openai_api_version,
            "deployment_name": self.azure_openai_chat_deployment
        }

    def health_check(self):
        """
        Performs a health check on the configured Azure services.
        """
        print("\n--- Performing Health Checks ---")
        services_ok = True

        # Check Azure OpenAI connection
        try:
            from openai import AzureOpenAI
            client = AzureOpenAI(
                azure_endpoint=self.azure_openai_endpoint,
                api_key=self.azure_openai_api_key,
                api_version=self.azure_openai_api_version
            )
            client.models.list()
            print("✅ Azure OpenAI connection successful.")
        except Exception as e:
            print(f"❌ Azure OpenAI connection failed: {e}")
            services_ok = False

        # Check Azure AI Search connection
        try:
            from azure.core.credentials import AzureKeyCredential
            from azure.search.documents import SearchClient
            credential = AzureKeyCredential(self.azure_ai_search_api_key)
            search_client = SearchClient(
                endpoint=self.azure_ai_search_endpoint,
                index_name=self.pcornet_icd_index,
                credential=credential
            )
            # A simple way to test the connection is to get the document count
            search_client.get_document_count()
            print("✅ Azure AI Search connection successful.")
        except Exception as e:
            print(f"❌ Azure AI Search connection failed: {e}")
            services_ok = False
        
        print("--------------------------------")
        if not services_ok:
            print("🚨 One or more health checks failed. Please check your .env file and service status.")
        
        return services_ok

# global instance
config = AppConfig()

# Prompt Templates
CONCEPT_SET_CLASSIFICATION_PROMPT = """
You are an expert at classifying user intent. Your task is to determine if the user's query is asking to create, generate, or find a "concept set".
A "concept set" is a group of medical codes (like ICD-10) related to a specific clinical idea, such as "Diabetes" or "Heart Failure".

Respond with "True" if the query is about creating a concept set.
Respond with "False" if the query is about anything else.

User Query: "{query}"
"""

CONCEPT_SET_FORMATTING_PROMPT = """
You are a helpful AI assistant. Your task is to format the provided data into a clear and readable format based on the user's original request.
The data you are given is the only source of information you should use for ICD codes and their descriptions. Do not add any information that is not in the provided data.

User's original request: "{query}"
Data to format:
---
{context_data}
---

Based on the user's request, present the data in the best possible format.
If the user asks for a table, create a markdown table.
If the user does not specify a format, default to a markdown table with "Code" and "Description" columns.
"""

# Prompt Templates
CONCEPT_SET_CLASSIFICATION_PROMPT = """
You are an expert at classifying user intent. Your task is to determine if the user's query is asking to create, generate, or find a "concept set".
A "concept set" is a group of medical codes (like ICD-10) related to a specific clinical idea, such as "Diabetes" or "Heart Failure".

Respond with "True" if the query is about creating a concept set.
Respond with "False" if the query is about anything else.

User Query: "{query}"
"""

CONCEPT_SET_FORMATTING_PROMPT = """
You are a helpful AI assistant. Your task is to format the provided data into a clear and readable format based on the user's original request.
The data you are given is the only source of information you should use for ICD codes and their descriptions. Do not add any information that is not in the provided data.

User's original request: "{query}"
Data to format:
---
{context_data}
---

Based on the user's request, present the data in the best possible format.
If the user asks for a table, create a markdown table.
If the user does not specify a format, default to a markdown table with "Code" and "Description" columns.
"""

