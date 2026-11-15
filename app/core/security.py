import secrets

from fastapi import Header

from app.core.config import settings
from app.core.errors import ApiError


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Level 2: every API request needs the right X-API-Key."""
    if not x_api_key or not secrets.compare_digest(
        x_api_key.encode(), settings.api_key.encode()
    ):
        raise ApiError(401, "missing or invalid API key")
