"""SQLColumnInfo class."""

import astropy.units as u
import sqlalchemy as sa
from astropy.units.cds import ppm

from .types import ColumnType, NDArray

u.add_enabled_units([ppm])


class SQLColumnInfo:
    """
    Contain info required to create a `sa.Column` object.

    The data representing the column is system-independent,
    using in particular the generic types in `.types`,
    only the `generate_column()` method is specialized for
    `sqlalchemy` (returning a `sa.Column` object).

    Attributes
    ----------
    name: str
        Field name

    field_type: ColumnType
        Field `type.` See the `.types` import for possible types

    is_deferred: bool (optional, default=None)
        If given, tell if the field must be deferred i.e. loaded
        only later (when queried) if a cache system is in place.
        If not given, only `NDArray` objects are deferred.
    """

    def __init__(
        self,
        name: str,
        field_type: ColumnType,
        unit: str | None = "",
        is_deferred: bool | None = None,
        **kwargs,
    ) -> None:
        """
        Initialize the column data.

        Any keyword argument required to build the final Column object
        (here sa.Column for sqlachemy) in the generate_column() method
        can be given to the initializer.
        """
        self.name = name
        self.type = field_type
        self.unit = u.Unit(unit)
        if is_deferred is not None:
            self.is_deferred = is_deferred
        else:
            # If not specified defer automatically arrays and arrays only
            self.is_deferred = field_type == NDArray
        self.kwargs = {**kwargs}

    def generate_column(self) -> sa.Column:
        """Generate a new corresponding sa.Column object."""
        column = sa.Column(self.name, self.type, comment=str(self.unit), **self.kwargs)
        return column

    def is_primary_key(self) -> bool:
        """Check if the column is a primary key."""
        return "primary_key" in self.kwargs and self.kwargs["primary_key"]
