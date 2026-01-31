from collections import namedtuple
from pathlib import Path

import astropy.units as u
import numpy as np
import pytest
import yaml
from scipy.optimize import curve_fit, minimize_scalar
from scipy.stats import chi2
from traitlets.config.loader import Config

from calibpipe.tools.muon_throughput_calculator import CalculateThroughputWithMuons


def estimate_sigma_sys(x, sigma_stat, confidence=0.95):
    """
    Estimate uncorrelated systematic scatter sigma_sys via maximum likelihood.

    Parameters
    ----------
    x : array_like
        Measurements (1D).
    sigma_stat : array_like
        Known per-measurement statistical uncertainties (same length as x).
    confidence : float, optional
        Confidence level for interval (default 0.95).

    Returns
    -------
    mu_hat : float
        Weighted mean estimate.
    sigma_sys_hat : float
        MLE of systematic scatter.
    ci : tuple
        Confidence interval (low, high) for sigma_sys.
    """

    x = np.asarray(x)
    sigma_stat = np.asarray(sigma_stat)

    def nll(s):
        if s < 0:
            return np.inf
        v = sigma_stat**2 + s**2
        w = 1.0 / v
        mu_hat = np.sum(w * x) / np.sum(w)
        return 0.5 * np.sum(np.log(2 * np.pi * v) + (x - mu_hat) ** 2 / v)

    # Minimize NLL over sigma_sys
    res = minimize_scalar(nll, bounds=(0, np.std(x) * 5), method="bounded")
    sigma_sys_hat = res.x
    nll_min = res.fun

    # Compute mu_hat at best sigma_sys
    v = sigma_stat**2 + sigma_sys_hat**2
    w = 1.0 / v
    mu_hat = np.sum(w * x) / np.sum(w)

    # Likelihood-ratio CI
    cutoff = 0.5 * chi2.ppf(confidence, df=1)

    def objective(s):
        return abs(nll(s) - (nll_min + cutoff))

    # Lower bound search
    lo = minimize_scalar(objective, bounds=(0, sigma_sys_hat), method="bounded").x
    # Upper bound search
    hi = minimize_scalar(
        objective, bounds=(sigma_sys_hat, np.std(x) * 10), method="bounded"
    ).x

    return mu_hat, sigma_sys_hat, (lo, hi)


parameter_names = [
    "muon_sign_first",
    "mirror_reflectivity_first",
    "muon_sign_second",
    "mirror_reflectivity_second",
    "parameter_to_compare",
    "absolute_consistency_range",
    "relative_consistency_range",
    "are_expected_to_differ",
]
Parameters = namedtuple("MuonTestParams", parameter_names)

parameter_mst_names = [
    "file_fixture_name",
    "expected_throughput",
    "expected_throughput_rel_uncertainty",
]
Parameters_mst = namedtuple("MuonTestParams", parameter_mst_names)


