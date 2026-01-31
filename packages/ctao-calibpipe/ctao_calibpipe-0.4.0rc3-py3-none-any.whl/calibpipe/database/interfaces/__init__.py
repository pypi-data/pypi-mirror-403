"""
Various interfaces for database access.

This module contains field, column, row and table interfaces
to interact with a database. In general the module is tightly
coupled to sqlalchemy though some parts have been preserved
from an explicit dependency.

Module content:
  - `types.py`: Type definition for DB fields using sqlalchemy
    types and defining the specific case of the `numpy.ndarray`.
  - `sql_metadata.py`: Simple metadata variable definition for
    sqlalchemy.
  - `sql_column_info.py`: Container for column information, useful
    to e.g. define the corresponding LST fields at the DB level.
  - `sql_table_info.py`: Container for table information, used in
    particular to create sqlalchemy table objects from a list
    of column information.
  - `hashable_row_data.py`: Hashable container of a (single) row
    information (table_name + primary_key value). This can be
    (and is) used to index data using the row to which they belong
    and create a cache for data retrieved from the database.
  - `table_handler.py`: Container for functions to handle
    tables in the DB.
  - `queries.py`: Built-in queries that can be used to retrieve camera calibration data.

"""

from .hashable_row_data import HashableRowData
from .queries import query_from_date, query_from_run, query_full_table
from .sql_column_info import SQLColumnInfo
from .sql_metadata import sql_metadata
from .sql_table_info import SQLTableInfo
from .table_handler import TableHandler
from .types import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Double,
    Float,
    Integer,
    NDArray,
    Numeric,
    SmallInteger,
    String,
    Time,
)

__all__ = [
    "Boolean",
    "SmallInteger",
    "Integer",
    "BigInteger",
    "Float",
    "Double",
    "Numeric",
    "String",
    "Date",
    "Time",
    "DateTime",
    "NDArray",
    "sql_metadata",
    "SQLTableInfo",
    "SQLColumnInfo",
    "HashableRowData",
    "TableHandler",
    "query_full_table",
    "query_from_date",
    "query_from_run",
]
