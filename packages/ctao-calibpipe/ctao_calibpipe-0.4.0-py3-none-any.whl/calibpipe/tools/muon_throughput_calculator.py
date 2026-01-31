"""Tool for calculating of optical throughput."""

import numpy as np
from astropy.time import Time
from ctapipe.io.hdf5dataformat import DL1_TEL_MUON_THROUGHPUT_GROUP

from calibpipe.telescope.throughput.containers import OpticalThoughtputContainer
from calibpipe.tools.muon_calculator_base import (
    CalculateWithMuons,
    traits,
)


class CalculateThroughputWithMuons(CalculateWithMuons):
    """Perform throughput calibration using muons for each telescope allowed in the EventSource."""

    name = traits.Unicode("ThroughputCalibration")
    description = __doc__

    # Name of the table directory for throughput calibration
    group = DL1_TEL_MUON_THROUGHPUT_GROUP

    aliases = {
        ("i", "input"): "CalculateThroughputWithMuons.input_url",
    }

    def _process_tel(self, tel_id):
        """Process muon data for a single telescope ID."""
        filtered_table = self._read_filter_sort_table(tel_id)

        # Add time_mono column for aggregator (reusing original table)
        filtered_table["time_mono"] = filtered_table["time"]

        # Run aggregator with chunk processing - will raise ValueError if insufficient data
        chunk_stats = self.aggregator(
            table=filtered_table,
            col_name="muonefficiency_optical_efficiency",
        )

        # Convert aggregator results to throughput containers
        containers = []
        for i in range(len(chunk_stats)):
            # Create container with all parameters at once
            container = OpticalThoughtputContainer(
                obs_id=filtered_table["obs_id"],
                method=self.METHOD,
                mean=chunk_stats["mean"][i],
                median=chunk_stats["median"][i],
                std=chunk_stats["std"][i],
                sem=np.squeeze(
                    chunk_stats["std"][i] / (chunk_stats["n_events"][i] ** 0.5)
                ),
                time_start=Time(
                    chunk_stats["time_start"][i], format="mjd", scale="tai"
                ),
                time_end=Time(chunk_stats["time_end"][i], format="mjd", scale="tai"),
                n_events=np.squeeze(chunk_stats["n_events"][i]),
            )
            containers.append(container)
        return containers


def main():
    """Run the app."""
    tool = CalculateThroughputWithMuons()
    tool.run()
