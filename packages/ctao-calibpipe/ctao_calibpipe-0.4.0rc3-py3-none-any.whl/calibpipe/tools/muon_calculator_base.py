"""A basic tool (abstract base class) for calculating quantities such as opt. throughput, PSF, or other using muons."""

from abc import ABCMeta, abstractmethod

from astropy.table import Table, join
from ctapipe.core import QualityQuery, Tool, traits
from ctapipe.core.traits import (
    Bool,
    CInt,
    ComponentName,
    List,
    Path,
    Set,
)
from ctapipe.instrument import SubarrayDescription
from ctapipe.io import read_table, write_table
from ctapipe.io.hdf5dataformat import (
    DL1_TEL_MUON_GROUP,
    DL1_TEL_TRIGGER_TABLE,
)
from ctapipe.monitoring.aggregator import StatisticsAggregator


class MuonQualityQuery(QualityQuery):
    """Quality criteria for muon parameters."""

    quality_criteria = List(
        default_value=[
            ("min impact parameter", "muonefficiency_impact >= 0.0"),
            ("max impact parameter", "muonefficiency_impact <= 10.0"),
            (
                "muon efficiency parameters are not at limit",
                "~muonefficiency_parameters_at_limit",
            ),
            ("throughput calculation is valid", "muonefficiency_is_valid"),
        ],
        allow_none=True,
        help=QualityQuery.quality_criteria.help,
    ).tag(config=True)


class _CombinedMeta(ABCMeta, type(Tool)):
    pass


class CalculateWithMuons(Tool, metaclass=_CombinedMeta):
    """Perform calibration using muons for each telescope allowed in the EventSource."""

    name = traits.Unicode("CalibrationWithMuons")
    description = __doc__

    # Name of the table directory for calibration
    group = "CalibrationWithMuons"

    input_url = Path(
        help="CTAO HDF5 files for DL1 calibration (muons).",
        allow_none=False,
        exists=True,
        directory_ok=False,
        file_ok=True,
    ).tag(config=True)

    allowed_tels = Set(
        trait=CInt(),
        default_value=None,
        allow_none=True,
        help=(
            "List of allowed telescope IDs, others will be ignored. If None, all "
            "telescopes in the input stream will be included. Requires the "
            "telescope IDs to match between the groups of the monitoring file."
        ),
    ).tag(config=True)

    aggregator_type = ComponentName(
        StatisticsAggregator,
        default_value="SigmaClippingAggregator",
        help="The aggregation strategy to use for calculation.",
    ).tag(config=True)

    append = Bool(
        default_value=False,
        help="If the data table already exists in the file, append to it.",
    ).tag(config=True)

    # Set the method name for calculation with muons
    METHOD = "Muon Rings"

    def setup(self):
        """Read from the .h5 file necessary info and save it for further processing."""
        # Load the subarray description from the input file
        self.subarray = SubarrayDescription.from_hdf(self.input_url)

        # Select a new subarray if the allowed_tels configuration is used
        if self.allowed_tels is not None:
            self.subarray = self.subarray.select_subarray(self.allowed_tels)

        # Initialize the quality query for muon selection
        self.quality_query = MuonQualityQuery(parent=self)

        # Initialize the aggregator based on configuration
        self.aggregator = StatisticsAggregator.from_name(
            self.aggregator_type,
            parent=self,
        )

        self.tel_containers_map = {}

    def _read_filter_sort_table(self, tel_id):
        """Read filter and sort the table with muon parameters."""
        muon_table = read_table(
            self.input_url,
            f"{DL1_TEL_MUON_GROUP}/tel_{tel_id:03d}",
        )

        filtered_table = muon_table[self.quality_query.get_table_mask(muon_table)]

        # Read trigger table to get time information
        trigger_table = read_table(
            self.input_url,
            DL1_TEL_TRIGGER_TABLE,
        )

        # Join timing information from trigger table
        filtered_table = join(
            filtered_table,
            trigger_table[["obs_id", "event_id", "time"]],
            keys=["obs_id", "event_id"],
            join_type="left",  # keeps all muon events, even if no trigger match
        )

        # Ensure table is sorted by time
        filtered_table.sort("time")

        return filtered_table

    @abstractmethod
    def _process_tel(self, tel_id):
        """Process muon data for a single telescope ID."""
        pass

    def start(self):
        """
        Apply the cuts on the muon data and process in chunks.

        Only the events that passed quality cuts provided by configuration are considered.
        """
        for tel_id in self.subarray.tel_ids:
            try:
                containers = self._process_tel(tel_id)
                self.tel_containers_map[tel_id] = containers
            except ValueError as e:
                self.log.warning("Skipping telescope %s: %s", tel_id, e)
                self.tel_containers_map[tel_id] = {}
                continue

    def finish(self):
        """Write the chunk-based results to the output file using write_table."""
        for tel_id in self.subarray.tel_ids:
            containers_list = self.tel_containers_map[tel_id]

            # Convert containers to table data using as_dict()
            table_data = []
            for container in containers_list:
                table_data.append(container.as_dict())

            if not table_data:
                self.log.info("No the data to write for telescope %s", tel_id)
                continue
            # Create astropy Table from container data
            the_table = Table(table_data)

            # Write table to HDF5 file
            if self.append:
                write_table(
                    the_table,
                    self.input_url,
                    f"{self.group}/tel_{tel_id:03d}",
                    append=True,
                )
            else:
                write_table(
                    the_table,
                    self.input_url,
                    f"{self.group}/tel_{tel_id:03d}",
                    overwrite=True,
                )
