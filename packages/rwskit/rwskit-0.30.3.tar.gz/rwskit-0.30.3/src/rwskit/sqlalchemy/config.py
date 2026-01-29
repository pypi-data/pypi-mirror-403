"""Classes for configuring SqlAlchemy engines."""

# Future Library
from __future__ import annotations

# Standard Library
import logging

from functools import cached_property
from typing import Any, Literal, Optional, Type, cast

# 3rd Party Library
from pydantic.dataclasses import dataclass
from sqlalchemy import (
    URL,
    AsyncAdaptedQueuePool,
    Engine,
    NullPool,
    Pool,
    QueuePool,
    StaticPool,
    create_engine,
)
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

log = logging.getLogger("__name__")

PoolClass = Literal["AsyncAdaptedQueuePool", "NullPool", "QueuePool", "StaticPool"]

POOL_CLASS_LOOKUP: dict[PoolClass, Type[Pool]] = {
    "NullPool": NullPool,
    "QueuePool": QueuePool,
    "StaticPool": StaticPool,
    "AsyncAdaptedQueuePool": AsyncAdaptedQueuePool,
}


# TODO Look for '@cache' throughout my projects and make sure I am not using
#      them on class methods, which probably aren't working as expected because
#      of 'self'. `@cached_property` should work for class properties, but
#      it's not clear if it will work for other class instance methods.


@dataclass(kw_only=True, frozen=True)
class DatabaseConnectionConfig:
    """The options necessary to connect to a database using SqlAlchemy."""

    database: str
    """The name of the database or the path to the database file if using sqlite3."""

    drivername: str = "sqlite"
    """The name of the driver used to connect to the database."""

    username: Optional[str] = None
    """The user name to use when connecting to the database, if needed."""

    password: Optional[str] = None
    """The password to use when connecting to the database, if needed."""

    host: Optional[str] = None
    """The database host, if applicable."""

    port: Optional[int] = None
    """The database port, if applicable."""

    use_async: bool = False
    """Whether to use an asynchronous engine or not."""

    # Other engine keyword parameters
    echo: bool = False
    """Whether to echo SQL statements to the log."""

    poolclass_name: Optional[PoolClass] = None
    """The name of the ``poolclass`` to use."""

    pool_size: Optional[int] = 10
    """The size of the connection pool or 0 for no limit."""

    max_overflow: Optional[int] = 20
    """The maximum temporary connections that can be added to the pool."""

    pool_pre_ping: bool = True
    """Ping the database before checking out a connection from the pool. """

    pool_recycle: int = 3600
    """Consider any connection stale if it hasn't been active for this long."""

    future: bool = True
    """Ensure the new 2.0 style Engine and Connection API is used."""

    @property
    def url(self) -> URL:
        """Return the :class:`sqlalchemy.URL` representation of this class."""
        return URL.create(
            drivername=self.drivername,
            username=self.username,
            password=self.password,
            host=self.host,
            port=self.port,
            database=self.database,
        )

    @cached_property
    def dialect(self) -> str:
        """Get just the dialect part of the drivername."""
        tokens = self.drivername.split("+")
        return tokens[0]

    @cached_property
    def driver(self) -> Optional[str]:
        """Get just the driver part of the drivername, if specified."""
        tokens = self.drivername.split("+")
        return tokens[1] if len(tokens) > 1 else None

    @cached_property
    def poolclass(self) -> Optional[Type[Pool]]:
        """Get the ``poolclass`` from its name."""
        if self.poolclass_name is None:
            return None

        return POOL_CLASS_LOOKUP[self.poolclass_name]

    def create_engine(self, **kwargs) -> Engine | AsyncEngine:
        """Create an sqlalchemy engine from the configuration.

        Any keyword arguments passed to this function will be added to
        (or override) any engine configuration parameters defined by the
        configuration class.

        Returns
        -------
        Engine | AsyncEngine
            Either a synchronous or asynchronous engine depending on the value
            of ``use_async``.
        """
        engine_kwargs = self._get_engine_kwargs() | kwargs

        if self.use_async:
            return create_async_engine(self.url, **engine_kwargs)
        else:
            return create_engine(self.url, **engine_kwargs)

    def create_sync_engine(self, **kwargs) -> Engine:
        """Create a synchronous :class:`sa.Engine`. See: :method:`create_engine`."""
        engine = self.create_engine(**kwargs)

        return cast(Engine, engine)

    def create_async_engine(self, **kwargs) -> AsyncEngine:
        """Create a synchronous :class:`sa.Engine`. See: :method:`create_engine`."""
        if not self.use_async:
            raise ValueError(
                "You cannot create an 'AsyncEngine' when 'use_async=False'"
            )

        engine = self.create_engine(**kwargs)

        return cast(AsyncEngine, engine)

    def _get_engine_kwargs(self) -> dict[str, Any]:
        if self.pool_size is not None:
            pool_size = None if self.pool_size < 0 else self.pool_size
        else:
            pool_size = None

        kwargs = {
            "echo": self.echo,
            "poolclass": self.poolclass,
            "pool_size": pool_size,
            "max_overflow": self.max_overflow,
            "pool_pre_ping": self.pool_pre_ping,
            "pool_recycle": self.pool_recycle,
            "future": self.future,
        }

        return {k: v for k, v in kwargs.items() if v is not None}
