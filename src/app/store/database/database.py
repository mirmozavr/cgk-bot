import typing as t
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from src.app.store.database import Base

if t.TYPE_CHECKING:
    from src.app.web.app import Application


class Database:
    def __init__(self, app: "Application"):
        self.app = app
        self._engine: Optional[AsyncEngine] = None
        self._db: Optional[declarative_base] = None
        self.session: Optional[AsyncSession] = None

    async def connect(self, *_: list, **__: dict) -> None:
        self._db = Base
        self._engine = create_async_engine(
            url=self.app.config.database.get_db_url(),
            echo=False,
            future=True,
        )
        # noinspection PyTypeChecker
        self.session = sessionmaker(
            self._engine, expire_on_commit=False, class_=AsyncSession
        ).begin()

    async def disconnect(self, *_: list, **__: dict) -> None:
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
