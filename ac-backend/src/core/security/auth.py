from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from starlette import status

from src.core.config.config import settings
from src.core.security.dependencies import UserServiceDep
from src.core.security.enums import TokenType
from src.core.security.models import User
from src.core.security.schemas import UserRoleEnum, UserDto


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/security/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], service: UserServiceDep
) -> UserDto:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid access token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY.get_secret_value(),
            algorithms=[settings.ALGORITHM],
        )

        token_type: TokenType = payload.get("type")
        if token_type != TokenType.ACCESS:
            raise credentials_exception

        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception

    except InvalidTokenError:
        raise credentials_exception

    user = await service.get_user(user_id)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def required_roles(*roles: UserRoleEnum):
    async def check_roles(current_user: User = Depends(get_current_active_user)):
        if current_user.role.name in roles:
            return current_user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
        )

    return check_roles
