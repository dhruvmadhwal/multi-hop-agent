"""
Helper functions for the Multi-Hop Agent system.

This module contains utility functions used throughout the system.
"""
import re
import json
import traceback
from typing import Dict, Any

def extract_after_think(s: str) -> str:
    """
    Remove everything before and including the LAST closing think tag.
    Useful for cleaning up LLM responses.
    """
    if not s:
        return ""
    if s[0:1] in "'\"" and s[-1:] == s[0]:
        s = s[1:-1]
    # Remove everything before and including the LAST closing think tag.
    # Accept both proper "</think>" and the typo "<\think>".
    return re.sub(r'(?si).*(?:</\s*think\s*>|<\\\s*think\s*>)\s*', '', s).strip()

def save_answers(answers, file_path):
    """
    Save answers to a JSON file.
    
    Args:
        answers: List of answer dictionaries
        file_path: Path to save the file
    """
    with open(file_path, "w") as f:
        json.dump(answers, f, indent=2)

def cast_to_agent_state(state_dict: Dict[str, Any]):
    """
    Cast a dictionary to AgentState type, ensuring required fields are present.
    
    Args:
        state_dict: Dictionary to cast to AgentState
        
    Returns:
        The same dictionary, now typed as AgentState
    
    Raises:
        ValueError: If required fields are missing
    """
    # Ensure the required fields exist
    if "task" not in state_dict:
        raise ValueError("Required field 'task' is missing from AgentState")
    
    # Cast and return
    return state_dict  # Type checker will see this as AgentState 