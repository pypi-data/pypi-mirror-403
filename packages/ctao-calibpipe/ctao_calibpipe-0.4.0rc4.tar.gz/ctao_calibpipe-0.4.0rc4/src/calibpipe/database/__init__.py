"""
Database utilities.

This sub-package contains general purpose utilities for database management,
and also the specialization for LST. LST-related code is contained in
the sub-packages starting with `lst_`, the rest is decoupled from it.

*Content:*
 - :mod:`connections <calibpipe.database.connections>`:

 General purpose connection (`SQLConnection`) using sqlalchemy
 and specialisation for a `PostgreSQL+psycopg` database.

 - :mod:`interfaces <calibpipe.database.interfaces>`:

 General utilities to create and manipulate database objects
 (fields, columns, tables, and the hashable row information used for cache
 indexing, queries).

 - :mod:`adapter <calibpipe.database.adapter>`:

All containers and utilities to convert ctapipe containers to tables that fill
the CalibPipe postgres database.
"""
