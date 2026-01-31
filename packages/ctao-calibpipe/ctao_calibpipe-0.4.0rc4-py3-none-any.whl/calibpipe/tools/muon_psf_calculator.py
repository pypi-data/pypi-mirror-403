"""Tool for calculating of optical PSF with muons."""

import numpy as np
from astropy.time import Time
from ctapipe.core.traits import Int
from ctapipe.io.hdf5dataformat import DL1_TEL_OPTICAL_PSF_GROUP

from calibpipe.telescope.psf.containers import OpticalPSFContainer
from calibpipe.tools.muon_calculator_base import (
    CalculateWithMuons,
    traits,
)


class CalculatePSFWithMuons(CalculateWithMuons):
    """Perform PSF calibration using muons for each telescope allowed in the EventSource."""

    name = traits.Unicode("PSFCalibration")
    description = __doc__

    # Name of the table directory for psf calibration
    group = DL1_TEL_OPTICAL_PSF_GROUP

    aliases = {
        ("i", "input"): "CalculatePSFWithMuons.input_url",
    }

    _sigma_clipping_metric = "mean"

    muonring_radius_fit_nbins = Int(
        default_value=10,
        allow_none=False,
        help="Number of muon ring radius bins within the specified fitting range.",
    ).tag(config=True)

    min_number_of_muon = Int(
        default_value=100,
        allow_none=False,
        help="Minimum number of muons per ring-radius bin required to be accepted for the fit.",
    ).tag(config=True)

    def _process_tel(self, tel_id):
        """Process muon data for a single telescope ID."""
        filtered_table = self._read_filter_sort_table(tel_id)

        muonring_radius_bins = np.linspace(
            np.nanmin(filtered_table["muonring_radius"]),
            np.nanmax(filtered_table["muonring_radius"]),
            self.muonring_radius_fit_nbins,
        )
        bins_right_edge = muonring_radius_bins[1:]
        bins_left_edge = muonring_radius_bins[:-1]
        bins_center = (bins_right_edge + bins_left_edge) / 2
        bins_width = bins_right_edge - bins_left_edge

        data_x = []
        data_y = []
        data_x_err = []
        data_y_err = []
        n_events_after_clipping = []

        for bin_right_edge, bin_left_edge, bin_center, bin_width in zip(
            bins_right_edge, bins_left_edge, bins_center, bins_width
        ):
            the_table = filtered_table[
                (filtered_table["muonring_radius"] >= bin_left_edge)
                & (filtered_table["muonring_radius"] < bin_right_edge)
            ]

            if len(the_table) > self.min_number_of_muon:
                chunk_stats = self.aggregator(
                    table=the_table,
                    col_name="muonefficiency_width",
                )

                n_events_after_clipping.append(chunk_stats["n_events"][0])

                data_y.append(chunk_stats[self._sigma_clipping_metric][0] / bin_center)

                data_y_err.append(
                    chunk_stats["std"][0] / np.sqrt(chunk_stats["n_events"][0])
                )

                data_x.append(bin_center)
                data_x_err.append(bin_width / 2)
            else:
                data_x.append(np.nan)
                data_x_err.append(np.nan)
                data_y.append(np.nan)
                data_y_err.append(np.nan)
                n_events_after_clipping.append(np.nan)

        data_to_fit = np.array(
            list(
                zip(
                    data_x,
                    data_y,
                    data_x_err,
                    data_y_err,
                )
            )
        )

        data_to_fit = data_to_fit[~np.isnan(data_to_fit).any(axis=1)]

        data_tot_err = np.sqrt(data_to_fit[:, 0] ** 2 + data_to_fit[:, 1] ** 2)

        # Fit polynomial of degree 1, also request covariance matrix
        fit_coeff, fit_cov = np.polyfit(
            data_to_fit[:, 0], data_to_fit[:, 1], 1, w=1 / data_tot_err**2, cov=True
        )

        data_y_fit = data_to_fit[:, 0] * fit_coeff[0] + fit_coeff[1]

        fit_errors = np.sqrt(np.diag(fit_cov))

        # Compute chi-square
        chi2 = np.sum(((data_to_fit[:, 1] - data_y_fit) / data_to_fit[:, 3]) ** 2)

        # Degrees of freedom = number of points - number of parameters
        ndf = len(data_to_fit[:, 1]) - len(fit_coeff)

        # Reduced chi-square
        chi2_red = chi2 / ndf

        return [
            OpticalPSFContainer(
                obs_id=filtered_table["obs_id"],
                method=self.METHOD,
                slope=fit_coeff[0],
                intercept=fit_coeff[1],
                slope_err=fit_errors[0],
                intercept_err=fit_errors[1],
                chi2=chi2_red,
                time_start=Time(filtered_table["time"][0], format="mjd", scale="tai"),
                time_end=Time(filtered_table["time"][-1], format="mjd", scale="tai"),
            )
        ]


def main():
    """Run the app."""
    tool = CalculatePSFWithMuons()
    tool.run()
