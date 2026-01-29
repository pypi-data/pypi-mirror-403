"""Utilities for working with collections."""

# Future Library
from __future__ import annotations

# Standard Library
import logging as log

from collections import defaultdict
from itertools import islice
from types import GeneratorType
from typing import Any, Callable, Generator, Iterable, Mapping, Optional, TypeVar

# 3rd Party Library
import yaml

log = log.getLogger(__name__)

T = TypeVar("T")


def is_iterable(obj: Any, consider_string_iterable: bool = False) -> bool:
    """
    Tests if the object is iterable.

    Parameters
    ----------
    obj : any
        An object.
    consider_string_iterable : bool, default = False
        Whether to consider strings iterable or not.

    Returns
    -------
    bool
        ``True`` if ``obj`` is iterable.
    """
    if isinstance(obj, str):
        return consider_string_iterable

    try:
        iter(obj)
    except TypeError:
        return False
    else:
        return True


def is_generator(obj: Any) -> bool:
    """
    Checks if the object is a generator.

    Parameters
    ----------
    obj : any
        An object.

    Returns
    -------
    bool
        ``True`` if the object is a generator.

    """
    return isinstance(obj, GeneratorType)


def get_first_non_null_value(collection: Iterable) -> Optional[Any]:
    """Recursively try to get the first non-null value in a collection.

    This method will recursively traverse the collection until it finds
    a non-iterable value that is not ``None``.

    Parameters
    ----------
    collection : Iterable
        The collection to retrieve the value from.

    Returns
    -------
    Any, optional
        The first non-null value in the series, if one exists, otherwise return
        ``None``.

    """
    for value in collection:
        if is_iterable(value) and not isinstance(value, str):
            value = get_first_non_null_value(value)

        if value is not None:
            return value

    return None


def recursive_sort(obj: Any) -> Any:
    """
    Attempts to sort an object recursively according to the following rules:

    * If the object is a dictionary, it will be sorted by its keys and its
      values will be sorted recursively.
    * If the object is a list or tuple, it will be sorted by its values.
      Typically, a value is a primitive, but lists, tuples, and dictionaries
      are also valid. In these cases, the collections are compared after
      sorting.
    * Any other value is returned unchanged.

    .. note::
        Collections of dictionaries (e.g., lists, tuples, sets, other
        dictionaries) cannot be directly compared because ``__lt__`` is not
        defined. When a collection of dictionaries is encountered, they are
        compared using (sorted) yaml strings. Yaml is used because it supports
        sorting by keys, similar to json, but supports more data types.

    Parameters
    ----------
    obj : Any
        The input object

    Returns
    -------
    Any
        The returned object sorted.

    Raises
    ------
    TypeError
        If you have a collection of dictionaries that cannot be converted to
        yaml strings.
    """

    def _key_fn(e: Any) -> Any:
        if isinstance(e, dict):
            return yaml.dump(
                e,
                sort_keys=True,
                default_flow_style=True,
                explicit_start=False,
                explicit_end=False,
                width=float("inf"),
            )
        elif is_iterable(e):
            return sorted(e, key=lambda x: _key_fn(x))
        else:
            return e

    if isinstance(obj, dict):
        return {k: recursive_sort(obj[k]) for k in sorted(obj)}
    elif isinstance(obj, list):
        values = sorted(obj, key=lambda e: _key_fn(e))
        return [recursive_sort(e) for e in values]
    elif isinstance(obj, tuple):
        values = sorted(obj, key=_key_fn)
        return tuple([recursive_sort(e) for e in values])
    elif is_iterable(obj) or is_generator(obj):
        return list(obj)
    else:
        return obj


def remove_none_from_dict(d: dict[Any, Any]) -> dict[Any, Any]:
    """Recursively remove ``None`` values from a (nested) dictionary."""

    def _do_removal(obj: Any) -> Any:
        if isinstance(obj, Mapping):
            return {k: _do_removal(v) for k, v in obj.items() if v is not None}
        elif isinstance(obj, list):
            return [remove_none_from_dict(e) for e in obj]
        elif isinstance(obj, set):
            return {remove_none_from_dict(e) for e in obj}  # type: ignore
        else:
            return obj

    return _do_removal(d)


def nested_defaultdict(
    default_factory: Callable, depth: int = 1, current_depth: int = 0
) -> defaultdict:
    """
    Create a nested defaultdict with ``depth`` levels that eventually
    bottoms out with the given ``default_factory``.

    Parameters
    ----------
    default_factory : callable
        The function used to create the default values.
    depth : int (default=1)
        How many levels to the dict.
    current_depth : int
        The current depth during creation.

    Returns
    -------
    defaultdict
        The nested defaultdict.
    """
    if current_depth == depth:
        return default_factory()

    def _inner_dict():
        return nested_defaultdict(default_factory, depth, current_depth + 1)

    return defaultdict(_inner_dict)


def defaultdict_to_dict(obj: Any) -> Any:
    """
    Convert a possibly nested defaultdict to a regular dictionary.

    Parameters
    ----------
    obj : defaultdict
        The default dict to convert.

    Returns
    -------
    dict
        A possibly nested regular dictionary.
    """
    if isinstance(obj, defaultdict):
        obj = dict(obj)

    if isinstance(obj, dict):
        for key, value in obj.items():
            obj[key] = defaultdict_to_dict(value)

    return obj


def chunk(iterable: Iterable[T], size: int) -> Generator[list[T]]:
    """Return chunks of at most ``size`` items from the given ``iterable``.

    Parameters
    ----------
    iterable : Iterable[T]
        The iterable to draw chunks from.
    size : int
        The max number of elements in a chunk.

    Yields
    ------
    Generator[list[T]]
        Chunks.

    Raises
    ------
    ValueError
        If ``size`` is not positive.
    """
    if size <= 0:
        raise ValueError(f"'size' must be positive. Got: {size}")

    itr = iter(iterable)
    while chunk := list(islice(itr, size)):
        yield chunk
