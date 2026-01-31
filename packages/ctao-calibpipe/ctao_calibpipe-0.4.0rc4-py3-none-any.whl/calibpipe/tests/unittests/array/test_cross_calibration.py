import logging
from enum import Enum
from unittest.mock import MagicMock

import astropy.units as u
import pytest
from astropy.table import Table
from ctapipe.instrument import SubarrayDescription
from ctapipe.io import read_table
from traitlets.config import Config

from calibpipe.tools.telescope_cross_calibration_calculator import (
    CalculateCrossCalibration,
    RelativeThroughputFitter,
)

logger = logging.getLogger("calibpipe.application")


class TestTelescopeCrossCalibration:
    @pytest.fixture(scope="class")
    def test_calibrator(self, cross_calibration_dl2_file):
        test_config = {
            "CalculateCrossCalibration": {
                "input_url": str(cross_calibration_dl2_file),
                "event_filters": {
                    "min_gammaness": 0.5,
                },
                "reconstruction_algorithm": "RandomForest",
                "RelativeThroughputFitter": {
                    "throughput_normalization": [
                        ["type", "LST*", 1.0],
                        ["type", "MST*", 1.0],
                        ["type", "SST*", 1.0],
                    ],
                    "reference_telescopes": [
                        ["type", "LST*", 1],
                        ["type", "MST*", 5],
                        ["type", "SST*", 37],
                    ],
                },
                "PairFinder": {
                    "max_impact_distance": [
                        ["type", "LST*", 125.0],
                        ["type", "MST*", 125.0],
                        ["type", "SST*", 225.0],
                    ],
                },
            },
        }
        tool = CalculateCrossCalibration(config=Config(test_config))

        return tool

    @pytest.fixture
    def test_fitter_config(self):
        fitter_config = {
            "RelativeThroughputFitter": {
                "throughput_normalization": [
                    ["type", "LST*", 1.0],
                    ["type", "MST*", 1.0],
                    ["type", "SST*", 1.0],
                ],
                "reference_telescopes": [
                    ["type", "LST*", 1],
                    ["type", "MST*", 5],
                    ["type", "SST*", 37],
                ],
            },
        }
        return Config(fitter_config)

    @pytest.fixture
    def mock_minuit(self):
        m = MagicMock()
        m.values = {"x0": 0.74, "x1": 0.75, "x2": 0.76}
        m.errors = {"x0": 1e-6, "x1": 2e-6, "x2": 3e-6}
        return m

    @pytest.mark.verifies_usecase("UC-120-2.3")
    def test_create_telescope_pairs(self, test_calibrator):
        test_calibrator.setup()
        telescope_pairs = test_calibrator.pair_finder.find_pairs()
        assert "MST" in telescope_pairs
        assert len(telescope_pairs["MST"]) > 0
        assert "SST" in telescope_pairs
        assert len(telescope_pairs["SST"]) > 0
        telescope_pairs = test_calibrator.pair_finder.find_pairs(by_tel_type=False)
        assert "ALL" in telescope_pairs
        assert len(telescope_pairs["ALL"]) > 0

    @pytest.mark.verifies_usecase("UC-120-2.3")
    def test_distance(self, test_calibrator):
        # if the requested maximum telescope distance is too small, no tel pair should be returned
        updated_pair_finder_config = {
            "CalculateCrossCalibration": {
                "PairFinder": {
                    "max_impact_distance": [
                        ["type", "LST*", 10.0],
                        ["type", "MST*", 10.0],
                        ["type", "SST*", 10.0],
                    ],
                },
            },
        }

        test_calibrator.update_config(Config(updated_pair_finder_config))
        test_calibrator.setup()

        telescope_pairs = test_calibrator.pair_finder.find_pairs()
        assert all(
            isinstance(value, set) and len(value) == 0
            for value in telescope_pairs.values()
        )

    @pytest.mark.verifies_usecase("UC-120-2.3")
    def test_no_reverse_pairs(self, test_calibrator):
        # Ensure the reverse pair (j, i) is not present
        test_calibrator.setup()
        telescope_pairs = test_calibrator.pair_finder.find_pairs()

        for telescope_type, pairs in telescope_pairs.items():
            for i, j in pairs:
                assert (j, i) not in pairs, (
                    f"Reverse pair ({j}, {i}) exists in {telescope_type} pairs"
                )

    @pytest.mark.verifies_usecase("UC-120-2.3")
    def test_allowed_telescope_names(self, test_calibrator):
        # Ensure all keys in the dictionary belong to the allowed names
        allowed_telescope_names = {"MST", "SST"}
        test_calibrator.setup()
        telescope_pairs = test_calibrator.pair_finder.find_pairs()
        for telescope_name in telescope_pairs.keys():
            assert telescope_name in allowed_telescope_names, (
                f"Unexpected telescope type '{telescope_name}' found in the output"
            )

    @pytest.mark.verifies_usecase("UC-120-2.3")
    def test_maximum_telescope_pairs(self, test_calibrator):
        updated_pair_finder_config = {
            "CalculateCrossCalibration": {
                "PairFinder": {
                    "max_impact_distance": [
                        ["type", "LST*", 150000.0],
                        ["type", "MST*", 150000.0],
                        ["type", "SST*", 150000.0],
                    ],
                },
            },
        }

        test_calibrator.update_config(Config(updated_pair_finder_config))
        test_calibrator.setup()

        telescope_pairs = test_calibrator.pair_finder.find_pairs()

        array = read_table(
            test_calibrator.input_url,
            "configuration/instrument/subarray/layout",
        )
        telescope_types = [str(t).strip() for t in array["type"] if t]
        for tel_type in set(telescope_types):
            tel_type_counts = (array["type"] == tel_type).sum()
            if tel_type_counts > 0:
                assert (
                    len(telescope_pairs[tel_type])
                    == (tel_type_counts * (tel_type_counts - 1)) // 2
                )

    @pytest.mark.verifies_usecase("UC-120-2.3")
    def test_merge_tables_success(self, test_calibrator):
        """Test successful merging of tables for telescope pairs."""
        telescope_pairs = {"SST": [(37, 39)], "MST": [(6, 12)]}
        result = test_calibrator.merge_tables(telescope_pairs)

        assert (37, 39) in result["SST"]
        assert (6, 12) in result["MST"]
        assert len(result["SST"][(37, 39)]) > 0  # Ensure merged table is not empty

    @pytest.mark.verifies_usecase("UC-120-2.3")
    def test_merge_tables_empty_input(self, test_calibrator):
        """Test merge_tables returns empty dict when given an empty input."""
        telescope_pairs = {}
        result = test_calibrator.merge_tables(telescope_pairs)
        assert result == {}

    @pytest.mark.verifies_usecase("UC-120-2.3")
    def test_merge_tables_missing_data(self, test_calibrator):
        """Test `merge_tables` handles missing telescope data correctly."""
        telescope_pairs = {"SST": [(37, 39), (42, 143)], "MST": [(5, 6), (6, 120000)]}
        result = test_calibrator.merge_tables(telescope_pairs)
        assert set(result["MST"].keys()) == {(5, 6)}

    @pytest.mark.verifies_usecase("UC-120-2.3")
    def test_inter_calibration_result_format(
        self, test_fitter_config, cross_calibration_dl2_file
    ):
        data_subsystem = {
            (5, 6): {"mean_asymmetry": 0.1, "mean_uncertainty": 0.01},
            (6, 8): {"mean_asymmetry": -0.05, "mean_uncertainty": 0.02},
        }

        measured_telescopes = set(
            tel_id for (i, j), entry in data_subsystem.items() for tel_id in (i, j)
        )

        subarray = SubarrayDescription.read(cross_calibration_dl2_file)

        test_fitter = RelativeThroughputFitter(
            subarray=subarray.select_subarray(tel_ids=measured_telescopes),
            config=test_fitter_config,
        )

        result = test_fitter.fit("MST", data_subsystem)
        assert "MST" in result
        assert isinstance(result["MST"], dict)
        assert set(result["MST"].keys()) == {"5", "6", "8"}
        assert all(isinstance(v, tuple) and len(v) == 2 for v in result["MST"].values())

    @pytest.mark.verifies_usecase("UC-120-2.3")
    def test_event_selection_with_multiple_filters(self, test_calibrator, monkeypatch):
        test_calibrator.setup()
        test_calibrator.event_filters = {
            "min_gammaness": 0.5,
            "min_energy": u.Quantity(0.0, u.GeV),
        }
        gamma_set = {(1, 100), (2, 200), (3, 300)}
        energy_set = {(1, 100), (3, 300)}

        monkeypatch.setattr(
            test_calibrator,
            "_apply_min_gammaness",
            lambda tel_id1, tel_id2, threshold: gamma_set,
        )
        monkeypatch.setattr(
            test_calibrator,
            "_apply_min_energy",
            lambda tel_id1, tel_id2, threshold: energy_set,
        )
        merged_table = Table({"obs_id": [1, 2, 3, 4], "event_id": [100, 200, 300, 400]})

        filtered = test_calibrator.event_selection(merged_table, tel1=1, tel2=3)
        assert len(filtered) == 2

    @pytest.mark.verifies_usecase("UC-120-2.3")
    def test_event_selection_with_invalid_filter(self, test_calibrator):
        test_calibrator.setup()
        test_calibrator.event_filters = {
            "non_existent_filter": 4,
        }
        merged_table = Table({"obs_id": [1, 2, 3, 4], "event_id": [100, 200, 300, 400]})

        with pytest.raises(
            ValueError,
            match="Filter non_existent_filter is not implemented or not recognized.",
        ):
            _ = test_calibrator.event_selection(merged_table, tel1=1, tel2=2)

    @pytest.mark.verifies_usecase("UC-120-2.3")
    def test_system_cross_calibrator(self, test_calibrator, caplog):
        # Small scale integration test
        caplog.set_level(logging.ERROR, logger="calibpipe.application")
        updated_cc_config = {
            "CalculateCrossCalibration": {
                "event_filters": {
                    "min_gammaness": 0.5,
                },
                "RelativeThroughputFitter": {
                    "throughput_normalization": [
                        ["type", "LST*", 1.0],
                        ["type", "MST*", 1.0],
                        ["type", "SST*", 1.0],
                    ],
                    "reference_telescopes": [
                        ["type", "LST*", 1],
                        ["type", "MST*", 5],
                        ["type", "SST*", 37],
                    ],
                },
                "PairFinder": {
                    "max_impact_distance": [
                        ["type", "LST*", 125.0],
                        ["type", "MST*", 125.0],
                        ["type", "SST*", 225.0],
                    ],
                },
            },
        }
        test_calibrator.update_config(Config(updated_cc_config))
        test_calibrator.setup()
        telescope_pairs = test_calibrator.pair_finder.find_pairs()
        merged_tables = test_calibrator.merge_tables(telescope_pairs)
        energy_asymmetry_results = test_calibrator.calculate_energy_asymmetry(
            merged_tables
        )
        results = {}

        for subarray_name, subarray_data in energy_asymmetry_results.items():
            measured_telescopes = set(
                tel_id for (i, j), entry in subarray_data.items() for tel_id in (i, j)
            )
            fitter = RelativeThroughputFitter(
                subarray=test_calibrator.subarray.select_subarray(
                    tel_ids=measured_telescopes, name=subarray_name
                ),
                parent=test_calibrator,
            )
            results.update(fitter.fit(subarray_name, subarray_data))

        cross_type_pairs = test_calibrator.pair_finder.find_pairs(
            by_tel_type=False, cross_type_only=True
        )
        cross_calibration_results = test_calibrator.compute_cross_type_energy_ratios(
            cross_type_pairs["XTEL"], results
        )
        assert cross_calibration_results[("MST", "SST")][0] == pytest.approx(
            1.0119, rel=1e-2
        )
        assert cross_calibration_results[("MST", "SST")][1] == pytest.approx(
            0.0042591, rel=1e-2
        )
        # Below testing energy asymmetry
        assert energy_asymmetry_results["MST"][(6, 12)][
            "mean_uncertainty"
        ] == pytest.approx(1.3613071073770851e-06, rel=1e-4)
        assert energy_asymmetry_results["MST"][(6, 12)][
            "mean_asymmetry"
        ] == pytest.approx(-0.0008690296768284202, rel=1e-2)
        # Below testing the fixed telescopes
        assert results["SST"]["37"][0] == pytest.approx(1.0, rel=1e-4)
        assert results["MST"]["5"][0] == pytest.approx(1.0, rel=1e-4)

    @pytest.mark.verifies_usecase("UC-120-2.3")
    def test_save_monitoring_data(self, test_calibrator, tmp_path):
        # Prepare input
        class SizeType(Enum):
            MST = "MST"
            SST = "SST"
            LST = "LST"

        intercalibration_results = {
            SizeType.MST: {
                "6": (1.23, 0.01),
                "8": (0.97, 0.02),
            }
        }
        cross_calibration_results = {
            (SizeType.MST, SizeType.SST): (1.05, 0.05),
            (SizeType.LST, SizeType.SST): (1.15, 0.05),
            (SizeType.LST, SizeType.MST): (0.95, 0.05),
        }

        # Run
        updated_cc_config = {
            "CalculateCrossCalibration": {
                "event_filters": {
                    "get_gamma_like_events": 0.5,
                },
                "output_url": "x_calib_test_dl2.h5",
                "overwrite": True,
                "RelativeThroughputFitter": {
                    "throughput_normalization": [
                        ["type", "LST*", 1.0],
                        ["type", "MST*", 1.0],
                        ["type", "SST*", 1.0],
                    ],
                    "reference_telescopes": [
                        ["type", "LST*", 1],
                        ["type", "MST*", 5],
                        ["type", "SST*", 37],
                    ],
                },
                "PairFinder": {
                    "max_impact_distance": [
                        ["type", "LST*", 125.0],
                        ["type", "MST*", 125.0],
                        ["type", "SST*", 225.0],
                    ],
                },
            },
        }
        test_calibrator.update_config(Config(updated_cc_config))
        test_calibrator.setup()
        test_calibrator.save_monitoring_data(
            intercalibration_results, cross_calibration_results
        )

        # Validate inter calibration table
        inter_table = read_table(
            test_calibrator.output_url, "/dl2/monitoring/inter_calibration"
        )
        assert len(inter_table) == 2
        assert "tel_id" in inter_table.colnames
        assert "value" in inter_table.colnames
        assert "error" in inter_table.colnames

        # Validate cross calibration table
        cross_table = read_table(
            test_calibrator.output_url, "/dl2/monitoring/cross_calibration"
        )
        assert len(cross_table) == 3
        assert cross_table["ratio"][0] == pytest.approx(1.05)
        assert cross_table["error"][0] == pytest.approx(0.05)
        assert cross_table["ratio"][1] == pytest.approx(1.15)
        assert cross_table["ratio"][2] == pytest.approx(0.95)

    @pytest.mark.verifies_usecase("UC-120-2.3")
    def test_get_equidistant_events(self, test_calibrator):
        test_calibrator.setup()
        set_of_events = test_calibrator._apply_max_distance_asymmetry(42, 143, 0.05)
        assert (4991, 1181519) in set_of_events
        assert (4991, 2196419) not in set_of_events
