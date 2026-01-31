==================
Camera calibration
==================

-----------------
Camera Calibrator
-----------------

The **Camera Calibrator** calculates the final camera calibration coefficients, which includes the pedestal offset per waveform sample and the timing correction for each pixel, using interleaved calibration events. It uses the **FFactor** method to perform the **gain** calibration of the camera pixels. This calibration process is done using the ``calibpipe-calculate-camcalib-coefficients`` tool.

The following parameters shall be provided:

* **input_url**: CTAO HDF5 files for DL1 calibration monitoring.
* **allowed_tels**: Optional list of allowed telescope IDs, others will be ignored.
* **faulty_pixels_fraction**: Minimum fraction of faulty camera pixels to identify regions of trouble.
* **squared_excess_noise_factor**: Excess noise factor squared: :math:`1 + \frac{\text{Var}(\text{Gain})}{\text{Mean}(\text{Gain})^2}`.
* **window_width**: Width of the window used for the image extraction.

Below is an example configuration for the camera calibration using the **FFactor** method. The configuration is designed to perform the camera calibration using the ``calibpipe-calculate-camcalib-coefficients`` tool.

.. literalinclude:: telescope/camera/configuration/calibpipe_calculate_camcalib_coefficients.yaml
  :language: YAML

----------------------------
Additional outlier detection
----------------------------

The additional outlier detection is used to identify and remove outliers from the calibration data.
The outlier detection, based on the deviation from the
expected standard deviation of the number of photoelectrons (**NpeStdOutlierDetector**)
is included in the ``calibpipe-calculate-camcalib-coefficients`` tool.

To configure it, the following fields are required:

* **n_events**: Number of events used for the chunk-wise aggregation of the statistic values of the calibration data.
* **relative_qe_dispersion**: Relative (effective) quantum efficiency dispersion of PMs over the camera.
* **linear_noise_coeff**: Linear noise coefficients [high gain, low gain] or [single gain].
* **linear_noise_offset**: Linear noise offsets [high gain, low gain] or [single gain].
* **quadratic_noise_coeff**: Quadratic noise coefficients [high gain, low gain] or [single gain].
* **quadratic_noise_offset**: Quadratic noise offsets [high gain, low gain] or [single gain].
* **std_range_factors**: Defines the range of acceptable values (lower, upper) in units of standard deviations.

Below is an example configuration to include the additional outlier detection for the camera calibration. The values have been obtained with a fit of the ``std`` of the LST-1 filter scan taken on 2023/05/10:

.. literalinclude:: telescope/camera/configuration/npe_std_outlier_detector.yaml
  :language: YAML

In order to perform the camera calibration with the additional outlier detection the user has to provide the two standard configuration files or a single concatenated configuration file in the CLI.
