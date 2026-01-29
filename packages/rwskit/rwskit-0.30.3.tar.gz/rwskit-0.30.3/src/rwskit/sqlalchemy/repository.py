################################################################################
# Copyright (c) 2023 - 2025 Reid Swanson. All Rights Reserved                  #
#                                                                              #
# File: /src/rwskit/sqlalchemy/repository.py                                   #
# Created Date: 24-04-2025T07:27 pm -07:00                                     #
# Author: Reid Swanson                                                         #
#                                                                              #
# Unauthorized copying of this file, via any medium is strictly prohibited     #
# proprietary and confidential.                                                #
################################################################################
"""Database repository implementations."""

# Future Library
from __future__ import annotations

# Standard Library
import asyncio
import logging
import random

from collections import defaultdict
from contextlib import asynccontextmanager, contextmanager
from enum import StrEnum
from typing import (
    Any,
    AsyncGenerator,
    Awaitable,
    Callable,
    Generator,
    Generic,
    Iterable,
    Optional,
    ParamSpec,
    Type,
    TypeVar,
    cast,
    overload,
)

from psycopg.errors import DeadlockDetected
# 3rd Party Library
from sqlalchemy import (
    Insert,
    QueuePool,
    RowMapping,
    Select,
    Table,
    delete,
    inspect,
    select,
)
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.dialects.postgresql.dml import Insert as PostgresInsert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.dialects.sqlite.dml import Insert as SqliteInsert
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Session

# 1st Party Library
from rwskit.collections_ import chunk, is_iterable
from rwskit.sqlalchemy.base import BaseModel, DtoModel
from rwskit.sqlalchemy.engine import (
    AlchemyEngine,
    AsyncAlchemyEngine,
    SyncAlchemyEngine,
)
from rwskit.sqlalchemy.expressions import (
    SqlBinaryExpression,
    SqlOrderCriteria,
    SqlOrderExpression,
    SqlSelectionCriteria,
)

EngineT = TypeVar("EngineT", bound=AlchemyEngine)
"""A generic type for an ``AlchemyEngine``."""


log = logging.getLogger(__name__)

DeclBaseT = TypeVar("DeclBaseT", bound=DeclarativeBase)
"""A type extending :class:`~sqlalchemy.orm.DeclarativeBase`."""

ModelT = TypeVar("ModelT", bound=BaseModel)
"""A generic type for a ``BaseModel``."""

ReturnT = TypeVar("ReturnT", bound=BaseModel)
"""A generic return type for ``query_model``."""


SessionT = TypeVar("SessionT", Session, AsyncSession)
"""A generic type for an sqlalchemy Session."""


# Type variables for generic async function
P = ParamSpec("P")  # parameters of the wrapped function
R = TypeVar("R")    # return type of the wrapped function


