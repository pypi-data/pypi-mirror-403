============================
Pixel statistics description
============================

The statistical description is assessed based on the image extracted from the interleaved calibration data. The pixel statistics description is done using the ``ctapipe-calculate-pixel-statistics`` tool. In order to produce test data for the camera calibration tools in the calibpipe package, the utility tool ``calibpipe-produce-camcalib-test-data`` can be used with the configuration files below.

The following configuration parameters are required:

* **allowed_tels**: Optional list of allowed telescope IDs, others will be ignored.
* **input_column_name**: Column name of the pixel-wise image data to calculate statistics.
* **output_table_name**: Table name of the output statistics.
* **output_path**: Output filename.

**PixelStatisticsCalculator** component is used to calculate the statistical description of the calibration events. It needs the following fields:

* **stats_aggregator_type**: Name of the StatisticsAggregator subclass to be used.
* **outlier_detector_list**: List of dicts containing the OutlierDetector and configuration to be used.
* **chunk_shift**: Number of samples to shift the aggregation chunk for the calculation of the statistical values.
* **faulty_pixels_fraction**: Minimum fraction of faulty camera pixels to identify regions of trouble.

Additionally, the user can provide the following fields for the **StatisticsAggregator** component:

* **PlainAggregator**: Compute aggregated statistic values from a chunk of images using numpy functions.
* **SigmaClippingAggregator**: Compute aggregated statistic values from a chunk of images using astropy's sigma clipping functions.

Below are examples of configurations for assessing the statistical description of interleaved calibration events using the ``ctapipe-calculate-pixel-statistics`` tool.

**Interleaved pedestal events - charge image**

.. literalinclude:: telescope/camera/configuration/ctapipe_calculate_pixel_stats_sky_pedestal_image.yaml
  :language: YAML

**Interleaved flat-field events - charge image**

.. literalinclude:: telescope/camera/configuration/ctapipe_calculate_pixel_stats_flatfield_image.yaml
  :language: YAML

**Interleaved flat-field events - peak arrival time**

.. literalinclude:: telescope/camera/configuration/ctapipe_calculate_pixel_stats_flatfield_peak_time.yaml
  :language: YAML
