"""SQLTableInfo class."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import declarative_base
from sqlalchemy.schema import (
    CheckConstraint,
    ForeignKeyConstraint,
    PrimaryKeyConstraint,
    UniqueConstraint,
)

from ..interfaces import sql_metadata
from .sql_column_info import SQLColumnInfo


class InvalidTableError(Exception):
    """Raised when a table is invalid e.g. has no primary key."""


class SQLTableInfo:
    """
    Collection of attributes defining a Table's columns.

    The class contains the column information (`SQLColumnInfo`)
    and additional arguments required to build the sqlalchemy
    table when the `get_table()` method is called.

    This class can provide useful information on the corresponding
    table. For example the primary-key or the list of undeferred
    and deferred columns, i.e. that must be loaded directly or
    looked up in a cache system (if implemented) respectively.
    Note that no cache implementation lies here, only the information
    that some columns must be deferred if possible.

    The `SQLTableInfo` also can manage several tables of the same type
    (e.g. for versioning, table_A_v1 && table_A_v2). When calling
    the `get_table()` method, a custom table name can be given. The
    object will ensure that only one table is created for a given
    name (otherwise `sqlalchemy` cannot work properly).
    """

    table_base_class = declarative_base()

    def __init__(
        self,
        table_name: str,
        metadata: sql_metadata,
        columns: list[SQLColumnInfo],
        constraints: list[
            ForeignKeyConstraint
            | UniqueConstraint
            | CheckConstraint
            | PrimaryKeyConstraint
        ]
        | None = None,
    ) -> None:
        """Initialize the table data and sqlachemy metadata."""
        self.table_name = table_name
        self.metadata = metadata
        self.columns = columns
        self.constraints = constraints if constraints else []
        self._table_instances: dict[str, sa.Table] = {}

    def get_primary_keys(self) -> list[SQLColumnInfo]:
        """Get list of primary keys for the table.

        Returns
        -------
        list
            list with SQLColumnInfo objects that are the primary keys

        Raises
        ------
        InvalidTableError
            If there are no primary key in the table
        """
        pk_columns = []
        for column in self.columns:
            if column.is_primary_key():
                pk_columns.append(column)
        if pk_columns:
            return pk_columns
        raise InvalidTableError(f"Table {self.table_name!r} has no primary key.")

    def get_deferred_columns(self) -> list[SQLColumnInfo]:
        """
        Return the columns that must be deferred.

        Deferred columns won't be loaded directly when queried.
        """
        return [column for column in self.columns if column.is_deferred]

    def get_undeferred_columns(self) -> list[SQLColumnInfo]:
        """Return the columns that must not be deferred.

        These columns are loaded directly when queried.
        """
        return [column for column in self.columns if not column.is_deferred]

    def get_table(self, table_name: str | None = None) -> sa.Table:
        """
        Return a table with a given name, create it if necessary.

        Parameters
        ----------
        table_name: str (optional, default=None)
            Name of the table to create. If not given, the `table_name`
            attribute is used. If the table with the given name has
            already been created it is returned and no new table
            is generated.
        """
        table_name = table_name or self.table_name
        if table_name not in self._table_instances:
            if table_name in self.metadata.tables:
                self._table_instances[table_name] = sa.Table(table_name, self.metadata)
            else:
                self._table_instances[table_name] = self._generate_table(
                    table_name=table_name
                )
        return self._table_instances[table_name]

    def _generate_table(self, table_name: str) -> sa.Table:
        """Generate a table corresponding to the info with a specific name."""
        return sa.Table(
            table_name,
            self.metadata,
            *[col.generate_column() for col in self.columns],
            *self.constraints,
        )
