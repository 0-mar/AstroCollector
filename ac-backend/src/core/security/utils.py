import datetime
from uuid import UUID

import jwt
from fastapi import HTTPException
from jwt import InvalidTokenError
from starlette import status

from src.core.config.config import settings
from src.core.security.enums import TokenType
from src.core.security.schemas import UserInDbDto
from src.core.security.service import UserService


def verify_password(plain_password, hashed_password):
    return settings.pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return settings.pwd_context.hash(password)


def create_token(data: dict, expires_delta: datetime.timedelta):
    to_encode = data.copy()
    expire = datetime.datetime.now(datetime.timezone.utc) + expires_delta
    to_encode["exp"] = expire
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY.get_secret_value(), algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_user_tokens(user_id: UUID):
    access_token = create_token(
        {"sub": str(user_id), "type": TokenType.ACCESS},
        datetime.timedelta(seconds=settings.ACCESS_TOKEN_EXPIRE_SECONDS),
    )
    refresh_token = create_token(
        {"sub": str(user_id), "type": str(TokenType.REFRESH)},
        datetime.timedelta(seconds=settings.REFRESH_TOKEN_EXPIRE_SECONDS),
    )
    return access_token, refresh_token


def get_user_id_from_refresh_token(refresh_token: str):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
    )
    try:
        payload = jwt.decode(
            refresh_token,
            settings.SECRET_KEY.get_secret_value(),
            algorithms=[settings.ALGORITHM],
        )

        token_type: TokenType = payload.get("type")
        if token_type != TokenType.REFRESH:
            raise credentials_exception

        user_id: UUID = payload.get("sub")
        if user_id is None:
            raise credentials_exception

    except InvalidTokenError:
        raise credentials_exception

    return user_id


async def authenticate_user(
    user_service: UserService, email: str, password: str
) -> UserInDbDto | None:
    user = await user_service.get_user_by_email(email)
    if user is None:
        return None
    if not settings.pwd_context.verify(password, user.hashed_password):
        return None
    return user
