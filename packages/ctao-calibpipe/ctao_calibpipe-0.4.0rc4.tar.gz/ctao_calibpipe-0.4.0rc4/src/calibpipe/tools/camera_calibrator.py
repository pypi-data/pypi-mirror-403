"""Calculate camera calibration coefficients using the FFactor method."""

import astropy.units as u
import h5py
import numpy as np
from astropy.table import Column, Table
from astropy.time import Time
from ctapipe.core import Tool, ToolConfigurationError
from ctapipe.core.traits import (
    AstroQuantity,
    Bool,
    Float,
    Int,
    List,
    Path,
    classes_with_traits,
)
from ctapipe.io import HDF5MonitoringSource, write_table
from ctapipe.io.hdf5dataformat import (
    DL1_CAMERA_COEFFICIENTS_GROUP,
)
from ctapipe.monitoring import (
    StdOutlierDetector,
)

__all__ = [
    "CameraCalibratorTool",
    "NpeStdOutlierDetector",
]


class NpeStdOutlierDetector(StdOutlierDetector):
    """
    Detect outliers based on the deviation from the expected standard deviation of the number of photoelectrons.

    The clipping interval to set the thresholds for detecting outliers is computed by multiplying
    the configurable factors and the expected standard deviation of the number of photoelectrons. The
    expected standard deviation of the number of photoelectrons is calculated based on the median number
    of photoelectrons and the number of events.
    """

    n_events = Int(
        default_value=2500,
        help="Number of events used for the chunk-wise aggregation of the statistic values of the calibration data.",
    ).tag(config=True)

    relative_qe_dispersion = Float(
        0.07,
        help="Relative (effective) quantum efficiency dispersion of PMs over the camera",
    ).tag(config=True)

    linear_noise_coeff = List(
        trait=Float(),
        default_value=[1.79717813, 1.72458305],
        minlen=1,
        maxlen=2,
        help=(
            "Linear noise coefficients [high gain, low gain] or [single gain] obtained with a fit of the std of the "
            "LST-1 filter scan taken on 2023/05/10."
        ),
    ).tag(config=True)

    linear_noise_offset = List(
        trait=Float(),
        default_value=[0.0231544, -0.00162036639],
        minlen=1,
        maxlen=2,
        help=(
            "Linear noise offsets [high gain, low gain] or [single gain] obtained with a fit of the std of the "
            "LST-1 filter scan taken on 2023/05/10."
        ),
    ).tag(config=True)

    quadratic_noise_coeff = List(
        trait=Float(),
        default_value=[0.000499670969, 0.00142218],
        minlen=1,
        maxlen=2,
        help=(
            "Quadratic noise coefficients [high gain, low gain] or [single gain] obtained with a fit of the std of the "
            "LST-1 filter scan taken on 2023/05/10."
        ),
    ).tag(config=True)

    quadratic_noise_offset = List(
        trait=Float(),
        default_value=[0.0000249034290, 0.0001207],
        minlen=1,
        maxlen=2,
        help=(
            "Quadratic noise offsets [high gain, low gain] or [single gain] obtained with a fit of the std of the LST-1 "
            "LST-1 filter scan taken on 2023/05/10."
        ),
    ).tag(config=True)

    def __call__(self, column):
        r"""
        Detect outliers based on the deviation from the expected standard deviation of the number of photoelectrons.

        The clipping interval to set the thresholds for detecting outliers is computed by multiplying
        the configurable factors and the expected standard deviation of the number of photoelectrons
        (npe) over the camera. The expected standard deviation of the estimated npe is given by
        ``std_pe_mean = \frac{std_npe}{\sqrt{n_events + (relative_qe_dispersion \cdot npe)^2}}`` where the
        relative_qe_dispersion is mainly due to different detection QE among PMs. However, due to
        the systematics correction associated to the B term, a linear and quadratic noise component
        must be added, these components depend on the sample statistics (n_events).

        Parameters
        ----------
        column : astropy.table.Column
            Column of the calculated the number of photoelectrons using the chunk-wise aggregated statistic values
            of the calibration data of shape (n_entries, n_channels, n_pixels).

        Returns
        -------
        outliers : np.ndarray of bool
            The mask of outliers of shape (n_entries, n_channels, n_pixels) based on the deviation
            from the expected standard deviation of the number of photoelectrons.
        """
        # Calculate the median number of photoelectrons
        npe_median = np.nanmedian(column, axis=2)
        # Calculate the basic variance
        basic_variance = (
            npe_median / self.n_events + (self.relative_qe_dispersion * npe_median) ** 2
        )
        # Calculate the linear noise term
        linear_term = (
            self.linear_noise_coeff / (np.sqrt(self.n_events))
            + self.linear_noise_offset
        )
        # Calculate the quadratic noise term
        quadratic_term = (
            self.quadratic_noise_coeff / (np.sqrt(self.n_events))
            + self.quadratic_noise_offset
        )
        # Calculate the added variance
        added_variance = (linear_term * npe_median) ** 2 + (
            quadratic_term * npe_median
        ) ** 2
        # Calculate the total standard deviation of the number of photoelectrons
        npe_std = np.sqrt(basic_variance + added_variance)
        # Detect outliers based on the deviation of the standard deviation distribution
        deviation = column - npe_median[:, :, np.newaxis]
        outliers = np.logical_or(
            deviation < self.std_range_factors[0] * npe_std[:, :, np.newaxis],
            deviation > self.std_range_factors[1] * npe_std[:, :, np.newaxis],
        )
        return outliers


