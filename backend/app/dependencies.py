"""
SAWS Dependency Injection

Provides dependency injection for FastAPI endpoints including:
- Database sessions
- Redis connections
- Authentication
- Rate limiting
"""

from collections.abc import AsyncGenerator, Generator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.base import async_session_maker, get_db_session

settings = get_settings()

# Security
security = HTTPBearer()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session.

    Yields an async database session and ensures it's closed after use.
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_redis() -> AsyncGenerator[Redis, None]:
    """
    Get Redis connection.

    Yields an async Redis connection and ensures it's closed after use.
    """
    redis = Redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
    try:
        yield redis
    finally:
        await redis.close()


async def verify_api_key(
    x_api_key: Annotated[str | None, Header()] = None,
) -> str:
    """
    Verify API key from request header.

    Args:
        x_api_key: API key from X-API-Key header

    Returns:
        The verified API key

    Raises:
        HTTPException: If API key is invalid or missing
    """
    # TODO: Implement actual API key verification against database
    # For now, this is a placeholder
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required",
        )
    return x_api_key


async def verify_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> str:
    """
    Verify JWT token from Authorization header.

    Args:
        credentials: HTTP authorization credentials

    Returns:
        The user ID from the token

    Raises:
        HTTPException: If token is invalid or expired
    """
    # TODO: Implement actual JWT verification
    # For now, this is a placeholder that always succeeds
    token = credentials.credentials
    # Placeholder: extract user_id from token
    return "user_id_placeholder"


async def require_admin(
    user_id: Annotated[str, Depends(verify_token)],
) -> str:
    """
    Require admin role.

    Args:
        user_id: User ID from token

    Returns:
        The user ID if admin

    Raises:
        HTTPException: If user is not an admin
    """
    # TODO: Implement actual admin check
    # For now, this is a placeholder
    return user_id


async def get_request_id(
    x_request_id: Annotated[str | None, Header()] = None,
) -> str:
    """
    Get or generate request ID for tracing.

    Args:
        x_request_id: Optional request ID from header

    Returns:
        The request ID
    """
    if x_request_id:
        return x_request_id
    import uuid

    return str(uuid.uuid4())


async def check_rate_limit(
    request: Request,
    redis: Annotated[Redis, Depends(get_redis)],
) -> None:
    """
    Check rate limit for client IP.

    Args:
        request: FastAPI request object
        redis: Redis connection

    Raises:
        HTTPException: If rate limit exceeded
    """
    if not settings.rate_limit_enabled:
        return

    client_ip = request.client.host if request.client else "unknown"
    key = f"ratelimit:{client_ip}"

    current = await redis.incr(key)
    if current == 1:
        await redis.expire(key, settings.rate_limit_period)

    if current > settings.rate_limit_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Try again in {settings.rate_limit_period} seconds.",
        )


# Type aliases for cleaner dependency injection
DBSession = Annotated[AsyncSession, Depends(get_db)]
RedisConnection = Annotated[Redis, Depends(get_redis)]
UserId = Annotated[str, Depends(verify_token)]
AdminUser = Annotated[str, Depends(require_admin)]
RequestID = Annotated[str, Depends(get_request_id)]
