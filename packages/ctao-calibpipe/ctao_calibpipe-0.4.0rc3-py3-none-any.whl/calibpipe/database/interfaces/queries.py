"""
Built-in queries for camera calibration data.

All built-in queries are obtained by calling functions that
return a tuple of query and a list of strings, e.g.::

    light_query, deferred_column_names = some_builtin_query()

Each time, the query object can be directly sent to an `execute()`
SQLConnection method and it will retrieve from the DB the primary
key and all light fields (by default non-array types, see the
deferred property of `SQLColumnInfo`). This can be done e.g. using::

    db.execute(light_query)

The list of strings returned in the
tuple is the list of deferred fields, that must be queried
separately later on, e.g. using::

    query = sa.select(deferred_column_names)
    res = db.execute(query)

The built-in queries are:

 - `query_full_table()`: Return the query utilities
   to retrieve a full table from the database
   (used e.g. to retrieve the run metadata table).
 - `query_from_run()`: Return the query utilities
   to retrieve data of a given run in a given table.
 - `query_from_date()`: Return the query utilities
   to retrieve data at a given date in a given table.

The queries have an undefined type (internal to sqlalchemy and
not fully defined), an alias to `Any` is used in this file to express
what objects are SQL queries.
"""

import datetime
from typing import Any

import sqlalchemy as sa

from ..adapter.database_containers.table_version_manager import (
    TableVersionManager,
)
from .sql_table_info import SQLTableInfo

Query = Any
""" Alias to express which objects are queries as `sqlalchemy` does not define it. """


def _get_deferred_column(table: sa.Table, info: SQLTableInfo) -> list[str]:
    """Return the names of deferred columns to use in a select statement."""
    return [getattr(table.c, column.name) for column in info.get_deferred_columns()]


def _get_undeferred_column(table: sa.Table, info: SQLTableInfo) -> list[str]:
    """Return the names of undeferred columns to use in a select statement."""
    return [getattr(table.c, column.name) for column in info.get_undeferred_columns()]


def _process_table_info(
    table_info: SQLTableInfo, version: str
) -> tuple[sa.Table, list[str], list[str]]:
    """Return objects necessary to build queries from a table info."""
    table = TableVersionManager.apply_version(table_info=table_info, version=version)
    deferred_columns = _get_deferred_column(table=table, info=table_info)
    undeferred_columns = _get_undeferred_column(table=table, info=table_info)
    return table, deferred_columns, undeferred_columns


def _select_and_filter(column: list[Any], condition: Any) -> Query | None:
    """Return a select clause on several columns using a simple filter."""
    if not column:
        return None
    return sa.select(*column).filter(condition)


def _select_by_date(
    table: sa.Table, column: list[str], date: datetime.date
) -> Query | None:
    """Return a query selecting a list of columns from a date."""
    return _select_and_filter(
        column=column,
        condition=(table.c.date == date),  # pylint: disable=superfluous-parens
    )


def _select_by_run(table: sa.Table, column: list[str], run: int) -> Query | None:
    """Return a query selecting a list of columns from a run."""
    return _select_and_filter(
        column=column,
        condition=(table.c.run == run),  # pylint: disable=superfluous-parens
    )


def query_full_table(
    table_info: SQLTableInfo, version: str | None = None
) -> tuple[Query, list[str]]:
    """
    Return a query for a complete table.

    Parameters
    ----------
    table_info: SQLTableInfo
        Table to which the query must be built.

    version: Optional[str], default=None
        Software version of the data to retrieve. If `None` is given, the
        `_pro` version will be used i.e. the latest available.

    Returns
    -------
    tuple[Query, list[str]]
        A tuple containing the light query to retrieve small fields and the list
        of field names for deferred fields (cached and loaded later).
    """
    _unused_table, deferred_columns, undeferred_columns = _process_table_info(
        table_info, version=version
    )
    light_query = sa.select(undeferred_columns)
    return light_query, deferred_columns


def query_from_date(
    table_info: SQLTableInfo, version: str, date: datetime.date
) -> tuple[Query, list[str]]:
    """
    Return a query from a date.

    Parameters
    ----------
    table_info: SQLTableInfo
        Table to which the query must be built.

    version: Optional[str], default=None
        Software version of the data to retrieve. If `None` is given, the
        `_pro` version will be used i.e. the latest available.

    Returns
    -------
    tuple[Query, list[str]]
        A tuple containing the light query to retrieve small fields and the list
        of field names for deferred fields (cached and loaded later).
    """
    table, deferred_columns, undeferred_columns = _process_table_info(
        table_info, version=version
    )
    light_query = _select_by_date(table, undeferred_columns, date)

    return light_query, deferred_columns


def query_from_run(
    table_info: SQLTableInfo, version: str, run: int
) -> tuple[Query, list[str]]:
    """
    Return a query from a run.

    Parameters
    ----------
    table_info: SQLTableInfo
        Table to which the query must be built.

    version: Optional[str], default=None
        Software version of the data to retrieve. If `None` is given, the
        `_pro` version will be used i.e. the latest available.

    Returns
    -------
    tuple[Query, list[str]]
        A tuple containing the light query to retrieve small fields and the list
        of field names for deferred fields (cached and loaded later).
    """
    table, deferred_columns, undeferred_columns = _process_table_info(
        table_info, version=version
    )
    light_query = _select_by_run(table, undeferred_columns, run)

    return light_query, deferred_columns
