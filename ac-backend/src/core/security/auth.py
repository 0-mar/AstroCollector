import json
from typing import Annotated

from fastapi import Depends, HTTPException
from redis.asyncio import Redis
from starlette import status
from starlette.requests import Request

from src.core.config.config import settings
from src.core.security.dependencies import UserServiceDep
from src.core.security.schemas import UserRoleEnum, UserDto
from src.deps import get_redis_client


async def get_user(
    request: Request,
    redis_client: Annotated[Redis, Depends(get_redis_client)],
    service: UserServiceDep,
) -> UserDto:
    """
    Retrieves and authenticates a user based on their session information stored in Redis.
    This function verifies session validity, ensures CSRF token integrity for added security,
    and retrieves the user's details from the service. It also refreshes the session expiration
    time if the user is successfully authenticated.

    :param request: The HTTP request object that contains session cookies and headers.
    :type request: Request
    :param redis_client: Redis client instance used to interact with the Redis database.
    :param service: User service to fetch user-related data.
    :return: User DTO object containing the user's details after successful authentication.
    :rtype: UserDto
    :raises HTTPException: If session is invalid, user is inactive, or CSRF token validation fails.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized",
    )

    try:
        session_id = request.cookies.get(settings.SESSION_COOKIE_NAME)
        csrf_token_header = request.headers.get("X-CSRF-Token")
    except KeyError:
        raise credentials_exception

    # retrieve and decode session data from Redis
    raw = await redis_client.get(f"session:{session_id}")
    if raw is None:
        # session ID was invalid
        raise credentials_exception

    try:
        session_data: dict[str, str] = json.loads(raw)
    except json.JSONDecodeError:
        raise credentials_exception

    user_id = session_data["user_id"]
    user = await service.get_user(user_id)
    if user is None:
        raise credentials_exception
    if user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")

    # CSRF protection
    csrf_token_session = session_data["csrf_token"]
    if csrf_token_header != csrf_token_session:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid CSRF token",
        )

    # refresh session expiration time
    await redis_client.set(
        f"session:{session_id}", raw, ex=settings.SESSION_EXPIRE_SECONDS
    )

    return user


def required_roles(*roles: UserRoleEnum):
    """
    A function to enforce role-based access control by
    validating a user's role against a set of required roles. The
    function is designed to be used with FastAPI dependency injection
    to verify if the current user's role is authorized to perform
    certain operations. If the user's role matches one of the required
    roles, access is granted; otherwise, an HTTPException is raised
    with a 403 Forbidden status.

    :param roles: A variable-length argument specifying the
        roles allowed for access. Each role is an instance
        of the UserRoleEnum enumeration.
    :return: A callable asynchronous function that validates
        the current user's role by comparing it with the
        required roles and either returns the user if
        authorized or raises an exception if access
        is denied.
    """

    async def check_roles(current_user: Annotated[UserDto, Depends(get_user)]):
        if current_user.role.name in roles:
            return current_user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
        )

    return check_roles
