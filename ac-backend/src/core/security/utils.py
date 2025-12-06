import secrets
from uuid import UUID

from redis.asyncio import Redis

from src.core.config.config import settings
from src.core.security.schemas import UserInDbDto
from src.core.security.service import UserService
import json


def verify_password(plain_password, hashed_password):
    return settings.pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return settings.pwd_context.hash(password)


async def authenticate_user(
    user_service: UserService, email: str, password: str
) -> UserInDbDto | None:
    user = await user_service.get_user_by_email(email)
    if user is None:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def _make_session_id() -> str:
    return secrets.token_urlsafe(32)


def _make_csrf_token() -> str:
    return secrets.token_urlsafe(32)


async def create_session(user_id: UUID, redis_client: Redis) -> (str, str):
    session_id = _make_session_id()
    csrf_token = _make_csrf_token()

    session_data = json.dumps({"user_id": str(user_id), "csrf_token": csrf_token})

    await redis_client.set(
        f"session:{session_id}", session_data, ex=settings.SESSION_EXPIRE_SECONDS
    )
    return session_id, csrf_token
