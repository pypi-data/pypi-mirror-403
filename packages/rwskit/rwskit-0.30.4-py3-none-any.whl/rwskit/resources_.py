"""Methods and utilities for working with resource files."""

# Standard Library
from importlib import resources
from types import ModuleType


def read_text(package: str | ModuleType, filename: str, encoding="utf-8") -> str:
    """Open a text-based resource and return it as a string.

    Parameters
    ----------
    package : str or ModuleType
        ``anchor`` is either a name or a module object which conforms to the
        Package requirements
    filename : str
        The name of the resource to open in the package.
    encoding : str, default='utf-8'
        The name of the file encoding.

    Returns
    -------
    str
        The loaded resource.

    """
    return resources.files(package).joinpath(filename).read_text(encoding=encoding)
