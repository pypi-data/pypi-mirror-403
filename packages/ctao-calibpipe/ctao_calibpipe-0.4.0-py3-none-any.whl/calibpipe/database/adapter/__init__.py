"""
Adapter sub-package.

Contains all utilities to adapt CalibPipe data to a DB and use it.

Sub-package content:

 - :mod:`database_containers<calibpipe.database.adapter.database_containers>`:
   DB containers (in correspondence with CalibPipe containers)
   to connect CalibPipe data and the DB system.
 - :mod:`adapter<calibpipe.database.adapter.adapter>`:
   Small class used to translate CalibPipe container data
   to DB-level data that can be directly inserted in a DB.

"""

from . import database_containers
from .adapter import Adapter

__all__ = [
    "database_containers",
    "Adapter",
]