def retry_deadlocks_async(
        max_retries: int = 10,
        min_sleep: float = 0.01,
        max_sleep: float = 0.1,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """A decorator to retry operations on postgresql deadlocks.

    Parameters
    ----------
    max_retries
    min_sleep
    max_sleep

    Returns
    -------

    """
    def decorator(fn: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        async def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
            last_exception: OperationalError | None = None

            for attempt in range(1, max_retries + 1):
                try:
                    return await fn(*args, **kwargs)
                except OperationalError as e:
                    if isinstance(e.orig, DeadlockDetected):
                        last_exception = e

                        if attempt == max_retries:
                            raise

                        await asyncio.sleep(random.uniform(min_sleep, max_sleep))
                    else:
                        raise

            # Let's the type checker know there are no more return paths.
            assert last_exception is not None
            raise last_exception

        return wrapped
    return decorator


class ConflictResolutionStrategy(StrEnum):
    DO_NOTHING = "do_nothing"
    UPDATE = "update"


class IndexElementSet(StrEnum):
    PRIMARY_KEYS = "primary_keys"
    NATURAL_KEYS = "natural_keys"


class Repository(Generic[ModelT, EngineT]):
    """A class implementing the basic find and insert operations for the data access layer."""

    def __init__(
        self, engine: EngineT, model_class: Type[ModelT], insert_batch_size: int = 1000
    ):
        self.engine = engine
        self.model_class = model_class

        # Batch inserts and upserts so that no more than this number of items
        # are added in a single transaction.
        self.insert_batch_size = insert_batch_size

    def normalize_insert_data(
        self, data: ModelT | Iterable[ModelT]
    ) -> Iterable[ModelT]:
        """Ensure the insert data is always an iterable."""
        if not is_iterable(data):
            data = cast(Iterable[ModelT], [data])

        # The above check ensures that 'data' is iterable, but pylance
        # can't figure that out.
        return cast(Iterable[ModelT], data)

    def _make_upsert_statements(
        self,
        data: Iterable[ModelT],
        on_conflict: ConflictResolutionStrategy,
        index_element_set: Iterable[str] | IndexElementSet,
        exclude_from_update: Iterable[str] = (),
        filter_duplicates: bool = False
    ) -> list[Insert]:
        """
        Create upsert statements for each type of ``BaseModel`` found when
        walking the data.
        """
        # Recursively traverse each instance and any children, i.e.,
        # relationships, to dictionaries and group the converted instances
        # by their type. We do the conversion and grouping in one method
        # because it is easier to implement this way using
        # 'BaseModel.walk_children'. Although the input items should all be
        # of 'ModelT', the resulting items could be of any type derived from
        # 'BaseModel'.
        grouped_values = self._convert_to_dict_and_group_by_type(data)

        if filter_duplicates:
            grouped_values = self._filter_duplicates(grouped_values)

        # Sort the groups by their insertion order so that we will insert
        # items with no dependencies before items with dependencies.
        grouped_values = self._sort_instances_by_insertion_order(grouped_values)

        # Create an alias to make the list comprehension more readable.
        make_stmt = self._make_upsert_statement

        return [
            make_stmt(m, v, on_conflict, index_element_set, exclude_from_update)
            for m, v in grouped_values.items()
        ]

    def _make_upsert_statement(
        self,
        model_class: Type[BaseModel],
        model_values: list[dict[str, Any]],
        on_conflict: Optional[ConflictResolutionStrategy],
        index_element_set: Iterable[str] | IndexElementSet,
        exclude_from_update: Iterable[str] = (),
    ) -> Insert:
        def _get_insert_function() -> Callable[..., PostgresInsert | SqliteInsert]:
            if self.engine.dialect == "postgresql":
                return postgres_insert
            elif self.engine.dialect == "sqlite":
                return sqlite_insert
            else:
                raise ValueError(
                    f"The dialect '{self.engine.dialect}' does not support 'upserts'"
                )

        insert = _get_insert_function()

        if index_element_set == IndexElementSet.PRIMARY_KEYS:
            index_elements = model_class.primary_key_column_names()
        elif index_element_set == IndexElementSet.NATURAL_KEYS:
            index_elements = model_class.natural_key_column_names()
        else:
            index_elements: set[str] = set(index_element_set)

        # The base insert
        stmt = insert(model_class).values(model_values)

        if on_conflict == ConflictResolutionStrategy.DO_NOTHING:
            stmt = stmt.on_conflict_do_nothing(index_elements=index_elements)
        elif on_conflict == ConflictResolutionStrategy.UPDATE:
            # Exclude the index elements, computed columns, and any manually
            # specified columns.
            columns = inspect(model_class).columns
            computed_columns = {
                c.name for c in columns if hasattr(c, "computed") and c.computed
            }
            excludes = index_elements | computed_columns | set(exclude_from_update)

            stmt = stmt.on_conflict_do_update(
                index_elements=index_elements,
                set_={c.name: c for c in stmt.excluded if c.name not in excludes},
            )
        else:
            raise ValueError(f"Invalid 'on_conflict' value: {on_conflict}")

        return stmt

    @classmethod
    def _convert_to_dict_and_group_by_type(
        cls, data: Iterable[BaseModel]
    ) -> dict[Type[BaseModel], list[dict[str, Any]]]:
        result: dict[Type[BaseModel], list[dict[str, Any]]] = defaultdict(list)

        def add_to_result(node: BaseModel):
            """Convert the node to a dictionary and add it to the result."""
            # Computed columns should never be inserted
            valid_columns = [c for c in node.table_columns() if not c.computed]
            column_names = [str(c.key) for c in valid_columns]
            lookup_attr_name = node.get_attribute_name_from_column_name
            attr_names = [lookup_attr_name(c) for c in column_names]
            attr_names = [name for name in attr_names if name is not None]
            value: dict[str, Any] = {a: getattr(node, a, None) for a in attr_names}
            result[node.__class__].append(value)

        for item in data:
            item.walk_children(add_to_result, traverse_viewonly=False)

        return result

    @classmethod
    def _filter_duplicates(
            cls,
            data: dict[Type[BaseModel], list[dict[str, Any]]]
    ) -> dict[Type[BaseModel], list[dict[str, Any]]]:
        result: dict[Type[BaseModel], list[dict[str, Any]]] = defaultdict(list)

        for model_type, values in data.items():
            collected_values: dict[tuple, list[dict[str, Any]]] = defaultdict(list)
            pk_columns = model_type.__mapper__.primary_key

            for value in values:
                pk_values = tuple([value[c.name] for c in pk_columns])
                collected_values[pk_values].append(value)

            for pk, items in collected_values.items():
                if len(items) > 1:
                    log.debug(
                        "Found more than one entry with the same primary key '%s': %s",
                        pk,
                        items
                    )
                result[model_type].append(items[0])

        return result

    def _sort_instances_by_insertion_order(
        self, data: dict[Type[BaseModel], list[dict[str, Any]]]
    ) -> dict[Type[BaseModel], list[dict[str, Any]]]:
        order_lookup = self.model_class.table_insertion_order()

        def _get_table_order(entry: tuple[Type[BaseModel], Any]) -> int:
            return order_lookup[cast(Table, entry[0].__table__)]

        return {k: v for k, v in sorted(data.items(), key=_get_table_order)}

    def _make_select_statement(
        self,
        filter_by: Iterable[SqlBinaryExpression],
        order_by: Iterable[SqlOrderExpression],
        limit: Optional[int] = None,
    ):
        filter_criteria = SqlSelectionCriteria(list(filter_by))
        order_criteria = SqlOrderCriteria(list(order_by))

        return (
            select(self.model_class)
            .where(filter_criteria.to_conjunction(self.model_class))
            .order_by(*order_criteria.to_criteria(self.model_class))
            .limit(limit)
        )


class SyncRepository(Repository[ModelT, SyncAlchemyEngine]):
    # region API
    def merge(
        self, instances: ModelT | Iterable[ModelT], session: Optional[Session] = None
    ):
        """
        Insert one or more model instances into the database.

        Parameters
        ----------
        instances : ModelT | Iterable[ModelT]
            The data to insert.
        session : Session, optional
            A session to use.

        Raises
        ------
        Exception
            If there is a problem adding the data to the database.
        """
        instances = self.normalize_insert_data(instances)

        with self.get_or_create_session(session) as local_session:
            for instance in instances:
                local_session.merge(instance)

    def insert(
        self, instances: ModelT | Iterable[ModelT], session: Optional[Session] = None
    ):
        """
        Insert one or more model instances into the database.

        Parameters
        ----------
        instances : ModelT | Iterable[ModelT]
            The data to insert.
        session : Session, optional
            A session to use.

        Raises
        ------
        Exception
            If there is a problem adding the data to the database.
        """
        instances = self.normalize_insert_data(instances)

        with self.get_or_create_session(session) as local_session:
            for batch in chunk(instances, self.insert_batch_size):
                local_session.add_all(batch)
                local_session.flush()

    def upsert(
        self,
        instance_or_instances: ModelT | Iterable[ModelT],
        on_conflict: ConflictResolutionStrategy = ConflictResolutionStrategy.DO_NOTHING,
        index_set: Iterable[str] | IndexElementSet = IndexElementSet.PRIMARY_KEYS,
        exclude_from_update: Iterable[str] = [],
        session: Optional[Session] = None,
    ):
        """
        Upsert one or more model instances into the database.

        ..note::
            This only works with dialects that support INSERT ... ON CONFLICT.
            This should include ``postgresql``, ``mysql/mariadb``, and
            ``sqlite``. However, currently only ``postgresql`` is supported.

        ..note::
            This method creates several copies of the data, so you should be
            careful about memory management if you are inserting a large number
            of objects.

        ..warning::
            This only works if all non-null fields are provided **including
            primary and foreign keys.**

        ..warning::
            This is not well tested with complex model configurations such as
            hybrid properties and column properties.

        Parameters
        ----------
        instances : ModelT | Iterable[ModelT]
            The instances to upsert.
        on_conflict : ConflictResolutionStrategy
            The conflict resolution strategy (e.g., 'do nothing' or 'update')
        index_set : Iterable[str] | IndexElementSet
            The set of columns to use for the ``index_elements``.
        exclude_from_update : Iterable[str], default = ()
            Any columns that should not be updated on conflict.
        session : Session, optional
            An optional session to use instead of creating a new one.

        Raises
        ------
        OperationalError
            If the ``index_set`` does not correspond to a collection of columns
            that have a unique index defined on them.
        """
        instances: Iterable[ModelT] = self.normalize_insert_data(instance_or_instances)

        for batch in chunk(instances, self.insert_batch_size):
            upsert_statements = self._make_upsert_statements(
                batch,
                on_conflict,
                index_set,
                exclude_from_update,
            )

            # The for loop could be around or inside the 'get_or_create_session'
            # method. It would be more efficient to have it inside, but for large
            # collections it might cause problems.
            for stmt in upsert_statements:
                with self.get_or_create_session(session) as local_session:
                    local_session.execute(stmt)
                    local_session.flush()

    def find_all_models(
        self,
        filter_by: Iterable[SqlBinaryExpression] = (),
        order_by: Iterable[SqlOrderExpression] = (),
        limit: Optional[int] = None,
        session: Optional[Session] = None,
    ) -> list[ModelT]:
        """
        Finds and retrieves multiple models from the database based on specified
        filters, ordering, and a limit. Converts the retrieved models to their
        corresponding DTO (Data Transfer Object) representation.

        Parameters
        ----------
        filter_by : Iterable[SqlBinaryExpression], optional
            Collection of SQL binary expressions defining the conditions for
            filtering the query. Default is an empty iterable.
        order_by : Iterable[SqlOrderExpression], optional
            Collection of SQL order expressions defining the sorting order for the
            query. Default is an empty iterable.
        limit : int, optional
            Maximum number of records to retrieve. If None, no limit is applied.
            Default is None.
        session : Session, optional
            An optional database session instance. If not provided, a new session
            will be created internally for executing the query.

        Returns
        -------
        list[DtoModel]
            A list of DTO instances that correspond to the retrieved database models.
        """
        stmt = self._make_select_statement(filter_by, order_by, limit)

        with self.get_or_create_session(session) as local_session:
            result = local_session.scalars(stmt)
            models = list(result.all())

        return models

    def find_all_dtos(
        self,
        filter_by: Iterable[SqlBinaryExpression] = (),
        order_by: Iterable[SqlOrderExpression] = (),
        limit: Optional[int] = None,
        session: Optional[Session] = None,
    ) -> list[DtoModel]:
        """
        Finds and retrieves multiple models from the database based on specified
        filters, ordering, and a limit. Converts the retrieved models to their
        corresponding DTO (Data Transfer Object) representation.

        Parameters
        ----------
        filter_by : Iterable[SqlBinaryExpression], optional
            Collection of SQL binary expressions defining the conditions for
            filtering the query. Default is an empty iterable.
        order_by : Iterable[SqlOrderExpression], optional
            Collection of SQL order expressions defining the sorting order for the
            query. Default is an empty iterable.
        limit : int, optional
            Maximum number of records to retrieve. If None, no limit is applied.
            Default is None.
        session : Session, optional
            An optional database session instance. If not provided, a new session
            will be created internally for executing the query.

        Returns
        -------
        list[DtoModel]
            A list of DTO instances that correspond to the retrieved database models.
        """
        stmt = self._make_select_statement(filter_by, order_by, limit)

        with self.get_or_create_session(session) as local_session:
            result = local_session.scalars(stmt)
            models = result.all()
            dtos = [m.to_dto() for m in models]

        return dtos

    def find_one_model(
        self,
        filter_by: Iterable[SqlBinaryExpression] = (),
        session: Optional[Session] = None,
        raise_on_none: bool = True,
    ) -> Optional[ModelT]:
        """
        Retrieve a single record from the database that matches the provided filter
        criteria. An exception is raised when more than one result is returned or no
        results are found when `raise_on_none` is True.

        Parameters
        ----------
        filter_by : Iterable[SqlBinaryExpression], optional
            Filter conditions to apply when querying the database. Defaults to an
            empty tuple.

        session : Optional[Session], optional
            SQLAlchemy session to use for querying. If not provided, a new session
            will be created and used for the operation.

        raise_on_none : bool, optional
            Specifies whether to raise an exception if no records match the specified
            filter criteria. Defaults to True.

        Returns
        -------
        ModelT
            The retrieved data model if a record is found; otherwise, ``None``
            when ``raise_on_none`` is set to False.

        """
        # 'find_one' doesn't need an 'order_by', because it will be an exception
        # if more than one result is found by the query.
        stmt = self._make_select_statement(filter_by, ())
        with self.get_or_create_session(session) as local_session:
            result = local_session.scalars(stmt)
            model = result.one() if raise_on_none else result.one_or_none()

        return model

    def find_one_dto(
        self,
        filter_by: Iterable[SqlBinaryExpression] = (),
        session: Optional[Session] = None,
        raise_on_none: bool = True,
    ) -> Optional[DtoModel]:
        """
        Retrieve a single record from the database that matches the provided filter
        criteria. Converts the obtained database model into a data transfer object
        (DTO). An exception is raised when more than one result is returned or no
        results are found when `raise_on_none` is True.

        Parameters
        ----------
        filter_by : Iterable[SqlBinaryExpression], optional
            Filter conditions to apply when querying the database. Defaults to an
            empty tuple.

        session : Optional[Session], optional
            SQLAlchemy session to use for querying. If not provided, a new session
            will be created and used for the operation.

        raise_on_none : bool, optional
            Specifies whether to raise an exception if no records match the specified
            filter criteria. Defaults to True.

        Returns
        -------
        DtoModel
            The retrieved data model in DTO form if a record is found; otherwise, ``None``
            when ``raise_on_none`` is set to False.

        """
        # 'find_one' doesn't need an 'order_by', because it will be an exception
        # if more than one result is found by the query.
        stmt = self._make_select_statement(filter_by, ())
        with self.get_or_create_session(session) as local_session:
            result = local_session.scalars(stmt)
            model = result.one() if raise_on_none else result.one_or_none()
            dto = model.to_dto() if model is not None else None

        return dto

    def query(self, stmt: Select, session: Session | None = None) -> list[RowMapping]:
        """Execute an arbitrary select statement and return the results as a list."""
        with self.get_or_create_session(session) as local_session:
            return list(local_session.execute(stmt).mappings())

    # endregion API

    # region Helpers
    @contextmanager
    def get_or_create_session(self, session: Optional[Session]) -> Generator[Session]:
        """
        Use the existing session if it is not ``None``, otherwise create and
        return a new one.

        Parameters
        ----------
        session : Optional[Session], default=``None``
            An existing session to use.

        Yields
        ------
        Generator[Session]
            The existing or new session as a context manager.
        """
        if session is None:
            with self.engine.session_scope() as engine_session:
                yield engine_session
        else:
            yield session

    # endregion Helpers


class AsyncRepository(Repository[ModelT, AsyncAlchemyEngine]):
    def __init__(
        self,
        engine: AsyncAlchemyEngine,
        model_class: Type[ModelT],
        insert_batch_size: int = 1000,
    ):
        super().__init__(engine, model_class, insert_batch_size)

        # Use a semaphore to limit concurrency to the size of the
        # connection pool.
        self._semaphore = asyncio.Semaphore(self._get_pool_size())

    def _get_pool_size(self) -> int:
        pool = self.engine.raw_engine.sync_engine.pool

        if isinstance(pool, QueuePool):
            return pool.size()
        else:
            return 1

    # region API
    @retry_deadlocks_async()
    async def merge(
        self,
        instances: ModelT | Iterable[ModelT],
        session: Optional[AsyncSession] = None,
    ):
        """
        Insert one or more model instances into the database.

        Parameters
        ----------
        instances : ModelT | Iterable[ModelT]
            The data to insert.
        session : AsyncSession, optional
            A session to use.

        Raises
        ------
        Exception
            If there is a problem adding the data to the database.
        """
        instances = self.normalize_insert_data(instances)

        async with self.get_or_create_session(session) as local_session:
            for instance in instances:
                async with self._semaphore:
                    await local_session.merge(instance)

    @retry_deadlocks_async()
    async def insert(
        self,
        instances: ModelT | Iterable[ModelT],
        session: Optional[AsyncSession] = None,
    ):
        """
        Insert one or more model instances into the database.

        Parameters
        ----------
        instances : ModelT | Iterable[ModelT]
            The data to insert.
        session : AsyncSession, optional
            A session to use.

        Raises
        ------
        Exception
            If there is a problem adding the data to the database.
        """
        instances = self.normalize_insert_data(instances)

        async with self.get_or_create_session(session) as local_session:
            for batch in chunk(instances, self.insert_batch_size):
                local_session.add_all(batch)

                async with self._semaphore:
                    await local_session.flush()

    @retry_deadlocks_async()
    async def upsert(
        self,
        instance_or_instances: ModelT | Iterable[ModelT],
        on_conflict: ConflictResolutionStrategy = ConflictResolutionStrategy.DO_NOTHING,
        index_set: Iterable[str] | IndexElementSet = IndexElementSet.PRIMARY_KEYS,
        *,
        exclude_from_update: Iterable[str] = [],
        filter_duplicates: bool = False,
        session: Optional[AsyncSession] = None,
    ):
        """
        Upsert one or more model instances into the database.

        ..note::
            This only works with dialects that support INSERT ... ON CONFLICT.
            This should include ``postgresql``, ``mysql/mariadb``, and
            ``sqlite``. However, currently only ``postgresql`` is supported.

        ..note::
            This method creates several copies of the data, so you should be
            careful about memory management if you are inserting a large number
            of objects.

        ..warning::
            This only works if all non-null fields are provided **including
            primary and foreign keys.**

        ..warning::
            This is not well tested with complex model configurations such as
            hybrid properties and column properties.

        Parameters
        ----------
        instance_or_instances : ModelT | Iterable[ModelT]
            The instances to upsert.
        on_conflict : ConflictResolutionStrategy
            The conflict resolution strategy (e.g., 'do nothing' or 'update')
        index_set : Iterable[str] | IndexElementSet
            The set of columns to use for the ``index_elements``.
        exclude_from_update : Iterable[str], default = ()
            Any columns that should not be updated on conflict.
        filter_duplicates : bool, default=False
            Filter duplicates from the input list based on the primary key.
        session : AsyncSession, optional
            An optional session to use instead of creating a new one.

        Raises
        ------
        OperationalError
            If the ``index_set`` does not correspond to a collection of columns
            that have a unique index defined on them.
        """
        instances = self.normalize_insert_data(instance_or_instances)

        for batch in chunk(instances, self.insert_batch_size):
            upsert_statements = self._make_upsert_statements(
                batch,
                on_conflict,
                index_set,
                exclude_from_update=exclude_from_update,
                filter_duplicates=filter_duplicates
            )

            # The for loop could be around or inside the 'get_or_create_session'
            # method. It would be more efficient to have it inside, but for large
            # collections it might cause problems.
            for stmt in upsert_statements:
                async with self.get_or_create_session(session) as local_session:
                    async with self._semaphore:
                        await local_session.execute(stmt)
                        await local_session.flush()

    async def find_all_models(
        self,
        filter_by: Iterable[SqlBinaryExpression] = (),
        order_by: Iterable[SqlOrderExpression] = (),
        limit: Optional[int] = None,
        session: Optional[AsyncSession] = None,
    ) -> list[ModelT]:
        """
        Finds and retrieves multiple models from the database based on specified
        filters, ordering, and a limit. Converts the retrieved models to their
        corresponding DTO (Data Transfer Object) representation.

        Parameters
        ----------
        filter_by : Iterable[SqlBinaryExpression], optional
            Collection of SQL binary expressions defining the conditions for
            filtering the query. Default is an empty iterable.
        order_by : Iterable[SqlOrderExpression], optional
            Collection of SQL order expressions defining the sorting order for the
            query. Default is an empty iterable.
        limit : int, optional
            Maximum number of records to retrieve. If None, no limit is applied.
            Default is None.
        session : AsyncSession, optional
            An optional database session instance. If not provided, a new session
            will be created internally for executing the query.

        Returns
        -------
        list[DtoModel]
            A list of DTO instances that correspond to the retrieved database models.
        """
        stmt = self._make_select_statement(filter_by, order_by, limit)

        async with self.get_or_create_session(session) as local_session:
            async with self._semaphore:
                result = await local_session.scalars(stmt)

            models = list(result.all())

        return models

    async def find_all_dtos(
        self,
        filter_by: Iterable[SqlBinaryExpression] = (),
        order_by: Iterable[SqlOrderExpression] = (),
        limit: Optional[int] = None,
        session: Optional[AsyncSession] = None,
    ) -> list[DtoModel]:
        """
        Finds and retrieves multiple models from the database based on specified
        filters, ordering, and a limit. Converts the retrieved models to their
        corresponding DTO (Data Transfer Object) representation.

        Parameters
        ----------
        filter_by : Iterable[SqlBinaryExpression], optional
            Collection of SQL binary expressions defining the conditions for
            filtering the query. Default is an empty iterable.
        order_by : Iterable[SqlOrderExpression], optional
            Collection of SQL order expressions defining the sorting order for the
            query. Default is an empty iterable.
        limit : int, optional
            Maximum number of records to retrieve. If None, no limit is applied.
            Default is None.
        session : AsyncSession, optional
            An optional database session instance. If not provided, a new session
            will be created internally for executing the query.

        Returns
        -------
        list[DtoModel]
            A list of DTO instances that correspond to the retrieved database models.
        """
        stmt = self._make_select_statement(filter_by, order_by, limit)

        async with self.get_or_create_session(session) as local_session:
            async with self._semaphore:
                result = await local_session.scalars(stmt)

            models = result.all()
            dtos = [m.to_dto() for m in models]

        return dtos

    @overload
    async def find_one_model(
        self,
        filter_by: Iterable[SqlBinaryExpression] = (),
        session: Optional[AsyncSession] = None,
        raise_on_none: bool = True,
    ) -> ModelT: ...
    @overload
    async def find_one_model(
        self,
        filter_by: Iterable[SqlBinaryExpression] = (),
        session: Optional[AsyncSession] = None,
        raise_on_none: bool = False,
    ) -> ModelT | None: ...
    async def find_one_model(
        self,
        filter_by: Iterable[SqlBinaryExpression] = (),
        session: Optional[AsyncSession] = None,
        raise_on_none: bool = True,
    ) -> ModelT | None:
        """
        Retrieve a single record from the database that matches the provided filter
        criteria. An exception is raised when more than one result is returned or no
        results are found when `raise_on_none` is True.

        Parameters
        ----------
        filter_by : Iterable[SqlBinaryExpression], optional
            Filter conditions to apply when querying the database. Defaults to an
            empty tuple.

        session : Optional[Session], optional
            SQLAlchemy session to use for querying. If not provided, a new session
            will be created and used for the operation.

        raise_on_none : bool, optional
            Specifies whether to raise an exception if no records match the specified
            filter criteria. Defaults to True.

        Returns
        -------
        ModelT
            The retrieved data model if a record is found; otherwise, ``None``
            when ``raise_on_none`` is set to False.

        Raises
        ------
        NoResultFound
            If `raise_on_none` is `True` and no results are found.

        MultipleResultsFound
            If more than one result is found.
        """
        # 'find_one' doesn't need an 'order_by', because it will be an exception
        # if more than one result is found by the query.
        stmt = self._make_select_statement(filter_by, ())
        async with self.get_or_create_session(session) as local_session:
            async with self._semaphore:
                result = await local_session.scalars(stmt)

            model = result.one() if raise_on_none else result.one_or_none()

        return model

    async def find_one_dto(
        self,
        filter_by: Iterable[SqlBinaryExpression] = (),
        session: Optional[AsyncSession] = None,
        raise_on_none: bool = True,
    ) -> Optional[DtoModel]:
        """
        Retrieve a single record from the database that matches the provided filter
        criteria. Converts the obtained database model into a data transfer object
        (DTO). An exception is raised when more than one result is returned or no
        results are found when `raise_on_none` is True.

        Parameters
        ----------
        filter_by : Iterable[SqlBinaryExpression], optional
            Filter conditions to apply when querying the database. Defaults to an
            empty tuple.

        session : Optional[Session], optional
            SQLAlchemy session to use for querying. If not provided, a new session
            will be created and used for the operation.

        raise_on_none : bool, optional
            Specifies whether to raise an exception if no records match the specified
            filter criteria. Defaults to True.

        Returns
        -------
        DtoModel
            The retrieved data model in DTO form if a record is found; otherwise, ``None``
            when ``raise_on_none`` is set to False.

        """
        # 'find_one' doesn't need an 'order_by', because it will be an exception
        # if more than one result is found by the query.
        stmt = self._make_select_statement(filter_by, ())
        async with self.get_or_create_session(session) as local_session:
            async with self._semaphore:
                result = await local_session.scalars(stmt)

            model = result.one() if raise_on_none else result.one_or_none()
            dto = model.to_dto() if model is not None else None

        return dto

    async def query(
        self, stmt: Select, session: AsyncSession | None = None
    ) -> list[RowMapping]:
        """Execute an arbitrary select statement and return the results as a list."""

        async with self.get_or_create_session(session) as local_session:
            async with self._semaphore:
                return list((await local_session.execute(stmt)).mappings())

    async def query_model(
        self,
        stmt: Select,
        model_type: Type[ReturnT],
        session: AsyncSession | None = None,
    ) -> list[ReturnT]:
        """Execute a select statement that is known to return a specific model type.

        ..warning::
            No run time validation is performed, so if your select statement
            does not return objects of ``ModelT`` it will raise a run time error.

        Parameters
        ----------
        stmt : Select
            _description_
        model_type : Type[ModelT]
            _description_
        session : AsyncSession | None, optional
            _description_, by default None

        Returns
        -------
        list[ModelT]
            _description_
        """
        async with self.get_or_create_session(session) as local_session:
            async with self._semaphore:
                return list((await local_session.scalars(stmt)).all())

    async def delete(
        self,
        model_class: Type[BaseModel],
        filter_by: Iterable[SqlBinaryExpression] = (),
        session: AsyncSession | None = None,
    ):
        """Delete objects from the database.

        Delete objects of type ``model_class`` that match the ``filter_by``
        criteria.

        Parameters
        ----------
        model_class : Type[BaseModel]
            The type of object to delete.
        filter_by : Iterable[SqlBinaryExpression]
            The conditions to filter by.
        session : AsyncSession | None, optional
            An SQLAlchemy session to use for querying. If not provided, a new session
            will be created and used for the operation.
        """
        where_clause = [e.to_expression(model_class) for e in filter_by]
        stmt = delete(model_class).where(*where_clause)

        async with self.get_or_create_session(session) as local_session:
            async with self._semaphore:
                await local_session.execute(stmt)

    # endregion API

    # region Helpers
    @asynccontextmanager
    async def get_or_create_session(
        self, session: Optional[AsyncSession]
    ) -> AsyncGenerator[AsyncSession]:
        """
        Use the existing session if it is not ``None``, otherwise create and
        return a new one.

        Parameters
        ----------
        session : AsyncSession], optional
            An existing session to use.

        Yields
        ------
        AsyncGenerator[AsyncSession]
            The existing or new session as a context manager.
        """
        if session is None:
            async with self.engine.session_scope() as engine_session:
                yield engine_session
        else:
            yield session

    # endregion Helpers
