"""
LLM interaction utilities for the Multi-Hop Agent system.

This module provides functions to interact with the LLM.
"""
import traceback
import json
from google.oauth2 import service_account
from multi_hop_agent.utils.helpers import extract_after_think
from langchain_google_vertexai import ChatVertexAI
from multi_hop_agent.config.settings import get_google_credentials, get_llm_config

def initialize_llm(temperature=0.1, top_p=0.95, top_k=40):
    """
    Initialize the LLM with the configured settings.
    
    Args:
        temperature (float): Controls randomness in responses (0.0-2.0)
        top_p (float): Controls diversity via nucleus sampling (0.0-1.0)
        top_k (int): Limits vocabulary to top k tokens (1-100)
    
    Returns:
        Initialized LLM instance
    
    Raises:
        Exception: If LLM initialization fails
    """
    try:
        # Get credentials when needed
        api_key, credentials_json, project_id, location = get_google_credentials()
        llm_model_name = get_llm_config()
        
        # Check if required Google Cloud settings are available
        if not project_id:
            raise Exception("GOOGLE_PROJECT_ID not found in Streamlit secrets")
        
        if not credentials_json:
            raise Exception("GOOGLE_CREDENTIALS_JSON not found in Streamlit secrets")
        
        # Create service account credentials object
        try:
            credentials_info = json.loads(credentials_json)
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON in service_account_json: {e}")
        
        credentials = service_account.Credentials.from_service_account_info(credentials_info)
        
        # Using Google Vertex AI with explicit credentials
        llm = ChatVertexAI(
            model_name=llm_model_name,
            project=project_id,
            location=location or "us-central1",
            credentials=credentials,  # This is the key fix!
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            verbose=True,
        )
        return llm
    except Exception as e:
        print(f"Error initializing ChatVertexAI: {e}")
        print("Please ensure you have provided project_id, location, and service_account_json in Streamlit secrets")
        raise

def chat(llm, system: str, user: str, parser=None) -> str:
    """
    Invokes the LLM with system and user messages, applying parser if provided.
    
    Args:
        llm: The LLM instance to use
        system: System prompt
        user: User message
        parser: Optional output parser
        
    Returns:
        Parsed or raw LLM response
    """
    try:
        # Insert format instructions if a parser is provided
        if parser:
            # Use placeholder replacement instead of format
            format_instructions = parser.get_format_instructions()
            formatted_system = system.replace("{format_instructions}", format_instructions)
        else:
            formatted_system = system.replace("{format_instructions}", "")
        
        response = llm.invoke(
            [
                {"role": "system", "content": formatted_system},
                {"role": "user", "content": user},
            ],
        )
        content = response.content
        
        cleaned_content = extract_after_think(content)
        
        # Parse if parser provided
        if parser:
            try:
                # First: Try parser directly on cleaned content (most robust)
                parsed_output = parser.parse(cleaned_content)
                return parsed_output
            except Exception as e:
                print(f"Parser failed on cleaned content: {e}. Returning raw content.")
                return cleaned_content
        else:
            return cleaned_content
    except Exception as e:
        print(f"Error during LLM invocation: {e}")
        traceback.print_exc()
        return f"Error: Could not get response from LLM. {e}" 