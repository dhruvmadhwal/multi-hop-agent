import os
import streamlit as st
from datetime import datetime

# Streamlit deployment - no local file paths
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
        return {}
    except:
        return {}

# Get configuration
secrets = get_secret_config()

# Google API credentials - load from Streamlit secrets
GOOGLE_API_KEY = secrets.get("google", {}).get("api_key") if secrets else None
GOOGLE_CREDENTIALS_JSON = secrets.get("google", {}).get("service_account_json") if secrets else None
GOOGLE_PROJECT_ID = secrets.get("google", {}).get("project_id") if secrets else None
GOOGLE_LOCATION = secrets.get("google", {}).get("location") if secrets else None

# Set environment variables if credentials are available
if GOOGLE_API_KEY:
    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
if GOOGLE_PROJECT_ID:
    os.environ["GOOGLE_CLOUD_PROJECT"] = GOOGLE_PROJECT_ID

# LLM configuration - load from Streamlit secrets or use defaults
LLM_MODEL_NAME = secrets.get("llm", {}).get("model", "gemini-2.5-flash") if secrets else "gemini-2.5-flash"
# Temperature and top_p are now configurable in the Streamlit UI
# Default values are set in the UI sliders

# Streamlit configuration
STREAMLIT_SERVER_PORT = 8501
STREAMLIT_SERVER_ADDRESS = "0.0.0.0" 