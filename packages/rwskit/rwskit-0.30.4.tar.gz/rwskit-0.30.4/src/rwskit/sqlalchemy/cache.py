"""Classes for caching models."""

# Future Library
from __future__ import annotations

# Standard Library
from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Any, Callable, Generic, Mapping, Self, Type, TypeVar

# 1st Party Library
from rwskit.sqlalchemy.base import BaseModel
from rwskit.sqlalchemy.engine import (
    AlchemyEngine,
    AsyncAlchemyEngine,
    SyncAlchemyEngine,
)
from rwskit.sqlalchemy.repository import AsyncRepository, Repository, SyncRepository

ModelT = TypeVar("ModelT", bound=BaseModel)
"""A generic type for a ``BaseModel``."""

EngineT = TypeVar("EngineT", bound=AlchemyEngine)

RepoT = TypeVar("RepoT", bound=Repository)
"A generic type for a ``Repository``."

KeyFunction = Callable[[ModelT], Any]
"""A function that takes a model DTO instance and returns the cache value key."""


class ModelCache(ABC, Mapping, Generic[ModelT, RepoT]):
    """A generic cache for preloading and accessing predefined model instances."""

    def __init__(self, model_cls: Type[ModelT], key_fn: KeyFunction):
        self.model_cls = model_cls
        self.key_fn = key_fn
        self._cache: dict[Any, ModelT] = {}

    def __getitem__(self, key: Any) -> ModelT:
        """
        Retrieve a model instance by its key.

        Parameters
        ----------
        key : Any
            The key to look up in the cache.

        Returns
        -------
        M
            The cached model instance.

        Raises
        ------
        KeyError
            If the key is not found in the cache.
        """
        return self._cache[key]

    def __iter__(self) -> Iterator[Any]:
        """
        Return an iterator over the keys in the cache.

        Returns
        -------
        Iterator[Any]
            An iterator over the keys.
        """
        return iter(self._cache)

    def __len__(self) -> int:
        """
        Return the number of items in the cache.

        Returns
        -------
        int
            The number of cached items.
        """
        return len(self._cache)

    def all(self) -> list[ModelT]:
        """
        Retrieve all cached model instances.

        Returns
        -------
        list[M]
            A list of all cached model instances.
        """
        return list(self._cache.values())


class SyncModelCache(ModelCache[ModelT, SyncRepository[ModelT]]):
    def load(self, repository: SyncRepository[ModelT]) -> Self:
        """Load the models in to the cache."""
        models = repository.find_all_models()
        self._cache = {self.key_fn(m): m for m in models}

        return self


class AsyncModelCache(ModelCache[ModelT, AsyncRepository[ModelT]]):
    async def load(self, repository: AsyncRepository[ModelT]) -> Self:
        """Load the models in to the cache."""
        models = await repository.find_all_models()
        self._cache = {self.key_fn(m): m for m in models}

        return self


CacheT = TypeVar("CacheT", bound=ModelCache)


class ModelCacheRegistry(Generic[CacheT, EngineT]):
    def __init__(self, engine: EngineT):
        self._engine = engine

    @property
    @abstractmethod
    def engine(self) -> EngineT: ...

    @property
    @abstractmethod
    def registry(self) -> dict[Type[BaseModel], CacheT]: ...

    def find(self, model_cls: Type[ModelT], key: Any):
        """Find an instance of the ``model_cls`` in the corresponding cache using the given ``key``.

        Parameters
        ----------
        model_cls : Type[ModelT]
            The type of model we want to find.
        key : Any
            The key to look up the instance.

        Returns
        -------
        ModelT
            The instance with the matching key value.

        Raises
        ------
        KeyError
            If the ``model_cls`` is not registered or if there are no instances
            in the cache with a matching ``key`` value.
        """
        return self.registry[model_cls][key]

    def get_cache(self, model_cls: Type[ModelT]) -> CacheT:
        """Get the class:`ModelCache` instance for the given ``model_cls``.

        Parameters
        ----------
        model_cls : Type[ModelT]
            The type of model we want to get the cache for.

        Returns
        -------
        CacheT
            The cache instance for the ``model_cls``.

        Raises
        ------
        KeyError
            If the ``model_cls`` is not registered.
        """
        return self.registry[model_cls]


class SyncModelCacheRegistry(ModelCacheRegistry[SyncModelCache, SyncAlchemyEngine]):
    def __init__(self, engine: SyncAlchemyEngine):
        super().__init__(engine)

        self._registry: dict[Type[BaseModel], SyncModelCache] = {}

    @property
    def engine(self) -> SyncAlchemyEngine:
        return self._engine

    @property
    def registry(self) -> dict[Type[BaseModel], SyncModelCache]:
        return self._registry

    def register(
        self,
        model_cls: Type[ModelT],
        key_fn: KeyFunction,
    ):
        """Register a new :class:`ModelCache`.

        If a cache already exists for the given ``model_cls`` it will be
        reloaded.

        Parameters
        ----------
        model_cls : Type[ModelT]
            The model class to create and load the cache for.
        key_fn : KeyFunction
            The function used to extract the key values from.
        """
        repository = SyncRepository(self._engine, model_cls)
        cache = SyncModelCache(model_cls, key_fn).load(repository)
        self._registry[model_cls] = cache


class AsyncModelCacheRegistry(ModelCacheRegistry[AsyncModelCache, AsyncAlchemyEngine]):
    def __init__(self, engine: AsyncAlchemyEngine):
        super().__init__(engine)

        self._registry: dict[Type[BaseModel], AsyncModelCache] = {}

    @property
    def engine(self) -> AsyncAlchemyEngine:
        return self._engine

    @property
    def registry(self) -> dict[Type[BaseModel], AsyncModelCache]:
        return self._registry

    async def register(self, model_cls: Type[ModelT], key_fn: KeyFunction):
        """Register a new :class:`ModelCache`.

        If a cache already exists for the given ``model_cls`` it will be
        reloaded.

        Parameters
        ----------
        model_cls : Type[ModelT]
            The model class to create and load the cache for.
        key_fn : KeyFunction
            The function used to extract the key values from.
        """
        repository = AsyncRepository(self._engine, model_cls)
        cache = await AsyncModelCache(model_cls, key_fn).load(repository)
        self._registry[model_cls] = cache
