"""Calculate the relative throughput of the telescopes."""

from collections import defaultdict
from itertools import combinations  # noqa: D100

import astropy.units as u
import numpy as np
from astropy.table import Table, join
from ctapipe.core import (
    TelescopeComponent,
    Tool,
)
from ctapipe.core.traits import (
    AstroQuantity,
    Bool,
    Dict,
    Float,
    FloatTelescopeParameter,
    IntTelescopeParameter,
    Path,
    Unicode,
)
from ctapipe.instrument import SubarrayDescription
from ctapipe.io import read_table, write_table
from iminuit import Minuit
from scipy.stats import norm
from tables.exceptions import NoSuchNodeError


class RelativeThroughputFitter(TelescopeComponent):
    """Perform relative throughput fitting for telescopes.

    This component is used to fit the relative throughput of telescopes based on the
    energy asymmetry of telescope pairs.
    """

    reference_telescopes = IntTelescopeParameter(
        default_value=None,
        help="ID of the telescopes whose throughput kept fixed during the intercalibration minimization",
        allow_none=True,
    ).tag(config=True)
    throughput_normalization = FloatTelescopeParameter(
        default_value=1.0,
        help="Setting the overall telescope throughput normalization. "
        "Depending the use case, it could reflect the "
        "absolute optical throughput measured by the muon rings / illuminator, "
        "if we want to compare or complement these methods. "
        "Alternatively it could get an arbitrary number, e.g. one that sets the average throughput to 1, "
        "if the user wants to 'flat-field' the array. "
        "Finally it could be set to 1, if we want to identify outlier telescopes or study the aging.",
        allow_none=False,
    ).tag(config=True)

    def fit(self, subarray_name, subarray_data):
        """
        Perform minimization for each telescope subsystem to compute optical throughput factors.

        Parameters
        ----------
        subarray_data : dict
            A dictionary where keys are telescope pairs and values are dictionaries containing
            "mean_asymmetry": the average energy asymmetry and "mean_uncertainty": the average
            uncertainty of the asymmetry for each telescope pair.
        subarray_name : str
            The name of the intercalibration subarray, used to identify the telescopes.
            Usually corresponds to the telescope type (e.g., "LST", "MST", "SST").

        Returns
        -------
        dict
            Dictionary of the form:
            {
                'subarray_name': {tel_id: (value, error), ...}
            }
        """
        results = {}

        tel_ids = self.subarray.tel_ids

        initial_values = {
            str(tel_id): self.throughput_normalization.tel[tel_id] for tel_id in tel_ids
        }

        def _chi2(*values):
            params = dict(zip(tel_ids, values))
            chi2 = 0.0
            for (i, j), entry in subarray_data.items():
                a_ij = entry["mean_asymmetry"]
                s_ij = entry["mean_uncertainty"]
                ci = params[i]
                cj = params[j]
                model = (ci - cj) / (ci + cj)
                chi2 += ((a_ij - model) ** 2) / (s_ij**2)
            return chi2

        fit = Minuit(_chi2, name=initial_values.keys(), **initial_values)

        # Create a list of unique reference telescope IDs
        unique_reference_telescopes = set(
            self.reference_telescopes.tel[tel_id]
            for tel_id in tel_ids
            if self.reference_telescopes.tel[tel_id] is not None
        )

        # Pass each unique reference telescope ID to fit.fixed
        for ref_tel_id in unique_reference_telescopes:
            fit.fixed[str(ref_tel_id)] = True

        fit.errordef = 1
        fit.migrad()

        results[subarray_name] = {
            tel_id: (fit.values[tel_id], fit.errors[tel_id])
            for tel_id in initial_values.keys()
        }
        return results