class CameraCalibratorTool(Tool):
    """Calculate camera calibration coefficients using the FFactor method."""

    name = "calibpipe-calculate-camcalib-coefficients"
    description = "Calculate camera calibration coefficients using the FFactor method"

    examples = """
    To calculate camera calibration coefficients using the FFactor method, run:

    > calibpipe-calculate-camcalib-coefficients --input_url monitoring.h5 --overwrite
    """

    timestamp_tolerance = AstroQuantity(
        default_value=u.Quantity(1.0, u.second),
        physical_type=u.physical.time,
        help="Time difference in seconds to consider two timestamps equal.",
    ).tag(config=True)

    faulty_pixels_fraction = Float(
        default_value=0.1,
        allow_none=True,
        help="Minimum fraction of faulty camera pixels to identify regions of trouble.",
    ).tag(config=True)

    # TODO These parameters are temporary and should be read from the metadata
    systematic_correction_path = Path(
        default_value=None,
        allow_none=True,
        exists=True,
        directory_ok=False,
        help=(
            "Temp Fix: Path to systematic correction file "
            "for additional noise component that is proportional to the signal amplitude "
        ),
    ).tag(config=True)

    # TODO These parameters are temporary and should be read from the metadata
    squared_excess_noise_factor = Float(
        1.222, help="Temp Fix: Excess noise factor squared: 1+ Var(gain)/Mean(Gain)**2"
    ).tag(config=True)

    # TODO These parameters are temporary and should be read from the metadata
    window_width = Int(
        12,
        help="Temp Fix: Width of the window used for the image extraction",
    ).tag(config=True)

    overwrite = Bool(
        help="Overwrite the tables of the camera calibration coefficients if they exist"
    ).tag(config=True)

    aliases = {
        ("i", "input_url"): "HDF5MonitoringSource.input_files",
    }

    flags = {
        "overwrite": (
            {"CameraCalibratorTool": {"overwrite": True}},
            "Overwrite existing tables of the camera calibration coefficients",
        ),
    }

    classes = classes_with_traits(HDF5MonitoringSource) + classes_with_traits(
        NpeStdOutlierDetector
    )

    def setup(self):
        """Set up the tool.

        - Set up the monitoring source.
        - Load the systematic correction term B.
        - Configure the outlier detector for the expected standard deviation of the number of photoelectrons.
        """
        # Set up the MonitoringSource
        self.mon_source = self.enter_context(HDF5MonitoringSource(parent=self))
        # Enforce only one input file
        if len(self.mon_source.input_files) != 1:
            raise ToolConfigurationError(
                "CameraCalibratorTool requires exactly one input file."
            )
        # Check if the monitoring source has aggregated pixel statistics
        if not self.mon_source.has_pixel_statistics:
            raise OSError(
                f"Monitoring source '{self.mon_source.input_files[0]}' does not have required pixel statistics."
            )
        # Check if camera calibration coefficients are available in the monitoring source
        # and break if the overwrite is not set. Better than letting the tool run till the end
        # and then break while it tries to write the table.
        if self.mon_source.has_camera_coefficients and self.overwrite is False:
            raise ToolConfigurationError(
                "CameraCalibratorTool: Camera calibration coefficients are already "
                f"available in the monitoring source '{self.mon_source.input_files[0]}'. "
                "Use --overwrite to overwrite the existing tables."
            )
        # Load systematic correction term B
        self.quadratic_term = 0
        if self.systematic_correction_path is not None:
            with h5py.File(self.systematic_correction_path, "r") as hf:
                self.quadratic_term = np.array(hf["B_term"])
        # Load the outlier detector for the expected standard deviation of the number of photoelectrons
        if "NpeStdOutlierDetector" in self.config:
            self.log.info(
                "Applying outlier detection 'NpeStdOutlierDetector' "
                "based on the deviation from the expected standard "
                "deviation of the number of photoelectrons."
            )
            self.outlier_detector = NpeStdOutlierDetector(
                parent=self, subarray=self.mon_source.subarray
            )
        else:
            self.log.info(
                "No outlier detection applied. 'NpeStdOutlierDetector' not in config."
            )
            self.outlier_detector = None

    def start(self):
        """Iterate over the telescope IDs and calculate the camera calibration coefficients."""
        self.camcalib_table = {}
        # Iterate over the telescope IDs and calculate the camera calibration coefficients
        for tel_id in self.mon_source.subarray.tel_ids:
            # Get the unique timestamp(s) from the tables
            unique_timestamps = self._get_unique_timestamps(
                *self.mon_source.pixel_statistics[tel_id].values()
            )
            # Get the camera monitoring container from the monitoring source
            if self.mon_source.is_simulation:
                cam_mon_con = self.mon_source.get_camera_monitoring_container(tel_id)
            else:
                cam_mon_con = self.mon_source.get_camera_monitoring_container(
                    tel_id=tel_id,
                    time=unique_timestamps,
                    timestamp_tolerance=self.timestamp_tolerance,
                )
            # Concatenate the outlier masks
            outlier_mask = np.logical_or.reduce(
                [
                    np.isnan(cam_mon_con.pixel_statistics[name]["median"])
                    for name in cam_mon_con.pixel_statistics.keys()
                ]
            )

            # Extract calibration coefficients with F-factor method
            # Calculate the signal
            signal = np.array(
                cam_mon_con.pixel_statistics.flatfield_image["median"]
            ) - np.array(cam_mon_con.pixel_statistics.pedestal_image["median"])
            # Calculate the gain with the excess noise factor must be known from elsewhere
            gain = (
                np.divide(
                    np.array(cam_mon_con.pixel_statistics.flatfield_image["std"]) ** 2
                    - np.array(cam_mon_con.pixel_statistics.pedestal_image["std"]) ** 2,
                    self.squared_excess_noise_factor * signal,
                )
                - self.quadratic_term**2 * signal / self.squared_excess_noise_factor
            )

            # Calculate the number of photoelectrons
            n_pe = np.divide(signal, gain)
            # Absolute gain calibration
            npe_median = np.nanmedian(n_pe, axis=-1, keepdims=True)

            data, units = {}, {}
            # Set the time column to the unique timestamps
            data["time"] = unique_timestamps
            data["factor"] = np.divide(npe_median, signal)
            # Pedestal offset
            # TODO: read window_width from metadata
            data["pedestal_offset"] = (
                np.array(cam_mon_con.pixel_statistics.pedestal_image["median"])
                / self.window_width
            )
            # Relative time calibration
            data["time_shift"] = np.array(
                cam_mon_con.pixel_statistics.flatfield_peak_time["median"]
            ) - np.nanmedian(
                np.array(cam_mon_con.pixel_statistics.flatfield_peak_time["median"]),
                axis=-1,
                keepdims=True,
            )
            # Add a new axis if needed
            if unique_timestamps.isscalar:
                outlier_mask = outlier_mask[np.newaxis, ...]
                for key in data.keys():
                    data[key] = data[key][np.newaxis, ...]

            # Apply outlier detection if selected
            if self.outlier_detector is not None:
                # Add a new axis if needed
                if n_pe.ndim == 2:
                    n_pe = n_pe[np.newaxis, ...]

                npe_outliers = self.outlier_detector(Column(data=n_pe, name="n_pe"))
                # Stack the outlier masks with the npe outlier mask
                outlier_mask = np.logical_or(
                    outlier_mask,
                    npe_outliers,
                )
            # Append the column of the new outlier mask
            data["outlier_mask"] = outlier_mask
            # Check if the camera has two gain channels
            if outlier_mask.shape[1] == 2:
                # Combine the outlier mask of both gain channels
                outlier_mask = np.logical_or.reduce(outlier_mask, axis=1)
            # Calculate the fraction of faulty pixels over the camera
            faulty_pixels = (
                np.count_nonzero(outlier_mask, axis=-1) / np.shape(outlier_mask)[-1]
            )
            # Check for valid chunks if the predefined threshold ``faulty_pixels_fraction``
            # is not exceeded and append the is_valid column
            data["is_valid"] = faulty_pixels < self.faulty_pixels_fraction

            # Create the table for the camera calibration coefficients
            self.camcalib_table[tel_id] = Table(data, units=units)

    def finish(self):
        """Write the camera calibration coefficients to the output file."""
        # Write the camera calibration coefficients and their outlier mask
        # to the output file for each telescope
        for tel_id in self.mon_source.subarray.tel_ids:
            write_table(
                self.camcalib_table[tel_id],
                self.mon_source.input_files[0],
                f"{DL1_CAMERA_COEFFICIENTS_GROUP}/tel_{tel_id:03d}",
                overwrite=self.overwrite,
            )
            self.log.info(
                "DL1 monitoring data was stored in '%s' under '%s'",
                self.mon_source.input_files[0],
                f"{DL1_CAMERA_COEFFICIENTS_GROUP}/tel_{tel_id:03d}",
            )
        self.log.info("Tool is shutting down")

    def _get_unique_timestamps(
        self, pedestal_image_table, flatfield_image_table, flatfield_peak_time_table
    ):
        """
        Extract unique timestamps from the given tables.

        This method collects the start and end timestamps from the provided
        chunks in the pedestal_image, flatfield_image, and flatfield_peak_time
        tables. It then sorts the timestamps and filters them based on the
        specified timestamp tolerance.

        Parameters
        ----------
        pedestal_image_table : astropy.table.Table
            Table containing pedestal image data.
        flatfield_image_table : astropy.table.Table
            Table containing flatfield image data.
        flatfield_peak_time_table : astropy.table.Table
            Table containing flatfield peak time data.

        Returns
        -------
        unique_timestamps : astropy.time.Time
            Unique timestamps sorted and filtered based on the timestamp tolerance.
        """
        # Check if there is a single chunk for all the tables
        if (
            all(
                len(table) == 1
                for table in (
                    pedestal_image_table,
                    flatfield_image_table,
                    flatfield_peak_time_table,
                )
            )
            or self.mon_source.is_simulation
        ):
            # If there is only a single chunk, return the unique timestamp(s) to the start time
            return Time(
                min(
                    pedestal_image_table["time_start"][0],
                    flatfield_image_table["time_start"][0],
                )
            )
        # Collect all start and end times in MJD (days)
        timestamps = []
        for mon_table in (
            pedestal_image_table,
            flatfield_image_table,
            flatfield_peak_time_table,
        ):
            # Append timestamps from the start and end of chunks
            timestamps.append(mon_table["time_start"])
            timestamps.append(mon_table["time_end"])
        # Sort the timestamps
        timestamps = np.concatenate(timestamps)
        timestamps.sort()
        # Filter the timestamps based on the timestamp tolerance
        unique_timestamps = [timestamps[-1]]
        for t in reversed(timestamps[:-1]):
            if (unique_timestamps[-1] - t) > self.timestamp_tolerance:
                unique_timestamps.append(t)
        unique_timestamps.reverse()
        # Ensure that the first unique timestamp is set to the first timestamp of the provided
        # tables if within the timestamp tolerance. It might be that the first chunk starts
        # before the first unique timestamp if they are in the timestamp tolerance.
        if (min(timestamps) - unique_timestamps[0]) < self.timestamp_tolerance:
            unique_timestamps[0] = min(timestamps)
        return Time(unique_timestamps)


def main():
    # Run the tool
    tool = CameraCalibratorTool()
    tool.run()


if __name__ == "main":
    main()
