# noqa: D100

import astropy.units as u
import numpy as np
from astropy.table import Table

# CTA-related imports
from ctapipe.core.traits import (
    Dict,
    Path,
    Unicode,
)
from molecularprofiles.molecularprofiles import MolecularProfile

from ..atmosphere.atmosphere_containers import (
    AtmosphericModelContainer,
    MolecularAtmosphericProfileContainer,
    MolecularDensityContainer,
)

# Internal imports
from ..core.exceptions import (
    CorruptedInputDataError,
    MissingInputDataError,
)
from ..database.connections import CalibPipeDatabase
from ..database.interfaces import TableHandler
from ..utils.observatory import Observatory
from .atmospheric_base_tool import AtmosphericBaseTool


class CreateMolecularAtmosphericModel(AtmosphericBaseTool):
    """
    Create an atmospheric model to be used as input for tailored MC simulations.

    The model consists of:
    - An atmospheric profile.
    - A Rayleigh extinction table.

    The output data is provided in ECSV data format.

    Raises
    ------
    CorruptedInputDataError
        If the MACOBAC12 table does not contain exactly one row.
    MissingInputDataError
        If the requested atmospheric DAS data is not available.
    """

    name = Unicode("CreateAtmosphericModel")
    description = "Create an atmospheric profile"
    aliases = Dict(
        {"macobac12-table-path": "CreateMolecularAtmosphericModel.macobac12_table_path"}
    )

    macobac12_table_path = Path(
        allow_none=False,
        directory_ok=False,
        default_value="macobac.ecsv",
        help="Path to the MACOBAC12 table.",
    ).tag(config=True)

    def setup(self):
        """
        Update configuration and set up the MeteoDataHandler.

        Raises
        ------
        CorruptedInputDataError
            If the MACOBAC12 table does not contain exactly one row.
        """
        super().setup()

        self.macobac12_table = Table.read(self.macobac12_table_path)
        if len(self.macobac12_table) != 1:
            raise CorruptedInputDataError(
                "The MACOBAC12 table should contain exactly one row."
            )
        self.contemporary_atmospheric_profile = None
        self.contemporary_rayleigh_extinction_profile = None

    def start(self):
        """
        Produce molecular atmopsheric model.

        This method performs the following steps:
        1. Retrieves necessary atmospheric data from the specified
            data assimilation system (usually ECMWF).
        2. Combines the retrieved data with the provided 12-MACOBAC
            and stored reference atmospheric model
            to create a contemporary atmospheric profile and a Rayleigh extinction table.

        Raises
        ------
        MissingInputDataError
            If there is an error retrieving the necessary atmospheric data.
        """
        observatory = Observatory.from_db(
            self.database_configuration,
            site=self.observatory["name"].upper(),
            version=self.observatory["version"],
        )

        latitude, longitude = observatory.coordinates
        dusk, dawn = observatory.get_astronomical_night(self._timestamp)
        self.data_handler.create_request(
            start=dusk, stop=dawn, latitude=latitude, longitude=longitude
        )
        data_status = self.data_handler.request_data()
        if data_status == 0:
            co2_concentration = self.macobac12_table["co2_concentration"][0]
            molecular_profile = MolecularProfile(
                f"{self.data_handler.data_path}/merged_file.ecsv",
                stat_columns=self.DEFAULT_METEO_COLUMNS,
            )
            molecular_profile.get_data()
            # compute the molecular density profile
            # in order to select a reference atmospheric model
            # for upper atmosphere
            site = observatory.name
            with CalibPipeDatabase(
                **self.database_configuration,
            ) as connection:
                atmospheric_model_table = TableHandler.read_table_from_database(
                    AtmosphericModelContainer,
                    connection,
                    condition=f"(c.current == True) & (c.name_Observatory == '{site}')",
                )
                reference_density_table = TableHandler.read_table_from_database(
                    MolecularDensityContainer,
                    connection,
                    condition=f"c.version.in_({list(atmospheric_model_table['version'].data)})",
                )
            contemporary_mdp = molecular_profile.create_molecular_density_profile()
            number_density_at_15km = contemporary_mdp[
                contemporary_mdp["altitude"] == 15000 * u.m
            ]["number density"].quantity[0]
            _, _, version = min(
                reference_density_table,
                key=lambda x: abs(
                    x["density"]
                    - number_density_at_15km  # FIXME: MDP table should have "number density" column instead of "density"
                ),
            )
            with CalibPipeDatabase(
                **self.database_configuration,
            ) as connection:
                reference_profile_table = TableHandler.read_table_from_database(
                    MolecularAtmosphericProfileContainer,
                    connection,
                    condition=f'c.version == "{version}"',
                )
                reference_profile_table.remove_columns(["version"])
                reference_profile = Table(
                    [
                        np.squeeze(reference_profile_table[col])
                        for col in reference_profile_table.columns
                    ],
                    names=reference_profile_table.columns,
                )

            self.contemporary_atmospheric_profile = (
                molecular_profile.create_atmospheric_profile(
                    co2_concentration=co2_concentration,
                    reference_atmosphere=reference_profile,
                )
            )
            self.contemporary_rayleigh_extinction_profile = (
                molecular_profile.create_rayleigh_extinction_profile(
                    co2_concentration=co2_concentration,
                    reference_atmosphere=reference_profile,
                )
            )
        else:
            raise MissingInputDataError(
                "Contemporary meteorological data is not available. "
                "Please check the configuration and/or try again later."
            )

    def finish(self):
        """Save the results and perform cleanup."""
        self.contemporary_atmospheric_profile.write(
            f"{self.output_path}/contemporary_atmospheric_profile.{self.output_format}",
            format=f"{self.output_format}",
        )
        self.contemporary_rayleigh_extinction_profile.write(
            f"{self.output_path}/contemporary_rayleigh_extinction_profile.{self.output_format}",
            format=f"{self.output_format}",
        )
        self.log.info("Shutting down.")
        self.data_handler.cleanup()


def main():
    """Run the tool."""
    tool = CreateMolecularAtmosphericModel()
    tool.run()
