"""Tool to upload atmospheric models to the CalibPipe DB."""

import astropy.units as u
import numpy as np
from astropy.table import QTable
from astropy.units import Quantity
from astropy.units.cds import ppm

# CTA-related imports
from ctapipe.core.traits import AstroTime, Bool, Dict, Integer, Path, Unicode

# Internal imports
from calibpipe.atmosphere.atmosphere_containers import (
    AtmosphericModelContainer,
    MacobacContainer,
    MolecularAtmosphericProfileContainer,
    MolecularAtmosphericProfileMetaContainer,
    MolecularDensityContainer,
    RayleighExtinctionContainer,
)
from calibpipe.database.connections import CalibPipeDatabase
from calibpipe.database.interfaces import TableHandler

from .basic_tool_with_db import BasicToolWithDB

u.add_enabled_units([ppm])


class UploadAtmosphericModel(BasicToolWithDB):
    """
    Upload a (reference) atmospheric model to the calibpipe database.

    For the time being the model consists of
    - a molecular atmospheric profile;
    - a molecular number density at 15km a.s.l.;
    - a 12MACOBAC value;
    - a Rayleigh extinction table - TBA.
    The input data  for the atmospheric profile is provided in ecsv data format.

    """

    name = Unicode("UploadAtmosphericModel")
    description = "Upload an atmospheric model to the calibpipe database"

    atmospheric_model = Dict(
        per_key_traits={
            "start": AstroTime(),
            "stop": AstroTime(),
            "version": Unicode(),
            "current": Bool(),
            "season": Unicode(),
            "name_Observatory": Unicode(),
            "version_Observatory": Integer(),
        },
        help="Atmospheric model metadata",
    ).tag(config=True)

    macobac_data_path = Path(
        help="Path to an ecsv file with macobac data that contains the 12-MACOBAC value and estimation date",
        directory_ok=False,
        allow_none=False,
    ).tag(config=True)
    molecular_density_data_path = Path(
        help="Path to an ecsv file that contains the molecular number density at 15km a.s.l. for a given atmospheric model",
        directory_ok=False,
        allow_none=False,
    ).tag(config=True)

    molecular_atmospheric_profile = Dict(
        per_key_traits={
            "data_assimilation_system": Unicode(),
            "dataset": Unicode(),
            "description": Unicode(),
            "data_path": Path(allow_none=False),
        },
        default_value={
            "data_assimilation_system": "GDAS",
            "dataset": "ds.083.2",
            "description": "Test",
            "data_path": "src/calibpipe/atmosphere/models/test.ecsv",
        },
        help="Molecular atmospheric profile data",
    ).tag(config=True)

    rayleigh_extinction_data_path = Path(
        help="Path to an ecsv file with rayleigh extinction profile data",
        directory_ok=False,
        allow_none=False,
    ).tag(config=True)

    def setup(self):
        """Configure atmopsheric model container."""
        super().setup()
        self.am_container = AtmosphericModelContainer(**self.atmospheric_model)
        if self.am_container.start is not None:
            self.am_container.start = self.am_container.start.to_datetime()
        if self.am_container.stop is not None:
            self.am_container.stop = self.am_container.stop.to_datetime()
        self.map_data_path = self.molecular_atmospheric_profile.pop("data_path", None)
        self.map_meta_container = MolecularAtmosphericProfileMetaContainer(
            **self.molecular_atmospheric_profile
        )
        self.map_meta_container.version = self.am_container.version

    def start(self):
        """Fetch atmospheric tables and upload them to the DB."""
        map_table = QTable.read(self.map_data_path)
        map_container = MolecularAtmosphericProfileContainer(**dict(map_table.items()))
        map_container.version = self.am_container.version
        macobac_table = QTable.read(self.macobac_data_path)
        macobac_container = MacobacContainer()
        macobac_container.co2_concentration = macobac_table["co2_concentration"][0]
        macobac_container.estimation_date = (
            macobac_table["estimation_date"][0].to_datetime().date()
        )
        macobac_container.version = self.am_container.version
        re_table = QTable.read(self.rayleigh_extinction_data_path)
        wl_cols = [
            wl
            for wl in re_table.colnames
            if wl != "altitude_min" and wl != "altitude_max"
        ]
        wls = np.array([Quantity(wl).to_value(u.nm) for wl in wl_cols]) * u.nm
        altitudes = re_table[["altitude_min", "altitude_max"]].to_pandas().values * u.km
        aods = re_table[wl_cols].to_pandas().values * u.dimensionless_unscaled
        re_container = RayleighExtinctionContainer(
            wavelength=wls,
            altitude=altitudes,
            AOD=aods,
        )
        re_container.version = self.am_container.version
        md_container = MolecularDensityContainer()
        md_container.version = self.am_container.version
        md_table = QTable.read(self.molecular_density_data_path)
        md_container.density = md_table["density"][0]
        md_container.season = md_table["season"][0]

        containers = [
            self.am_container,
            self.map_meta_container,
            map_container,
            macobac_container,
            re_container,
            md_container,
        ]
        with CalibPipeDatabase(
            **self.database_configuration,
        ) as connection:
            for container in containers:
                table, insertion = TableHandler.get_database_table_insertion(
                    container,
                )
                if (container == self.am_container) and (self.am_container.current):
                    stmt = (
                        table.update()
                        .where(
                            (table.c.current)
                            & (table.c.season == self.am_container.season)
                            & (
                                table.c.name_Observatory
                                == self.am_container.name_Observatory
                            )
                            & (
                                table.c.version_Observatory
                                == self.am_container.version_Observatory
                            )
                        )
                        .values(current=False)
                    )
                    connection.execute(stmt)
                TableHandler.insert_row_in_database(table, insertion, connection)

    def finish(self):
        """Do nothing."""
        self.log.info("Shutting down.")


def main():
    """Run the tool."""
    tool = UploadAtmosphericModel()
    tool.run()
