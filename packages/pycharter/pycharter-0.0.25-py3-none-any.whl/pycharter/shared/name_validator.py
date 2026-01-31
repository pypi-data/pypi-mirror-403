"""
Name and title validation utilities.

Enforces naming conventions for identifiers like:
- Data contract names
- Schema titles
- Data feed names
- Coercion rule titles
- Validation rule titles
- Metadata record titles

Allowed characters: lowercase alphanumerics and underscores only.
"""

import re
from typing import Optional

# Pattern: lowercase letters, numbers, and underscores only
NAME_PATTERN = re.compile(r'^[a-z0-9_]+$')

# Error message template
NAME_ERROR_MESSAGE = (
    "must contain only lowercase letters (a-z), numbers (0-9), and underscores (_). "
    "No spaces, uppercase letters, or special characters allowed."
)


def validate_name(name: str, field_name: str = "name") -> str:
    """
    Validate that a name/title follows the naming convention.
    
    Args:
        name: The name/title to validate
        field_name: The name of the field (for error messages)
        
    Returns:
        The validated name (normalized to lowercase)
        
    Raises:
        ValueError: If the name doesn't match the pattern
        
    Examples:
        >>> validate_name("user_schema")
        'user_schema'
        >>> validate_name("UserSchema")
        Traceback (most recent call last):
        ...
        ValueError: name must contain only lowercase letters...
        >>> validate_name("user-schema")
        Traceback (most recent call last):
        ...
        ValueError: name must contain only lowercase letters...
    """
    if not isinstance(name, str):
        raise ValueError(f"{field_name} must be a string")
    
    if not name:
        raise ValueError(f"{field_name} cannot be empty")
    
    # Normalize to lowercase and strip whitespace
    normalized = name.lower().strip()
    
    if not normalized:
        raise ValueError(f"{field_name} cannot be empty after normalization")
    
    if not NAME_PATTERN.match(normalized):
        raise ValueError(
            f"{field_name} {NAME_ERROR_MESSAGE}"
            f" Got: '{name}'"
        )
    
    return normalized


def is_valid_name(name: str) -> bool:
    """
    Check if a name/title is valid without raising an exception.
    
    Args:
        name: The name/title to check
        
    Returns:
        True if valid, False otherwise
        
    Examples:
        >>> is_valid_name("user_schema")
        True
        >>> is_valid_name("UserSchema")
        False
        >>> is_valid_name("user-schema")
        False
    """
    if not isinstance(name, str) or not name:
        return False
    
    normalized = name.lower().strip()
    return bool(NAME_PATTERN.match(normalized))


def normalize_name(name: str) -> Optional[str]:
    """
    Normalize a name to the allowed format (lowercase, alphanumeric + underscores).
    
    Attempts to convert invalid names to valid ones by:
    - Converting to lowercase
    - Replacing spaces and hyphens with underscores
    - Removing invalid characters
    
    Args:
        name: The name to normalize
        
    Returns:
        Normalized name, or None if normalization fails
        
    Examples:
        >>> normalize_name("UserSchema")
        'userschema'
        >>> normalize_name("user-schema")
        'user_schema'
        >>> normalize_name("user schema")
        'user_schema'
    """
    if not isinstance(name, str) or not name:
        return None
    
    # Convert to lowercase
    normalized = name.lower().strip()
    
    # Replace spaces and hyphens with underscores
    normalized = re.sub(r'[\s\-]+', '_', normalized)
    
    # Remove any characters that aren't lowercase letters, numbers, or underscores
    normalized = re.sub(r'[^a-z0-9_]', '', normalized)
    
    # Remove consecutive underscores
    normalized = re.sub(r'_+', '_', normalized)
    
    # Remove leading/trailing underscores
    normalized = normalized.strip('_')
    
    if not normalized:
        return None
    
    return normalized
