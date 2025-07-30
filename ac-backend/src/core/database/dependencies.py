from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.database import get_async_db_session

DBSessionDep = Annotated[AsyncSession, Depends(get_async_db_session)]
