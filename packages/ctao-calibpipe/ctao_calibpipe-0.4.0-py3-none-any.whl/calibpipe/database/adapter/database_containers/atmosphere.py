"""Atmospheric SQL table info."""

from sqlalchemy.schema import ForeignKeyConstraint

from ....atmosphere.atmosphere_containers import (
    AtmosphericModelContainer,
    MacobacContainer,
    MolecularAtmosphericProfileContainer,
    MolecularAtmosphericProfileMetaContainer,
    MolecularDensityContainer,
    RayleighExtinctionContainer,
    SelectedAtmosphericModelContainer,
)
from ...interfaces.sql_column_info import SQLColumnInfo
from ...interfaces.sql_metadata import sql_metadata
from ...interfaces.sql_table_info import SQLTableInfo
from ...interfaces.types import (
    ArrayF1D,
    ArrayF2D,
    Boolean,
    Date,
    Float,
    Integer,
    String,
)
from .container_map import ContainerMap

atmospheric_model_sql_info = SQLTableInfo(
    table_name="AtmosphericModel",
    metadata=sql_metadata,
    columns=[
        SQLColumnInfo("start", Date),
        SQLColumnInfo("stop", Date),
        SQLColumnInfo("version", String, primary_key=True),
        SQLColumnInfo("current", Boolean),
        SQLColumnInfo("season", String),
        SQLColumnInfo("name_Observatory", String, nullable=False),
        SQLColumnInfo("version_Observatory", Integer, nullable=False),
    ],
    constraints=[
        ForeignKeyConstraint(
            ["name_Observatory", "version_Observatory"],
            ["Observatory.name", "Observatory.version"],
        )
    ],
)

mdp_sql_info = SQLTableInfo(
    table_name="MolecularDensity",
    metadata=sql_metadata,
    columns=[
        SQLColumnInfo("season", String),
        SQLColumnInfo("density", Float, unit="1/cm^3"),
        SQLColumnInfo("version", String, primary_key=True),
    ],
    constraints=[
        ForeignKeyConstraint(
            [
                "version",
            ],
            [
                "AtmosphericModel.version",
            ],
        )
    ],
)

map_meta_sql_info = SQLTableInfo(
    table_name="MolecularAtmosphericProfileMeta",
    metadata=sql_metadata,
    columns=[
        SQLColumnInfo("data_assimilation_system", String),
        SQLColumnInfo("dataset", String),
        SQLColumnInfo("description", String),
        SQLColumnInfo("version", String, primary_key=True),
    ],
    constraints=[
        ForeignKeyConstraint(
            [
                "version",
            ],
            [
                "AtmosphericModel.version",
            ],
        )
    ],
)

map_sql_info = SQLTableInfo(
    table_name="MolecularAtmosphericProfile",
    metadata=sql_metadata,
    columns=[
        SQLColumnInfo("altitude", ArrayF1D, unit="km"),
        SQLColumnInfo("pressure", ArrayF1D, unit="hPa"),
        SQLColumnInfo("temperature", ArrayF1D, unit="K"),
        SQLColumnInfo("partial_water_pressure", ArrayF1D),
        SQLColumnInfo("refractive_index_m_1", ArrayF1D),
        SQLColumnInfo("atmospheric_density", ArrayF1D, unit="g/cm^3"),
        SQLColumnInfo("atmospheric_thickness", ArrayF1D, unit="g/cm^2"),
        SQLColumnInfo("version", String, primary_key=True),
    ],
    constraints=[
        ForeignKeyConstraint(
            [
                "version",
            ],
            [
                "AtmosphericModel.version",
            ],
        )
    ],
)

macobac_sql_info = SQLTableInfo(
    table_name="MACOBAC",
    metadata=sql_metadata,
    columns=[
        SQLColumnInfo("co2_concentration", Float, unit="ppm"),
        SQLColumnInfo("estimation_date", Date),
        SQLColumnInfo("version", String, primary_key=True),
    ],
    constraints=[
        ForeignKeyConstraint(
            [
                "version",
            ],
            [
                "AtmosphericModel.version",
            ],
        )
    ],
)

rayleigh_extinction_sql_info = SQLTableInfo(
    table_name="RayleighExtinction",
    metadata=sql_metadata,
    columns=[
        SQLColumnInfo("wavelength", ArrayF1D, unit="nm"),
        SQLColumnInfo("altitude", ArrayF2D, unit="km"),
        SQLColumnInfo("AOD", ArrayF2D),
        SQLColumnInfo("version", String, primary_key=True),
    ],
    constraints=[
        ForeignKeyConstraint(
            [
                "version",
            ],
            [
                "AtmosphericModel.version",
            ],
        )
    ],
)

selected_model_sql_info = SQLTableInfo(
    table_name="SelectedAtmosphericModel",
    metadata=sql_metadata,
    columns=[
        SQLColumnInfo("date", Date),
        SQLColumnInfo("provenance", String),
        SQLColumnInfo("season", String),
        SQLColumnInfo("site", String),
        SQLColumnInfo("version", String),
    ],
)

ContainerMap.register_container_pair(
    cp_container=AtmosphericModelContainer,
    db_container=atmospheric_model_sql_info,
)

ContainerMap.register_container_pair(
    cp_container=MolecularAtmosphericProfileMetaContainer,
    db_container=map_meta_sql_info,
)

ContainerMap.register_container_pair(
    cp_container=MolecularAtmosphericProfileContainer,
    db_container=map_sql_info,
)

ContainerMap.register_container_pair(
    cp_container=MolecularDensityContainer,
    db_container=mdp_sql_info,
)

ContainerMap.register_container_pair(
    cp_container=MacobacContainer,
    db_container=macobac_sql_info,
)

ContainerMap.register_container_pair(
    cp_container=RayleighExtinctionContainer,
    db_container=rayleigh_extinction_sql_info,
)
ContainerMap.register_container_pair(
    cp_container=SelectedAtmosphericModelContainer,
    db_container=selected_model_sql_info,
)
