import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import String, DateTime, func, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

from src.core.database.database import DbEntity
from src.core.security.schemas import UserRoleEnum


class User(DbEntity):
    __tablename__ = "ac_user"

    username: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    disabled: Mapped[bool] = mapped_column(nullable=False, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    role_id: Mapped[UUID] = mapped_column(ForeignKey("ac_user_role.id"))
    role: Mapped["UserRole"] = relationship(back_populates="users", lazy="joined")


class UserRole(DbEntity):
    __tablename__ = "ac_user_role"

    name: Mapped[UserRoleEnum] = mapped_column(nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    users: Mapped[list["User"]] = relationship(back_populates="role")
