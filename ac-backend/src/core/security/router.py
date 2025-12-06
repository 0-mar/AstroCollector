import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from starlette import status
from starlette.requests import Request
from starlette.responses import Response

from src.core.config.config import settings
from src.core.security.auth import required_roles, get_user
from src.core.security.dependencies import UserServiceDep
from src.core.security.schemas import UserDto, UserRoleEnum, LoginFormData
from src.core.security.utils import (
    authenticate_user,
    create_session,
)

router = APIRouter(
    prefix="/api/security",
    tags=["security"],
    responses={404: {"description": "Not found"}},
)

logger = logging.getLogger(__name__)


@router.post("/login")
async def login(
    user_service: UserServiceDep,
    response: Response,
    request: Request,
    form_data: LoginFormData = Depends(),
):
    """Authenticate user and set session ID in a cookie."""
    user = await authenticate_user(user_service, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    logger.info(f"User {user.email} logged in (ID: {user.id})")

    # create and save session id to the Redis DB
    session_id = await create_session(user.id, request.state.redis_client)

    response.set_cookie(
        settings.SESSION_COOKIE_NAME,
        session_id,
        httponly=settings.SESSION_HTTPONLY,
        samesite=settings.SESSION_SAME_SITE,
        secure=settings.SESSION_SECURE,
        expires=settings.SESSION_EXPIRE_SECONDS,
        domain=settings.SESSION_COOKIE_DOMAIN,
    )
    return {"message": "Successfully logged in!"}


@router.post("/logout")
async def logout(user: Annotated[UserDto, Depends(get_user)], response: Response):
    """Logout user by deleting the session cookie"""
    response.delete_cookie(settings.SESSION_COOKIE_NAME, domain=settings.COOKIE_DOMAIN)

    logger.info(f"User {user.email} logged out (ID: {user.id})")

    return {"message": "Successfully logged out!"}


@router.get("/me")
async def get_user_info(
    current_user: Annotated[UserDto, Depends(get_user)],
) -> UserDto:
    """Get current user information."""
    return current_user


@router.get("/protected")
async def protected_route(
    current_user: Annotated[UserDto, Depends(required_roles(UserRoleEnum.super_admin))],
):
    return {"message": f"Hello {current_user.username}, this is a protected route!"}