class PairFinder(TelescopeComponent):
    """Find pairs of telescopes based on their types and distances between them."""

    max_impact_distance = FloatTelescopeParameter(
        default_value=[
            ("type", "LST*", 125.0),
            ("type", "MST*", 125.0),
            ("type", "SST*", 225.0),
        ],
        help="Maximum distance between the telescopes and a shower core in meters. "
        "The maximum distance between the telescopes in pair "
        "should not exceed the sum of these values for the telescopes in pair.",
        allow_none=False,
    ).tag(config=True)

    def find_pairs(self, by_tel_type=True, cross_type_only=False):
        """
        Find pairs of telescope IDs.

        Parameters
        ----------
        by_tel_type : bool
            If True, find pairs of telescopes of the same type.
            If False, find pairs of all telescopes in the array.
        cross_type_only : bool
            If True, find pairs of telescopes of different types only.

        Returns
        -------
        dict
            A dictionary where keys are telescope types (str) and values are sets of
            pairs of telescope IDs (int, int). If by_tel_type is False, the key will be "ALL".
            If cross_type_only is True, the key will be "XTEL".
        """
        result = defaultdict(set)
        telescope_positions = self.subarray.positions

        def check_distance(tel1, tel2):
            """Check if the pair of telescopes is within the maximum distance."""
            pos1 = telescope_positions[tel1]
            pos2 = telescope_positions[tel2]
            distance = np.linalg.norm((pos1 - pos2).to(u.m).value)
            return (
                distance
                <= self.max_impact_distance.tel[tel1]
                + self.max_impact_distance.tel[tel2]
            )

        def check_type(tel1, tel2):
            """Check if the pair of telescopes are of the same type."""
            return self.subarray.tel[tel1].type == self.subarray.tel[tel2].type

        telescope_types = defaultdict(list)
        if by_tel_type:
            for tel_id, desc in self.subarray.tel.items():
                telescope_types[desc.type].append(tel_id)
        else:
            if cross_type_only:
                telescope_types["XTEL"] = list(self.subarray.tel_ids)
            else:
                telescope_types["ALL"] = list(self.subarray.tel_ids)

        for tel_type, tel_ids in telescope_types.items():
            for tel1, tel2 in combinations(tel_ids, 2):
                if cross_type_only and check_type(tel1, tel2):
                    continue
                if check_distance(tel1, tel2):
                    result[tel_type].add((tel1, tel2))

        return result


