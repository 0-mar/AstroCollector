import datetime
from enum import Enum

from src.core.repository.schemas import BaseDto, BaseIdDto


class UserRoleEnum(Enum):
    super_admin = "ROLE_SUPER_ADMIN"
    admin = "ROLE_ADMIN"
    user = "ROLE_USER"


class UserRoleDto(BaseIdDto):
    name: UserRoleEnum
    description: str | None


class UserRoleCreateDto(BaseDto):
    name: UserRoleEnum
    description: str | None


class UserDto(BaseIdDto):
    username: str
    email: str
    disabled: bool
    created_at: datetime.datetime
    role: UserRoleDto


class UserInDbDto(UserDto):
    hashed_password: str


class UserCreateDto(BaseDto):
    username: str
    email: str
    password: str
    role: UserRoleEnum


class Tokens(BaseDto):
    access_token: str
    refresh_token: str
    token_type: str
