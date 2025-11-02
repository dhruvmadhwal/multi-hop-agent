"""
Simple monthly request limiter using Supabase.

Tracks the number of questions asked per month and enforces a limit.
"""
import os
from datetime import datetime
from typing import Tuple, Dict, Any
import streamlit as st


def get_supabase_client():
    """
    Get Supabase client from credentials.
    
    Returns:
        Supabase client instance and usage limit
    """
    try:
        from supabase import create_client, Client
        
        # Get credentials from Streamlit secrets
        supabase_url = st.secrets.get("supabase", {}).get("url")
        supabase_key = st.secrets.get("supabase", {}).get("key")
        usage_limit = st.secrets.get("supabase", {}).get("usage_limit", 50)
        
        if not supabase_url or not supabase_key:
            raise Exception("Supabase credentials (url, key) not found in secrets")
        
        client = create_client(supabase_url, supabase_key)
        return client, usage_limit
    except Exception as e:
        raise Exception(f"Failed to initialize Supabase client: {e}")


def get_current_bucket() -> str:
    """
    Get the current month bucket identifier.
    
    Returns:
        Bucket string in format 'global:YYYY-MM'
    """
    current_month = datetime.now().strftime("%Y-%m")
    return f"global:{current_month}"


def get_request_count() -> Tuple[int, int, int]:
    """
    Get the current request count for this month.
    
    Returns:
        Tuple of (current_count, limit, remaining)
    """
    try:
        supabase, limit = get_supabase_client()
        bucket = get_current_bucket()
        
        # Query the current bucket
        response = supabase.table('request_counter').select('count').eq('bucket', bucket).execute()
        
        if response.data and len(response.data) > 0:
            current_count = response.data[0]['count']
        else:
            current_count = 0
        
        remaining = max(0, limit - current_count)
        return current_count, limit, remaining
        
    except Exception as e:
        print(f"Error getting request count: {e}")
        # Return conservative defaults on error
        try:
            _, limit = get_supabase_client()
        except:
            limit = 50
        return 0, limit, limit


def increment_request() -> Tuple[bool, int, str]:
    """
    Increment the request counter for the current month.
    
    Returns:
        Tuple of (success: bool, current_count: int, message: str)
    """
    try:
        supabase, limit = get_supabase_client()
        bucket = get_current_bucket()
        
        # Get current count
        current_count, limit, remaining = get_request_count()
        
        # Check if limit reached
        if current_count >= limit:
            return False, current_count, f"API Exhausted: Monthly limit of {limit} requests reached"
        
        # Check if bucket exists
        response = supabase.table('request_counter').select('count').eq('bucket', bucket).execute()
        
        if response.data and len(response.data) > 0:
            # Update existing row
            new_count = response.data[0]['count'] + 1
            supabase.table('request_counter').update({
                'count': new_count,
                'updated_at': datetime.now().isoformat()
            }).eq('bucket', bucket).execute()
        else:
            # Insert new row
            new_count = 1
            supabase.table('request_counter').insert({
                'bucket': bucket,
                'count': new_count,
                'updated_at': datetime.now().isoformat()
            }).execute()
        
        remaining = limit - new_count
        return True, new_count, f"Request logged: {new_count}/{limit} ({remaining} remaining this month)"
        
    except Exception as e:
        print(f"Error incrementing request count: {e}")
        return False, 0, f"Error: Could not update request counter - {e}"


def check_limit() -> Tuple[bool, str]:
    """
    Check if the monthly limit has been reached.
    
    Returns:
        Tuple of (can_proceed: bool, message: str)
    """
    try:
        current_count, limit, remaining = get_request_count()
        
        if current_count >= limit:
            return False, "Limit resets next month."
        
        return True, f"{remaining} remaining requests"
        
    except Exception as e:
        print(f"Error checking limit: {e}")
        # On error, allow the request but log the error
        return True, f"Warning: Could not verify request limit - {e}"


def get_usage_stats() -> Dict[str, Any]:
    """
    Get detailed usage statistics for the current month.
    
    Returns:
        Dict with usage statistics
    """
    try:
        current_count, limit, remaining = get_request_count()
        percentage = (current_count / limit * 100) if limit > 0 else 0
        bucket = get_current_bucket()
        
        return {
            "status": "exhausted" if current_count >= limit else "active",
            "current_count": current_count,
            "limit": limit,
            "remaining": remaining,
            "percentage_used": round(percentage, 2),
            "bucket": bucket,
            "month": bucket.split(':')[1] if ':' in bucket else "unknown"
        }
        
    except Exception as e:
        print(f"Error getting usage stats: {e}")
        try:
            _, limit = get_supabase_client()
        except:
            limit = 50  # Fallback default
        return {
            "status": "error",
            "error": str(e),
            "current_count": 0,
            "limit": limit,
            "remaining": limit
        }

