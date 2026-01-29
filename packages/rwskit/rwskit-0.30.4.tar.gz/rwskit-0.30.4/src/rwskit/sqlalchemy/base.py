"""An enhanced SqlAlchemy declarative base class."""

# Future Library
from __future__ import annotations

# Standard Library
import copy
import dataclasses
import importlib
import logging

from collections import deque
from dataclasses import MISSING, Field
from functools import cache
from types import ModuleType
from typing import (
    Any,
    Callable,
    ClassVar,
    Iterable,
    Optional,
    Protocol,
    Self,
    Type,
    TypeGuard,
    cast,
    dataclass_transform,
    get_type_hints,
)

# 3rd Party Library
import pydantic
import sqlalchemy as sa

from icontract import ensure, require
from sqlalchemy import ColumnElement, Index, MetaData, Table, event
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import (
    ColumnProperty,
    CompositeProperty,
    DeclarativeBase,
    InspectionAttr,
    MappedAsDataclass,
    MappedColumn,
    MappedSQLExpression,
    Mapper,
    MapperProperty,
    Relationship,
    RelationshipProperty,
    declared_attr,
    mapped_column,
)

# 1st Party Library
from rwskit.collections_ import remove_none_from_dict
from rwskit.strings_ import camel_to_snake_case
from rwskit.types_ import get_qualified_name, import_all_modules_in_path, is_optional

log = logging.getLogger(__name__)


DtoModelType = Type[pydantic.BaseModel]
"""The base type for a DTO model."""

DtoModel = pydantic.BaseModel
"""An alias of ``pydantic.BaseModel, which is the base class of all DTO objects."""

TableArgs = dict[str, Any] | tuple[Any, ...]
"""The type of the ``__table_args__`` attribute on a :class:`~sqlalchemy.Table`."""


def base_mapped_column(
    *args: Any, dto: bool = True, natural_key: bool = False, **kwargs: Any
) -> MappedColumn[Any]:
    """Extends :func:`sa.orm.mapped_column` to add kwargs for ``dto`` and ``natural_key``.

    This method is equivalent to ``mapped_column``, but allows for setting
    the ``dto`` and ``nk`` values as keyword parameters instead directly using
    the ``info`` parameter of the ``mapped_column``.

    By default ``dto=True``, which means the column will be included in the
    corresponding data transfer object created by :meth:`BaseModel.to_dto`.

    By default ``nk=False``. Set ``nk=True`` on columns you want to be part of
    the natural key.

    If the ``info`` parameter already contains mappings for ``dto`` or ``nk``
    those values will take precedence over the parameters of this method.

    Parameters
    ----------
    dto: bool, default = True
        Whether the column should be included in the data transfer object.
    natural_key: bool, default = False
        Whether the column should be a part of the natural key.

    Returns
    -------
    MappedColumn
        The ``MappedColumn``.
    """
    info = kwargs.pop("info", {})
    if "dto" not in info:
        info["dto"] = dto

    if "nk" not in info:
        info["nk"] = natural_key

    return mapped_column(*args, info=info, **kwargs)


def natural_key_column(
    *args: Any, dto: bool = True, **kwargs: Any
) -> MappedColumn[Any]:
    """A :func:`base_mapped_column` where ``natural_key`` and ``compare`` are ``True``.

    Parameters
    ----------
    dto: bool, default = True
        Whether the column should be included in the data transfer object.

    Returns
    -------
    MappedColumn[Any]
        The ``MappedColumn``.
    """
    return base_mapped_column(*args, compare=True, dto=dto, natural_key=True, **kwargs)


def data_column(*args: Any, dto: bool = True, **kwargs: Any) -> MappedColumn[Any]:
    """A :func:`base_mapped_column` where ``natural_key`` and ``compare`` are ``False``.

    Parameters
    ----------
    dto: bool, default = True
        Whether the column should be included in the data transfer object.

    Returns
    -------
    MappedColumn[Any]
        The ``MappedColumn``.
    """
    return base_mapped_column(
        *args, compare=False, dto=dto, natural_key=False, **kwargs
    )


def default_metadata() -> MetaData:
    """A default ``MetaData`` instance that defines some useful ``naming_conventions``."""
    return MetaData(
        naming_convention={
            "pk": "pk_%(table_name)s",
            "ix": "ix_%(table_name)s_%(column_0_N_name)s",
            "uq": "uq_%(table_name)s_%(column_0_N_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_N_name)s_R_%(referred_table_name)s",
        }
    )


def add_natural_key_index(model_cls: Type[BaseModel]):
    """Add an index to this model's table using the natural key columns."""

    tablename = model_cls.__tablename__

    if tablename is None:
        log.debug(
            f"Can't add a natural key to model class '{model_cls}' without a "
            f"tablename. This can happen for subclasses in a single table "
            f"inheritance hierarchy."
        )
        return

    index_name = f"nk_{tablename}"
    columns = [p.columns[0] for p in model_cls.natural_key_columns()]

    index = Index(index_name, unique=model_cls.unique_natural_key, *columns)
    table = cast(Table, model_cls.__table__)
    table.indexes.add(index)


# Note, you can't use 'once' here, because it will literally only run the
# listener once, not once per mapper, which is required.
@event.listens_for(Mapper, "mapper_configured")
def handle_after_mapper_configured(mapper: Mapper, cls: Type):
    """Validate the configuration and create an index on the natural key."""

    # Only execute this handler if the event was triggered by a ``BaseModel``
    if issubclass(cls, BaseModel):
        # To facilitate testing the validation code, a Mapper or Table can
        # include a "validate=False" entry in the 'info' dictionary to
        # exclude it from being validated by this event handler.
        info = cls.__table__.info  # type: ignore
        should_validate = isinstance(info, dict) and info.get("validate", True)

        if should_validate:
            cls.validate()
            add_natural_key_index(cls)


class ModelProtocol(Protocol): ...


