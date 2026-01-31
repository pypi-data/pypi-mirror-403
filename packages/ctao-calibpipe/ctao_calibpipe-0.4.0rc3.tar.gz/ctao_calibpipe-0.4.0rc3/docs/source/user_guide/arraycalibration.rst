=================
Array calibration
=================

Here we describe the configuration parameters of the relative throughput calibration using reconstructed shower energies tool.

* **event_filters**: a dictionary with the event selection filters. The keys are the name of the filters while the values are the thresholds. Currently implemented are:
* **min_gammaness**: used to select gamma-like showers.
* **min_energy**: the minimum energy.
* **max_distance_asymmetry**: used to select equidistant events.

* **reconstruction_algorithm**: name of the reconstruction algorithm.

* **throughput_normalization**: a FloatTelescopeParameter that sets the overall telescope throughput normalization. Dependingon the use case scenario, it could reflect the absolute optical throughput measured by the muon rings / illuminator, if we want to compare or complement these methods. Alternatively it could get an arbitrary number, e.g. one that sets the average throughput to 1, if the user wants to 'flat-field' the array. Finally it could be set to 1, if we want to identify outlier telescopes or study the aging.

* **reference_telescopes**: an IntTelescopeParameter that sets the ID of the telescopes whose throughput kept fixed during the intercalibration minimization.

* **max_impact_distance**: a FloatTelescopeParameter that sets the maximum distance between the telescopes and a shower core in meters. The maximum distance between the telescopes in pair should not exceed the sum of these values for the telescopes in pair.

.. literalinclude:: array/cross_calibration_configuration.yaml
  :language: YAML

The tool produces a new hdf5 file with the two following tables:

* /dl2/monitoring/inter_calibration

Where the inter-calibration results are stored. The table has the following fields:

+----------------------+--------------------+--------------------------------------------------+
| Column Name          | Type                 | Description                                    |
+======================+======================+================================================+
| ``size_type``        | `numpy.str`          | Telescope type (LST, MST, SST).                |
+----------------------+----------------------+------------------------------------------------+
| ``tel_id``           | `numpy.int64`        | Telescope ID.                                  |
+----------------------+----------------------+------------------------------------------------+
| ``value``            | `numpy.float64`      | Relative telescope throughput.                 |
+----------------------+----------------------+------------------------------------------------+
| ``error``            | `numpy.float64`      | Relative telescope throughput uncertainty.     |
+----------------------+----------------------+------------------------------------------------+


* /dl2/monitoring/cross_calibration

where the results of cross-calibration are stored.

+----------------------+----------------------+--------------------------------------------------+
| Column Name          | Type                 | Description                                      |
+======================+======================+==================================================+
| ``type_a``           | `numpy.str`          | Telescope type 1 (LST, MST, SST).                |
+----------------------+----------------------+--------------------------------------------------+
| ``type_b``           | `numpy.str`          | Telescope type 1 (LST, MST, SST).                |
+----------------------+----------------------+--------------------------------------------------+
| ``ratio``            | `numpy.float64`      | Throughput scaling ratio between different types.|
+----------------------+----------------------+--------------------------------------------------+
| ``error``            | `numpy.float64`      | Throughput scaling ratio uncertainty.            |
+----------------------+----------------------+--------------------------------------------------+
