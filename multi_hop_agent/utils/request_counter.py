"""
Request counter utility for tracking API usage across sessions.

This module provides functions to track and limit the number of agent requests
using a simple JSON file for persistent storage.
"""
import json
import os
from pathlib import Path
from datetime import datetime

# Default location for the counter file (in project root)
DEFAULT_COUNTER_FILE = Path(__file__).parent.parent.parent / "request_counter.json"

def get_counter_file_path():
    """
    Get the path to the request counter file.
    
    Returns:
        Path object pointing to the counter file
    """
    # Allow override via environment variable for flexibility
    counter_path = os.environ.get("REQUEST_COUNTER_FILE", str(DEFAULT_COUNTER_FILE))
    return Path(counter_path)

def initialize_counter(max_requests: int = 1000):
    """
    Initialize the request counter file if it doesn't exist.
    
    Args:
        max_requests: Maximum number of requests allowed (default: 1000)
    """
    counter_file = get_counter_file_path()
    
    if not counter_file.exists():
        data = {
            "total_requests": 0,
            "max_requests": max_requests,
            "last_updated": datetime.now().isoformat(),
            "history": []
        }
        
        with open(counter_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Request counter initialized at {counter_file}")
        print(f"Maximum requests allowed: {max_requests}")

def get_request_count():
    """
    Get the current request count and limit.
    
    Returns:
        Tuple of (current_count, max_requests, remaining)
    """
    counter_file = get_counter_file_path()
    
    # Initialize if doesn't exist
    if not counter_file.exists():
        initialize_counter()
    
    try:
        with open(counter_file, 'r') as f:
            data = json.load(f)
        
        current = data.get("total_requests", 0)
        maximum = data.get("max_requests", 1000)
        remaining = max(0, maximum - current)
        
        return current, maximum, remaining
    except Exception as e:
        print(f"Error reading counter file: {e}")
        # Return conservative defaults on error
        return 0, 1000, 1000

def increment_request_count(question: str = ""):
    """
    Increment the request counter and log the request.
    
    Args:
        question: Optional question text to log
        
    Returns:
        Tuple of (success: bool, current_count: int, message: str)
    """
    counter_file = get_counter_file_path()
    
    # Initialize if doesn't exist
    if not counter_file.exists():
        initialize_counter()
    
    try:
        # Read current data
        with open(counter_file, 'r') as f:
            data = json.load(f)
        
        current = data.get("total_requests", 0)
        maximum = data.get("max_requests", 1000)
        
        # Check if limit reached
        if current >= maximum:
            return False, current, f"API Exhausted: {current}/{maximum} requests used"
        
        # Increment counter
        data["total_requests"] = current + 1
        data["last_updated"] = datetime.now().isoformat()
        
        # Add to history (keep last 100 entries)
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "request_number": current + 1,
            "question": question[:100] if question else "N/A"  # Truncate long questions
        }
        data["history"] = data.get("history", [])[-99:] + [history_entry]
        
        # Write updated data
        with open(counter_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        remaining = maximum - data["total_requests"]
        return True, data["total_requests"], f"Request logged: {data['total_requests']}/{maximum} ({remaining} remaining)"
        
    except Exception as e:
        print(f"Error updating counter: {e}")
        return False, 0, f"Error: Could not update request counter - {e}"

def reset_request_counter():
    """
    Reset the request counter to zero.
    
    WARNING: This will reset all usage tracking!
    
    Returns:
        bool: True if successful, False otherwise
    """
    counter_file = get_counter_file_path()
    
    try:
        with open(counter_file, 'r') as f:
            data = json.load(f)
        
        data["total_requests"] = 0
        data["last_updated"] = datetime.now().isoformat()
        data["history"] = []
        
        with open(counter_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print("Request counter has been reset to 0")
        return True
        
    except Exception as e:
        print(f"Error resetting counter: {e}")
        return False

def set_max_requests(max_requests: int):
    """
    Update the maximum number of requests allowed.
    
    Args:
        max_requests: New maximum number of requests
        
    Returns:
        bool: True if successful, False otherwise
    """
    counter_file = get_counter_file_path()
    
    # Initialize if doesn't exist
    if not counter_file.exists():
        initialize_counter(max_requests)
        return True
    
    try:
        with open(counter_file, 'r') as f:
            data = json.load(f)
        
        data["max_requests"] = max_requests
        data["last_updated"] = datetime.now().isoformat()
        
        with open(counter_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Maximum requests updated to: {max_requests}")
        return True
        
    except Exception as e:
        print(f"Error updating max requests: {e}")
        return False

def get_request_stats():
    """
    Get detailed statistics about request usage.
    
    Returns:
        Dict with usage statistics
    """
    counter_file = get_counter_file_path()
    
    if not counter_file.exists():
        return {
            "status": "not_initialized",
            "total_requests": 0,
            "max_requests": 0,
            "remaining": 0,
            "percentage_used": 0.0,
            "last_updated": None
        }
    
    try:
        with open(counter_file, 'r') as f:
            data = json.load(f)
        
        current = data.get("total_requests", 0)
        maximum = data.get("max_requests", 1000)
        remaining = max(0, maximum - current)
        percentage = (current / maximum * 100) if maximum > 0 else 0
        
        return {
            "status": "exhausted" if current >= maximum else "active",
            "total_requests": current,
            "max_requests": maximum,
            "remaining": remaining,
            "percentage_used": round(percentage, 2),
            "last_updated": data.get("last_updated"),
            "history_count": len(data.get("history", []))
        }
        
    except Exception as e:
        print(f"Error getting stats: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

