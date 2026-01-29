# Standard Library
import importlib
import pkgutil

from types import ModuleType, UnionType
from typing import *

# 3rd Party Library
from icontract import require

# Project Modules

# TODO 'is_optional' and 'is_union' need to be refactored so that everything
#      from 'typing' doesn't need to be imported.


def is_union(type_: Any) -> bool:
    """Check if the given ``type_`` is a union of types.

    A type can be a union if it uses the :class:`~typing.Union` type hint or
    the ``|`` operator.

    Parameters
    ----------
    type_ : Any
        The type to check.

    Returns
    -------
    bool
        ``True`` if the given type is a union, otherwise ``False``.

    """
    # Using `from __future__ import annotations` defers the loading of types
    # so `type_` might not be a `typing` Type object, but a string instead.
    # If it is a string we'll try to evaluate it into its actual class Type.
    # `eval` will raise an exception if the evaluated type is not already
    # imported (in globals). We only care about `typing.Optional` so if
    # a NameError is raised we can just ignore it and return False.

    # TODO Using `typing._eval_type` might be a better way to do this,
    #      but it is a protected method and I have not looked closely
    #      at the implementation.
    try:
        type_ = eval(type_, globals()) if isinstance(type_, str) else type_
    except NameError:
        return False
    else:
        return get_origin(type_) is Union or isinstance(type_, UnionType)


def is_optional(type_: Any) -> bool:
    """Check if a type is optional.

    An optional type is either defined by class:`typing.Optional` or by
    a :class:`~typing.Union` containing ``None``.

    Parameters
    ----------
    type_ : Any
        The type to check.

    Returns
    -------
    bool
        ``True`` if ``type_`` is optional.

    """
    # See the note in `is_union` about lazy type evaluation.
    try:
        type_ = eval(type_, globals()) if isinstance(type_, str) else type_
    except NameError:
        return False
    else:
        return is_union(type_) and (type(None) in get_args(type_))


@require(lambda cls: isinstance(cls, type), "The input must be a class type.")
def get_qualified_name(cls: type) -> str:
    """Get the fully qualified name of this class.

    The fully qualified name is the full path of package names, the module
    name, and class name.

    Parameters
    ----------
    cls : Type[Any]

    Returns
    -------
    str
        The fully qualified name of this class.

    Raises
    ------
    icontract.ViolationError
        If the input ``cls`` is not a type.
    """
    module, name = cls.__module__, cls.__qualname__

    if module is not None and module != "__builtin__":
        name = module + "." + name

    return name


@require(
    lambda qualified_class_name: "." in qualified_class_name,
    "The 'qualified_class_name' must at least refer to a module (the "
    "provided name does not contain a '.').",
)
@require(
    lambda qualified_class_name: bool(qualified_class_name),
    "The 'qualified_class_name' cannot be empty.",
)
def type_from_string(qualified_class_name: str) -> type:
    """Import and return the type object from a fully qualified class name.

    Parameters
    ----------
    qualified_class_name : str
        The fully qualified class name.

    Returns
    -------
    type
        The type object corresponding to the fully qualified class name.

    Raises
    ------
    icontract.ViolationError
        If the input ``qualified_class_name`` is ``None`` or empty.
    ModuleNotFoundError
        If the input ``qualified_class_name`` cannot be loaded.
    """
    tokens = qualified_class_name.split(".")
    module_name, class_name = ".".join(tokens[:-1]), tokens[-1]

    module = importlib.import_module(module_name)

    return getattr(module, class_name)


def import_all_modules_in_path(module_path: str) -> dict[str, ModuleType]:
    """Import all modules in a given path and return a dict of their names and modules.

    Parameters
    ----------
    module_path : str
        The full path to the module, e.g. ``foo.bar.baz``

    Returns
    -------
    dict[str, ModuleType]
        A dictionary mapping the module path segments to their corresponding modules.
    """
    result = {}
    parts = module_path.split(".")
    for i in range(1, len(parts) + 1):
        m = importlib.import_module(".".join(parts[:i]))
        result[m.__name__] = m

    return result


def import_all_modules(package: ModuleType):
    """Recursively traverse a package and import all of its modules.

    Parameters
    ----------
    package : ModuleType
        The package to traverse.
    """
    if not hasattr(package, "__path__"):
        return

    for loader, module_name, is_pkg in pkgutil.walk_packages(package.__path__):
        # Import the submodule
        submodule = importlib.import_module(f"{package.__name__}.{module_name}")

        # Recurse
        import_all_modules(submodule)
