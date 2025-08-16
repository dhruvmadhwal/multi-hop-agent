"""
LLM interaction utilities for the Multi-Hop Agent system.

This module provides functions to interact with the LLM.
"""
import traceback
import json
from google.oauth2 import service_account
from multi_hop_agent.utils.helpers import extract_after_think
from langchain_google_vertexai import ChatVertexAI
from multi_hop_agent.config.settings import LLM_MODEL_NAME, GOOGLE_PROJECT_ID, GOOGLE_LOCATION, GOOGLE_CREDENTIALS_JSON

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
        # Check if required Google Cloud settings are available
        if not GOOGLE_PROJECT_ID:
            raise Exception("GOOGLE_PROJECT_ID not found in Streamlit secrets")
        
        if not GOOGLE_CREDENTIALS_JSON:
            raise Exception("GOOGLE_CREDENTIALS_JSON not found in Streamlit secrets")
        
        # 🔑 CRITICAL: Create service account credentials object
        credentials_info = json.loads(GOOGLE_CREDENTIALS_JSON)
        credentials = service_account.Credentials.from_service_account_info(credentials_info)
        
        # Using Google Vertex AI with EXPLICIT credentials
        llm = ChatVertexAI(
            model_name=LLM_MODEL_NAME,
            project=GOOGLE_PROJECT_ID,
            location=GOOGLE_LOCATION or "us-central1",
            credentials=credentials,  # 🔑 THIS IS THE KEY FIX!
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
    print(f"\n--- Calling LLM ---")
    print(f"System: {system}")
    print(f"User: {user}")
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
        print(f"LLM Raw Response: {cleaned_content}")
        
        # Parse if parser provided
        if parser:
            try:
                # First: Try parser directly on cleaned content (most robust)
                parsed_output = parser.parse(cleaned_content)
                print(f"Parser succeeded on cleaned content: {parsed_output}")
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