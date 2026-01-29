"""Utilities for numeric operations."""

# Future Library
from __future__ import annotations

# Standard Library
import ctypes

from typing import Optional

int_8_max = (1 << 8) - 1
int_16_max = (1 << 16) - 1
int_32_max = (1 << 32) - 1
int_64_max = (1 << 64) - 1


def int_(s: Optional[str], falsy_as_none: bool = True) -> Optional[int]:
    """
    Convert a string `s` to an integer. If `s` is `None` return `None`
    instead of raising an exception.

    Parameters
    ----------
    s : str, optional
        The string to convert.
    falsy_as_none : bool, default=True
        If `True` all falsy values of `s` (other than ``0``) will return
        `None`, otherwise only `None` values will be passed through and
        an exception will be raised.

    Returns
    -------
    int, optional
        `None` if `s` is `None`, otherwise an integer if `s` is not `None` and
        is parsable.

    Raises
    ------
    ValueError
        If the string cannot be parsed.


    """
    # Note `int` strips whitespace
    if falsy_as_none:
        return int(s) if s else None

    return int(s) if s is not None else None


def float_(s: Optional[str], falsy_as_none: bool = True) -> Optional[float]:
    """
    Convert a string `s` to a float. If `s` is `None` return `None`
    instead of raising an exception.

    Parameters
    ----------
    s : str, optional
        The string to convert.
    falsy_as_none : bool, default=True
        If `True` all falsy values of `s` will return `None` (other than ``0``),
        otherwise only `None` values will be passed through and an exception
        will be raised..

    Returns
    -------
    float, optional
        `None` if `s` is `None`, otherwise a float if `s` is not `None` and
        is parseable.

    Raises
    ------
    ValueError
        If the string cannot be parsed.


    """
    if falsy_as_none:
        return float(s) if s else None

    return float(s) if s is not None else None


def to_signed(value: int) -> int:
    """
    If the value is positive, this will return a signed version of the number
    that fits in the same size integer type. For example,  ``129`` is a valid
    8-bit signed integer, but a 16-bit unsigned integer. This method will
    convert the number to the corresponding signed integer that still fits
    in 8-bits. In this case ``127``.

    Parameters
    ----------
    value : int
        The value to convert.

    Returns
    -------
    int
        The signed version.

    Raises
    ------
    ValueError
        If the ``value`` is more than 64-bits.
    """
    if value > int_64_max:
        raise ValueError(f"Only 64-bit values or smaller are supported. Got: {value}")

    if value <= 0:
        return value

    if value <= int_8_max:
        return ctypes.c_int8(value).value
    if value <= int_16_max:
        return ctypes.c_int16(value).value
    if value <= int_32_max:
        return ctypes.c_int32(value).value
    if value <= int_64_max:
        return ctypes.c_int64(value).value

    raise ValueError(f"Unexpected value: {value}")


def round_to_nearest(x: float, *values: float) -> float:
    """
    Round x to either ``low`` or ``high`` depending on which one ``x`` is
    closer to.

    Parameters
    ----------
    x
    low
    high

    Returns
    -------
    float
        Either ``low`` or ``high`` depending on which ``x`` is closer to.
    """
    closest_value = min(values, key=lambda v: abs(x - v))

    return round(x / closest_value) * closest_value
