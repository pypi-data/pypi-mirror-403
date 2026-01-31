"""Observatory SQL table info."""

from sqlalchemy.schema import ForeignKeyConstraint, UniqueConstraint

from ....utils.observatory_containers import ObservatoryContainer, SeasonContainer
from ...interfaces.sql_column_info import SQLColumnInfo
from ...interfaces.sql_metadata import sql_metadata
from ...interfaces.sql_table_info import SQLTableInfo
from ...interfaces.types import Date, Float, Integer, String
from .container_map import ContainerMap

observatory_sql_info = SQLTableInfo(
    table_name="Observatory",
    metadata=sql_metadata,
    columns=[
        SQLColumnInfo("name", String, primary_key=True),
        SQLColumnInfo("latitude", Float, unit="deg"),
        SQLColumnInfo("longitude", Float, unit="deg"),
        SQLColumnInfo("elevation", Integer, unit="m"),
        SQLColumnInfo("version", Integer, primary_key=True),
    ],
    constraints=[
        UniqueConstraint("name", "version", name="observatory_name_version_unique"),
    ],
)

season_sql_info = SQLTableInfo(
    table_name="Season",
    metadata=sql_metadata,
    columns=[
        SQLColumnInfo("start", Date),
        SQLColumnInfo("stop", Date),
        SQLColumnInfo("name", String),
        SQLColumnInfo("alias", String),
        SQLColumnInfo("name_Observatory", String, nullable=False),
        SQLColumnInfo("version_Observatory", Integer, nullable=False),
    ],
    constraints=[
        ForeignKeyConstraint(
            ["name_Observatory", "version_Observatory"],
            ["Observatory.name", "Observatory.version"],
        ),
        UniqueConstraint(
            "start",
            "stop",
            "name_Observatory",
            "version_Observatory",
            name="season_unique",
        ),
    ],
)

ContainerMap.register_container_pair(
    cp_container=ObservatoryContainer,
    db_container=observatory_sql_info,
)

ContainerMap.register_container_pair(
    cp_container=SeasonContainer,
    db_container=season_sql_info,
)
