"""API key authentication middleware/dependency for FastAPI."""

from typing import Literal, Optional

from fastapi import Header, HTTPException, status

from task_framework.errors import AUTH_INVALID, AUTH_REQUIRED, problem_json_dict


async def verify_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    api_keys: Optional[list[str]] = None,
    admin_api_keys: Optional[list[str]] = None,
) -> tuple[str, Literal["regular", "admin"]]:
    """Verify API key from X-API-Key header.

    This function is kept for backward compatibility. The primary authentication
    method is `get_authenticated_request()` dependency function.

    Args:
        x_api_key: API key from X-API-Key header
        api_keys: List of valid regular API keys
        admin_api_keys: List of valid admin API keys (checked first)

    Returns:
        Tuple of (verified_api_key, key_type) where key_type is "regular" or "admin"

    Raises:
        HTTPException: If API key is missing or invalid (Problem+JSON format)
    """
    if not x_api_key:
        problem = problem_json_dict(
            status_code=status.HTTP_401_UNAUTHORIZED,
            title="Unauthorized",
            detail="Missing API key",
            code=AUTH_REQUIRED,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=problem,
        )

    # Check admin keys first (admin precedence)
    if admin_api_keys and x_api_key in admin_api_keys:
        return x_api_key, "admin"

    # Check regular keys
    if api_keys and x_api_key in api_keys:
        return x_api_key, "regular"

    # Invalid key
    problem = problem_json_dict(
        status_code=status.HTTP_401_UNAUTHORIZED,
        title="Unauthorized",
        detail="Invalid API key",
        code=AUTH_INVALID,
    )
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=problem,
    )

