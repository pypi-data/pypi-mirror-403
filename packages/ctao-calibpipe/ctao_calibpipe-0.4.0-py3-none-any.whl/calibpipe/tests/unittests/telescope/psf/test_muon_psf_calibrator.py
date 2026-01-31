import itertools
from collections import namedtuple
from pathlib import Path

import numpy as np
import pytest
import yaml
from traitlets.config.loader import Config

from calibpipe.tools.muon_psf_calculator import CalculatePSFWithMuons

parameter_names = [
    "file_fixture_name",
]
Parameters = namedtuple("MuonTestParams", parameter_names)


class TestCalculatePSFWithMuons:
    """Test class for muon PSF analysis"""

    config_path = Path(__file__).parent.joinpath(
        "../../../../../../docs/source/user_guide/telescope/psf/configuration/"
    )

    @pytest.fixture(scope="class")
    def psf_config(self):
        with open(
            self.config_path.joinpath("psf_muon_configuration.yaml")
        ) as yaml_file:
            data = yaml.safe_load(yaml_file)

        return data

    @pytest.mark.parametrize(
        parameter_names,
        [
            Parameters(
                file_fixture_name="muon_lst_psf_mu_minus_nominal_mirror_alignment_file",
            ),
            Parameters(
                file_fixture_name="muon_lst_psf_mu_minus_20p_degraded_mirror_alignment_file",
            ),
            Parameters(
                file_fixture_name="muon_lst_psf_mu_minus_50p_degraded_mirror_alignment_file",
            ),
        ],
    )
    @pytest.mark.muon
    def test_muon_psf(
        self,
        request,
        file_fixture_name,
        psf_config,
        muon_lst_psf_mu_minus_nominal_mirror_alignment_file,
        muon_lst_psf_mu_minus_20p_degraded_mirror_alignment_file,
        muon_lst_psf_mu_minus_50p_degraded_mirror_alignment_file,
    ):
        """
        Test PSF measurements with muons.
        """

        psf_config["CalculatePSFWithMuons"]["input_url"] = str(
            request.getfixturevalue(file_fixture_name)
        )
        tool = CalculatePSFWithMuons(config=Config(psf_config))
        tool.setup()
        tool.start()

        # Extract results if processing succeeded
        containers = tool.tel_containers_map.get(1, [])
        if containers:
            slope_val = np.array([container.slope for container in containers])
            intercept_val = np.array([container.intercept for container in containers])

        assert ~np.isnan(slope_val).any()
        assert ~np.isnan(intercept_val).any()
        assert np.all(slope_val < 0)
        assert np.all(intercept_val > 0)

    @pytest.mark.muon
    @pytest.mark.verifies_usecase("UC-120-2.10")
    def test_analysis_of_variance_separation_power(
        self,
        psf_config,
        muon_lst_psf_mu_minus_nominal_mirror_alignment_file,
        muon_lst_psf_mu_minus_20p_degraded_mirror_alignment_file,
        muon_lst_psf_mu_minus_50p_degraded_mirror_alignment_file,
        cut_value_h0,
        cut_value_h1,
        separation_power_cut,
    ):
        """
        Analysis of variance (calculates variance ratio), to detect differences in mirror alignment.
        """

        file_list = [
            muon_lst_psf_mu_minus_nominal_mirror_alignment_file,
            muon_lst_psf_mu_minus_20p_degraded_mirror_alignment_file,
            muon_lst_psf_mu_minus_50p_degraded_mirror_alignment_file,
        ]

        slope = []
        intercept = []
        slope_err = []
        intercept_err = []

        for infile in file_list:
            psf_config["CalculatePSFWithMuons"]["input_url"] = str(infile)
            tool = CalculatePSFWithMuons(config=Config(psf_config))
            tool.setup()
            tool.start()

            containers = tool.tel_containers_map.get(1, [])
            if containers:
                slope.append(np.array([container.slope for container in containers]))
                intercept.append(
                    np.array([container.intercept for container in containers])
                )
                slope_err.append(
                    np.array([container.slope_err for container in containers])
                )
                intercept_err.append(
                    np.array([container.intercept_err for container in containers])
                )

        slope = np.concatenate(slope)
        intercept = np.concatenate(intercept)
        slope_err = np.concatenate(slope_err)
        intercept_err = np.concatenate(intercept_err)

        # This test shows that small variations in mirror misalignment cannot be detected.
        assert self.analysis_of_variance(slope, slope_err) < cut_value_h0
        assert self.analysis_of_variance(intercept, intercept_err) < cut_value_h0

        # This test shows that large variations in mirror misalignment can be detected.
        for comb in itertools.combinations([0, 1, 2], 2):
            assert (
                self.analysis_of_variance(
                    slope[np.array(comb)], slope_err[np.array(comb)]
                )
                > cut_value_h1
            )
            assert (
                self.analysis_of_variance(
                    intercept[np.array(comb)], intercept_err[np.array(comb)]
                )
                > cut_value_h1
            )
            assert (
                self.calculate_separation_power(
                    slope[np.array(comb)][0],
                    slope_err[np.array(comb)][0],
                    slope[np.array(comb)][1],
                    slope_err[np.array(comb)][1],
                )
                > separation_power_cut
            )
            assert (
                self.calculate_separation_power(
                    intercept[np.array(comb)][0],
                    intercept_err[np.array(comb)][0],
                    intercept[np.array(comb)][1],
                    intercept_err[np.array(comb)][1],
                )
                > separation_power_cut
            )

    def analysis_of_variance(self, val, err):
        """
        Analysis of variance function returns variance ratio values.

        Numerator: average variance between groups
        Denominator: average variance within the group
        To estimate the variance between groups, we use a new mean value, which is the average of two or more measurements.
        """

        return np.mean((np.mean(val) - val) ** 2 + err**2) / np.mean(err) ** 2

    def calculate_separation_power(self, val1, err1, val2, err2):
        """
        Calculate the separation power (in sigma) for two measurements with errors.
        """

        return np.abs(val1 - val2) / np.sqrt(err1**2 + err2**2)
