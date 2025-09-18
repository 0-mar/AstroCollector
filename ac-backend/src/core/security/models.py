import datetime
from typing import Optional

from sqlalchemy import String, DateTime, func, Table, Column, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

from src.core.database.database import DbEntity
from src.core.security.schemas import UserRoleEnum

ac_user_user_roles_table = Table(
    "ac_user_user_roles",
    DbEntity.metadata,
    Column("ac_user_id", ForeignKey("ac_user.id"), primary_key=True),
    Column("ac_user_role_id", ForeignKey("ac_user_role.id"), primary_key=True),
)


class User(DbEntity):
    __tablename__ = "ac_user"

    username: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    disabled: Mapped[bool] = mapped_column(nullable=False, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    roles: Mapped[list["UserRole"]] = relationship(
        secondary=ac_user_user_roles_table, back_populates="users"
    )


class UserRole(DbEntity):
    __tablename__ = "ac_user_role"

    name: Mapped[UserRoleEnum] = mapped_column(nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    users: Mapped[list["User"]] = relationship(
        secondary=ac_user_user_roles_table, back_populates="roles"
    )
