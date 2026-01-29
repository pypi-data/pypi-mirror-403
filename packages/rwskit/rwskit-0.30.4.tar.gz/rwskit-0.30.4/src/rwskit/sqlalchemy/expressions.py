"""Classes for declaratively creating SQL expressions."""

# Future Library
from __future__ import annotations

# Standard Library
from typing import Any, Literal, Type, TypeVar

# 3rd Party Library
import sqlalchemy as sa

from icontract import require
from pydantic.dataclasses import dataclass
from sqlalchemy import FromClause
from sqlalchemy.orm import DeclarativeBase

# 1st Party Library
from rwskit.config import YamlConfig

DeclBaseT = TypeVar("DeclBaseT", bound=DeclarativeBase)
"""A type extending :class:`~sqlalchemy.orm.DeclarativeBase`."""

SqlOperator = Literal[
    "==", "!=", ">", ">=", "<", "<=", "like", "in", "not_in", "is_null", "is_not_null"
]
"""The supported SQL operators for use in an :class:`SqlBinaryExpression`."""


@dataclass(frozen=True, kw_only=False)
class SqlBinaryExpression(YamlConfig):
    """A class that represents the basic binary expression for an SQL column."""

    column: str
    """The column name."""

    operator: SqlOperator
    """The operator to compare the ``column`` and ``value`` with."""

    value: Any
    """The value used as a comparison."""

    def __call__(
        self, model_or_table: Type[DeclBaseT] | sa.Table | FromClause
    ) -> sa.BinaryExpression:
        return self.to_expression(model_or_table)

    @require(
        lambda self, model_or_table: (
            self.column in model_or_table.columns
            if isinstance(model_or_table, sa.Table)
            else hasattr(model_or_table, self.column)
        ),
        "Invalid column",
    )
    @require(
        lambda model_or_table: isinstance(model_or_table, sa.Table)
        or issubclass(model_or_table, DeclarativeBase),
        (
            "The 'model_or_table' must either be an SqlAlchemy Table or an SqlAlchemy "
            "ORM model (subclass of DeclarativeBase)."
        ),
    )
    def to_expression(
        self, model_or_table: Type[DeclBaseT] | sa.Table | FromClause
    ) -> sa.BinaryExpression:
        """Return a clause that can be used with an SqlAlchemy ``where`` statement.

        Parameters
        ----------
        model_or_table : sqlalchemy.Table
            The table object that contains the column.

        Returns
        -------
        BinaryExpression
            The corresponding SqlAlchemy binary expression.

        """
        column = (
            model_or_table.c[self.column]
            if isinstance(model_or_table, sa.Table)
            else getattr(model_or_table, self.column)
        )

        handlers = {
            "==": lambda v: column.is_(None) if v is None else column == v,
            "!=": lambda v: column.is_not(None) if v is None else column != v,
            ">": lambda v: column > v,
            ">=": lambda v: column >= v,
            "<": lambda v: column < v,
            "<=": lambda v: column <= v,
            "like": lambda v: column.like(v),
            "in": lambda v: column.in_(v),
            "not_in": lambda v: column.not_in(v),
            "is_null": lambda v: column.is_(None),
            "is_not_null": lambda v: column.isnot(None),
        }

        try:
            return handlers[self.operator](self.value)
        except KeyError:
            raise ValueError(f"Invalid operator: {self.operator}")


@dataclass(kw_only=False, frozen=True)
class SqlSelectionCriteria(YamlConfig):
    """A class that represents a conjunction of SqlBinaryExpression."""

    expressions: list[SqlBinaryExpression]
    """The list of binary expressions that will be used to filter the query."""

    @require(
        lambda model_or_table: isinstance(model_or_table, sa.Table)
        or issubclass(model_or_table, DeclarativeBase),
        (
            "The 'model_or_table' must either be an SqlAlchemy Table or an SqlAlchemy "
            "ORM model (subclass of DeclarativeBase)."
        ),
    )
    def to_conjunction(
        self, model_or_table: Type[DeclBaseT] | sa.Table
    ) -> sa.BinaryExpression | sa.BooleanClauseList | sa.ColumnElement[bool]:
        """
        Return a conjunction of binary expressions that can be used with an
        SqlAlchemy ``where`` statement.

        Returns
        -------
        BinaryExpression | BooleanClauseList
        """
        table = (
            model_or_table
            if isinstance(model_or_table, sa.Table)
            else model_or_table.__table__
        )

        # SqlAlchemy will be deprecating the use of 'and_' and 'or_' with empty
        # argument lists (which will happen if 'self.expressions' is empty).
        # So, when 'self.expressions' is empty, we'll use a dummy 'True' value
        # as the single argument.
        if self.expressions:
            expressions = [e.to_expression(table) for e in self.expressions]
        else:
            expressions = [sa.true()]

        return sa.and_(*expressions)


@dataclass(kw_only=False, frozen=True)
class SqlOrderExpression(YamlConfig):
    """A class that represents a basic order expression for an SQL column."""

    column: str
    """The name of the column to sort by."""

    ascending: bool = True
    """Whether to sort the column in ascending order."""

    def to_expression(
        self, model_or_table: Type[DeclBaseT] | sa.Table
    ) -> sa.UnaryExpression:
        """Convert the order expression to a SqlAlchemy ``UnaryExpression``."""

        column = (
            model_or_table.c[self.column]
            if isinstance(model_or_table, sa.Table)
            else getattr(model_or_table, self.column)
        )

        return column.asc() if self.ascending else column.desc()


@dataclass(kw_only=False, frozen=True)
class SqlOrderCriteria(YamlConfig):
    """A class that represents a list of ``SqlOrderExpressions``."""

    expressions: list[SqlOrderExpression]
    """The list of order expressions."""

    def to_criteria(
        self, model_or_table: Type[DeclBaseT] | sa.Table
    ) -> list[sa.UnaryExpression]:
        """
        Convert the order criteria to a list of SqlAlchemy ``UnaryExpressions``
        that can be used with an SqlAlchemy ``order_by`` statement."""
        return [e.to_expression(model_or_table) for e in self.expressions]
