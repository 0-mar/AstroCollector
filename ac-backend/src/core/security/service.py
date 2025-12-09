from typing import Annotated

from fastapi import Depends

from src.core.config.config import settings
from src.core.repository.repository import Repository, get_repository, Filters
from src.core.security.models import User, UserRole
from src.core.security.schemas import UserCreateDto, UserDto, UserInDbDto

UserRepositoryDep = Annotated[
    Repository[User],
    Depends(get_repository(User)),
]

UserRoleRepositoryDep = Annotated[
    Repository[UserRole],
    Depends(get_repository(UserRole)),
]


class UserService:
    """
    Provides operations for managing user data including retrieval, creation,
    and validation of users.

    :ivar _user_repository: Repository interface for user data access.
    :type _user_repository: UserRepositoryDep
    :ivar _user_role_repository: Repository interface for user role data access.
    :type _user_role_repository: UserRoleRepositoryDep
    """

    def __init__(
        self,
        user_repository: UserRepositoryDep,
        user_role_repository: UserRoleRepositoryDep,
    ) -> None:
        self._user_repository = user_repository
        self._user_role_repository = user_role_repository

    async def get_user_by_email(self, email: str) -> UserInDbDto | None:
        user = await self._user_repository.find_first(
            Filters(filters={"email__eq": email})
        )
        if user is None:
            return None
        return UserInDbDto.model_validate(user)

    async def get_user(self, user_id: str) -> UserDto | None:
        user = await self._user_repository.find_first(
            Filters(filters={"id__eq": user_id})
        )
        if user is None:
            return None
        return UserDto.model_validate(user)

    async def create_user(self, create_dto: UserCreateDto):
        role_entity = await self._user_role_repository.find_first_or_raise(
            Filters(filters={"name__eq": create_dto.role.value})
        )

        user_to_save = User(
            username=create_dto.username,
            email=create_dto.email,
            hashed_password=settings.pwd_context.hash(create_dto.password),
            role=role_entity,
        )
        user = await self._user_repository.save(user_to_save)

        return UserDto.model_validate(user)

    # async def delete_user(self, email: str):
    #     user = await self.get_user(email)
    #     if user is None:
    #         raise RepositoryException("User not found")
    #     await self.user_repository.delete(user.id)
