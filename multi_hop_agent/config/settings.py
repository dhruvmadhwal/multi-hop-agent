import os
import streamlit as st
from datetime import datetime

# Users will provide data through the Streamlit interface
DATASET_FILE = None  # Will be uploaded via Streamlit
ANSWERS_FILE = None  # Will be saved to Streamlit session state
LOGS_DIR = None      # Will use Streamlit session state for logging

# Date information for prompts - dynamically generated
CURRENT_DATE = datetime.now().strftime("%d-%m-%Y")
DATE_HEADER = f"NOTE: Today's date is {CURRENT_DATE}.\n\n"

# Function to get configuration from Streamlit secrets
def get_secret_config():
    """Get configuration from Streamlit secrets"""
    try:
        if hasattr(st, 'secrets'):
            return st.secrets
        else:
            return {}
    except Exception:
        return {}

# Lazy loading of secrets - only when actually needed
def get_google_credentials():
    """Get Google credentials when needed"""
    secrets = get_secret_config()
    
    api_key = secrets.get("google", {}).get("api_key") if secrets else None
    credentials_json = secrets.get("google", {}).get("service_account_json") if secrets else None
    project_id = secrets.get("google", {}).get("project_id") if secrets else None
    location = secrets.get("google", {}).get("location") if secrets else None
    
    return api_key, credentials_json, project_id, location

# LLM configuration - load from Streamlit secrets or use defaults
def get_llm_config():
    """Get LLM configuration when needed"""
    secrets = get_secret_config()
    return secrets.get("llm", {}).get("model", "gemini-2.5-flash") if secrets else "gemini-2.5-flash"

# Streamlit configuration
STREAMLIT_SERVER_PORT = 8501
STREAMLIT_SERVER_ADDRESS = "0.0.0.0" 