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
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized",
    )

    try:
        session_id = request.cookies.get(settings.SESSION_COOKIE_NAME)
    except KeyError:
        raise credentials_exception

    user_id = await redis_client.get(f"session:{session_id}")
    if user_id is None:
        raise credentials_exception

    user = await service.get_user(user_id)
    if user is None:
        raise credentials_exception
    if user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")

    # refresh session expiration time
    await redis_client.set(
        f"session:{session_id}", user_id, ex=settings.SESSION_EXPIRE_SECONDS
    )

    return user


def required_roles(*roles: UserRoleEnum):
    async def check_roles(current_user: Annotated[UserDto, Depends(get_user)]):
        if current_user.role.name in roles:
            return current_user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
        )

    return check_roles
