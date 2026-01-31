# noqa: D100
from ctapipe.core.traits import (
    Dict,
    Unicode,
)
from molecularprofiles.molecularprofiles import MolecularProfile

from ..core.exceptions import MissingInputDataError
from ..utils.observatory import Observatory
from .atmospheric_base_tool import AtmosphericBaseTool


class CreateMolecularDensityProfile(AtmosphericBaseTool):
    """
    Tool for creating a contemporary Molecular Density Profile (MDP).

    This tool downloads and processes meteorological data from a specified data assimilation system
    for a night, corresponding to the provided timestamp, and produces a molecular density profile.
    This implementation follows the specifications outlined in UC-DPPS-CP-115.
    """

    name = Unicode("CreateMDP")
    description = "Create a contemporary MDP"
    aliases = Dict(
        {
            "timestamp": "CreateMDP.timestamp",
            "output_path": "CreateMDP.output_path",
        }
    )

    def setup(self):
        """Parse configuration and setup the database connection and MeteoDataHandler."""
        super().setup()
        self.mdp_table = None

    def start(self):
        """
        Download meteorological data and create a molecular density profile.

        This method performs the following operations:
        1. Retrieves the observatory data from the database.
        2. Calculates the astronomical night based on the observatory's coordinates and the provided timestamp.
        3. Creates a data request for the calculated time frame and coordinates.
        4. Attempts to fetch the meteorological data; raises an exception if unavailable.
        5. Generates and saves the molecular density profile to the specified output path.

        Raises
        ------
            MissingInputDataError: If the required meteorological data is not available.
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
        if data_status:
            raise MissingInputDataError(
                f"Meteorologocal data from {self.meteo_data_handler} is not available."
            )

        molecular_profile = MolecularProfile(
            f"{self.data_handler.data_path}/merged_file.ecsv",
            stat_columns=self.DEFAULT_METEO_COLUMNS,
        )
        molecular_profile.get_data()
        self.mdp_table = molecular_profile.create_molecular_density_profile()

    def finish(self):
        """Store the molecular density profile in the output file and perform cleanup."""
        self.mdp_table.write(
            f"{self.output_path}/contemporary_molecular_density_profile.{self.output_format}",
            format=f"{self.output_format}",
        )
        self.log.info("Shutting down.")
        self.data_handler.cleanup()


def main():
    """Run the app."""
    tool = CreateMolecularDensityProfile()
    tool.run()
