"""HashableRowData class."""

from collections.abc import Hashable


class HashableRowData:
    """
    Contain hashable row information (table and primary key).

    A table name and a primary key **value** is enough information
    to uniquely identify a row inside the entire database. This
    information can therefore be hashed to create a map indexed
    by a row.

    Attributes
    ----------
    table_name: str
        Name of the table in which the row is stored.

    primary_key: Hashable
        Any python object that can be hashed, must contain the primary
        key value of the row.
    """

    table_name: str
    primary_key: Hashable  # Any hashable value

    def __init__(self, table_name: str, primary_key: Hashable) -> None:
        """Initialize hashable table."""
        self.table_name = table_name
        self.primary_key = primary_key

    def __eq__(self, object_: object) -> bool:
        """Compare two HashableRowData objects."""
        if not isinstance(object_, HashableRowData):
            return False
        return (
            self.table_name == object_.table_name
            and self.primary_key == object_.primary_key
        )

    def __hash__(self) -> int:
        """
        Hash function.

        The xor (operator ^) seems ok because the table name and primary_key
        will in general be different, or at least it should be extremely
        rare and performance should not be affected.
        """
        return hash(self.table_name) ^ hash(self.primary_key)

    def __str__(self) -> str:
        """Generate a string representation for HashableRowData object. Unicity is guaranteed."""
        return f"{self.primary_key}_{self.table_name}"
