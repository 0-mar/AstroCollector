from typing import Annotated

from fastapi import Depends

from src.core.security.service import UserService

UserServiceDep = Annotated[
    UserService,
    Depends(UserService),
]
