import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from starlette import status
from starlette.requests import Request
from starlette.responses import Response

from src.core.config.config import settings
from src.core.repository.schemas import BaseDto
from src.core.security.auth import get_current_active_user, required_roles
from src.core.security.dependencies import UserServiceDep
from src.core.security.models import User
from src.core.security.schemas import UserDto, UserRoleEnum, Tokens
from src.core.security.utils import (
    authenticate_user,
    create_user_tokens,
    get_user_id_from_refresh_token,
)

router = APIRouter(
    prefix="/api/security",
    tags=["security"],
    responses={404: {"description": "Not found"}},
)

logger = logging.getLogger(__name__)


@router.post("/login")
async def login_for_access_token(
    user_service: UserServiceDep,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Tokens:
    """Authenticate user and return access and refresh token."""
    user = await authenticate_user(user_service, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token, refresh_token = create_user_tokens(user.id)

    logger.info(f"User {user.email} logged in (ID: {user.id})")

    response.set_cookie(
        "refresh_token_ac",
        refresh_token,
        httponly=settings.REFRESH_HTTPONLY,
        samesite=settings.REFRESH_SAME_SITE,
        secure=settings.REFRESH_SECURE,
        expires=settings.REFRESH_TOKEN_EXPIRE_SECONDS,
        domain=settings.COOKIE_DOMAIN,
    )

    return Tokens(
        access_token=access_token, refresh_token=refresh_token, token_type="bearer"
    )


class RefreshToken(BaseDto):
    refresh_token: str


@router.post("/refresh")
async def refresh_access_token(
    user_service: UserServiceDep,
    request: Request,
    response: Response,
    refresh_token_dto: RefreshToken | None = None,
) -> Tokens:
    """Return fresh tokens."""
    refresh_token = (
        refresh_token_dto.refresh_token
        if refresh_token_dto is not None
        else request.cookies.get("refresh_token_ac")
    )

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    user_id = get_user_id_from_refresh_token(refresh_token)
    user_exists = await user_service.get_user(user_id)

    if user_exists is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    if user_exists.disabled:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User account is disabled"
        )

    access_token, refresh_token = create_user_tokens(user_id)

    logger.info(f"User {user_exists.email} refreshed tokens (ID: {user_exists.id})")

    response.set_cookie(
        "refresh_token_ac",
        refresh_token,
        httponly=settings.REFRESH_HTTPONLY,
        samesite=settings.REFRESH_SAME_SITE,
        secure=settings.REFRESH_SECURE,
        expires=settings.REFRESH_TOKEN_EXPIRE_SECONDS,
        domain=settings.COOKIE_DOMAIN,
    )

    return Tokens(
        access_token=access_token, refresh_token=refresh_token, token_type="bearer"
    )


@router.post("/logout")
async def logout(
    user: Annotated[User, Depends(get_current_active_user)], response: Response
):
    """Logout user."""
    response.delete_cookie("refresh_token_ac", domain=settings.COOKIE_DOMAIN)

    logger.info(f"User {user.email} logged out (ID: {user.id})")

    return {"message": "Successfully logged out!"}


@router.get("/me")
async def get_user_info(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> UserDto:
    """Get current user information."""
    return UserDto.model_validate(current_user)


@router.get("/protected")
async def protected_route(
    current_user: Annotated[User, Depends(required_roles(UserRoleEnum.super_admin))],
):
    return {"message": f"Hello {current_user.username}, this is a protected route!"}