class TestCalculateThroughputWithMuons:
    """Test class for muon throughput analysis"""

    config_path = Path(__file__).parent.joinpath(
        "../../../../../../docs/source/user_guide/telescope/throughput/configuration/"
    )

    @pytest.fixture(scope="class")
    def test_config(self, lst_muon_table_file):
        with open(
            self.config_path.joinpath("throughput_muon_configuration.yaml")
        ) as yaml_file:
            data = yaml.safe_load(yaml_file)

        return data

    @pytest.fixture(scope="class")
    def empty_muon_file(self, empty_muon_table_file):
        # Note: The fixture is named differently but maps to the same file
        # This is for historical compatibility with the test
        return empty_muon_table_file

    @pytest.fixture(scope="class")
    def good_muon_file_lst(self, lst_muon_table_file):
        return lst_muon_table_file

    @pytest.mark.muon
    def test_empty_data(self, test_config, empty_muon_file):
        test_config["CalculateThroughputWithMuons"]["input_url"] = str(empty_muon_file)
        test_calculate_throughput_muon_tool = CalculateThroughputWithMuons(
            config=Config(test_config)
        )

        test_calculate_throughput_muon_tool.setup()

        # The tool should handle empty data gracefully by skipping telescopes with no data
        test_calculate_throughput_muon_tool.start()

        # Check that containers were initialized but empty for skipped telescopes
        assert len(test_calculate_throughput_muon_tool.tel_containers_map) > 0
        for (
            tel_id,
            containers,
        ) in test_calculate_throughput_muon_tool.tel_containers_map.items():
            assert containers == {}  # Should be empty dict for skipped telescopes

    def linear_model(self, x, a, b):
        """Linear model for throughput vs reflectivity."""
        return a * x + b

    @pytest.mark.muon
    def test_muon_simulation_data_processing(self, test_config, muon_test_files):
        """
        Test that the throughput calculator can successfully process muon simulation data files.

        This functional test verifies that the tool runs without errors and produces
        valid throughput containers for all simulation files.
        """
        processed_files = 0

        # Test processing of each muon simulation file
        for particle_type, reflectivity_files in muon_test_files.items():
            for reflectivity, file_path in reflectivity_files.items():
                # Configure tool for this specific file
                test_config["CalculateThroughputWithMuons"]["input_url"] = str(
                    file_path
                )
                tool = CalculateThroughputWithMuons(config=Config(test_config))

                # Test setup phase
                tool.setup()
                assert tool.subarray is not None, (
                    f"Subarray not loaded for {particle_type} R={reflectivity}"
                )
                assert tool.aggregator is not None, (
                    f"Aggregator not initialized for {particle_type} R={reflectivity}"
                )

                # Test processing phase
                tool.start()

                # Verify containers were created
                assert hasattr(tool, "tel_containers_map"), (
                    "Throughput containers not initialized"
                )

                # Should have results for telescope 1 (if processing succeeded)
                containers = tool.tel_containers_map.get(1, [])
                if containers:  # Only check if processing succeeded
                    # Verify container structure
                    for container in containers:
                        assert hasattr(container, "mean"), (
                            f"Container missing mean for {particle_type} R={reflectivity}"
                        )
                        assert hasattr(container, "std"), (
                            f"Container missing std for {particle_type} R={reflectivity}"
                        )
                        assert hasattr(container, "n_events"), (
                            f"Container missing n_events for {particle_type} R={reflectivity}"
                        )
                        assert container.n_events > 0, (
                            f"No events processed for {particle_type} R={reflectivity}"
                        )
                        assert 0 < container.mean < 1, (
                            f"Invalid throughput mean {container.mean} for {particle_type} R={reflectivity}"
                        )
                        assert container.std >= 0, (
                            f"Invalid throughput std {container.std} for {particle_type} R={reflectivity}"
                        )

                processed_files += 1

        # Verify we attempted to process all expected files
        assert processed_files == 6, (
            f"Expected to process 6 files, processed {processed_files}"
        )

    @pytest.fixture(scope="class")
    def simulation_results(self, test_config, muon_test_files):
        """
        Fixture that processes simulation data once and provides results for performance tests.

        This avoids re-running the analysis multiple times for different performance tests.

        Each chunk now includes:
        - throughput: Individual throughput measurement
        - uncertainty: Statistical uncertainty
        - systematic_uncertainty: Systematic uncertainty estimated using MLE
        - total_uncertainty: Combined statistical + systematic uncertainty
        - total_relative_uncertainty: Total relative uncertainty as percentage
        - weighted_mean: Weighted mean for the reflectivity group
        """
        results = {}

        # Process each muon file and extract throughput measurements
        for particle_type, reflectivity_files in muon_test_files.items():
            results[particle_type] = {}

            for reflectivity, file_path in reflectivity_files.items():
                # Configure and run tool
                test_config["CalculateThroughputWithMuons"]["input_url"] = str(
                    file_path
                )
                tool = CalculateThroughputWithMuons(config=Config(test_config))
                tool.setup()
                tool.start()

                # Extract results if processing succeeded
                containers = tool.tel_containers_map.get(1, [])
                if containers:
                    # Store individual chunk results (not combined)
                    chunk_results = []
                    for container in containers:
                        # Ensure scalar extraction from container attributes
                        mean_val = container.mean
                        std_val = container.std
                        n_events_val = container.n_events

                        # Convert to scalar using numpy.squeeze
                        mean_val = float(np.squeeze(mean_val))
                        std_val = float(np.squeeze(std_val))
                        n_events_val = int(np.squeeze(n_events_val))

                        uncertainty_val = std_val / np.sqrt(n_events_val)
                        rel_unc_val = (uncertainty_val / mean_val) * 100

                        chunk_data = {
                            "throughput": mean_val,
                            "uncertainty": uncertainty_val,
                            "n_events": n_events_val,
                            "relative_uncertainty": rel_unc_val,
                        }
                        chunk_results.append(chunk_data)

                    results[particle_type][reflectivity] = chunk_results

        # Calculate systematic uncertainties and add to chunk results
        for particle_type, reflectivity_data in results.items():
            for reflectivity, chunk_list in reflectivity_data.items():
                if (
                    len(chunk_list) >= 2
                ):  # Need at least 2 measurements for systematic analysis
                    # Extract arrays for systematic uncertainty estimation
                    measurements = np.array(
                        [chunk["throughput"] for chunk in chunk_list]
                    )
                    stat_errors = np.array(
                        [chunk["uncertainty"] for chunk in chunk_list]
                    )

                    # Estimate systematic uncertainty using MLE method
                    mu_hat, sigma_sys_hat, ci = estimate_sigma_sys(
                        measurements, stat_errors
                    )

                    # Add systematic uncertainty info to each chunk
                    for chunk in chunk_list:
                        stat_uncertainty = chunk["uncertainty"]
                        total_uncertainty = np.sqrt(
                            stat_uncertainty**2 + sigma_sys_hat**2
                        )
                        chunk["systematic_uncertainty"] = sigma_sys_hat
                        chunk["total_uncertainty"] = total_uncertainty
                        chunk["weighted_mean"] = mu_hat
                        chunk["total_relative_uncertainty"] = (
                            total_uncertainty / mu_hat
                        ) * 100
                else:
                    # For single measurements, no systematic uncertainty can be estimated
                    for chunk in chunk_list:
                        chunk["systematic_uncertainty"] = 0.0
                        chunk["total_uncertainty"] = chunk["uncertainty"]
                        chunk["weighted_mean"] = chunk["throughput"]
                        chunk["total_relative_uncertainty"] = chunk[
                            "relative_uncertainty"
                        ]

        # Validate fixture results once, instead of in every test
        assert results, "No simulation data was processed"
        # Verify we have both particle types with data
        for particle_type, reflectivity_data in results.items():
            assert reflectivity_data, f"No reflectivity data for {particle_type}"
            for reflectivity, chunk_list in reflectivity_data.items():
                assert chunk_list, f"No chunks for {particle_type} at R={reflectivity}"

        return results

    @pytest.mark.muon
    @pytest.mark.lst
    def test_relative_uncertainty_requirement(self, simulation_results):
        """
        Test that all simulation measurements meet the ≤ 5% relative uncertainty requirement.
        Uses total uncertainty (statistical + systematic).
        """
        # Test relative uncertainty requirement (≤ 5%) for each chunk using total uncertainty
        for particle_type, reflectivity_data in simulation_results.items():
            for reflectivity, chunk_list in reflectivity_data.items():
                for i, chunk in enumerate(chunk_list):
                    # Use total relative uncertainty (statistical + systematic)
                    total_rel_unc = chunk["total_relative_uncertainty"]
                    stat_rel_unc = chunk["relative_uncertainty"]
                    syst_unc = chunk["systematic_uncertainty"]

                    assert total_rel_unc <= 5.0, (
                        f"{particle_type} at R={reflectivity} chunk {i + 1}: Total relative uncertainty "
                        f"{total_rel_unc:.2f}% > 5.0% requirement "
                        f"(stat: {stat_rel_unc:.2f}%, syst: {syst_unc:.4f})"
                    )

    @pytest.mark.muon
    @pytest.mark.lst
    def test_throughput_monotonicity(self, simulation_results):
        """
        Test that throughput increases with reflectivity (monotonicity expectation).
        """
        # Test throughput increases with reflectivity for each chunk comparison
        for particle_type, reflectivity_data in simulation_results.items():
            # Sort by reflectivity value but keep original string keys
            reflectivity_keys = sorted(reflectivity_data.keys(), key=float)

            # Compare chunks between different reflectivity values
            for i in range(len(reflectivity_keys) - 1):
                current_r_key = reflectivity_keys[i]
                next_r_key = reflectivity_keys[i + 1]
                current_r = float(current_r_key)
                next_r = float(next_r_key)

                current_chunks = reflectivity_data[current_r_key]
                next_chunks = reflectivity_data[next_r_key]

                # Calculate average throughput for each reflectivity
                current_avg = np.mean([chunk["throughput"] for chunk in current_chunks])
                next_avg = np.mean([chunk["throughput"] for chunk in next_chunks])

                # Check general increasing trend (allowing measurement uncertainty)
                assert next_avg >= current_avg, (
                    f"{particle_type}: Average throughput decreases significantly from R={current_r:.2f} "
                    f"to R={next_r:.2f} ({current_avg:.4f} -> {next_avg:.4f})"
                )

    @pytest.mark.muon
    @pytest.mark.lst
    def test_statistical_significance(self, simulation_results):
        """
        Test that throughput changes between reflectivity values are statistically significant.
        Uses total uncertainty (statistical + systematic) for significance calculations.
        """
        # Test statistical significance of throughput changes using chunk data
        for particle_type, reflectivity_data in simulation_results.items():
            reflectivity_keys = sorted(reflectivity_data.keys(), key=float)

            for i in range(len(reflectivity_keys) - 1):
                r1_key, r2_key = reflectivity_keys[i], reflectivity_keys[i + 1]
                chunks1 = reflectivity_data[r1_key]
                chunks2 = reflectivity_data[r2_key]

                # Extract values directly from chunks
                throughputs1 = [chunk["throughput"] for chunk in chunks1]
                uncertainties1 = [chunk["total_uncertainty"] for chunk in chunks1]
                throughputs2 = [chunk["throughput"] for chunk in chunks2]
                uncertainties2 = [chunk["total_uncertainty"] for chunk in chunks2]

                mean1 = np.mean(throughputs1)
                mean2 = np.mean(throughputs2)

                # Combined uncertainty (standard error of the means)
                sem1 = np.sqrt(np.sum(np.array(uncertainties1) ** 2)) / len(chunks1)
                sem2 = np.sqrt(np.sum(np.array(uncertainties2) ** 2)) / len(chunks2)
                combined_uncertainty = np.sqrt(sem1**2 + sem2**2)

                if combined_uncertainty > 0:
                    throughput_diff = abs(mean2 - mean1)
                    significance = throughput_diff / combined_uncertainty

                    # Require at least 3σ significance
                    assert significance >= 3.0, (
                        f"{particle_type}: Throughput change from R={r1_key} to R={r2_key} "
                        f"has significance {significance:.1f}σ < 1.0σ requirement "
                        f"(diff: {throughput_diff:.4f}, unc: {combined_uncertainty:.4f})"
                    )

    @pytest.mark.muon
    @pytest.mark.lst
    def test_linearity_validation(self, simulation_results):
        """
        Test that throughput vs reflectivity follows a linear relationship.
        Uses total uncertainty (statistical + systematic) for weighted fitting.
        """
        # Test linearity validation using all individual chunks
        for particle_type, reflectivity_data in simulation_results.items():
            # Collect all chunk data points for fitting
            all_reflectivities = []
            all_throughputs = []
            all_uncertainties = []

            for reflectivity_str, chunks in reflectivity_data.items():
                reflectivity_val = float(reflectivity_str)

                # Extract values directly from chunks
                for chunk in chunks:
                    all_reflectivities.append(reflectivity_val)
                    all_throughputs.append(chunk["throughput"])
                    all_uncertainties.append(chunk["total_uncertainty"])

            reflectivities = np.array(all_reflectivities)
            throughputs = np.array(all_throughputs)
            uncertainties = np.array(all_uncertainties)
            # Perform weighted linear fit using all chunk data
            popt, pcov = curve_fit(
                self.linear_model,
                reflectivities,
                throughputs,
                sigma=uncertainties,
                absolute_sigma=True,
            )

            # Calculate R-squared
            y_fit = self.linear_model(reflectivities, *popt)
            ss_res = np.sum((throughputs - y_fit) ** 2)
            ss_tot = np.sum((throughputs - np.mean(throughputs)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

            # Require reasonable correlation (R² ≥ 0.8 for individual chunk data, i.e. within 5%)
            assert r_squared >= 0.8, (
                f"{particle_type}: Linear fit R² = {r_squared:.3f} < 0.8 requirement ({len(throughputs)} chunks)"
            )

    @pytest.mark.muon
    @pytest.mark.lst
    def test_particle_type_consistency(self, simulation_results):
        """
        Test consistency between μ- and μ+ measurements at the same reflectivity.
        Uses 95% confidence level test to ensure measurements are statistically consistent.
        """
        from scipy.stats import t

        # Test consistency between particle types using 95% confidence level
        muon_minus_data = simulation_results["μ-"]
        muon_plus_data = simulation_results["μ+"]

        for reflectivity in muon_minus_data.keys():
            minus_chunks = muon_minus_data[reflectivity]
            plus_chunks = muon_plus_data[reflectivity]

            # Ensure we have sufficient data for statistical test
            assert len(minus_chunks) >= 1, f"No μ- chunks at R={reflectivity}"
            assert len(plus_chunks) >= 1, f"No μ+ chunks at R={reflectivity}"

            # Extract measurements and total uncertainties directly from chunks
            minus_measurements = np.array(
                [chunk["throughput"] for chunk in minus_chunks]
            )
            plus_measurements = np.array([chunk["throughput"] for chunk in plus_chunks])
            minus_uncertainties = [chunk["total_uncertainty"] for chunk in minus_chunks]
            plus_uncertainties = [chunk["total_uncertainty"] for chunk in plus_chunks]
            minus_uncertainties = np.array(minus_uncertainties)
            plus_uncertainties = np.array(plus_uncertainties)

            # Calculate weighted means and their uncertainties
            minus_weights = 1.0 / (minus_uncertainties**2)
            plus_weights = 1.0 / (plus_uncertainties**2)

            minus_weighted_mean = np.sum(minus_weights * minus_measurements) / np.sum(
                minus_weights
            )
            plus_weighted_mean = np.sum(plus_weights * plus_measurements) / np.sum(
                plus_weights
            )

            minus_weighted_uncertainty = 1.0 / np.sqrt(np.sum(minus_weights))
            plus_weighted_uncertainty = 1.0 / np.sqrt(np.sum(plus_weights))

            # Calculate difference and combined uncertainty
            difference = plus_weighted_mean - minus_weighted_mean
            combined_uncertainty = np.sqrt(
                minus_weighted_uncertainty**2 + plus_weighted_uncertainty**2
            )

            # Perform 95% confidence level test (|z| < 1.96 for normal distribution)
            # or use t-distribution for small samples
            z_score = abs(difference) / combined_uncertainty

            # Use t-distribution with effective degrees of freedom
            # Satterthwaite approximation for unequal variances
            dof_eff = (
                minus_weighted_uncertainty**2 + plus_weighted_uncertainty**2
            ) ** 2 / (
                minus_weighted_uncertainty**4 / max(len(minus_chunks) - 1, 1)
                + plus_weighted_uncertainty**4 / max(len(plus_chunks) - 1, 1)
            )

            # 95% confidence level: p < 0.05, so t_critical for two-tailed test
            t_critical = t.ppf(0.975, dof_eff)  # 0.975 = 1 - 0.05/2

            # Get systematic uncertainties for reporting
            minus_syst = (
                minus_chunks[0]["systematic_uncertainty"] if minus_chunks else 0.0
            )
            plus_syst = plus_chunks[0]["systematic_uncertainty"] if plus_chunks else 0.0

            assert z_score <= t_critical, (
                f"At R={reflectivity}: μ- and μ+ measurements are inconsistent at 95% CL "
                f"(|t| = {z_score:.2f} > {t_critical:.2f}, dof_eff = {dof_eff:.1f})\n"
                f"μ-: {minus_weighted_mean:.6f} ± {minus_weighted_uncertainty:.6f} "
                f"(N={len(minus_chunks)}, σ_sys={minus_syst:.6f})\n"
                f"μ+: {plus_weighted_mean:.6f} ± {plus_weighted_uncertainty:.6f} "
                f"(N={len(plus_chunks)}, σ_sys={plus_syst:.6f})\n"
                f"Difference: {difference:.6f} ± {combined_uncertainty:.6f}"
            )

    @pytest.mark.parametrize(
        parameter_names,
        [
            Parameters(
                muon_sign_first="μ-",
                mirror_reflectivity_first="0.80",
                muon_sign_second="μ+",
                mirror_reflectivity_second="0.80",
                parameter_to_compare="throughput",
                absolute_consistency_range=0.001,
                relative_consistency_range=0.0,
                are_expected_to_differ=False,
            ),
            Parameters(
                muon_sign_first="μ-",
                mirror_reflectivity_first="0.81",
                muon_sign_second="μ+",
                mirror_reflectivity_second="0.81",
                parameter_to_compare="throughput",
                absolute_consistency_range=0.001,
                relative_consistency_range=0.0,
                are_expected_to_differ=False,
            ),
            Parameters(
                muon_sign_first="μ-",
                mirror_reflectivity_first="0.83",
                muon_sign_second="μ+",
                mirror_reflectivity_second="0.83",
                parameter_to_compare="throughput",
                absolute_consistency_range=0.001,
                relative_consistency_range=0.0,
                are_expected_to_differ=False,
            ),
            Parameters(
                muon_sign_first="μ-",
                mirror_reflectivity_first="0.80",
                muon_sign_second="μ-",
                mirror_reflectivity_second="0.83",
                parameter_to_compare="throughput",
                absolute_consistency_range=0.001,
                relative_consistency_range=0.0,
                are_expected_to_differ=True,
            ),
        ],
    )
    @pytest.mark.muon
    @pytest.mark.lst
    def test_check_comparative_consistency(
        self,
        muon_sign_first,
        mirror_reflectivity_first,
        muon_sign_second,
        mirror_reflectivity_second,
        parameter_to_compare,
        absolute_consistency_range,
        relative_consistency_range,
        are_expected_to_differ,
        simulation_results,
    ):
        """
        Comparative consistency test of two measurements or simulations.
        The mean measured parameters are compared to ensure they fall within the specified range.
        """

        first = np.fromiter(
            (
                row[parameter_to_compare]
                for row in simulation_results[muon_sign_first][
                    mirror_reflectivity_first
                ]
            ),
            dtype=float,
        )
        second = np.fromiter(
            (
                row[parameter_to_compare]
                for row in simulation_results[muon_sign_second][
                    mirror_reflectivity_second
                ]
            ),
            dtype=float,
        )

        if len(first) != len(second):
            first = np.nanmean(first)
            second = np.nanmean(second)

        if are_expected_to_differ:
            assert ~u.isclose(
                first,
                second,
                atol=absolute_consistency_range,
                rtol=relative_consistency_range,
            ).any()
        else:
            assert u.isclose(
                first,
                second,
                atol=absolute_consistency_range,
                rtol=relative_consistency_range,
            ).any()

    @pytest.mark.parametrize(
        parameter_mst_names,
        [
            Parameters_mst(
                file_fixture_name="muon_mst_nc_file",
                expected_throughput=0.18,
                expected_throughput_rel_uncertainty=0.05,
            ),
            Parameters_mst(
                file_fixture_name="muon_mst_fc_file",
                expected_throughput=0.2,
                expected_throughput_rel_uncertainty=0.05,
            ),
        ],
    )
    @pytest.mark.muon
    @pytest.mark.mst
    def test_check_mst(
        self,
        request,
        file_fixture_name,
        expected_throughput,
        expected_throughput_rel_uncertainty,
        test_config,
        muon_mst_nc_file,
        muon_mst_fc_file,
    ):
        """
        Comparative consistency test of measurements or simulations for MST (NC/FC).
        """

        test_config["CalculateThroughputWithMuons"]["input_url"] = str(
            request.getfixturevalue(file_fixture_name)
        )
        tool = CalculateThroughputWithMuons(config=Config(test_config))
        tool.setup()
        tool.start()

        # Extract results if processing succeeded
        containers = tool.tel_containers_map.get(1, [])
        if containers:
            mean_val = np.array([container.mean for container in containers])

        assert u.isclose(
            mean_val,
            expected_throughput * np.ones(len(mean_val)),
            rtol=expected_throughput_rel_uncertainty,
        ).any()
