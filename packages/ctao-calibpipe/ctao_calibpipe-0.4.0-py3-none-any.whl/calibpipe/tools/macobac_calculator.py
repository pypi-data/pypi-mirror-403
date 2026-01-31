"""Calculate the average CO2 concentration of the last 12 months (12-MACOBAC)."""

# Python built-in imports
from datetime import datetime, timezone

# Third-party imports
import astropy.units as u
import numpy as np
from astropy.table import QTable, Table
from astropy.time import Time
from astropy.units.cds import ppm

# CTA-related imports
from ctapipe.core import Tool
from ctapipe.core.traits import Path, Unicode

from ..atmosphere.atmosphere_containers import MacobacContainer

# Internal imports
from ..atmosphere.meteo_data_handlers import CO2DataHandler


class CalculateMACOBAC(Tool):
    """Download Keeling curve data and calculate the average CO2 concentration of the past 12 months."""

    name = Unicode("CalculateMACOBAC")
    description = "Download Keeling curve data and calculate average CO2 concentration of the past 12 months."

    output_file = Path(
        "macobac.ecsv", help="Output ecsv file where macobac container will be written"
    ).tag(config=True)

    classes = [CO2DataHandler]

    def setup(self):
        """Create CO2DataHandler."""
        u.add_enabled_units([ppm])
        self.data_handler = CO2DataHandler(parent=self)
        self.macobac12_table = None

    def start(self):
        """Request meteorological data from Scripps server and compute 12-MACOBAC."""
        self.data_handler.request_data()
        macobac_table = Table.read(
            f"{self.data_handler.data_path}/macobac.csv",
            comment='"',
            skipinitialspace=True,
            format="pandas.csv",
        )
        mask = macobac_table["CO2"].value != "-99.99"
        co2_values = macobac_table[mask][::-1][0:12]["CO2"].data
        macobac12 = np.mean(co2_values.data.astype(float)) * ppm
        self.log.debug(
            "CO2 average atmospheric concentration for the previous 12 months: %f",
            macobac12,
        )
        macobac12_container = MacobacContainer(
            co2_concentration=macobac12,
            estimation_date=Time(
                str(datetime.now(timezone.utc).date()), out_subfmt="date"
            ),
        )
        self.macobac12_table = QTable(
            names=macobac12_container.keys(),
            rows=[macobac12_container.values()],
        )

    def finish(self):
        """Store results and perform the cleanup."""
        self.log.info("Storing the results and performing the cleanup.")
        self.macobac12_table.write(
            self.output_file,
            format="ascii.ecsv",
            serialize_method={"estimation_date": "formatted_value"},
        )
        self.data_handler.cleanup()


def main():
    """Run the app."""
    tool = CalculateMACOBAC()
    tool.run()
