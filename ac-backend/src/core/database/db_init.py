from src.core.config.config import settings
from src.core.database.database import async_sessionmanager
from src.core.repository.repository import Repository
from src.core.security.models import UserRole, User
from src.core.security.schemas import UserRoleEnum
from src.plugin.model import Plugin
from src.plugin.service import PluginService


async def init_db():
    # load plugins on startup
    async with async_sessionmanager.session() as session:
        plugin_repository = Repository(Plugin, session)
        plugin_service = PluginService(plugin_repository)
        await plugin_service.create_default_plugins()

    async with async_sessionmanager.session() as session:
        role_repository = Repository(UserRole, session)
        role = UserRole(name=UserRoleEnum.super_admin, description="Super admin role")
        super_admin_role = await role_repository.save(role)
        role = UserRole(name=UserRoleEnum.admin, description="Admin role")
        await role_repository.save(role)
        role = UserRole(name=UserRoleEnum.user, description="User role")
        user_role = await role_repository.save(role)

    async with async_sessionmanager.session() as session:
        user_repository = Repository(User, session)
        user = User(
            username="admin",
            email="admin@physics.muni.cz",
            hashed_password=settings.pwd_context.hash("admin"),
            disabled=False,
            role=super_admin_role,
        )
        await user_repository.save(user)

        user = User(
            username="User",
            email="user@user.cz",
            hashed_password=settings.pwd_context.hash("user"),
            disabled=False,
            role=user_role,
        )
        await user_repository.save(user)
