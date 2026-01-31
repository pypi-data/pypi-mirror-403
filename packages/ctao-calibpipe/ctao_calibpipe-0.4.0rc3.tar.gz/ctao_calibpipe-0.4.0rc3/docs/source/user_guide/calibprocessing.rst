============================
Calibration event processing
============================

------
Common
------

The common first step in the calibration process is **image extraction**. In this step, pixel-wise quantities such as charges, peak times, and/or variances are computed from the waveforms, which conform to the CTAO DL0 Data Model. This is typically done by integrating or otherwise reducing the waveform data for each pixel. The image extraction is performed using the `ctapipe-process` tool.

* **DataWriter**: Responsible for saving the extracted quantities to a file, following the reference implementation of the ctapipe DL1 data format.
* **EventTypeFilter**: Used to select the calibration events that will be processed.

The configuration required for image extraction varies depending on the type of calibration event. The following standard fields must be provided (except when using the `VarianceExtractor`):

* **window_shift**: Defines the shift of the integration window relative to the `peak_index` (`peak_index - shift`).
* **window_width**: Defines the width of the integration window.
* **apply_integration_correction**: Indicates whether to apply the integration window correction.

-----------------
Flat-field events
-----------------

The standard processing of flat-field events for the camera calibration uses
the **LocalPeakWindowSum** extractor, which sums the signal in
a window around the peak in each pixel's waveform.

Below is an example configuration for the camera calibration using flat-field events.
It includes the necessary components for image extraction,
event type filtering, and  data writing.
The configuration is designed to handle flat-field events
and performs the required processing steps using the ``ctapipe-process`` tool.

.. literalinclude:: telescope/camera/configuration/ctapipe_process_flatfield.yaml
  :language: YAML

-------------------
Sky pedestal events
-------------------

The standard processing of sky pedestal events for the camera calibration uses
the **FixedWindowSum** extractor, which sums the signal within a fixed, user-defined window.

In addition to the standard fields, the **peak_index**, indicating the signal summing reference point, must be provided.

Below is an example configuration for the camera calibration using sky pedestal events. It includes the necessary components for image extraction, event type filtering, and data writing. The configuration is designed to handle sky pedestal events and performs the required processing steps using the ``ctapipe-process`` tool.

.. literalinclude:: telescope/camera/configuration/ctapipe_process_pedestal.yaml
  :language: YAML

The standard processing of sky pedestal events for the pointing correction uses the
**VarianceExtractor**, which calculates the signal variance in each waveform.

Below is an example configuration for the pointing correction using sky pedestal events. It includes the necessary components for variance image extraction, event type, and  data writing. The configuration is designed to handle variance images of sky pedestal events and performs the required processing steps using the ``ctapipe-process`` tool.

.. literalinclude:: telescope/pointing/configuration/ctapipe_process_pointing.yaml
  :language: YAML

-----------
Muon events
-----------

The standard processing of muon events for the optical throughput uses the
**GlobalPeakWindowSum** extractor, which sums signal in a window
around the peak position of the global average waveform.

In addition to the standard parameters, the **pixel_fraction** is required to identify the position of the integration window.

Below is an example configuration for the calibration pipeline of the muon processing. It includes the necessary components for image extraction, event type filtering, image cleaning, muon processing/fitting, and data writing. The configuration is designed to handle muon events and performs the required processing steps using the ``ctapipe-process`` tool.

.. literalinclude:: telescope/throughput/configuration/ctapipe_process_muon_image.yaml
  :language: YAML

The processing of muon events goes beyond the standard image extraction and requires additional steps, the extraction of muon parameters. We are also providing two more configuration section, that are mandatory for the muon processing. These sections are:

* **Image cleaning**: The image cleaning step is responsible for removing noise pixels from the extracted images. It uses the ctapipe's ImageCleaner class to apply a specific cleaning algorithm to the images.
* **Muon processing/fitting**: This step is responsible for processing and fitting the muon events. It uses the ctapipe's MuonProcessor class to perform the muon reconstruction and fitting.

.. literalinclude:: telescope/throughput/configuration/ctapipe_process_muon_fitter.yaml
  :language: YAML


The fields of these two configurations have been already presented above. It is worth noticing that for the muon processing the DL1 images do not have to be stored in the output file for the further analysis. In order to perform the whole muon processing the user has to provide the two standard configuration files or a single concatenated configuration file in the CLI.
