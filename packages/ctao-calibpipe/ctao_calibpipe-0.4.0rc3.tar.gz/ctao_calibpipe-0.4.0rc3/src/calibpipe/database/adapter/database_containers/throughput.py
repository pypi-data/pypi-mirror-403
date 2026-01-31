"""OpticalThroughput SQL info."""

from calibpipe.telescope.throughput.containers import OpticalThoughtputContainer

from ...interfaces.sql_column_info import SQLColumnInfo
from ...interfaces.sql_metadata import sql_metadata
from ...interfaces.sql_table_info import SQLTableInfo
from ...interfaces.types import DateTime, Float, Integer, String
from .container_map import ContainerMap

optical_throughput_sql_info = SQLTableInfo(
    table_name="optical_throughput",
    metadata=sql_metadata,
    columns=[
        SQLColumnInfo("ID", Integer, primary_key=True, autoincrement=True),
        SQLColumnInfo("tel_id", Integer),
        SQLColumnInfo("obs_id", Integer),
        SQLColumnInfo("validity_start", DateTime(timezone=True)),
        SQLColumnInfo("validity_end", DateTime(timezone=True)),
        SQLColumnInfo("optical_throughput_coefficient", Float),
        SQLColumnInfo("optical_throughput_coefficient_std", Float),
        SQLColumnInfo("method", String),
        SQLColumnInfo("n_events", Integer),
    ],
)

ContainerMap.register_container_pair(
    cp_container=OpticalThoughtputContainer,
    db_container=optical_throughput_sql_info,
)
