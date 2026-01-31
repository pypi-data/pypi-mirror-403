==================
Product definition
==================

The calibration pipeline is a DPPS subsystem ensuring the best possible instrument accuracy and
precision under all kinds of observation conditions. Its task is the production of calibration coefficients at
DL0-DL3 data levels and for Category B & C data. Towards that goal, calibration pipeline analyses physics,
monitoring and service data of the CTAO instruments, as well as external to CTAO meteorological data.

========================
Functional decomposition
========================

.. image:: ../_static/FD.png

------------------------
Atmospheric calibrations
------------------------

Atmosphere is the medium where γ-rays interact and Cherenkov radiation is produced and propagates through.
A continuous monitoring and calibration of the state of the atmosphere is required in CTAO.
The atmospheric calibration is split into molecular atmosphere calibration and aerosols / clouds calibration.
The split is based on the sources of the calibration data: for the molecular atmosphere calibration is based on meteorological data while aerosols / clouds calibration is based mostly on data coming from CTAO monitoring devices (e.g. LIDAR, FRAM) and made available to DPPS through ACADA.


Molecular atmosphere calibration
--------------------------------

The modeling of the molecular component of the atmosphere affects both the shower development and the Cherenkov light transmission. The purpose of the calibration pipeline is to provide
the best possible instrumental accuracy and precision under all kinds of observation conditions. In the context of molecular atmosphere calibration, this is translated into
the selection / production and storage of atmospheric profiles for showers simulation and the selection / production and storage of Molecular Extinction Profiles.
The calibration pipeline will provide two categories of data. Category-B will be provided the next day,
after an observation night, while category-C will be of the highest quality and should be provided within
a time period of two to four weeks. For category-C it currently uses the ERA-5 datasets of ECMWF. ERA-5 provides hourly estimates on 37 pressure level
(from 1000hPa to 1hPa, roughly corresponding to 45km a.s.l.) with a geographical resolution of :math:`0.25^{\circ}\times0.25^{\circ}`.
It is an early reanalysis data with a latency of 5 days, publicly available via European Union `Copernicus service <https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-pressure-levels?tab=overview>`_.
The data is free but the creation of an account is required for data retrieval. For category-B, calibration pipeline uses the GDAS dataset ds083.2, available via the `Research Data Archive <https://rda.ucar.edu/datasets/ds083.2/>`_.
Similarly, the data is free but the creation of an account is required for data retrieval. ds083.2 provides estimates in 6 hours interval, up to ~26 km a.s.l. with a geographical resolution of :math:`1^{\circ}\times1^{\circ}`. The data become publicly available in near real time, so they can be used for "next day" calibration.

Please find below a mind map of the molecular atmosphere calibration usecases. The colour code depicts the status of the implementation.

.. image:: diagrams/legend.svg
.. image:: diagrams/molecular_atmosphere.svg


Aerosols/clouds calibration
---------------------------

-----------------
Array calibration
-----------------

Relative calibration of the telescope's throughput based on reconstructed gamma-like showers energies. It is based on the expectation that all telescopes observing the same shower should reconstruct the same energy. It is complementary to muon rings calibration, helping to mitigate statistical uncertainties in cases where the muon trigger rate is low, particularly for SSTs. Moreover, unlike muon rings calibration, it uses directly the light from the showers, helping to resolve
throughput variations with wavelength or crossed airmass. It can be used as an array "flat-fielding" or alternatively as a crosscheck of muon rings calibration. The implementation of the algorithm in based on the study documented in “Cross Calibration of Telescope Optical Throughput Efficiencies using Reconstructed Shower Energies for the Cherenkov Telescope Array”, Astroparticle Physics 75 (2016), pp. 1–7 from Alison Mitchell et al.

---------------------
Telescope calibration
---------------------

Optical throughput calibration via muon rings
---------------------------------------------

Muons rings is the main method of optical throughput calibration.

.. image:: diagrams/muon_calibration.svg

Camera calibration
------------------

.. image:: diagrams/camera_calibration.svg

==================
Command line tools
==================

The command line tools of calibration pipeline are based on `ctapipe tools <https://ctapipe.readthedocs.io/en/latest/user-guide/tools.html>`_.
A tool can be used by typing its name and providing as argument a configuration file in yaml format:

.. code-block:: console

    name_of_the_tool -c configuration_file.yaml

The tools currently provided are:

- calibpipe-create-molecular-density-profile: Produces a contemporary molecular density profile.
- calibpipe-select-reference-atmospheric-model: Selects the closest reference atmospheric model (molecular density profile and Rayleigh extinction profile) for the current observation.
- calibpipe-calculate-macobac: Calculates the average :math:`CO_{2}` background concentration for the previous 12 months.
- calibpipe-calculate-camcalib-coefficients: Calculates the camera calibration coefficients.
- calibpipe-produce-camcalib-test-data: Produces test data for camera calibration unit and integration tests.
- calibpipe-create-molecular-atmospheric-model: Creates an atmospheric model (molecular atmosphere profiles and Rayleigh extinction profile).
- calibpipe-upload-observatory-data: Uploads observatory data to the database.
- calibpipe-upload-atmospheric-model-data: Uploads reference atmospheric model data to the database.
- calibpipe-init-db: Initializes the CalibPipe database and creates required tables.

Example configuration files can be find :doc:`here </user_guide/index>`.