@dataclass_transform(kw_only_default=True, eq_default=True)
class BaseModel(
    DeclarativeBase,
    MappedAsDataclass,
    kw_only=True,
    eq=True,
    unsafe_hash=True,
):
    """A base class for creating declarative SqlAlchemy models.

    Features
    --------
    Table Lookup
    ~~~~~~~~~~~~
    Find any model derived from this base class by their table name.

    Merging Table Args
    ~~~~~~~~~~~~~~~~~~
    SqlAlchemy does not merge ``__table_args__`` during inheritance. For
    example, if you have a base class that will set the schema for all
    child classes, it will not work if the child class defines its own
    ``__table_args__`` (e.g., to create a multi-column index). This base
    class provides a function to merge the ``__table_args__`` of parents
    with their children.

    This functionality is enabled by defining ``__table_args__`` as a
    ``@declared_attr.directive`` on the class and returning the value of
    :meth:`merge_table_args`. ``merge_table_args`` accepts one optional
    parameter, which can be a tuple or dictionary (the expected types of
    ``__table_args__``) and will merge these with the table args of its
    ancestors. In addition to, or alternatively, the ``merge_table_args``
    method will also look for table arguments in a class attribute named
    ``__custom_table_args__``.

    >>> class Parent(BaseModel):
    >>>     @orm.declared_attr.directive
    >>>     @classmethod
    >>>     def __table_args__(cls):
    >>>         return {"schema": "my_schema"}
    >>>
    >>> class Child(Parent):
    >>>     __custom_table_args__ = {"schema": "my_schema"}
    >>>
    >>>     @orm.declared_attr.directive
    >>>     @classmethod
    >>>     def __table_args__(cls):
    >>>         child_table_args = (
    >>>             Index("child_index_name", "column_1", "column_2"),
    >>>         )
    >>>         return cls.merge_table_args(child_table_args)
    >>>
    >>>     column_1: orm.Mapped[int]
    >>>     column_2: orm.Mapped[int]

    Natural Keys
    ~~~~~~~~~~~~
    Classes derived from this model must define a natural key.
    Natural keys are specified by explicitly setting ``hash=True`` on a
    ``mapped_column``.  A natural key is intended to
    identify a set of attributes that uniquely identify a row in the table.
    The key will be used to define ``__hash__`` and ``__eq__`` for the class.
    Additionally, a non-unique index will be created on the natural key columns.

    Serializable to a Dictionary
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    There is currently a bug representing models using ``dataclasses.asdict``
    when the model inherits from ``MappedAsDataclass`` and contains a
    relationship with ``back_populate`` defined.

    See: https://github.com/sqlalchemy/sqlalchemy/issues/9785

    This class provides methods for converting the model to and from
    dictionaries. This has been tested for several common use cases, but
    may not be robust for more complex models.

    Data Transfer Objects
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Any class derived from this base class can build a corresponding DTO
    class type using the :meth:`to_dto_class` method. The created DTO class
    derives from ``pydantic.BaseModel``, which is convenient for offline use
    and data transfers, for example with FastAPI.

    In addition to mirroring the columns, composites, hybrid_properties, and
    relationships, the DTO object also provides a ``pretty_print`` method to
    format the string representation of the object. It takes one optional
    parameter ``line_length``.

    A DTO instance can be constructed from a :class:``BaseModel`` instance
    using either the `model_validate` classmethod method on the DTO or
    from the :meth:`to_dto` method of the ``BaseModel`` instance.

    To exclude an attribute (column, composite, hybrid, relationship, etc.)
    add ``dto=False` to the ``info`` dictionary of the attribute.

    Known Limitations
    -----------------
    * Many-to-Many relationships are basically not supported at all.
    * A composite column must be a dataclass.
    * Only regular columns (e.g., no composite columns) can be used as natural
      keys.
    * Only the parent side of a relationship is added to the DTO. Namely, a
      reference to the child and children will be included in the parent, but
      a reference to the parent will not be included in the child or children.
      The parent is determined by the presence of foreign keys. For 1t1 and 1tM
      relationships the parent is the model that does not contain a foreign
      key. For MtM relationships the parent is determined by looking at the
      first column of the association table. If all the foreign keys of
      that column are in the relationship's local columns then that model
      is considered the parent. This may cause problems if you directly select
      the child objects, because their parents will not be loaded into the
      DTO object.
    * In general you cannot convert a model to a dictionary or DTO and then
      back to the exact same model. The :meth:`from_dict` method does not
      handle cyclic relationships and will typically not be able to associate
      a parent instance from the child.
    * ``to_dict`` only has limited support for one-to-many/many-to-one
      relationships. When converting to a dict, the relationship collection
      will always be a ``list`` regardless of the ``collection_class``
      attribute. Furthermore, the collection will not be sorted according to
      the ``comparator_factory`` even if one is specified.
    * ``to_dict`` and ``from_dict`` currently only consider mapped properties.
      `Unmapped attributes <https://docs.sqlalchemy.org/en/20/orm/dataclasses.html#using-non-mapped-dataclass-fields>`__
      are not included in the dictionary representation.
    """

    # Note: In general SqlAlchemy collections like '__table__.columns' are
    # usually more like 'Mapping' or 'dict' like objects. However, when
    # iterated over, they iterate over the **values** not the keys. This is
    # why my previous code tended to work, but the linter would complain.
    __abstract__ = True

    # metadata: MetaData = MetaData(  # noqa SqlAlchemy  # type: ignore
    #     naming_convention={
    #         "pk": "pk_%(table_name)s",
    #         "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    #         "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    #         "ck": "ck_%(table_name)s_%(constraint_name)s",
    #         "fk": "fk_%(table_name)s_%(column_0_N_name)s_R_%(referred_table_name)s",
    #     }
    # )

    unique_natural_key: ClassVar[bool] = False
    """Subclasses can set this variable to make the index on the natural key to be unique or not."""

    _registered_dto_classes = dict()
    """A dictionary of all DTO classes that have been registered.

    A DTO is registered any time :meth:`to_dto_class` is called, which may
    recursively call :meth:`to_dto_class` for any relationships.
    """

    _column_to_attribute_name_lookup: ClassVar[Optional[dict[str, str]]] = None

    @declared_attr.directive
    def __tablename__(cls):
        return camel_to_snake_case(cls.__name__)

    @classmethod
    def merge_table_args(cls, new_args: TableArgs = ()) -> TableArgs:
        """
        This method is intended to be called from ``__table_args__`` when used
        as a ``@declared_attr``. It will merge the ``new_args`` with the
        arguments of its ancestors. You can also specify additional table
        arguments in the class variable ``__custom_table_args__``, which will
        also be merged.

        Parameters
        ----------
        new_args : TableArgs
            Additional table arguments to be merged with the arguments of our ancestors.

        Returns
        -------
        TableArgs
            The merged table arguments as a tuple. The first ``N`` arguments
            of the tuple contain positional arguments passed to the constructor
            of :class:`sa.Table``. If the last element is a dictionary, then it
            is the keyword arguments passed to the ``Table`` constructor,
            otherwise it is the final positional argument.

        Examples
        --------
        >>> class Parent(BaseModel):
        >>>     @declared_attr.directive
        >>>     @classmethod
        >>>     def __table_args__(cls):
        >>>         return {"schema": "my_schema"}
        >>>
        >>> class Child(Parent):
        >>>     __custom_table_args__ = {"schema": "my_schema"}
        >>>
        >>>     @declared_attr.directive
        >>>     @classmethod
        >>>     def __table_args__(cls):
        >>>         child_table_args = (
        >>>             Index("child_index_name", "column_1", "column_2"),
        >>>         )
        >>>         return cls.merge_table_args(child_table_args)
        >>>
        >>>     column_1: Mapped[int]
        >>>     column_2: Mapped[int]

        """
        # Adapted from another personal project and from:
        # https://github.com/sqlalchemy/sqlalchemy/discussions/8911#discussioncomment-6763269
        # Get the __table__args from our immediate parents.
        # Each element of the accumulated list could be a dict or a tuple.
        bases = reversed(cls.__bases__)
        accumulated_args = [new_args]
        accumulated_args += [getattr(cls, "__custom_table_args__", ())]

        # Process the base classes in reverse order so that args are prioritized
        # from left (least priority) to right (highest priority).
        # Note, this will recurse if a base class calls 'merge_table_args'
        # in their '__table_args__' definition.
        accumulated_args += [getattr(b, "__table_args__", ()) for b in bases]

        # Remove empty arguments and reverse the order. 'new_args' have the
        # highest priority, then  '__custom_args__', and finally parent
        # '__table_args__'.
        accumulated_args = reversed([a for a in accumulated_args if a])

        # Keep track of positional (tuple) and kwargs (dict) arguments.
        # positional_args: set[Any] = set()
        # @notallshaw-gts suggest using a set for the positional arguments
        # to eliminate duplicates, but it's actually not clear to me what
        # positional arguments could reasonably be duplicates.
        positional_args: set[Any] = set()
        kwargs: dict[str, Any] = dict()

        # The items should be processed from root to leaf in the inheritance
        # hierarchy. Within a class, the '__table_args__' are processed first,
        # then the '__custom_table_args__', and finally the passed in
        # 'new_args'.
        #
        # They are in reverse priority, because items inserted earlier can be
        # overwritten by later entries.
        #
        # The output order will be unpredictable because the order of sets is
        # non-deterministic..
        for current_args in accumulated_args:
            if isinstance(current_args, dict):
                kwargs |= current_args
            elif isinstance(current_args, tuple):
                last_arg = current_args[-1]
                if isinstance(last_arg, dict):
                    kwargs |= last_arg
                    current_args = current_args[:-1]

                positional_args |= set(current_args)
            else:
                ValueError(f"Table args must be a dict or tuple, not '{current_args}'")

        return tuple(positional_args) + (kwargs,)

    @classmethod
    @cache
    @require(lambda table_name: table_name.count(".") < 2)
    def find_by_table_name(cls, table_name: str) -> Optional[Type[BaseModel]]:
        """
        Find a model derived from this class by its table name.

        Parameters
        ----------
        table_name : str
            The name of the table whose model class you want to find.

        Returns
        -------
        Type[FindByNameBase], optional
            Returns the model class if the table is found, otherwise ``None``.
        """
        # See: https://stackoverflow.com/a/68862329
        registry = getattr(cls, "registry")

        try:
            find_schema, find_table_name = table_name.split(".", 1)
        except ValueError:
            find_schema, find_table_name = "public", table_name

        for mapper in registry.mappers:
            model = mapper.class_
            table = model.__table__
            candidate_schema = table.schema or "public"
            candidate_table_name = model.__tablename__

            if (
                candidate_schema == find_schema
                and candidate_table_name == find_table_name
            ):
                return model

        return None

    @property
    def primary_key(self) -> tuple[tuple[str, Any], ...]:
        """
        Get the primary key of this instance.

        The ``primary key`` is the set of ``key/value`` pairs corresponding
        to the configured primary key columns. For efficiency reasons, the
        result is returned as a tuple of tuples.
        """
        attribute_names = [c.class_attribute.key for c in self.primary_key_columns()]

        # Sort the names so the order is always predictable and return as a
        # tuple so the result is immutable (i.e., can stored in a set).
        return tuple((n, getattr(self, n, None)) for n in sorted(attribute_names))

    @property
    def natural_key(self) -> tuple[tuple[str, Optional[Any]], ...]:
        """
        Get the natural key of this instance.

        The ``natural key`` is the set of ``key/value`` pairs that uniquely
        identify this instance. The keys are the names of the columns returned
        by :meth:`natural_key_columns` and the values are the current value
        of the instance. For efficiency when used by the hash function the
        pairs are returned as a tuple of tuples.
        """
        attribute_names = [c.class_attribute.key for c in self.natural_key_columns()]

        # Sort the names so the order is always predictable and return as a
        # tuple so the result is immutable (i.e., can stored in a set).
        return tuple((n, getattr(self, n, None)) for n in sorted(attribute_names))

    @require(
        lambda self: all(len(a.columns) == 1 for a in self.__mapper__.column_attrs),
        "One of the mapped columns is a composite column.",
    )
    def as_table_dict(self) -> dict[str, Any]:
        """
        Returns the table data of the instance as a dictionary.

        ..warning::
            This only works for simple models that have a one to one
            mapping from mapped columns to table columns. For example,
            it will break for models containing composite columns.

        Returns
        -------
        dict[str, Any]
            The keys of the dictionary are the table column names and the
            values are the corresponding values from the instance.

        """
        result = {
            a.columns[0].name: getattr(self, a.key, None)
            for a in self.__mapper__.column_attrs  # noqa SqlAlchemy
            if a.columns[0].table is not None  # Only include table columns
        }

        return result

    @classmethod
    def get_attribute_name_from_column_name(cls, column_name: str) -> Optional[str]:
        lookup = cls._get_column_to_attribute_name_lookup()

        # Not raising an exception might hide a subtle error between column
        # and attribute names. However, I need to handle single table
        # inheritance, in which case a subclass could be defined with fewer
        # attributes than columns in the underlying model.
        return lookup.get(column_name)

    @classmethod
    def _get_column_to_attribute_name_lookup(cls) -> dict[str, str]:
        if cls._column_to_attribute_name_lookup is None:
            m = cls.__mapper__
            cls._column_to_attribute_name_lookup = {
                c.name: a.key
                for a in m.attrs
                if hasattr(a, "columns")
                for c in a.columns
            }

        return cls._column_to_attribute_name_lookup

    def to_dict(
        self,
        exclude_attributes: Iterable[str] = (),
        drop_none: bool = False,
    ):
        if any(k in exclude_attributes for k in self.natural_key_attribute_names()):
            raise ValueError("Natural key attributes cannot be excluded.")

        exclude_attributes = set(exclude_attributes) | {"metadata"}

        result = self._do_to_dict(exclude_attributes, seen=set())

        return remove_none_from_dict(result) if drop_none else result

    @classmethod
    def from_dict(cls: Type[Self], data: dict) -> Self:
        """
        Creates an instance of the class from a dictionary representation of the data,
        allowing for nested structures and relationships between models. This method
        also ensures that instances with shared natural keys are not duplicated.

        Parameters
        ----------
        data : dict
            A dictionary containing the attributes and nested relationships of the
            model. The keys should correspond to the field names of the model, and
            values should represent their corresponding data. For nested relationships,
            values are also expected to be dictionaries (for single relationships)
            or lists of dictionaries (for collections).

        Returns
        -------
        BaseModel
            An instance of the BaseModel subclass created from the dictionary input.
        """
        return cast(Self, cls._do_from_dict(data, {}))

    @classmethod
    def dto_module(cls) -> ModuleType:
        """Get the module where the DTO class is defined."""
        return importlib.import_module(cls.__module__)

    @classmethod
    def dto_module_name(cls) -> str:
        """Get the name of the module where the DTO class is defined."""
        return f"{cls.__module__}"

    @classmethod
    def dto_class_name(cls) -> str:
        """Get the name of the DTO class."""
        return f"{cls.__name__}Dto"

    @classmethod
    def dto_import_path(cls) -> str:
        """Get the import path of the DTO class."""
        return f"{cls.dto_module_name()}.{cls.dto_class_name()}"

    @classmethod
    def dto_exclude_attributes(cls) -> set[str]:
        """A set of attribute names to exclude from the DTO representation."""
        attrs = cls.__mapper__.all_orm_descriptors

        def _exclude(name: str) -> bool:
            attr = attrs.get(name)
            info = getattr(attr, "info", {})

            return any(info.get(key) is False for key in ("dto", "DTO"))

        return {n for n in cls.fields() if _exclude(n)}

    @classmethod
    @cache
    def to_dto_class(cls) -> Type[pydantic.BaseModel]:
        """
        Create a Data Transfer Object (DTO) class that corresponds with this model.

        The DTO class will have the same name as the model class but end
        with the prefix ``Dto``. So, if the model name is ``MyModel`` the DTO
        class will be named ``MyModelDto``.

        The DTO class inherits from the ``pydantic.BaseModel`` class and
        contains fields for all regular, composites, hybrid properties, and
        relationships of this model.

        ..note::
            Regardless of how the SqlAlchemy model class is configured,
            all primary and foreign key columns are treated as optional
            and included in the ``__init__`` method with a default value of
            ``None``. The same applies to database generated integer columns.

        ..note::
            To exclude an attribute from the DTO, set ``dto=False`` in the
            ``info`` dictionary of the attribute when defining the model.

        Returns
        -------
        Type[pydantic.BaseModel]
            The DTO type.
        """
        # In order to build the DTO, all models referenced in
        # relationships must also be available as DTOs. It is hard (maybe not
        # possible) to do this recursively. Instead, we'll use a queue of
        # unprocessed models (seeded with this one) and add the relationship
        # classes to the queue as we build. Once all referenced models have
        # corresponding DTOs we can rebuild our top level DTO to resolve the
        # forward references.
        # Pydantic appears to require each segment of a module path (i.e., each
        # package in the hierarchy) to be available in a namespace it searches.
        # However, adding the module or package into the global namespace
        # does not appear to work. As a workaround adding the values into a
        # custom namespace `types_namespace`, which can be passed to
        # `model_rebuild` does work.
        # Keeps track of the packages and modules pydantic needs to initialize
        # our DTO classes, but are not available globally.
        types_namespace = {}

        # The DTO of this class that we'll return.
        dto: Type[pydantic.BaseModel] | None = None

        # The queue of unprocessed models.
        queue: deque[Type[BaseModel]] = deque([cls])

        while len(queue) > 0:
            model = queue.pop()

            types_namespace |= import_all_modules_in_path(model.dto_module_name())
            result = model._do_dto_conversion(children := set())
            queue.extend([c for c in children if c not in cls._registered_dto_classes])

            # The first DTO is the one we want to return.
            # It would be more efficient to process this outside the loop, but
            # this is hardly a hot path and would be less readable and
            # maintainable.
            dto = dto or result

        # After creating the all the referenced DTOs we need to rebuild the
        # pydantic model to resolve the forward references.
        if dto is None:
            raise ValueError("There was an error creating the DTO")

        dto.model_rebuild(_types_namespace=types_namespace)

        return dto

    def to_dto(self) -> Any:
        """
        Convert this model to a DTO instance.

        Returns
        -------
        Any
            The equivalent DTO instance. The actual return type will be an
            instance of ``pydantic.BaseModel` with the non-excluded attributes
            of the corresponding model class. However, typing the dynamically
            created DTO instance is difficult and I haven't found a good way
            to do it yet. Setting the return type to ``pydantic.BaseModel``
            will cause the type checker to complain on all the attributes
            defined in the class, because they are only available at runtime.
            Setting it to ``Any`` will supress these errors, but also disables
            basically all auto-completion.

        Raises
        ------
        pydantic.ValidationError
            If any of the required fields are not present. **Note**: this
            includes database generated fields, such as ``ids``.

        """
        return self.to_dto_class().model_validate(self)

    @classmethod
    def from_dto(cls: Type[Self], dto: pydantic.BaseModel) -> Self:
        """Create a model instance from a DTO instance.

        .. warning::
            This is broken and does not work.

        Parameters
        ----------
        cls : Type[Self]
            _description_
        dto : pydantic.BaseModel
            _description_

        Returns
        -------
        Self
            _description_
        """
        return cls.from_dict(dto.model_dump())

    def walk_children(
        self,
        callback: Callable[[BaseModel], None],
        traverse_viewonly: bool = True,
    ):
        """
        A method to traverse the relationships of a given instance and apply a
        callback to each node in the traversal.

        Parameters
        ----------
        callback : Callable[[DeclarativeBase], None]
            The function to call on each traversed node.
        traverse_viewonly: bool, default=True
            Whether to traverse viewonly relationships.
        """
        queue: deque[BaseModel] = deque([self])
        seen: set[BaseModel] = set()

        def _should_traverse(relationship_, related_) -> bool:
            """Return True if we should traverse the relationship."""
            if related_ is None:
                return False
            elif relationship_.viewonly and not traverse_viewonly:
                return False

            return True

        while queue:
            current = queue.pop()

            # Prevent cycles
            if current in seen:
                continue

            seen.add(current)

            # Apply the callback to the current node
            callback(current)

            # Enqueue all related nodes for traversal
            for relationship in current.relationships():
                related = getattr(current, relationship.key)

                if _should_traverse(relationship, related):
                    related = [related] if not relationship.uselist else related
                    queue.extend(related)

    def copy(self) -> Self:
        """
        Return a deep copy of the instance that is not associated in any
        way with this instance. For example, the new instance is not added
        to a session when the original item is (which appears to happen if
        you use ``copy.deepcopy`` or ``dataclasses.replace``.

        Returns
        -------
        BaseModel
            A copy of this instance.

        """
        # Note, both copy.deepcopy(self) and dataclasses.replace(self) copy
        # SqlAlchemy metadata that cause unexpected behavior.
        return self.from_dict(copy.deepcopy(self.to_dict()))

    @classmethod
    @cache
    def class_name(cls) -> str:
        """Get the name of the class including the package and module prefix."""
        return get_qualified_name(cls)

    @classmethod
    @cache
    def fields(cls: Type[Self]) -> dict[str, Field]:
        """
        Return a mapping of the field names to their corresponding ``Field``
        objects. Note, the dictionary is ordered by the field name.
        """
        sorted_fields = sorted(dataclasses.fields(cls), key=lambda f: f.name)
        return {f.name: f for f in sorted_fields}

    @classmethod
    def get_field_and_column_pairs(
        cls, column_attributes: list[MapperProperty]
    ) -> list[tuple[Field, MapperProperty]]:
        fields = cls.fields()
        pairs = [(fields.get(a.class_attribute.key), a) for a in column_attributes]

        return [(f, a) for f, a in pairs if f is not None]

    @classmethod
    def get_field_and_relationship_pairs(
        cls, relationships: list[RelationshipProperty]
    ) -> list[tuple[Field, RelationshipProperty]]:
        fields = cls.fields()
        pairs = [(fields.get(r.key), r) for r in relationships]

        return [(f, r) for f, r in pairs if f is not None]

    @classmethod
    @cache
    def primary_key_columns(cls) -> list[MapperProperty]:
        """
        Return the list of primary key columns of this class sorted by their ``key``.
        """
        attrs = cls.regular_columns()
        columns = [a for a in attrs if any(c.primary_key for c in a.columns)]

        return list(sorted(columns, key=lambda c: c.key))

    @classmethod
    @cache
    def primary_key_attribute_names(cls) -> set[str]:
        """
        Returns the set of class attribute names corresponding to the primary key
        columns.
        """
        return {c.class_attribute.key for c in cls.primary_key_columns()}

    @classmethod
    @cache
    def primary_key_column_names(cls) -> set[str]:
        return {c.key for c in cls.primary_key_columns()}

    @classmethod
    @cache
    def natural_key_columns(cls) -> list[ColumnProperty]:
        """Return the list of natural key columns of this class."""
        attrs = cast(list[ColumnProperty], cls.regular_columns())

        return [a for a in attrs if a.class_attribute.info.get("nk") is True]

    @classmethod
    @cache
    def natural_key_attribute_names(cls) -> set[str]:
        """
        Returns the set of class attribute names corresponding to the natural key
        columns.

        Returns
        -------
        set[str]
            The set of attribute names.
        """
        return {c.class_attribute.key for c in cls.natural_key_columns()}

    @classmethod
    @cache
    def natural_key_column_names(cls) -> set[str]:
        return {c.key for c in cls.natural_key_columns()}

    # It's less efficient, but we need to iterate through all the fields below
    # because the `mapper.attrs` collections map from **column** names, not
    # attribute names.
    @classmethod
    @cache
    def regular_columns(cls: Type[Self]) -> list[MapperProperty]:
        """
        Return a mapping from an attribute name to its ``ColumnProperty``
        instance for all regular columns of this class. A regular column is a
        column listed in ``Mapper.column_attrs`` and maps to only one column that
        is an instance of :class:`sa.Column`.
        """
        attrs = cls.__mapper__.column_attrs
        return [a for a in attrs if cls._is_regular_column(a)]

    @classmethod
    @cache
    def _is_regular_column(cls, attr: MapperProperty) -> bool:
        if not isinstance(attr, ColumnProperty):
            return False

        if attr.key in cls._composite_table_column_names():
            return False

        columns = attr.columns
        return len(columns) == 1 and all(isinstance(c, sa.Column) for c in columns)

    @classmethod
    @cache
    def column_properties(cls: Type[Self]) -> list[MapperProperty]:
        attrs = cls.__mapper__.column_attrs

        return [a for a in attrs if cls._is_column_property(a)]

    @classmethod
    @cache
    def _is_column_property(cls, attr: MapperProperty) -> bool:
        return isinstance(attr, MappedSQLExpression)

    @classmethod
    @cache
    def composite_columns(cls: Type[Self]) -> list[MapperProperty]:
        """
        Return a mapping from an attribute name to its ``CompositeProperty``
        instance for all ``composite`` attributes of this class. A ``composite``
        attribute is an attribute configured using ``sa.composite``.
        """
        attrs = cls.__mapper__.attrs
        return [a for a in attrs if cls._is_composite(a)]

    @classmethod
    @cache
    def _is_composite(cls, attr: InspectionAttr) -> bool:
        return isinstance(attr, CompositeProperty)

    @classmethod
    @cache
    def _composite_table_column_names(cls) -> set[str]:
        composites = cls.composite_columns()

        return {col.key for composite in composites for col in composite.columns}

    @classmethod
    @cache
    def hybrid_properties(cls: Type[Self]) -> list[hybrid_property]:
        """
        Returns a mapping from an attribute name to a ``hybrid_property``
        instance. A ``hybrid_property`` attribute is a getter style method
        annotated with the ``@hybrid_property`` decorator.
        """
        attrs = cls.__mapper__.all_orm_descriptors
        return [a for a in attrs if cls._is_hybrid_property(a)]

    @classmethod
    @cache
    def _is_hybrid_property(
        cls, attr: Optional[MapperProperty]
    ) -> TypeGuard[hybrid_property]:
        return (
            attr is not None and attr.extension_type is hybrid_property.extension_type
        )

    @classmethod
    @cache
    def relationships(cls) -> list[RelationshipProperty]:
        """
        Returns a mapping from an attribute name to a ``Relationship`` for
        all relationships defined on this class.
        """
        return list(cls.__mapper__.relationships.values())

    @classmethod
    @cache
    def _is_relationship(
        cls, attr: Optional[MapperProperty]
    ) -> TypeGuard[Relationship]:
        return attr is not None and isinstance(attr, Relationship)

    @classmethod
    @cache
    def table_columns(cls) -> list[ColumnElement]:
        """Get a list of the table column names for this model."""

        return [c for c in cls.__table__.columns.values()]

    @classmethod
    @cache
    @ensure(lambda result: result is not None)
    def table_insertion_order(cls) -> dict[sa.Table, int]:
        """
        The insertion priority for each table. A lower number has a higher
        priority and should be inserted before a table with a higher number.
        The priorities are determined using a topological sort of the
        dependency tree created by the relationships between models.

        Returns
        -------
        dict[Table, int]
            A mapping from an SqlAlchemy table to its insertion priority (lower
            numbers indicate higher priority).
        """
        return {t: i for i, t in enumerate(cls.metadata.sorted_tables)}

    @classmethod
    def validate(cls):
        cls.validate_natural_keys()
        cls.validate_dto_configuration()

    @classmethod
    def validate_natural_keys(cls):
        model_name = cls.__name__
        attrs = cls.natural_key_columns()

        def _is_abstract(model_cls: Type[BaseModel]) -> bool:
            return model_cls.__abstract__ and not model_cls.__tablename__

        if not _is_abstract(cls) and len(attrs) == 0:
            raise ValueError(f"'{model_name}' has no natural key columns.")

        cols = [c for a in attrs for c in a.columns]
        if any(c.nullable for c in cols):
            raise ValueError("Natural keys cannot be optional")

    @classmethod
    def validate_dto_configuration(cls):
        dto_excludes = cls.dto_exclude_attributes()
        fields = cls.fields().values()
        excluded_fields = {f for f in fields if f.name in dto_excludes}
        natural_key = [k for k in cls.natural_key_attribute_names()]

        def _is_required(type_: Any) -> bool:
            return not is_optional(type_)

        def _has_any_default(field: Field) -> bool:
            default_missing = field.default == dataclasses.MISSING
            factory_missing = field.default_factory == dataclasses.MISSING

            return not (default_missing and factory_missing)

        def _has_value_default(field: Field) -> bool:
            missing = dataclasses.MISSING
            default_value = field.default
            factory_value = field.default_factory
            has_default = default_value is not missing and default_value is not None
            has_factory = factory_value is not missing and factory_value is not None

            return has_default or has_factory

        for field in excluded_fields:
            # A field can be excluded if:
            #   * It is optional, and default or default_factory is not missing,
            #     or init is False.
            #   * It is not optional, and  `default` or default_factory is not
            #     missing.
            if field.name in natural_key:
                raise ValueError("A DTO cannot exclude a natural key column.")

            # Assume, 'field.type' is an actual type and not a forward
            # declared string. Note, this might be problematic.
            if _is_required(field.type) and not _has_value_default(field):
                raise ValueError(
                    "A DTO cannot exclude a required field that does not provide "
                    "a non-None default or default_factory value."
                )

            if is_optional(field.type):
                if _has_any_default(field):
                    continue
                elif field.init is False:
                    continue
                else:
                    raise ValueError(
                        "A DTO cannot exclude an optional field unless it is "
                        "excluded from the 'init' method or has a default value or "
                        "default_factory (even if it is None)."
                    )

    # region Utility Methods
    # region to_dict Utility Methods
    def _do_to_dict(
        self,
        exclude_attributes: set[str],
        seen: set[BaseModel],
    ) -> dict[str, Any]:
        """Covert the instance to a dictionary.

        This method represents the model as a dictionary as it is defined
        by the class mapping (as opposed to the table mapping).

        .. note::
            As of 01/01/2025 calling `dataclasses.asdict` will raise a
            recursion error on models that have relationships with
            `back_populate` defined.

        .. note::
            ``exclude_attributes`` does a simple string match on any attribute
            name in the model and any of its children.

            See: https://github.com/sqlalchemy/sqlalchemy/issues/9785

        .. note::
            The collection class for all relationships (that use them) will
            be converted to a list in the dictionary representation.

        Parameters
        ----------
        exclude_attributes : Iterable[str], default = ()
            A list of attribute names that should be excluded in the converted
            dictionary.
        drop_none : bool, default = False
            Don't include attributes whose value are ``None`` in the dictionary.
        sort_relationships : bool, default = False
            By default the order of items in a one-to-many relationship is
            undefined and appears to be non-deterministic. This is not a
            problem in general, but makes testing difficult. Set this parameter
            to ``True`` to sort by the string representation of the related
            object. This does not guarantee a deterministic order in all
            cases, but can make it easier to do so.

        Returns
        -------
        dict[str, Any]
            A dictionary representation of this object.
        """
        # TODO I might want to wrap the model in a class that only uses the
        #      natural key for hashing and equality for the seen items.
        if self in seen:
            result = self._to_dict_process_seen()

            return {k: v for k, v in result.items() if k not in exclude_attributes}

        seen.add(self)

        result: dict[str, Any] = {}

        fields = self.fields()
        orm_descriptors = self.__mapper__.all_orm_descriptors
        valid_attribute_names = [n for n in fields if n not in exclude_attributes]

        process_composite = self._to_dict_process_composite
        process_hybrid = self._to_dict_process_hybrid
        process_relationship = self._to_dict_process_relationship
        process_common_attribute = self._to_dict_process_common_attribute

        for attribute_name in valid_attribute_names:
            # Apparently all_orm_descriptors sometimes/always returns a proxy
            # object.
            proxy = orm_descriptors.get(attribute_name)

            # The code below is designed to work with the actual MapperProperty
            # or InspectionAttr object. So, we try to extract it from the
            # proxy.
            attribute = None if proxy is None else getattr(proxy, "property", proxy)

            if self._is_composite(attribute):
                value = process_composite(attribute_name)
            elif self._is_relationship(attribute):
                value = process_relationship(attribute, exclude_attributes, seen)
            else:
                value = process_common_attribute(attribute_name)

            result[attribute_name] = value

        # Process hybrids separately.
        hybrids = self.hybrid_properties()
        hybrids = [h for h in hybrids if h.__name__ not in exclude_attributes]
        for hybrid in hybrids:
            result[hybrid.__name__] = process_hybrid(hybrid)

        return result

    def _to_dict_process_seen(self) -> dict[str, Any]:
        return dict(self.primary_key) | dict(self.natural_key)

    def _to_dict_process_composite(
        self, attribute_name: str
    ) -> Optional[dict[str, Any]]:
        value = getattr(self, attribute_name, None)
        return None if value is None else dataclasses.asdict(value)

    def _to_dict_process_hybrid(self, hybrid: hybrid_property) -> Optional[Any]:
        return hybrid.fget(self)

    def _to_dict_process_relationship(
        self,
        relationship: Relationship,
        exclude_attributes: Iterable[str],
        seen: set[BaseModel],
    ) -> list[dict[str, Any]] | dict[str, Any] | None:
        value = getattr(self, relationship.key, None)

        if value is None:
            return None

        if relationship.uselist:
            return [e._do_to_dict(exclude_attributes, seen) for e in value]
        else:
            return value._do_to_dict(exclude_attributes, seen)

    def _to_dict_process_common_attribute(self, attribute_name: str) -> Any:
        return getattr(self, attribute_name, None)

    # endregion to_dict Utility Methods
    # region from_dict Utility Methods
    @classmethod
    def _do_from_dict(
        cls: Type[Self],
        data: dict[str, Any],
        seen: dict[frozenset[tuple[str, Any]], BaseModel],
    ) -> BaseModel:
        # Create aliases for our utility functions here to help with
        # readability, because the full names are long and unwieldy.
        make_hash_key = cls._from_dict_hash_key
        get_regular_columns_kwargs = cls._from_dict_get_regular_columns_kwargs
        get_composite_columns_kwargs = cls._from_dict_get_composite_columns_kwargs
        get_relationship_kwargs = cls._from_dict_get_relationship_kwargs
        update_regular_columns = cls._from_dict_update_regular_columns
        update_column_properties = cls._from_dict_update_column_properties
        update_composite_columns = cls._from_dict_update_composite_columns
        update_relationships = cls._from_dict_update_relationships

        # Use the 'seen' items to prevent recursion.
        hash_key = make_hash_key(data)
        if hash_key in seen:
            return seen[hash_key]

        # We construct the instance in two phases.
        # First, we build the keyword arguments for the constructor, which
        # may not include all available data depending on the value of 'init'
        # when the field was defined. Once built, we construct an instance
        # (and add it to the 'seen' items).
        # Second, we populate any other fields that we have data for and
        # 'init' was set to 'False'.
        init_kwargs = {}

        # Phase 1
        init_kwargs |= get_regular_columns_kwargs(data)
        init_kwargs |= get_composite_columns_kwargs(data)
        init_kwargs |= get_relationship_kwargs()

        # We should have all the info we need to construct an instance.
        # However, there may still be attributes not included in the __init__
        # (e.g., autogenerated IDs) that need to be set below.
        seen[hash_key] = instance = cls(**init_kwargs)

        # Phase 2
        update_regular_columns(instance, data)
        update_column_properties(instance, data)
        update_composite_columns(instance, data)
        update_relationships(instance, data, seen)

        return instance

    @classmethod
    def _from_dict_hash_key(cls, data: dict[str, Any]) -> frozenset[tuple[str, Any]]:
        key = [("__class__", get_qualified_name(cls))]
        key += [(n, data[n]) for n in cls.natural_key_attribute_names()]

        return frozenset(key)

    @classmethod
    def _from_dict_get_regular_columns_kwargs(
        cls, data: dict[str, Any]
    ) -> dict[str, Any]:
        # Get the __init__ kwargs related to the regular columns
        pairs = cls.get_field_and_column_pairs(cls.regular_columns())
        pairs = [(f, a) for f, a in pairs if f.init is not False]

        kwargs: dict[str, Any] = {}

        for field, _ in pairs:
            # We want to distinguish between a value explicitly set to
            # `None` and a missing value. Missing values should use their
            # corresponding `default` or `default_factory` during
            # construction, while an explicit `None` should be preserved.
            attribute_name = field.name
            try:
                kwargs[attribute_name] = copy.deepcopy(data[attribute_name])
            except KeyError:
                pass

        return kwargs

    @classmethod
    def _from_dict_get_composite_columns_kwargs(
        cls, data: dict[str, Any]
    ) -> dict[str, Any]:
        # Get the __init__ kwargs related to the composite columns
        pairs = cls.get_field_and_column_pairs(cls.composite_columns())
        pairs = [(f, a) for f, a in pairs if f.init is not False]

        kwargs: dict[str, Any] = {}

        for field, composite in pairs:
            try:
                composite_kwargs = copy.deepcopy(data[field.name])
                composite_class = composite.composite_class
                kwargs[field.name] = composite_class(**composite_kwargs)
            except KeyError:
                pass

        return kwargs

    @classmethod
    def _from_dict_get_relationship_kwargs(cls):
        # Get the __init__ kwargs related to the relationships
        pairs = cls.get_field_and_relationship_pairs(cls.relationships())
        pairs = [(f, a) for f, a in pairs if f.init is not False]

        kwargs: dict[str, Any] = {}

        def _has_default(f: Field) -> bool:
            return f.default is not None and f.default is not MISSING

        def _has_default_factory(f: Field) -> bool:
            return f.default_factory is not None and f.default_factory is not MISSING

        for field, relationship in pairs:
            if _has_default(field):
                default_value = field.default
            elif _has_default_factory(field):
                # Pylance can't determine that field.default_factory is not
                # missing despite the conditional check above, so we cast
                # it to avoid the warning.
                default_factory = cast(Callable, field.default_factory)
                default_value = default_factory()
            else:
                default_value = None
            kwargs[field.name] = default_value

        return kwargs

    @classmethod
    def _from_dict_update_regular_columns(cls, obj: BaseModel, data: dict[str, Any]):
        pairs = cls.get_field_and_column_pairs(cls.regular_columns())
        pairs = [(f, a) for f, a in pairs if f.init is False]

        for f, a in pairs:
            try:
                setattr(obj, f.name, copy.deepcopy(data[f.name]))
            except KeyError:
                pass

    @classmethod
    def _from_dict_update_column_properties(cls, obj: BaseModel, data: dict[str, Any]):
        # Column properties are not evaluated until the model is queried
        # or associated with a session, so they will be `None` if we don't
        # set them here.
        pairs = cls.get_field_and_column_pairs(cls.column_properties())
        pairs = [(f, a) for f, a in pairs if f.init is False]

        for f, a in pairs:
            try:
                setattr(obj, f.name, copy.deepcopy(data[f.name]))
            except KeyError:
                pass

    @classmethod
    def _from_dict_update_composite_columns(cls, obj: BaseModel, data: dict[str, Any]):
        pairs = cls.get_field_and_column_pairs(cls.composite_columns())
        pairs = [(f, a) for f, a in pairs if f.init is False]

        for f, a in pairs:
            try:
                composite_kwargs = copy.deepcopy(data[f.name])
                composite_class = a.composite_class
                composite_instance = composite_class(**composite_kwargs)
                setattr(obj, f.name, composite_instance)
            except KeyError:
                pass

    @classmethod
    def _from_dict_update_relationships(
        cls,
        obj: BaseModel,
        data: dict[str, Any],
        seen: dict[frozenset[tuple[str, Any]], BaseModel],
    ):
        pairs = cls.get_field_and_relationship_pairs(cls.relationships())
        pairs = [(f, a) for f, a in pairs]

        # Currently, this does not handle back populating parent relationships.
        # It should be possible, but is not trivial. In addition to keeping
        # track of entities seen by their natural key, you'd also have to
        # keep track of instances by foreign key columns. Then in the
        # 'KeyError' below, you could try to find the entity using the
        # foreign key value from the 'data' dictionary.
        for f, r in pairs:
            name = f.name
            try:
                values = data[name]
            except KeyError:
                pass
            else:
                rel_class = cast(Type[BaseModel], r.mapper.class_)
                if r.uselist:
                    collection_class = r.collection_class or list
                    children = [rel_class._do_from_dict(v, seen) for v in values]
                    children = collection_class(children)  # type: ignore
                    setattr(obj, name, children)
                else:
                    child = (
                        None
                        if values is None
                        else rel_class._do_from_dict(values, seen)
                    )
                    setattr(obj, name, child)

    # endregion from_dict Utility Methods
    # region to_dto_class Utility Methods
    @classmethod
    def _do_dto_conversion(
        cls: Type[Self],
        forward_declarations: set[Type[BaseModel]],
    ):
        """
        Convert the SqlAlchemy model to a DTO implemented as a
        ``pydantic.BaseModel``.

        ..note::
            This only transforms mapped model attributes. Namely, the columns,
            composites, column properties, hybrid properties, and relationships.
            It will not transform non-mapped attributes, for example, any
            ``ClassVar`` or unmapped attributes.

        Parameters
        ----------
        forward_declarations : set[str]
            A set of fully qualified (import path) class names of SqlAlchemy
            models that are referenced in relationships, but may not be defined
            yet. This set will be populated during the execution of this
            function.

        Returns
        -------
        Type[pydantic.BaseModel]
            The DTO class.
        """
        # TODO It might be better to refactor this so that it processes all
        #      fields of the original model, so that it can handle non-mapped
        #      attributes.
        # Create some function aliases to help readability
        process_regular_columns = cls._to_dto_class_process_regular_columns
        process_column_properties = cls._to_dto_class_process_column_properties
        process_composite_columns = cls._to_dto_class_process_composite_columns
        process_hybrid_properties = cls._to_dto_class_process_hybrid_properties
        process_relationships = cls._to_dto_class_process_relationships
        make_dto_class = cls._to_dto_class_make_dto_class

        # To dynamically create our DTO class/type we need the types of each
        # field, which will populate the `__annotations__`` attribute of the
        # class and we need the attributes of the class. The following
        # dictionary will be used to accumulate the new, transformed,  type and
        # corresponding Field objects for each attribute of the original
        # SqlAlchemy model. The dictionary maps from the attribute name to
        # a pair containing the new DTO type and new DTO Field.
        dto_attributes: dict[str, tuple[Any, Any]] = {}

        # Process each of the attributes we know how to handle.
        dto_attributes |= process_regular_columns()
        dto_attributes |= process_column_properties()
        dto_attributes |= process_composite_columns()
        dto_attributes |= process_hybrid_properties()
        dto_attributes |= process_relationships(forward_declarations)

        dto_class = make_dto_class(dto_attributes)
        dto_class = cast(DtoModelType, dto_class)

        # Register the DTO class with the BaseModel
        cls._registered_dto_classes[cls] = dto_class

        # Add the class to the appropriate module
        setattr(cls.dto_module(), cls.dto_class_name(), dto_class)

        return dto_class

    @classmethod
    def _to_dto_class_is_auto_generated(cls, attr: MapperProperty) -> bool:
        # Check if the attribute represents an auto generated primary key.
        columns = getattr(attr, "columns", [])
        is_int = any(c.type.python_type is int for c in columns)
        is_primary = any(c.primary_key for c in columns)

        try:
            has_default = any(c.default is not None for c in columns)
        except AttributeError:
            has_default = False

        return is_int and is_primary and not has_default

    @classmethod
    def _to_dto_class_is_foreign_key(cls, attr) -> bool:
        return any(bool(c.foreign_keys) for c in getattr(attr, "columns", []))

    @classmethod
    def _is_parent_relationship(cls, rel: RelationshipProperty) -> bool:
        owns_fk = any(c.foreign_keys for c in rel.local_columns)
        is_primary_association = cls._is_primary_association(rel)

        return not owns_fk and is_primary_association

    @classmethod
    def _is_primary_association(cls, rel: RelationshipProperty) -> bool:
        """True if the local column is the first entry in the association table."""
        secondary = rel.secondary

        # This is only applicable to MtM relationships with an
        # association table.
        if secondary is None:
            return True

        local_columns = rel.local_columns
        foreign_keys = secondary.columns[0].foreign_keys

        return all(fk.column in local_columns for fk in foreign_keys)

    @classmethod
    def _to_dto_class_field(
        cls, model_field: Field, model_attr: MapperProperty
    ) -> Optional[Any]:
        field_kwargs = {}

        if model_field.default is not dataclasses.MISSING:
            field_kwargs["default"] = model_field.default
        elif model_field.default_factory is not dataclasses.MISSING:
            field_kwargs["default_factory"] = model_field.default_factory
        elif cls._to_dto_class_is_auto_generated(model_attr):
            field_kwargs["default"] = None
        elif cls._to_dto_class_is_foreign_key(model_attr):
            field_kwargs["default"] = None

        if model_field.repr is not dataclasses.MISSING:
            field_kwargs["repr"] = model_field.repr

        return pydantic.Field(**field_kwargs)

    @classmethod
    def _to_dto_class_type(
        cls, model_field: Field, model_attr: MapperProperty
    ) -> Optional[Any]:
        """Create the pydantic type from the model field information."""
        # The following attribute categories should always be optional in
        # the DTO class:
        #   * autogenerated keys
        #   * foreign keys
        #   * column_property attributes
        #   * hybrid_property attributes
        if cls._to_dto_class_is_auto_generated(model_attr):
            return Optional[model_field.type]

        if cls._to_dto_class_is_foreign_key(model_attr):
            return Optional[model_field.type]

        if cls._is_column_property(model_attr):
            return Optional[model_field.type]

        return model_field.type

    @classmethod
    def _to_dto_class_filter_excluded_columns(
        cls,
        attrs: list[MapperProperty],
    ) -> dict[str, MapperProperty]:
        excluded = cls.dto_exclude_attributes()
        return {n: a for a in attrs if (n := a.class_attribute.key) not in excluded}

    @classmethod
    def _to_dto_class_filter_excluded_relationships(
        cls,
        relationships: list[RelationshipProperty],
    ) -> dict[str, RelationshipProperty]:
        excluded = cls.dto_exclude_attributes()
        return {n: r for r in relationships if (n := r.key) not in excluded}

    @classmethod
    def _to_dto_class_process_regular_columns(cls) -> dict[str, tuple[Any, Any]]:
        return cls._to_dto_class_process_mapper_properties(cls.regular_columns())

    @classmethod
    def _to_dto_class_process_column_properties(cls) -> dict[str, tuple[Any, Any]]:
        return cls._to_dto_class_process_mapper_properties(cls.column_properties())

    @classmethod
    def _to_dto_class_process_composite_columns(cls) -> dict[str, tuple[Any, Any]]:
        return cls._to_dto_class_process_mapper_properties(cls.composite_columns())

    @classmethod
    def _to_dto_class_process_hybrid_properties(cls) -> dict[str, tuple[Any, Any]]:
        excluded_attributes = cls.dto_exclude_attributes()
        hybrids = cls.hybrid_properties()
        hybrids = [h for h in hybrids if h.__name__ not in excluded_attributes]

        result: dict[str, tuple[Any, Any]] = {}
        for hybrid in hybrids:
            inner_type = get_type_hints(hybrid.fget).get("return", None)
            dto_type = Optional[inner_type]
            dto_field = pydantic.Field(init=True, default=None)
            result[hybrid.__name__] = (dto_type, dto_field)

        return result

    @classmethod
    def _to_dto_class_process_relationships(
        cls, forward_declarations: set[Type[BaseModel]]
    ) -> dict[str, tuple[Any, Any]]:
        excluded_attributes = cls.dto_exclude_attributes()
        pairs = cls.get_field_and_relationship_pairs(cls.relationships())
        pairs = [(f, r) for f, r in pairs if f.name not in excluded_attributes]
        pairs = [(f, r) for f, r in pairs if cls._is_parent_relationship(r)]

        result: dict[str, tuple[Any, Any]] = {}
        for field, relationship in pairs:
            dto_field = cls._to_dto_class_field(field, relationship)
            model_type = relationship.entity.class_

            # Add the relationship class to the set of additional classes
            # we may need to process later.
            forward_declarations.add(model_type)

            # We need to use a forward declaration of the relationship
            # DTO type, otherwise we'll run into cyclic recursion issues.
            dto_entity_type = model_type.dto_import_path()
            collection_class = relationship.collection_class

            if relationship.uselist:
                dto_type = collection_class[dto_entity_type]  # type: ignore
            else:
                dto_type = dto_entity_type

            result[field.name] = (dto_type, dto_field)

        return result

    @classmethod
    def _to_dto_class_process_mapper_properties(
        cls,
        attrs: list[MapperProperty],
    ) -> dict[str, tuple[Any, Any]]:
        excluded_attributes = cls.dto_exclude_attributes()
        pairs = cls.get_field_and_column_pairs(attrs)
        pairs = [(f, c) for f, c in pairs if f.name not in excluded_attributes]

        to_type = cls._to_dto_class_type
        to_field = cls._to_dto_class_field

        return {f.name: (to_type(f, c), to_field(f, c)) for f, c in pairs}

    @classmethod
    def _to_dto_class_make_dto_class(cls, attrs: dict[str, tuple[Any, Any]]) -> type:
        excluded_attributes = cls.dto_exclude_attributes()
        attrs = {k: v for k, v in attrs.items() if k not in excluded_attributes}
        dto_types = {k: v[0] for k, v in attrs.items()}
        dto_fields = {k: v[1] for k, v in attrs.items()}

        # These methods will be attached to the DTO class
        def _dto_pretty_print(self, line_length=1):
            # Pretty print the DTO
            # See: https://github.com/pydantic/pydantic/discussions/7787#discussioncomment-9658140
            s = repr(self)

            # 3rd Party Library
            import black

            return black.format_str(s, mode=black.FileMode(line_length=line_length))

        def _dto_natural_keys(self) -> list[str]:
            # Return the list of natural key attribute names
            return [k.class_attribute.key for k in cls.natural_key_columns()]

        # model_config: ConfigDict(from_attributes=True) enables creating a
        # Pydantic BaseModel from a dictionary.
        return type(
            cls.dto_class_name(),
            (pydantic.BaseModel,),
            {
                "__module__": cls.dto_module_name(),
                "__annotations__": dto_types,
                "model_config": pydantic.ConfigDict(from_attributes=True),
                "natural_keys": _dto_natural_keys,
                "pretty_print": _dto_pretty_print,
                **dto_fields,
            },
        )
