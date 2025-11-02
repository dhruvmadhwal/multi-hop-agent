"""
Simple monthly request limiter using PostgreSQL (Supabase).

Tracks the number of questions asked per month and enforces a limit.
"""
import os
from datetime import datetime
from typing import Tuple, Dict, Any
import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor


def get_db_config():
    """
    Get database configuration from Streamlit secrets.
    
    Returns:
        Dict with database connection parameters
    """
    try:
        db_config = {
            'host': st.secrets.get("database", {}).get("host"),
            'port': st.secrets.get("database", {}).get("port", "5432"),
            'database': st.secrets.get("database", {}).get("name", "postgres"),
            'user': st.secrets.get("database", {}).get("user"),
            'password': st.secrets.get("database", {}).get("password"),
            'sslmode': st.secrets.get("database", {}).get("sslmode", "require")
        }
        
        # Get usage limit from secrets or use default
        limit = st.secrets.get("database", {}).get("usage_limit", 50)
        
        if not db_config['host'] or not db_config['user'] or not db_config['password']:
            raise Exception("Database credentials not found in secrets")
        
        return db_config, limit
    except Exception as e:
        raise Exception(f"Failed to get database config: {e}")


def get_db_connection():
    """
    Get a database connection.
    
    Returns:
        psycopg2 connection object
    """
    db_config, _ = get_db_config()
    return psycopg2.connect(**db_config)


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
    conn = None
    try:
        _, limit = get_db_config()
        bucket = get_current_bucket()
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Query the current bucket
        cursor.execute(
            "SELECT count FROM request_counter WHERE bucket = %s",
            (bucket,)
        )
        result = cursor.fetchone()
        
        current_count = result['count'] if result else 0
        remaining = max(0, limit - current_count)
        
        cursor.close()
        conn.close()
        
        return current_count, limit, remaining
        
    except Exception as e:
        print(f"Error getting request count: {e}")
        if conn:
            conn.close()
        # Return conservative defaults on error
        _, limit = get_db_config()
        return 0, limit, limit


def increment_request() -> Tuple[bool, int, str]:
    """
    Increment the request counter for the current month.
    
    Returns:
        Tuple of (success: bool, current_count: int, message: str)
    """
    conn = None
    try:
        _, limit = get_db_config()
        bucket = get_current_bucket()
        
        # Get current count
        current_count, limit, remaining = get_request_count()
        
        # Check if limit reached
        if current_count >= limit:
            return False, current_count, f"API Exhausted: Monthly limit of {limit} requests reached"
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Use UPSERT to increment or insert
        cursor.execute("""
            INSERT INTO request_counter (bucket, count, updated_at)
            VALUES (%s, 1, NOW())
            ON CONFLICT (bucket)
            DO UPDATE SET 
                count = request_counter.count + 1,
                updated_at = NOW()
            RETURNING count
        """, (bucket,))
        
        new_count = cursor.fetchone()[0]
        conn.commit()
        
        cursor.close()
        conn.close()
        
        remaining = limit - new_count
        return True, new_count, f"Request logged: {new_count}/{limit} ({remaining} remaining this month)"
        
    except Exception as e:
        print(f"Error incrementing request count: {e}")
        if conn:
            conn.rollback()
            conn.close()
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
            return False, f"API Exhausted: You have used {current_count}/{limit} requests this month. Limit resets next month."
        
        return True, f"{remaining} requests remaining this month"
        
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
            _, limit = get_db_config()
        except:
            limit = 50  # Fallback default
        return {
            "status": "error",
            "error": str(e),
            "current_count": 0,
            "limit": limit,
            "remaining": limit
        }

