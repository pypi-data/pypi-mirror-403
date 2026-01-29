# Future Library
from __future__ import annotations

# Standard Library
import logging

from typing import List, Union


class LogLevel(int):
    """A class for converting logging level string names to their integer counterparts."""

    def __new__(cls, level: Union[str, int]):
        if isinstance(level, int):
            if level in logging._levelToName:
                return super().__new__(cls, level)
            else:
                raise TypeError(f"Invalid logging level: {level}")

        # Otherwise assume we've got a string.
        level = level.upper()

        try:
            return super().__new__(cls, logging._nameToLevel[level])
        except KeyError:
            raise TypeError(f"invalid logging level: {level}")

    def __repr__(self):
        return logging._levelToName[self]

    def __str__(self):
        return self.__repr__()

    @classmethod
    def valid_levels(cls) -> List[LogLevel]:
        """
        Returns the list of valid log levels.

        Returns
        -------
        list[LogLevel]
            The list of valid log levels.
        """
        return [LogLevel(name) for name in logging.getLevelNamesMapping()]
