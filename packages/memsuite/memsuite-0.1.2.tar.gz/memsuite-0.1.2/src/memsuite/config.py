"""
Configuration utilities for MemSuite
"""
import os
from typing import Optional


def get_db_url() -> str:
    """
    Get database URL from environment variables.
    
    Raises:
        ValueError: If DB_URL is not set
        
    Returns:
        str: Database connection URL
    """
    db_url = os.getenv("DB_URL")
    if not db_url:
        raise ValueError(
            "DB_URL environment variable is required. "
            "Please set it in your .env file or environment."
        )
    return db_url


def validate_db_url(url: Optional[str]) -> bool:
    """
    Validate that a database URL is properly formatted.
    
    Args:
        url: Database URL to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not url:
        return False
    
    # Basic validation for PostgreSQL URLs
    return url.startswith(("postgresql://", "postgres://"))
