"""TableVersionManager class."""

from sqlalchemy import Table

from ...interfaces.sql_table_info import SQLTableInfo


class TableVersionManager:
    """
    Create versioned tables for CalibPipe.

    The main method is `apply_version()` that returns a table given
    a table information and a version. The returned table will
    contain the same data as the table information and have
    a unique name containing the common table name and the
    software version.
    """

    @staticmethod
    def get_safe_version_string(version: str) -> str:
        """Create a string from a version that is safe for table names."""
        return version.replace("-", "_").replace(".", "_")

    @staticmethod
    def update_version(old_name: str, version: str) -> str:
        """Update the DB object name with a new version number."""
        safe_version = TableVersionManager.get_safe_version_string(version)
        root_name = old_name.rsplit("_v")[0]
        new_name = "".join([root_name, "_v", safe_version])
        return new_name

    @staticmethod
    def apply_version(table_info: SQLTableInfo, version: str | None = None) -> Table:
        """Create a DB object class with a particular version number."""
        if not version:
            return table_info.get_table()
        safe_version = TableVersionManager.get_safe_version_string(version)
        table_name = "".join([table_info.table_name, "_v", safe_version])
        return table_info.get_table(table_name=table_name)