class CalculateCrossCalibration(Tool):
    """Calibrator that performs cross calibration of telescopes."""

    input_url = Path(
        default_value="dl2.h5",
        help="Path to the input file with the DL2 (merged) data.",
    ).tag(config=True)
    output_url = Path(
        default_value="monitoring_cross_calibration_dl2.h5",
        help="Path to the output file where the produced calibration"
        "products will be stored",
    ).tag(config=True)
    overwrite = Bool(default_value=False, help="Overwrite output file.").tag(
        config=True
    )
    reconstruction_algorithm = Unicode(
        default_value="RandomForest",
        help="Name of the reconstruction algorithm",
        allow_none=False,
    ).tag(config=True)
    event_filters = Dict(
        per_key_traits={
            "min_gammaness": Float(allow_none=True),
            "min_energy": AstroQuantity(
                physical_type=u.physical.energy, allow_none=True
            ),
            "max_distance_asymmetry": Float(allow_none=True),
        },
        default_value={
            "min_gammaness": None,
            "min_energy": None,
            "max_distance_asymmetry": None,
        },
        help=(
            "Dictionary of event filters:\n"
            "  - min_gammaness is used to select the gamma-like events\n"
            "  - min_energy defines the energy range suitable for different types of telescopes\n"
            "  - max_distance_asymmetry sets the equidistance asymmetry limit\n"
            "If a filter parameter is set to None (the default value), "
            "it will not be applied during event selection."
        ),
    ).tag(config=True)

    aliases = {
        ("i", "input_url"): "CalculateCrossCalibration.input_url",
        ("o", "output_url"): "CalculateCrossCalibration.output_url",
    }

    classes = [RelativeThroughputFitter, PairFinder]

    def merge_tables(self, telescope_pairs):
        """
        Merge telescope energy tables for specified telescope pairs.

        Parameters
        ----------
        telescope_pairs : dict
            A dictionary where keys are telescope types (str), and values are lists of
            tuples. Each tuple contains two telescope IDs (int) representing a pair.

        Returns
        -------
        dict
            A dictionary where keys are tuples of telescope IDs (int, int),
            representing the telescope pairs. The values are lists of merged tables
            for the specified telescope pairs. If no tables are successfully merged
            for a telescope pair, the list will be empty.
        """
        merged_tables = {}
        unique_telescope_ids = {
            tel_id
            for pairs in telescope_pairs.values()
            for pair in pairs
            for tel_id in pair
        }

        telescope_tables = {}
        for tel_id in unique_telescope_ids:
            try:
                path = f"dl2/event/telescope/energy/{self.reconstruction_algorithm}Regressor/tel_{tel_id:03d}"
                telescope_tables[tel_id] = read_table(
                    self.input_url,
                    path,
                    condition=f"{self.reconstruction_algorithm}Regressor_tel_is_valid",
                )
            except NoSuchNodeError:
                pass  # data for one telescope is missing, will be reported in application to a particular pair later.
        for telescope_type, pairs in telescope_pairs.items():
            if telescope_type not in merged_tables:
                merged_tables[telescope_type] = {}
            for tel1, tel2 in pairs:
                table_1 = telescope_tables.get(tel1)
                table_2 = telescope_tables.get(tel2)
                if table_1 is None or table_2 is None:
                    self.log.warning(
                        "Missing telescope data for tel %s in pair (%s, %s)",
                        tel1 if table_1 is None else tel2,
                        tel1,
                        tel2,
                    )
                    continue

                try:
                    merged_table = join(
                        table_1[
                            [
                                "obs_id",
                                "event_id",
                                f"{self.reconstruction_algorithm}Regressor_tel_energy",
                                f"{self.reconstruction_algorithm}Regressor_tel_energy_uncert",
                            ]
                        ],
                        table_2[
                            [
                                "obs_id",
                                "event_id",
                                f"{self.reconstruction_algorithm}Regressor_tel_energy",
                                f"{self.reconstruction_algorithm}Regressor_tel_energy_uncert",
                            ]
                        ],
                        keys=["obs_id", "event_id"],
                    )

                    if len(merged_table) > 0:
                        pair = (tel1, tel2)
                        if pair not in merged_tables[telescope_type]:
                            merged_tables[telescope_type][pair] = []

                        merged_tables[telescope_type][pair].append(merged_table)
                except MemoryError as e:
                    self.log.error(
                        "MemoryError: The data is too large to process: %s", e
                    )
                    raise

        return merged_tables

    def _apply_min_gammaness(self, tel_id1, tel_id2, threshold):
        """Select gamma-like events based on the gammaness threshold."""
        events_tel1 = self._get_gamma_like_events(tel_id1, threshold)
        events_tel2 = self._get_gamma_like_events(tel_id2, threshold)
        return events_tel1 & events_tel2

    def _apply_min_energy(self, tel_id1, tel_id2, threshold):
        """Select showers over an energy threshold."""
        events_tel1 = self._set_energy_threshold(tel_id1, threshold)
        events_tel2 = self._set_energy_threshold(tel_id2, threshold)
        return events_tel1 & events_tel2

    def _apply_max_distance_asymmetry(self, tel_id1, tel_id2, threshold):
        """Select showers with similar impact distances."""

        def load_distance_table(tel_id):
            path = f"dl2/event/telescope/impact/HillasReconstructor/tel_{tel_id:03d}"
            return read_table(self.input_url, path)[
                ["obs_id", "event_id", "HillasReconstructor_tel_impact_distance"]
            ]

        table1 = load_distance_table(tel_id1)
        table2 = load_distance_table(tel_id2)

        merged = join(table1, table2, keys=["obs_id", "event_id"])
        dist1 = merged["HillasReconstructor_tel_impact_distance_1"]
        dist2 = merged["HillasReconstructor_tel_impact_distance_2"]

        asym = ((dist2 - dist1) / (dist1 + dist2)).value
        mask = np.abs(asym) < threshold
        return set(zip(merged["obs_id"][mask], merged["event_id"][mask]))

    def _get_gamma_like_events(self, tel_id, threshold):
        """Select showers that are gamma like."""
        path = f"dl2/event/telescope/classification/{self.reconstruction_algorithm}Classifier/tel_{tel_id:03d}"
        class_table = read_table(
            self.input_url,
            path,
            condition=f"{self.reconstruction_algorithm}Classifier_tel_is_valid",
        )
        mask = (
            class_table[f"{self.reconstruction_algorithm}Classifier_tel_prediction"]
            > threshold
        )
        return set(zip(class_table["obs_id"][mask], class_table["event_id"][mask]))

    def _set_energy_threshold(self, tel_id, threshold):
        """Select showers over an energy threshold."""
        path = f"dl2/event/telescope/energy/{self.reconstruction_algorithm}Regressor/tel_{tel_id:03d}"
        energy_table = read_table(
            self.input_url,
            path,
            condition=f"{self.reconstruction_algorithm}Regressor_tel_is_valid",
        )
        mask = (
            energy_table[f"{self.reconstruction_algorithm}Regressor_tel_energy"]
            > threshold
        )
        return set(zip(energy_table["obs_id"][mask], energy_table["event_id"][mask]))

    def event_selection(self, merged_table, tel1, tel2):
        """
        Filter merged table based on energy, classification, and optionally equidistant impact criteria.

        Parameters
        ----------
        merged_table : Table
            Merged table from two telescopes.
        tel1, tel2 : int
            Telescope IDs.

        Returns
        -------
        Table
            Filtered table.
        """
        selected_events = self._get_valid_events(tel1, tel2)

        event_ids = set(zip(merged_table["obs_id"], merged_table["event_id"]))
        valid_mask = np.array(
            [(obs_id, event_id) in selected_events for obs_id, event_id in event_ids]
        )
        return merged_table[valid_mask]

    def _get_valid_events(self, tel_id1, tel_id2):
        """Apply all event filters for a given telescope."""
        event_sets = []
        for filter_name, threshold in self.event_filters.items():
            if threshold is None:
                self.log.debug("Skipping filter %s", filter_name)
                continue
            try:
                filter_func = getattr(self, f"_apply_{filter_name}")
            except AttributeError:
                self.log.error(
                    "Filter function _apply_%s not found for filter %s",
                    filter_name,
                    filter_name,
                )
                raise ValueError(
                    f"Filter {filter_name} is not implemented or not recognized."
                )
            event_sets.append(filter_func(tel_id1, tel_id2, threshold))

        return set.intersection(*event_sets) if event_sets else set()

    def calculate_energy_asymmetry(self, merged_tables):
        """
        Calculate the mean energy asymmetry and its uncertainty for each telescope pair from the merged tables.

        Parameters
        ----------
        merged_tables : dict
            A dictionary where keys are telescope types. Each value is another dictionary where keys are tuples
            of telescope IDs (int, int), representing telescope pairs, and the values are lists of merged tables
            containing energy data.

        Returns
        -------
        dict
            A nested dictionary with telescope types as the first level of keys.
            Each value is a dictionary with telescope pairs as keys and a dictionary as value containing:
            - "mean_asymmetry": the average energy asymmetry
            - "mean_uncertainty": the average uncertainty of the asymmetry
        """
        energy_asymmetry_results = {}

        for telescope_type, pairs in merged_tables.items():
            energy_asymmetry_results[telescope_type] = {}
            for pair, merged_tables_list in pairs.items():
                asymmetry_values = []
                uncertainty_values = []
                for merged_table_unfiltered in merged_tables_list:
                    merged_table = self.event_selection(
                        merged_table_unfiltered,
                        pair[0],
                        pair[1],
                    )
                    energy_tel1 = merged_table[
                        f"{self.reconstruction_algorithm}Regressor_tel_energy_1"
                    ]
                    energy_tel2 = merged_table[
                        f"{self.reconstruction_algorithm}Regressor_tel_energy_2"
                    ]
                    energy_uncertainty_tel1 = merged_table[
                        f"{self.reconstruction_algorithm}Regressor_tel_energy_uncert_1"
                    ]
                    energy_uncertainty_tel2 = merged_table[
                        f"{self.reconstruction_algorithm}Regressor_tel_energy_uncert_2"
                    ]

                    energy_sum = energy_tel1 + energy_tel2
                    energy_asymmetry = ((energy_tel1 - energy_tel2) / energy_sum).value
                    mean_asymmetry = energy_asymmetry.mean()

                    energy_asymmetry_uncertainty = (2.0 / energy_sum**2) * np.sqrt(
                        (energy_tel1 * energy_uncertainty_tel2) ** 2
                        + (energy_tel2 * energy_uncertainty_tel1) ** 2
                    )
                    asymmetry_uncertainty = energy_asymmetry_uncertainty.mean()
                    mean_asymmetry_uncertainty = asymmetry_uncertainty / len(
                        energy_asymmetry
                    )

                    asymmetry_values.append(mean_asymmetry)
                    uncertainty_values.append(mean_asymmetry_uncertainty)

                if asymmetry_values:
                    energy_asymmetry_results[telescope_type][pair] = {
                        "mean_asymmetry": sum(asymmetry_values) / len(asymmetry_values),
                        "mean_uncertainty": sum(uncertainty_values)
                        / len(uncertainty_values),
                    }

        return energy_asymmetry_results

    def _load_telescope_energy_tables(self, pairs):
        """Load energy tables for unique telescopes in the given pairs."""
        telescope_tables = {}
        unique_tel_ids = {tel for pair in pairs for tel in pair}
        for tel_id in unique_tel_ids:
            try:
                path = f"dl2/event/telescope/energy/{self.reconstruction_algorithm}Regressor/tel_{tel_id:03d}"
                telescope_tables[tel_id] = read_table(self.input_url, path)
            except NoSuchNodeError:
                continue
        return telescope_tables

    def _merge_valid_energy_tables(self, tel1, table1, tel2, table2):
        """Merge valid energy tables for two telescopes based on common events."""
        valid1 = table1[
            table1[f"{self.reconstruction_algorithm}Regressor_tel_is_valid"]
        ]
        valid2 = table2[
            table2[f"{self.reconstruction_algorithm}Regressor_tel_is_valid"]
        ]

        merged = join(
            valid1[
                [
                    "obs_id",
                    "event_id",
                    f"{self.reconstruction_algorithm}Regressor_tel_energy",
                ]
            ],
            valid2[
                [
                    "obs_id",
                    "event_id",
                    f"{self.reconstruction_algorithm}Regressor_tel_energy",
                ]
            ],
            keys=["obs_id", "event_id"],
            table_names=["1", "2"],
            uniq_col_name="{col_name}_{table_name}",
        )
        return merged

    def compute_cross_type_energy_ratios(self, cross_type_pairs, fit_results):
        """
        Compute energy ratios grouped by telescope type pairs using throughput-corrected energies.

        Parameters
        ----------
        telescope_pairs : dict
            A dictionary where keys are telescope types and values are lists of
            tuples. Each tuple contains two telescope IDs (int) representing a pair.
        fit_results : dict
            Dictionary from `fit()` with format {subarray_name: {tel_id: (throughput, error)}}

        Returns
        -------
        dict
            Dictionary of format {(type1, type2): [corrected energy ratios]}
        """
        energy_ratios_by_type = {}
        mean_ratios = {}
        telescope_tables = self._load_telescope_energy_tables(cross_type_pairs)

        # Build lookup tables
        throughput_map = {
            tel_id: value[0]
            for subarray in fit_results.values()
            for tel_id, value in subarray.items()
        }
        type_map = {
            tel_id: self.subarray.tel[tel_id].type for tel_id in self.subarray.tel_ids
        }

        self.relative_throughput_fitter.subarray = self.subarray
        for tel1, tel2 in cross_type_pairs:
            table1 = telescope_tables.get(tel1)
            table2 = telescope_tables.get(tel2)
            if table1 is None or table2 is None:
                continue
            merged = self._merge_valid_energy_tables(tel1, table1, tel2, table2)
            if (
                len(merged) > 0
                and str(tel1) in throughput_map
                and str(tel2) in throughput_map
            ):
                throughput1 = throughput_map[str(tel1)]
                throughput2 = throughput_map[str(tel2)]
                normalisation1 = (
                    self.relative_throughput_fitter.throughput_normalization.tel[tel1]
                )
                normalisation2 = (
                    self.relative_throughput_fitter.throughput_normalization.tel[tel2]
                )

                corrected_energy1 = merged[
                    f"{self.reconstruction_algorithm}Regressor_tel_energy_1"
                ] * (throughput1 / normalisation1)
                corrected_energy2 = merged[
                    f"{self.reconstruction_algorithm}Regressor_tel_energy_2"
                ] * (throughput2 / normalisation2)
                ratios = corrected_energy1 / corrected_energy2

                type1 = type_map[tel1]
                type2 = type_map[tel2]
                type_pair = tuple(sorted((type1, type2)))

                if type_pair not in energy_ratios_by_type:
                    energy_ratios_by_type[type_pair] = []

                energy_ratios_by_type[type_pair].extend(ratios.tolist())

        for type_pair, ratios in energy_ratios_by_type.items():
            if ratios:
                mu, std = norm.fit(ratios)
                err = std / np.sqrt(len(ratios))
                mean_ratios[type_pair] = (mu, err)

        return mean_ratios

    def save_monitoring_data(self, intercalibration_results, cross_calibration_results):
        """
        Save the calibration products in DL2 monitoring data.

        Parameters
        ----------
        intercalibration_results : dict
            Dictionary of the form:
            {
                'subarray_name': {tel_id: (value, error), ...}
            }
            that stores the relative throughput coefficients for
            each telescope.
        cross_calibration_results : dict
            Dictionary of format {(type1, type2): [corrected energy ratios]}
        """
        tel_rows = []
        for size_type, tel_data in intercalibration_results.items():
            size_type_str = str(size_type.value)
            for tel_id, (value, error) in tel_data.items():
                tel_rows.append((size_type_str, int(tel_id), value, error))

        tel_table = Table(
            rows=tel_rows, names=("size_type", "tel_id", "value", "error")
        )

        ratio_rows = []
        for (type_a, type_b), (mean, error) in cross_calibration_results.items():
            ratio_rows.append((str(type_a.value), str(type_b.value), mean, error))

            ratio_table = Table(
                rows=ratio_rows, names=("type_a", "type_b", "ratio", "error")
            )

        write_table(
            tel_table,
            self.output_url,
            "/dl2/monitoring/inter_calibration",
            overwrite=self.overwrite,
        )
        write_table(
            ratio_table,
            self.output_url,
            "/dl2/monitoring/cross_calibration",
            overwrite=self.overwrite,
        )

    def setup(self):
        """Set up the logic."""
        # Read subarray description
        self.subarray = SubarrayDescription.read(self.input_url)
        self.relative_throughput_fitter = RelativeThroughputFitter(
            subarray=self.subarray,
            parent=self,
        )
        self.pair_finder = PairFinder(
            subarray=self.subarray,
            parent=self,
        )

    def start(self):
        """Perform cross-calibration per telescope subsystem."""
        # Intercalibration
        tel_pairs = self.pair_finder.find_pairs()
        merged_tables = self.merge_tables(tel_pairs)
        energy_asymmetry_results = self.calculate_energy_asymmetry(merged_tables)
        intercalibration_results = {}

        for subarray_name, subarray_data in energy_asymmetry_results.items():
            measured_telescopes = set(
                tel_id for (i, j), entry in subarray_data.items() for tel_id in (i, j)
            )
            self.relative_throughput_fitter.subarray = self.subarray.select_subarray(
                tel_ids=measured_telescopes, name=subarray_name
            )
            intercalibration_results.update(
                self.relative_throughput_fitter.fit(subarray_name, subarray_data)
            )
            self.log.debug("intercalibration minimization", intercalibration_results)

        # Cross-calibration
        cross_type_pairs = self.pair_finder.find_pairs(
            by_tel_type=False, cross_type_only=True
        )
        cross_calibration_results = self.compute_cross_type_energy_ratios(
            cross_type_pairs["XTEL"], intercalibration_results
        )
        # Save calibration products to dl2/monitoring
        self.save_monitoring_data(intercalibration_results, cross_calibration_results)

    def finish(self):
        """Store the results."""
        self.log.info("Shutting down.")


def main():
    """Run the app."""
    tool = CalculateCrossCalibration()
    tool.run()
