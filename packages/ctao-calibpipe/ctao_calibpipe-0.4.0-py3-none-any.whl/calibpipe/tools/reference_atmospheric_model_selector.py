import astropy.units as u  # noqa: D100
import numpy as np
from astropy.table import Table
from ctapipe.core.traits import (
    Dict,
    Unicode,
)
from molecularprofiles.molecularprofiles import MolecularProfile

from ..atmosphere.atmosphere_containers import (
    AtmosphericModelContainer,
    MolecularAtmosphericProfileContainer,
    MolecularDensityContainer,
    RayleighExtinctionContainer,
    SelectedAtmosphericModelContainer,
)
from ..core.exceptions import IntermittentError
from ..database.connections import CalibPipeDatabase
from ..database.interfaces import TableHandler
from ..utils.observatory import Observatory, SeasonAlias
from .atmospheric_base_tool import AtmosphericBaseTool


class SelectMolecularAtmosphericModel(AtmosphericBaseTool):
    """Select a reference molecular atmospheric model."""

    name = Unicode("SelectMolecularAtmosphericModel")
    description = (
        "Select a reference Molecular Atmospheric Model "
        "based on the molecular number density at 15km a.s.l. "
        "computed from contemporary meteorological data."
    )
    aliases = Dict(
        {
            "timestamp": "SelectMolecularAtmosphericModel.timestamp",
            "output_path": "SelectMolecularAtmosphericModel.output_path",
        }
    )

    def setup(self):
        """Parse configuration and setup the database connection and MeteoDataHandler."""
        super().setup()
        self.selected_model_container = None
        self.failed_to_retrieve_meteo_data = True

    def start(self):
        """
        Download meteorological data and select a reference atmospheric model.

        This method performs the following operations:
        1. Retrieves the observatory data from the database.
        2. Calculates the astronomical night based on the observatory's coordinates and the provided timestamp.
        3. Creates a data request for the calculated time frame and coordinates.
        4. Attempts to fetch the meteorological data.
        5a. If meteorological data is not available, select a reference model based on the date.
        5b. If meteorological data is available, select a reference model based on the molecular number density at 15km a.s.l.
        """
        observatory = Observatory.from_db(
            self.database_configuration,
            site=self.observatory["name"].upper(),
            version=self.observatory["version"],
        )
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

        latitude, longitude = observatory.coordinates
        dusk, dawn = observatory.get_astronomical_night(self._timestamp)
        self.data_handler.create_request(
            start=dusk, stop=dawn, latitude=latitude, longitude=longitude
        )
        self.failed_to_retrieve_meteo_data = self.data_handler.request_data()
        if self.failed_to_retrieve_meteo_data:
            season = observatory.get_season_from_timestamp(self._timestamp)
            version = -1
        else:
            molecular_profile = MolecularProfile(
                f"{self.data_handler.data_path}/merged_file.ecsv",
                stat_columns=self.DEFAULT_METEO_COLUMNS,
            )
            molecular_profile.get_data()
            contemporary_mdp = molecular_profile.create_molecular_density_profile()
            number_density_at_15km = contemporary_mdp[
                contemporary_mdp["altitude"] == 15000 * u.m
            ]["number density"].quantity[0]
            season, _, version = min(
                reference_density_table,
                key=lambda x: abs(
                    x["density"]
                    - number_density_at_15km  # FIXME: MDP table should have "number density" column instead of "density"
                ),
            )

        selected_season_table = atmospheric_model_table[
            (atmospheric_model_table["season"] == season)
        ]
        if version == -1:
            version = selected_season_table[(selected_season_table["current"])][
                "version"
            ][0]

        self.selected_model_container = SelectedAtmosphericModelContainer(
            date=self._timestamp.date(),
            version=version,
            season=SeasonAlias[season.upper()].value,
            site=observatory.name,
            provenance=self.meteo_data_handler,
        )

    def finish(self):
        """Store the selected atmospheric model, and perform cleanup.

        Raises
        ------
        IntermittentError
            In case of missing meteorological data.
        """
        self.log.info(
            "Selected atmospheric model container:\n%s", self.selected_model_container
        )

        with CalibPipeDatabase(
            **self.database_configuration,
        ) as connection:
            table, insertion = TableHandler.get_database_table_insertion(
                self.selected_model_container,
            )
            TableHandler.insert_row_in_database(table, insertion, connection)
            selected_atmospheric_table = TableHandler.read_table_from_database(
                MolecularAtmosphericProfileContainer,
                connection,
                condition=f'c.version == "{self.selected_model_container["version"]}"',
            )
            selected_rayleigh_extinction_table = TableHandler.read_table_from_database(
                RayleighExtinctionContainer,
                connection,
                condition=f'c.version == "{self.selected_model_container["version"]}"',
            )
        selected_atmospheric_table.remove_column("version")
        selected_atmospheric_profile = Table(
            [
                np.squeeze(selected_atmospheric_table[col])
                for col in selected_atmospheric_table.columns
            ],
            names=selected_atmospheric_table.columns,
        )
        selected_atmospheric_profile.write(
            f"{self.output_path}/selected_atmospheric_profile.{self.output_format}",
            format=f"{self.output_format}",
        )
        selected_rayleigh_extinction_table.remove_column("version")

        rayleigh_extinction_col_names = ["altitude_min", "altitude_max"]
        rayleigh_extinction_col_names.extend(
            [
                f"{name:.1f}"
                for name in selected_rayleigh_extinction_table["wavelength"].squeeze()
            ]
        )
        data_array = np.hstack(
            (
                selected_rayleigh_extinction_table["altitude"].squeeze().to_value(u.km),
                selected_rayleigh_extinction_table["AOD"].squeeze(),
            )
        )
        selected_rayleigh_extinction_profile = Table(
            data=data_array,
            names=rayleigh_extinction_col_names,
        )
        selected_rayleigh_extinction_profile["altitude_min"] *= u.km
        selected_rayleigh_extinction_profile["altitude_max"] *= u.km

        selected_rayleigh_extinction_profile.write(
            f"{self.output_path}/selected_rayleigh_extinction_profile.{self.output_format}",
            format=f"{self.output_format}",
        )

        self.log.info("Shutting down.")
        self.data_handler.cleanup()
        if self.failed_to_retrieve_meteo_data:
            raise IntermittentError(
                f"Missing meteorological data from {self.meteo_data_handler}. "
                "This is a known issue, the reference model was selected based on the date."
            )


def main():
    """Run the app."""
    tool = SelectMolecularAtmosphericModel()
    tool.run()
