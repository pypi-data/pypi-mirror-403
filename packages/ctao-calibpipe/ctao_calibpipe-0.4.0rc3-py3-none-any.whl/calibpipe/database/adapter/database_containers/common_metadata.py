"""Common Metadata SQL info."""

from sqlalchemy.schema import ForeignKeyConstraint, UniqueConstraint

from ....core.common_metadata_containers import (
    ActivityReferenceMetadataContainer,
    ContactReferenceMetadataContainer,
    InstrumentReferenceMetadataContainer,
    ProcessReferenceMetadataContainer,
    ProductReferenceMetadataContainer,
    ReferenceMetadataContainer,
)
from ...interfaces.sql_column_info import SQLColumnInfo
from ...interfaces.sql_metadata import sql_metadata
from ...interfaces.sql_table_info import SQLTableInfo
from ...interfaces.types import Integer, String
from .container_map import ContainerMap

reference_metadata_sql_info = SQLTableInfo(
    table_name="reference_metadata",
    metadata=sql_metadata,
    columns=[
        SQLColumnInfo("ID", Integer, unique=True, primary_key=True, autoincrement=True),
        SQLColumnInfo("ID_optical_throughput", Integer),
        SQLColumnInfo("version_atmospheric_model", String),
        SQLColumnInfo("version", String),
    ],
    constraints=[
        ForeignKeyConstraint(["ID_optical_throughput"], ["optical_throughput.ID"]),
        ForeignKeyConstraint(
            ["version_atmospheric_model"], ["AtmosphericModel.version"]
        ),
        UniqueConstraint("ID"),
    ],
)

product_reference_metadata_sql_info = SQLTableInfo(
    table_name="product_reference_metadata",
    metadata=sql_metadata,
    columns=[
        SQLColumnInfo("ID", Integer, unique=True, primary_key=True),
        SQLColumnInfo("description", String),
        SQLColumnInfo("creation_time", String),
        SQLColumnInfo("product_id", String),
        SQLColumnInfo("data_category", String),
        SQLColumnInfo("data_level", String),
        SQLColumnInfo("data_association", String),
        SQLColumnInfo("data_type", String),
        SQLColumnInfo("data_model_name", String),
        SQLColumnInfo("data_model_version", String),
        SQLColumnInfo("data_model_url", String),
        SQLColumnInfo("format", String),
    ],
    constraints=[
        ForeignKeyConstraint(["ID"], ["reference_metadata.ID"]),
        UniqueConstraint("ID"),
    ],
)

contact_reference_metadata_sql_info = SQLTableInfo(
    table_name="contact_reference_metadata",
    metadata=sql_metadata,
    columns=[
        SQLColumnInfo("ID", Integer, unique=True, primary_key=True),
        SQLColumnInfo("organization", String),
        SQLColumnInfo("name", String),
        SQLColumnInfo("email", String),
    ],
    constraints=[
        ForeignKeyConstraint(["ID"], ["reference_metadata.ID"]),
        UniqueConstraint("ID"),
    ],
)

activity_reference_metadata_sql_info = SQLTableInfo(
    table_name="activity_reference_metadata",
    metadata=sql_metadata,
    columns=[
        SQLColumnInfo("ID", Integer, unique=True, primary_key=True),
        SQLColumnInfo("activity_id", String),
        SQLColumnInfo("name", String),
        SQLColumnInfo("type", String),
        SQLColumnInfo("start", String),
        SQLColumnInfo("end", String),
        SQLColumnInfo("software_name", String),
        SQLColumnInfo("software_version", String),
    ],
    constraints=[
        ForeignKeyConstraint(["ID"], ["reference_metadata.ID"]),
        UniqueConstraint("ID"),
    ],
)

process_reference_metadata_sql_info = SQLTableInfo(
    table_name="process_reference_metadata",
    metadata=sql_metadata,
    columns=[
        SQLColumnInfo("ID", Integer, unique=True, primary_key=True),
        SQLColumnInfo("type", String),
        SQLColumnInfo("subtype", String),
        SQLColumnInfo("subtype_id", String),
    ],
    constraints=[
        ForeignKeyConstraint(["ID"], ["activity_reference_metadata.ID"]),
        UniqueConstraint("ID"),
    ],
)

instrument_reference_metadata_sql_info = SQLTableInfo(
    table_name="instrument_reference_metadata",
    metadata=sql_metadata,
    columns=[
        SQLColumnInfo("ID", Integer, unique=True, primary_key=True),
        SQLColumnInfo("site", String),
        SQLColumnInfo("type", String),
        SQLColumnInfo("subtype", String),
        SQLColumnInfo("instrument_id", String),
    ],
    constraints=[ForeignKeyConstraint(["ID"], ["process_reference_metadata.ID"])],
)

ContainerMap.register_container_pair(
    cp_container=ReferenceMetadataContainer,
    db_container=reference_metadata_sql_info,
)

ContainerMap.register_container_pair(
    cp_container=ProductReferenceMetadataContainer,
    db_container=product_reference_metadata_sql_info,
)

ContainerMap.register_container_pair(
    cp_container=ContactReferenceMetadataContainer,
    db_container=contact_reference_metadata_sql_info,
)

ContainerMap.register_container_pair(
    cp_container=ActivityReferenceMetadataContainer,
    db_container=activity_reference_metadata_sql_info,
)

ContainerMap.register_container_pair(
    cp_container=ProcessReferenceMetadataContainer,
    db_container=process_reference_metadata_sql_info,
)

ContainerMap.register_container_pair(
    cp_container=InstrumentReferenceMetadataContainer,
    db_container=instrument_reference_metadata_sql_info,
)
