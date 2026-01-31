"""
Connection utilities for the database.

The framework used here is `sqlachemy` that can be used with
different engines and dialects. For now the calibration data
is stored in a `PostgreSQL` database and accessed using the
`psycopg` dialect.

The main connection object is the :class:`SQLConnection` that provides the
interface to a SQL database, not knowing which engine it is
(can be `Postgres`, `MySQL`, `Oracle` etc.).

To use the :class:`SQLConnection` with a different DB system or dialect,
it is enough to change the uri and generate the relevant one
following the example of the postgres uri.
"""

from .calibpipe_database import CalibPipeDatabase
from .postgres_utils import get_postgres_uri
from .sql_connection import SQLConnection
from .user_confirmation import get_user_confirmation

__all__ = [
    "SQLConnection",
    "get_user_confirmation",
    "get_postgres_uri",
    "CalibPipeDatabase",
]
