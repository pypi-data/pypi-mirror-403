"""Ref filtering utility functions."""

from typing import Optional


def matches_ref_pattern(ref: Optional[str], pattern: str) -> bool:
    """Check if artifact ref matches pattern (supports prefix wildcards).
    
    Args:
        ref: Artifact ref value to check
        pattern: Pattern to match (supports wildcard suffix with *)
        
    Returns:
        True if ref matches pattern, False otherwise
        
    Examples:
        >>> matches_ref_pattern("result:summary", "result:*")
        True
        >>> matches_ref_pattern("result:summary", "result:summary")
        True
        >>> matches_ref_pattern("output:data", "result:*")
        False
    """
    if not ref:
        return False
    
    # Handle prefix wildcard pattern (e.g., "result:*")
    if pattern.endswith("*"):
        prefix = pattern[:-1]
        return ref.startswith(prefix)
    
    # Exact match
    return ref == pattern

