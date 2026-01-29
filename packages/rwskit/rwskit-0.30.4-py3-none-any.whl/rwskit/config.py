# Future Library
from __future__ import annotations

# Standard Library
import abc
import dataclasses
import datetime
import json
import logging
import os
import re

from contextlib import contextmanager
from io import IOBase, StringIO
from pathlib import Path
from types import UnionType
from typing import (
    Any,
    Callable,
    ClassVar,
    Iterable,
    Literal,
    Mapping,
    Optional,
    Self,
    Type,
    TypeVar,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

# 3rd Party Library
import yaml
import yaml_include

from dateutil.parser import parse as parse_date
from icontract import ensure, require
from pydantic.dataclasses import dataclass
from yamlable import YamlAble

# 1st Party Library
from rwskit.cli import LogLevel
from rwskit.dataclasses_ import DataclassRegistry
from rwskit.types_ import get_qualified_name

log = logging.getLogger(__name__)


T = TypeVar("T", bound="YamlConfig")
E = TypeVar("E", bound="EnvironmentConfig")
I = TypeVar("I")

TypeParser = Callable[[str], I]


# Enable include directives inside yaml files
@contextmanager
def _enable_yaml_include(path: Path):
    tags = ("!inc", "!include")
    loaders = (yaml.Loader, yaml.BaseLoader, yaml.SafeLoader, yaml.FullLoader)
    base_dir = path.parent

    for tag in tags:
        for loader in loaders:
            yaml.add_constructor(
                tag, yaml_include.Constructor(base_dir=base_dir), loader
            )

    yield

    for tag in tags:
        for loader in loaders:
            del loader.yaml_constructors[tag]


# According to the python documentation the following (commented) code should
# allow any class that uses the 'YamlConfigMeta' to automatically be viewed
# as a dataclass from the perspective of the type checker. Unless I am doing
# something wrong (very possible), it does not work for me and PyCharm
# does not detect that subclasses should be considered as dataclasses. The
# code functions correctly, but PyCharm will issue warnings about unresolved
# attributes for all subclasses and cannot provide autocompletion.
#
# However, if you annotate each individual class with @dataclass_transform
# PyCharm will recognize the class as a dataclass. This is obviously not ideal
# but better than nothing.

# @dataclass_transform(kw_only_default=True, frozen_default=True)
# class DataclassMeta(type):
#     def __new__(mcs, name, bases, namespace, **kwargs):
#         new_cls = super().__new__(name, bases, namespace, **kwargs)
#         return pydantic_dataclass(new_cls, frozen=True, kw_only=True)
#
#
# class YamlConfigMeta(DataclassMeta, type(YamlAble)):
#     pass


class YamlConfig(YamlAble):
    """A base class for serializable configuration objects.

    Classes that inherit from this class can easily be serialized to and from
    YAML files. Given a YAML file, the class can be reconstructed as long
    as the YAML attributes can be uniquely mapped to a subclass of
    :class:`YamlConfig`.

    Additionally, the configuration can be split across multiple files for
    better modularity using the ``!include`` directive.

    Examples
    --------
    >>> class ChildConfig(YamlConfig):
    ...     id: int
    ...     name: str
    ...     timestamp: datetime.datetime
    >>> class ParentConfig(YamlConfig):
    ...     parent_attr: str = "parent_attr_value"
    ...     child_attr:
    >>> expected_config = ParentConfig(
    ...     id=1,
    ...     child_config=ChildConfig(
    ...         id=2,
    ...         name="child_config",
    ...         timestamp=datetime.datetime.now()
    ... )
    >>> plain_yaml = '''
    ... child_config:
    ...     id: 2
    ...     name: child_config
    ...     timestamp: 2024-11-19 13:55:34.064388
    ...  id: 1
    ... '''
    >>> from_plain_yaml = YamlConfig.loads_yaml(plain_yaml)
    >>> assert from_plain_yaml == expected_config

    The ``!yamlable`` tag can be used  to explicitly tell the YAML parser
    which class to construct. The syntax is ``!yamlable/<fully_qualified_class_name>``.

    >>> tagged_yaml = '''
    ... !yamlable/my_package.my_module.ParentConfig
    ... child_config: !yamlable/my_package.my_module.ChildConfig
    ...     id: 2
    ...     name: child_config
    ...     timestamp: 2024-11-19 13:55:34.064388
    ... id: 1
    ... '''
    >>> assert YamlConfig.loads_yaml(tagged_yaml) == expected_config

    You can use the ``!include`` directive to include other YAML files.
    For example, assume you have the following two YAML files:

    .. code-block:: yaml

        # child_config.yaml

        id: 2
        name: "child_config"
        timestamp: 2024-11-19 13:55:34.064388

    .. code-block:: yaml

        # parent_config.yaml

        id: 1
        child_config: !include child_config.yaml

    You can load the parent config using ``YamlConfig.load_yaml`` as follows:

    >>> YamlConfig.load_yaml("parent_config.yaml")
    """

    # Maintain a registry of all classes that inherit from this base class.
    # Although, I don't plan to use this in a multithreaded context, it is
    # pretty easy to make it thread safe with a lock.
    __registry: ClassVar[DataclassRegistry] = DataclassRegistry()

    default_type_parsers = {
        int: int,
        float: float,
        bool: lambda x: x.lower() in ("true", "1", "t", "y", "yes"),
        str: lambda x: x,
        datetime.datetime: parse_date,
        datetime.date: lambda x: parse_date(x).date(),
    }

    @require(
        lambda self: dataclasses.is_dataclass(self), "The class must be a dataclass."
    )
    def __init__(self):
        pass

    def __init_subclass__(cls: Type[Self], **kwargs: Any):
        """Initialize subclasses to make them suitable configuration objects.

        * Automatically assign the ``__yaml_tag_suffix__`` using the fully
          qualified class name.
        * Convert the class to a ``pydantic.dataclasses.dataclass`` that has
          ``frozen=True`` and ``kw_only=True``.

        Parameters
        ----------
        kwargs : Any
        """
        super().__init_subclass__(**kwargs)

        cls.__yaml_tag_suffix__ = get_qualified_name(cls)

        # Add the subclass to the registry so we can dynamically load the class
        # without having to import it first.
        YamlConfig.__registry.register(cls)  # noqa

    @classmethod
    def get_registered_classes(cls) -> set[Type[YamlConfig]]:
        """Get the set of classes currently registered as configuration objects.

        Returns
        -------
        set[Type[YamlConfig]]
            The set of registered yaml config classes.

        """
        return set(cls.__registry)

    def dumps_plain_yaml(self: Self) -> str:
        """
        Represent the class as plain YAML without any tags.

        .. note::
            It may not be possible to reconstruct the python object from this
            string.

        Returns
        -------
        str
            The object as plain YAML without any tags.
        """
        d = self._transform_sets_to_lists(self._dataclass_to_dict(self))

        return yaml.safe_dump(d)

    @classmethod
    def _dataclass_to_dict(cls, obj: Any) -> Any:
        if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
            return {
                k: cls._dataclass_to_dict(v) for k, v in dataclasses.asdict(obj).items()
            }
        elif isinstance(obj, str):
            return obj
        elif isinstance(obj, Mapping):
            return {k: cls._dataclass_to_dict(v) for k, v in obj.items()}
        elif isinstance(obj, Iterable):
            return [cls._dataclass_to_dict(v) for v in obj]
        else:
            return obj

    @classmethod
    def _transform_sets_to_lists(cls, obj: Any) -> Any:
        if isinstance(obj, set):
            return [cls._transform_sets_to_lists(e) for e in obj]
        elif isinstance(obj, Mapping):
            return {k: cls._transform_sets_to_lists(v) for k, v in obj.items()}
        elif isinstance(obj, str):
            return obj
        elif isinstance(obj, Iterable):
            return [cls._transform_sets_to_lists(v) for v in obj]
        else:
            return obj

    @classmethod
    @require(
        lambda file_path_or_stream: isinstance(
            file_path_or_stream, (str, Path, IOBase, StringIO)
        ),
        "'file_path_or_stream' must be a string, pathlib.Path, IOBase, or StringIO object.",
    )
    def load_yaml(
        cls: Type[T],
        file_path_or_stream: str | Path | IOBase | StringIO,
        safe: bool = True,
    ) -> T:
        raw_config = cls._load_raw_yaml(file_path_or_stream, safe)

        # If the deserialized object is an instance of the loader class then
        # we can simply return the object (i.e., it contained all the tags
        # necessary to reconstruct the config).
        if isinstance(raw_config, cls):
            return raw_config

        # Since a config file represents a data class the top level
        # object of a plain yaml config must be a dictionary (i.e., the
        # attributes of the dataclass).
        if not isinstance(raw_config, Mapping):
            raise TypeError("Invalid YAML config file.")

        return YamlConfig.__registry.construct_registered_dataclass(raw_config)

    @classmethod
    def _load_raw_yaml(
        cls: Type[T],
        file_path_or_stream: str | Path | IOBase | StringIO,
        safe: bool = True,
    ) -> Any:
        # Deserialize the yaml into an object. If the yaml contains known
        # tags it will return the appropriate python classes, otherwise
        # it will return primitive python types (e.g., ints, floats, lists,
        # dicts, etc.)

        if not safe:
            raise NotImplementedError("Only safe loading is supported.")

        yaml_loader = yaml.safe_load

        if isinstance(file_path_or_stream, (str, Path)):
            with open(file_path_or_stream, "rt") as fh:
                # This allows using paths relative to the input config file
                # rather than paths relative to the current working directory.
                with _enable_yaml_include(Path(file_path_or_stream)):
                    return yaml_loader(fh)
        else:
            with file_path_or_stream as fh:
                return yaml_loader(fh)


@dataclass(frozen=True, kw_only=True, config={"arbitrary_types_allowed": True})
class EnvironmentConfig(abc.ABC):
    """A mixin class for configuration objects to help constructing them from environment variables.

    This mixin adds a method :meth:`from_environment` that will try to parse
    environment variables into the correct type for the dataclass. All you
    have to do is implement the :meth:`environment_mapping` method to provide
    a mapping between environment variable names and the dataclass field names.
    """

    _default_type_parsers: ClassVar[dict[Any, Any]] = {
        bool: lambda x: x.lower() in ("true", "1", "t", "y", "yes"),
        int: int,
        float: float,
        str: lambda x: x,
        Literal: lambda x: x,
        datetime.datetime: parse_date,
        datetime.date: lambda x: parse_date(x).date(),
        re.Pattern: lambda x: re.compile(x),
        LogLevel: lambda x: LogLevel(x) if isinstance(x, (str, int)) else x,
    }
    _dataclass_fields = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def get_default_type_parsers(cls) -> dict[Any, TypeParser]:
        """Get the default type parsers for this class."""

        return cls._default_type_parsers.copy()

    @classmethod
    @abc.abstractmethod
    @ensure(
        lambda cls, result: all(cls._is_valid_field(v) for v in result.values()),
        "All values in the mapping must be a valid field name.",
    )
    def environment_mapping(cls: Type[E]) -> Mapping[str, str]:
        """Returns a mapping from environment variable names corresponding field names.

        Returns
        -------
        Mapping[str, str]

        Raises
        ------
        ViolationError
            If any of the returned values are not a field name of this
            class. Note, not all fields need to be included in the mapping, but
            any entry that is included must correspond to a field name.
        """
        pass

    @classmethod
    def _is_valid_field(cls, field_name: str) -> bool:
        # A valid field is any field that can be used in the constructor.
        field_names = {f.name for f in dataclasses.fields(cls) if f.init}  # type: ignore

        return field_name in field_names

    @classmethod
    def from_environment(
        cls, type_parsers: Optional[dict[Any, TypeParser]] = None, **kwargs
    ) -> Self:
        """
        Create an instance from environment variables.

        Environment variables can represent python primitive values,
        date objects, datetime objects. They can also be lists, sets, tuples,
        or dicts of these types. Collections are space separated string.
        Multi-word strings should be enclosed in double quotes. Dictionary
        key value pairs are delimited by '='. Spaces are not allowed in
        keys or values.

        Parameters
        ----------
        type_parsers: dict[Any, TypeParser]
            A mapping from python types to functions that parse a string
            into that type. These will be combined and override the default
            parsing rules described above.

        kwargs
            Additional keyword arguments to override the values from the
            environment or composite fields (e.g., other dataclasses),
            which are constructed externally.

        Returns
        -------

        """
        type_parsers = cls.get_default_type_parsers() | (type_parsers or {})
        environment_kwargs = cls.get_environment_kwargs(type_parsers)
        init_kwargs = environment_kwargs | kwargs

        return cls(**init_kwargs)

    @classmethod
    def get_environment_kwargs(
        cls, type_parsers: Optional[dict[Any, TypeParser]] = None
    ) -> dict[str, Any]:
        """
        Get the keyword arguments for this dataclass that are available
        from the environment.

        Parameters
        ----------
        type_parsers : dict[Type, TypeParser]
            The type parsers to use when parsing environment variables.

        Returns
        -------
        dict[str, Any], optional
            The keyword arguments as a dictionary.

        """
        type_parsers = cls.get_default_type_parsers() | (type_parsers or {})

        # Map the fields to the environment variable (string) values, for all
        # non-empty values.
        value_map = {
            fn: environment_value
            for vn, fn in cls.environment_mapping().items()
            if (environment_value := os.environ.get(vn)) is not None
        }

        # For each field, attempt to parse the value.
        resolved_types = get_type_hints(cls)
        kwargs = dict()
        for attribute_name, environment_value in value_map.items():
            actual_type = cls._get_actual_type(resolved_types[attribute_name])

            try:
                value = cls.parse_value_from_string(
                    environment_value,
                    actual_type,
                    type_parsers,
                )
            except ValueError as e:
                log.error(
                    f"Class '{cls.__name__}' unable to parse environment "
                    f"variable '{environment_value}' for attribute '{attribute_name}' "
                    f"into type '{actual_type}': {e}"
                )

                raise e
            else:
                kwargs[attribute_name] = value

        return kwargs

    # A utility method to make sure we get the actual field type in case
    # it is marked optional.
    @classmethod
    def _get_actual_type(cls, t: Type[I]) -> Type[I]:
        if get_origin(t) is Union:
            args = get_args(t)
            if len(args) == 2 and type(None) in args:
                args = [a for a in args if a is not type(None)]
                return args[0]
            else:
                raise NotImplementedError(
                    "Unions of more than one type are not supported"
                )
        return t

    @classmethod
    def get_dataclass_field_map(cls: Type[Self]) -> dict[str, dataclasses.Field]:
        """Get a mapping from field names to their dataclass fields."""

        if cls._dataclass_fields is None:
            cls._dataclass_fields = {f.name: f for f in dataclasses.fields(cls)}  # type: ignore

        return cls._dataclass_fields

    @classmethod
    def get_field_from_name(cls, field_name: str) -> dataclasses.Field:
        """Get the dataclass field from its name."""
        return cls.get_dataclass_field_map()[field_name]

    @classmethod
    def parse_value_from_string(
        cls,
        input_string: str,
        target_type: Type[I],
        type_parsers: Optional[dict[Type[I], TypeParser]] = None,
    ):
        """
        Try to parse an input string into the given python ``target_type``.

        The input string can be a single value that can be parsed by
        the default parsing rules or any of the rules implemented by the
        given ``type_parsers``. By default, the parsable values are: str, int,
        float, bool, datetime.datetime, datetime.date, re.Pattern, and any
        class that can be constructed from a single string argument (e.g.,
        ``pathlib.Path``.

        To handle more complex ``target_types``, the input string can also
        be a JSON string. The string will be parsed as JSON and the resulting
        object will be traversed to try to convert the leaf values using the
        all the available parsing rules.

        Parameters
        ----------
        input_string : str
            The string to parse.
        target_type : Type
            The python type to parse the value into.
        type_parsers : dict[Type, TypeParser], optional
            An optional dictionary that maps a type to a function that
            parses a string to that type. These rules will augment the default
            parsing rules given by :meth:`get_default_type_parsers` and will
            take precedent over the default rules if there is a conflict.

        Returns
        -------
        An instance of the target type parsed from the environment value.
        """
        type_parsers = cls.get_default_type_parsers() | (type_parsers or {})

        def parse_base_type(value: str, hint: Type[Any]):
            """Parse a base type (no origin) from a string."""

            def constructor_parser(x: str) -> Any:
                """Try parsing ``x`` assuming ``hint`` is callable"""
                # If hint is not callable, we'll catch the exception later.
                return hint(x)  # type: ignore

            hint = get_origin(hint) or hint

            try:
                return type_parsers.get(hint, constructor_parser)(value)
            except Exception as e:
                raise ValueError(
                    f"Unable to parse '{value}' of type '{type(value).__name__}' as {hint}. "
                    f"Raised from '{type(e).__name__}': {str(e)}"
                ) from e

        def parse_value(value: Any, hint: Type[Any]):
            """Recursively try to parse an arbitrary value to the given type."""
            origin = get_origin(hint)

            if origin is Literal:
                return parse_value(value, str)
            if origin is list:
                inner_type = get_args(hint)[0]
                return [parse_value(e, inner_type) for e in value]
            elif origin is set:
                inner_type = get_args(hint)[0]
                return set(parse_value(e, inner_type) for e in value)
            elif origin is tuple:
                inner_types = get_args(hint)
                return tuple(parse_value(e, t) for e, t in zip(value, inner_types))
            elif origin is dict:
                key_type, value_type = get_args(hint)
                return {
                    parse_value(k, key_type): parse_value(v, value_type)
                    for k, v in value.items()
                }
            elif origin in (Union, UnionType):
                inner_types = [t for t in get_args(hint) if t is not type(None)]
                for inner_type in inner_types:
                    try:
                        return parse_value(value, inner_type)
                    except Exception:
                        pass
                raise ValueError(f"Unable to parse '{value}' as an of {inner_types}.")
            elif origin is None:
                value_type = type(value)
                if value_type in (int, float, bool):
                    # Note, I shouldn't have to also check that the target_type
                    # matches the value_type, because pydantic will do that
                    # for us when it constructs the object.
                    return value
                elif value_type is str:
                    return parse_base_type(str(value), hint)
                else:
                    raise ValueError(
                        f"Unable to parse '{value}' of type '{value_type}' as {hint}."
                    )

            raise ValueError(f"Unsupported type: {hint}")

        try:
            return parse_value(json.loads(input_string), target_type)
        except json.JSONDecodeError:
            return parse_value(input_string, target_type)
