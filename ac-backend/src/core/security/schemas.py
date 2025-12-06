import datetime
from enum import Enum
from typing import Annotated

from fastapi import Form

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


class LoginFormData:
    def __init__(
        self, username: Annotated[str, Form()], password: Annotated[str, Form()]
    ):
        self.username = username
        self.password = password
