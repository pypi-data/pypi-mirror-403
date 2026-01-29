# Future Library
from __future__ import annotations

# Standard Library
import os

from importlib.resources.abc import Traversable
from typing import Union

PathLike = Union[str, os.PathLike, Traversable]
