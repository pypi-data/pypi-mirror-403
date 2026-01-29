"""Management classes and utilities for SqlAlchemy engines."""

# Future Library
from __future__ import annotations

# Standard Library
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager, contextmanager
from typing import Any, AsyncGenerator, Generator, Generic, Type, TypeVar, cast

# 3rd Party Library
from sqlalchemy import Engine
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# 1st Party Library
from rwskit.sqlalchemy.base import BaseModel
from rwskit.sqlalchemy.config import DatabaseConnectionConfig

ModelT = TypeVar("ModelT", bound=BaseModel)
"""A generic type for a ``BaseModel``."""

EngineT = TypeVar("EngineT", Engine, AsyncEngine)
"""A generic type for an sqlalchemy engine (sync or async)."""

SessionMakerT = TypeVar("SessionMakerT", sessionmaker, async_sessionmaker)
"""A generic type for a ``sessionmaker`` or ``async_sessionmaker``."""


# TODO It's very hard (maybe not possible) to store the cache registry within
#      the AlchemyEngine, because it leads to circular dependencies. The
#      registry needs an engine (or repository), but the engine needs the
#      registry. It seems like it should be possible, but I've already wasted
#      a lot of time trying to make it work and everything has failed.


class AlchemyEngine(ABC, Generic[EngineT, SessionMakerT]):
    """A synchronous ``SqlAlchemy`` engine manager."""

    def __init__(
        self,
        engine_or_config: EngineT | DatabaseConnectionConfig,
        base_model: Type[DeclarativeBase],
        **engine_kwargs: Any,
    ):
        self._engine = self.configure_engine(engine_or_config, **engine_kwargs)
        self._base_model = base_model
        self._session_factory = self.init_session_factory()

    @property
    def raw_engine(self) -> EngineT:
        return self._engine

    @property
    def dialect(self) -> str:
        """The name of the sqlalchemy dialect."""
        return self.raw_engine.dialect.name

    @abstractmethod
    def configure_engine(
        self, engine_or_config: EngineT | DatabaseConnectionConfig, **engine_kwargs
    ) -> EngineT:
        pass

    @abstractmethod
    def init_session_factory(self) -> SessionMakerT:
        pass


class SyncAlchemyEngine(AlchemyEngine[Engine, sessionmaker]):
    def configure_engine(
        self, engine_or_config: Engine | DatabaseConnectionConfig, **engine_kwargs
    ) -> Engine:
        if isinstance(engine_or_config, AsyncEngine):
            raise TypeError(
                "A SyncAlchemyEngine can only use a synchronous ``sqlalchemy.Engine``."
            )

        if isinstance(engine_or_config, Engine):
            return engine_or_config

        if engine_or_config.use_async:
            raise ValueError("'use_async=True' is not valid for synchronous engines.")

        return cast(Engine, engine_or_config.create_sync_engine(**engine_kwargs))

    def init_session_factory(self) -> sessionmaker:
        return sessionmaker(bind=self._engine)

    @contextmanager
    def session_scope(self, expire_on_commit: bool = False) -> Generator[Session]:
        """
        A context manager for committing successful transactions when the
        session is complete or rolling back if there was an exception.

        Parameters
        ----------
        expire_on_commit : bool, default=False
            If ``True`` model objects will be marked as stale on the
            next commit. This will invalidate all relationships and raise
            an exception if they are accessed outside the session.

        Returns
        -------
        Session
            An :class:`sqlalchemy.orm.Session`.
        """
        session: Session = self._session_factory()
        session.expire_on_commit = expire_on_commit

        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    @contextmanager
    def test_scope(self, expire_on_commit: bool = False) -> Generator[Session]:
        """
        A session scope for testing.

        This session will always roll back after exiting the context manager
        and should not persist any changes to the database.

        Parameters
        ----------
        expire_on_commit : bool, default=False
            If ``True`` model objects will be marked as stale when the
            next commit. This will invalidate all relationships and raise
            an exception if they are accessed outside the session.

        Returns
        -------
        Session
            An :class:`sqlalchemy.orm.Session`.

        Raises
        ------
        RuntimeError
            If the user tries to commit changes during the session.
        """

        def raise_on_commit():
            """Raise an exception if the session is committed."""
            raise RuntimeError(
                "Session.commit() is not allowed inside a test scope session."
            )

        session = self._session_factory()
        session.expire_on_commit = expire_on_commit
        session.commit = raise_on_commit

        try:
            yield session
        finally:
            session.rollback()
            session.close()


class AsyncAlchemyEngine(AlchemyEngine[AsyncEngine, async_sessionmaker]):
    def configure_engine(
        self, engine_or_config: AsyncEngine | DatabaseConnectionConfig, **engine_kwargs
    ) -> AsyncEngine:
        if isinstance(engine_or_config, Engine):
            raise TypeError(
                "An AsyncAlchemyEngine can only use an asynchronous "
                "``sqlalchemy.AsyncEngine``."
            )

        if isinstance(engine_or_config, AsyncEngine):
            return engine_or_config

        if engine_or_config.use_async is False:
            raise ValueError("'use_async=False' is not valid for asynchronous engines.")

        return cast(AsyncEngine, engine_or_config.create_engine(**engine_kwargs))

    def init_session_factory(self) -> async_sessionmaker:
        return async_sessionmaker(bind=self._engine)

    @asynccontextmanager
    async def session_scope(
        self, expire_on_commit: bool = False
    ) -> AsyncGenerator[AsyncSession]:
        """
        A context manager for committing successful transactions when the
        session is complete or rolling back if there was an exception.

        Parameters
        ----------
        expire_on_commit : bool, default=False
            If ``True`` model objects will be marked as stale when the
            next commit. This will invalidate all relationships and raise
            an exception if they are accessed outside the session.

        Returns
        -------
        AsyncSession
            An :class:`sqlalchemy.orm.AsyncSession`.

        """
        session: AsyncSession = self._session_factory()
        session.sync_session.expire_on_commit = expire_on_commit

        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()

    @asynccontextmanager
    async def test_scope(
        self, expire_on_commit: bool = False
    ) -> AsyncGenerator[AsyncSession]:
        """
        A session scope for testing.

        This session will always roll back after exiting the context manager
        and should not persist any changes to the database.

        Parameters
        ----------
        expire_on_commit : bool, default=False
            If ``True`` model objects will be marked as stale when the
            next commit. This will invalidate all relationships and raise
            an exception if they are accessed outside the session.

        Returns
        -------
        AsyncSession
            An :class:`sqlalchemy.orm.AsyncSession`.

        Raises
        ------
        RuntimeError
            If the user tries to commit changes during the session.
        """

        def raise_on_commit():
            """Raise an exception if the session is committed."""
            raise RuntimeError(
                "Session.commit() is not allowed inside a test scope session."
            )

        session: AsyncSession = self._session_factory()
        session.sync_session.expire_on_commit = expire_on_commit
        session.commit = raise_on_commit

        try:
            yield session
        finally:
            await session.rollback()
            await session.close()
