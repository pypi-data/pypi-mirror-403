"""Utility tool to produce test data for the camera calibration tools in the calibpipe package."""

import warnings

import astropy.units as u
import tables
import yaml
from astropy.time import Time
from ctapipe.core import Tool, run_tool
from ctapipe.core.traits import (
    Bool,
    CaselessStrEnum,
    CInt,
    List,
    Path,
    Set,
    Unicode,
)
from ctapipe.instrument import SubarrayDescription
from ctapipe.io import read_table, write_table
from ctapipe.io.hdf5dataformat import (
    DL1_PIXEL_STATISTICS_GROUP,
    DL1_TEL_IMAGES_GROUP,
    SIMULATION_GROUP,
)
from ctapipe.tools.calculate_pixel_stats import PixelStatisticsCalculatorTool
from ctapipe.tools.merge import MergeTool
from ctapipe.tools.process import ProcessorTool
from traitlets.config.loader import Config

__all__ = [
    "CamCalibTestDataTool",
]


class CamCalibTestDataTool(Tool):
    """Utility tool to produce test data for the camera calibration."""

    name = "calibpipe-produce-camcalib-test-data"

    description = "Produce test data for the camera calibration tools."

    examples = """
    To produce the test data for the camera calibration tools, you need to provide the input files
    for the pedestal and flatfield events, as well as the configuration files (see examples
    in the calibpipe documentation) for processing these events and aggregating the statistics.
    The timestamp of the events will be set to a realistic value based on the
    reference time and trigger rate defined in the tool. The output files will be created in the
    specified output directory, with the prefix defined in the configuration.

    Run with the following command to produce the test data:

    > calibpipe-produce-camcalib-test-data \\
        --pedestal pedestal_events.simtel.gz \\
        --flatfield flatfield_events.simtel.gz \\
        --output-dir ./output \\
        --CamCalibTestDataTool.process_pedestal_config ctapipe_process_pedestal.yaml \\
        --CamCalibTestDataTool.process_flatfield_config ctapipe_process_flatfield.yaml \\
        --CamCalibTestDataTool.agg_stats_sky_pedestal_image_config ctapipe_calculate_pixel_stats_sky_pedestal_image.yaml \\
        --CamCalibTestDataTool.agg_stats_flatfield_image_config ctapipe_calculate_pixel_stats_flatfield_image.yaml \\
        --CamCalibTestDataTool.agg_stats_flatfield_peak_time_config ctapipe_calculate_pixel_stats_flatfield_peak_time.yaml \\
        --CamCalibTestDataTool.prefix calibpipe_vX.Y.Z_statsagg \\
    """

    pedestal_input_url = Path(
        help="Simtel input file for pedestal events",
        allow_none=False,
        exists=True,
        directory_ok=False,
        file_ok=True,
    ).tag(config=True)

    flatfield_input_url = Path(
        help="Simtel input file for flatfield events",
        allow_none=False,
        exists=True,
        directory_ok=False,
        file_ok=True,
    ).tag(config=True)

    process_pedestal_config = Path(
        help="Path to the configuration file for processing pedestal events",
        allow_none=False,
        exists=True,
        directory_ok=False,
        file_ok=True,
    ).tag(config=True)

    process_flatfield_config = Path(
        help="Path to the configuration file for processing flatfield events",
        allow_none=False,
        exists=True,
        directory_ok=False,
        file_ok=True,
    ).tag(config=True)

    agg_stats_sky_pedestal_image_config = Path(
        help="Path to the configuration file for aggregating sky pedestal image statistics",
        allow_none=False,
        exists=True,
        directory_ok=False,
        file_ok=True,
    ).tag(config=True)

    agg_stats_flatfield_image_config = Path(
        help="Path to the configuration file for aggregating flatfield image statistics",
        allow_none=False,
        exists=True,
        directory_ok=False,
        file_ok=True,
    ).tag(config=True)

    agg_stats_flatfield_peak_time_config = Path(
        help="Path to the configuration file for aggregating flatfield peak time statistics",
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

    prefix = Unicode(
        default_value="statsagg_test_data",
        allow_none=False,
        help="Prefix to be used for the output files of the statistics aggregation",
    ).tag(config=True)

    aggregation_modes = List(
        trait=CaselessStrEnum(
            ["sims_single_chunk", "obslike_same_chunks", "obslike_different_chunks"]
        ),
        default_value=[
            "sims_single_chunk",
            "obslike_same_chunks",
            "obslike_different_chunks",
        ],
        allow_none=False,
        help=(
            "List of aggregation modes for the pixel statistics. "
            "Options are: 'sims_single_chunk', 'obslike_same_chunks', 'obslike_different_chunks'. "
            "If 'sims_single_chunk' is selected, all monitoring groups are aggregated in a single chunk (primarily simulation). "
            "If 'obslike_same_chunks' is selected, all monitoring groups are aggregated in the same chunks (observation-like). "
            "If 'obslike_different_chunks' is selected, each monitoring groups are aggregated in different chunks (observation-like)."
        ),
    ).tag(config=True)

    skip_r1_calibration = Bool(
        default_value=True,
        help=(
            "If True (default), skip the R1 calibration step in the simtel event source. "
            "This is useful for testing and validation purposes of the camera calibration routines. "
        ),
    ).tag(config=True)

    output_dir = Path(
        help="Directory to store the output files",
        allow_none=False,
        exists=True,
        directory_ok=True,
        file_ok=False,
    ).tag(config=True)

    aliases = {
        ("p", "pedestal"): "CamCalibTestDataTool.pedestal_input_url",
        ("f", "flatfield"): "CamCalibTestDataTool.flatfield_input_url",
        ("o", "output-dir"): "CamCalibTestDataTool.output_dir",
    }

    # Define reference time and trigger rate for the tests. These values
    # are used to create realistic timestamps for the aggregated chunks.
    REFERENCE_TIME = Time.now()
    REFERENCE_TRIGGER_RATE = 1000.0 * u.Hz

    def setup(self):
        """Set up the tool."""
        # Load the subarray description from the input files
        subarray_pedestal = SubarrayDescription.read(self.pedestal_input_url)
        subarray_flatfield = SubarrayDescription.read(self.flatfield_input_url)
        # Check if the subarray descriptions match
        if subarray_pedestal != subarray_flatfield:
            raise ValueError(
                "The subarray descriptions of the pedestal and flatfield input files do not match."
            )
        # Select a new subarray if the allowed_tels configuration is used
        self.subarray = (
            subarray_pedestal
            if self.allowed_tels is None
            else subarray_pedestal.select_subarray(self.allowed_tels)
        )
        # The monitoring groups and their configurations to be used in the tests
        self.monitoring_groups = {
            "sky_pedestal_image": self.agg_stats_sky_pedestal_image_config,
            "flatfield_image": self.agg_stats_flatfield_image_config,
            "flatfield_peak_time": self.agg_stats_flatfield_peak_time_config,
        }

    def start(self):
        """Iterate over the telescope IDs and calculate the camera calibration coefficients."""
        # Process pedestal and flatfield events
        pedestal_dl1_image_file = self._process_input_events(
            self.pedestal_input_url,
            self.process_pedestal_config,
            "pedestal_events.dl1.h5",
        )
        flatfield_dl1_image_file = self._process_input_events(
            self.flatfield_input_url,
            self.process_flatfield_config,
            "flatfield_events.dl1.h5",
        )

        for aggregation_mode in self.aggregation_modes:
            # Process statistics aggregation for the current aggregation mode
            for t, tel_id in enumerate(self.subarray.tel_ids):
                self._process_statistics_aggregation(
                    tel_id,
                    t,
                    pedestal_dl1_image_file,
                    flatfield_dl1_image_file,
                    aggregation_mode,
                )
            # Create and finalize monitoring file for the current aggregation mode
            self._create_monitoring_file(aggregation_mode)

    def _process_input_events(self, input_url, config_path, output_filename):
        """Process input events and return the output file path."""
        output_file = self.output_dir / output_filename
        with open(config_path) as yaml_file:
            config = yaml.safe_load(yaml_file)
            output_file = self._run_ctapipe_process_tool(input_url, output_file, config)
        return output_file

    def _process_statistics_aggregation(
        self, tel_id, tel_index, pedestal_file, flatfield_file, aggregation_mode
    ):
        """Process statistics aggregation for a given telescope and aggregation mode."""
        for mon_group, mon_config in self.monitoring_groups.items():
            output_file = (
                self.output_dir / f"{self.prefix}_{mon_group}_{aggregation_mode}.dl1.h5"
            )
            dl1_image_file = (
                pedestal_file if mon_group == "sky_pedestal_image" else flatfield_file
            )

            # Get configuration and prepare CLI arguments
            with open(mon_config) as yaml_file:
                pix_stats_config = yaml.safe_load(yaml_file)
                n_events = len(
                    read_table(
                        dl1_image_file,
                        path=f"{DL1_TEL_IMAGES_GROUP}/tel_{tel_id:03d}",
                    )
                )

                cli_argv = self._build_cli_argv(
                    dl1_image_file,
                    output_file,
                    tel_index,
                    aggregation_mode,
                    mon_group,
                    n_events,
                )

                # Run the PixelStatisticsCalculatorTool
                run_tool(
                    PixelStatisticsCalculatorTool(config=Config(pix_stats_config)),
                    argv=cli_argv,
                    cwd=self.output_dir,
                    raises=True,
                )

                # Update timestamps in the output file
                chunk_duration = self._get_chunk_duration(aggregation_mode, mon_group)
                self._update_aggregation_timestamps(
                    output_file, tel_id, mon_group, aggregation_mode, chunk_duration
                )

    def _build_cli_argv(
        self,
        dl1_image_file,
        output_file,
        tel_index,
        aggregation_mode,
        mon_group,
        n_events,
    ):
        """Build CLI arguments for PixelStatisticsCalculatorTool."""
        cli_argv = [
            f"--input_url={dl1_image_file}",
            f"--output_path={output_file}",
        ]
        if tel_index > 0:
            cli_argv.append("--append")

        # Add chunk size configuration based on aggregation mode
        chunk_config = self._get_chunk_config(aggregation_mode, mon_group, n_events)
        cli_argv.append(chunk_config)

        return cli_argv

    def _get_chunk_config(self, aggregation_mode, mon_group, n_events):
        """Get chunk size configuration string based on aggregation mode and monitoring group."""
        if aggregation_mode == "sims_single_chunk":
            return f"--SizeChunking.chunk_size={n_events}"
        elif aggregation_mode == "obslike_same_chunks":
            return f"--SizeChunking.chunk_size={n_events // 10}"
        elif aggregation_mode == "obslike_different_chunks":
            chunk_multipliers = {
                "sky_pedestal_image": 2,
                "flatfield_image": 1,
                "flatfield_peak_time": 5,
            }
            multiplier = chunk_multipliers.get(mon_group, 1)
            return f"--SizeChunking.chunk_size={multiplier * (n_events // 10)}"
        return ""

    def _get_chunk_duration(self, aggregation_mode, mon_group):
        """Get chunk duration based on aggregation mode and monitoring group."""
        if aggregation_mode == "sims_single_chunk":
            return 1000.0 * u.s
        elif aggregation_mode == "obslike_same_chunks":
            return 100.0 * u.s
        elif aggregation_mode == "obslike_different_chunks":
            durations = {
                "sky_pedestal_image": 200.0 * u.s,
                "flatfield_image": 100.0 * u.s,
                "flatfield_peak_time": 500.0 * u.s,
            }
            return durations.get(mon_group, 25.0 * u.s)
        return 25.0 * u.s

    def _update_aggregation_timestamps(
        self, output_file, tel_id, mon_group, aggregation_mode, chunk_duration
    ):
        """Update timestamps in the aggregation output file."""
        stats_aggregation_tab = read_table(
            output_file,
            path=f"{DL1_PIXEL_STATISTICS_GROUP}/{mon_group}/tel_{tel_id:03d}",
        )

        # Update chunk timestamps
        for chunk_nr in range(len(stats_aggregation_tab)):
            stats_aggregation_tab["time_start"][chunk_nr] = (
                self.REFERENCE_TIME
                + (1 / self.REFERENCE_TRIGGER_RATE).to(u.s)
                + chunk_nr * chunk_duration
            )
            stats_aggregation_tab["time_end"][chunk_nr] = (
                self.REFERENCE_TIME + (chunk_nr + 1) * chunk_duration
            )

        # Apply special adjustments for obslike_different_chunks mode
        if (
            aggregation_mode == "obslike_different_chunks"
            and mon_group == "sky_pedestal_image"
        ):
            stats_aggregation_tab["time_start"][0] -= 2 * u.s
            stats_aggregation_tab["time_end"][-1] += 2 * u.s

        # Write updated table back to file
        write_table(
            stats_aggregation_tab,
            output_file,
            f"{DL1_PIXEL_STATISTICS_GROUP}/{mon_group}/tel_{tel_id:03d}",
            overwrite=True,
        )

    def _create_monitoring_file(self, aggregation_mode):
        """Create monitoring file by merging aggregation output files."""
        output_files = [
            str(
                self.output_dir / f"{self.prefix}_{mon_group}_{aggregation_mode}.dl1.h5"
            )
            for mon_group in self.monitoring_groups
        ]
        monitoring_file = self.output_dir / f"{self.prefix}_{aggregation_mode}.dl1.h5"

        self.log.info(
            "Merge the following output files for the statistics aggregation: %s",
            ", ".join(str(f) for f in output_files),
        )

        run_tool(
            MergeTool(),
            argv=output_files
            + [
                f"--output={monitoring_file}",
                "--monitoring",
                "--attach-monitoring",
            ],
            cwd=self.output_dir,
            raises=True,
        )

        self.log.info(
            "The monitoring file was created in '%s' with the following groups: %s",
            monitoring_file,
            self.monitoring_groups.keys(),
        )

        # Mimic a real observation file if appropriate
        if aggregation_mode.startswith("obslike"):
            self._mimic_observation_file(monitoring_file)

    def _mimic_observation_file(self, monitoring_file):
        """Modify monitoring file to mimic a real observation file."""
        with tables.open_file(monitoring_file, "r+") as f:
            # Remove simulation group if present
            if SIMULATION_GROUP in f.root:
                f.remove_node(SIMULATION_GROUP, recursive=True)
                self.log.info(
                    "Removed the simulation group from the monitoring file '%s' to mimic a real observation file.",
                    monitoring_file,
                )

            # Update data category attribute
            data_category_string = "CTA PRODUCT DATA CATEGORY"
            if (
                data_category_string in f.root._v_attrs
                and f.root._v_attrs[data_category_string] == "Sim"
            ):
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", tables.NaturalNameWarning)
                    f.root._v_attrs[data_category_string] = "Other"
                self.log.info(
                    "Updated the '%s' attribute to 'Other' "
                    "in the monitoring file '%s' to mimic a real observation file.",
                    data_category_string,
                    monitoring_file,
                )

    def finish(self):
        """Shut down the tool."""
        self.log.info("Tool is shutting down")

    def _run_ctapipe_process_tool(self, input_data, output_file, config):
        """Produce the DL1A file containing the images."""
        # Run the ProcessorTool to create images
        run_tool(
            ProcessorTool(config=Config(config)),
            argv=[
                f"--input={input_data}",
                f"--output={output_file}",
                "--overwrite",
            ],
        )
        return output_file


def main():
    # Run the tool
    tool = CamCalibTestDataTool()
    tool.run()


if __name__ == "main":
    main()
