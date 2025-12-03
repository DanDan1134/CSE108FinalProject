"""
Authentication utilities for password hashing and verification.
"""
from werkzeug.security import generate_password_hash, check_password_hash


def hash_password(password: str) -> str:
    """
    Hash a password using werkzeug's security functions.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    return generate_password_hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        password_hash: Stored password hash
        password: Plain text password to verify
        
    Returns:
        True if password matches, False otherwise
    """
    return check_password_hash(password_hash, password)

