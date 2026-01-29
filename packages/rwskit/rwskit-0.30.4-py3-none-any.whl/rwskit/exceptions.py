"""Utilities related to exceptions."""

# Standard Library
from typing import Any, Type


def raise_exception(
    msg: str, exception_type: Type[Exception] = ValueError, **kwargs: Any
):
    """Always raises the given ``exception_type` with the supplied ``msg`` and ``kwargs``.

    Parameters
    ----------
    msg : str
        The message for the exception.
    exception_type : Type[Exception], default = ``ValueError``
        The type of exception to raise.
    kwargs : Any
        Any additional kwargs to pass to the exception

    Raises
    ------
    exception_type
    """
    raise exception_type(msg, **kwargs)
