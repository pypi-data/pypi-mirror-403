"""SQL info for run metadata."""

from ...interfaces.sql_column_info import SQLColumnInfo
from ...interfaces.sql_metadata import sql_metadata
from ...interfaces.sql_table_info import SQLTableInfo
from ...interfaces.types import DateTime, String

version_control_sql_info = SQLTableInfo(
    table_name="version_control_table",
    metadata=sql_metadata,
    columns=[
        SQLColumnInfo("name", String),
        SQLColumnInfo("version", String),
        SQLColumnInfo("validity_start", DateTime(timezone=True)),
        SQLColumnInfo("validity_end", DateTime(timezone=True)),
    ],
)
