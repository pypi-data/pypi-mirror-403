==================
Molecular profiles
==================

------
Common
------

Here we describe the common field in all molecular atmosphere calibration configuration files, which is the MolecularAtmosphereCalibrator. To construct a MolecularAtmosphereCalibrator one has to provide the following fields:

* **Observatory**: to construct an observatory object one has to provide a name, the geographical coordinates, the altitude above sea level and a definition for the start and the end of each season.
* **timestamp**: the provided timestamp will be used in the creation of the data request to the desired Data Assimilation System (DAS).
* **atmo_profile_out**: the molecular profile that can be used as input for Corsika simulations.
* **altitude_profile_list**: the altitude bins where the parameters of the aforementioned molecular profile will be given.
* **rayleigh_extinction_file**: an extinction profile due to Rayleigh scattering.
* **rayleigh_scattering_altitude_list**: the first altitude bins for the aforementioned extinction profile. It is important to have a high granularity close to the observation level, thus it is often different than the altitude bins list we provide for the molecular profile.
* **wavelength limits**: defines the wavelength range that the Rayleigh extinction profile is calculated.

-------------------------------------------------------------------
12 Months Average CO\ :sub:`2` BAckground Concentration (12MACOBAC)
-------------------------------------------------------------------

This configuration file is used as an input for the tool provides the  CO\ :sub:`2` background concentration. The data are provided by the Scripps Institute of Oceanography. In particular, we download a csv file that stores the Keeling curve data. The Keeling curve illustrates the evolution of the CO\ :sub:`2` background concentration as a function of time. The measurements are taking place in Mauna Loa, however the results should be valid for any pristine location on earth. The following fields are present:

* **dataset**: url with the address of the Keeling curve data.
* **timeout**: request timeout limit in seconds.

Please find below an example configuration.

.. literalinclude:: atmosphere/configuration/calculate_macobac.yaml
  :language: YAML


--------------------------------------------
Contemporary Molecular Density Profile (MDP)
--------------------------------------------

This configuration file is used as an input to the workflow that produces a contemporary MDP. The user should choose the desired DAS via the meteo_data_handler field.

* **meteo_data_handler**: The two DAS that are currently implemented are GDAS and ECMWF. So the user has to fill this field with either GDASDataHandler or ECMWFDataHandler

Then the user has to fill the following fields:

* **dataset**: name of the dataset. We currently use ds083.2 from GDAS and ERA-5 (reanalysis-era5-pressure-levels) from ECMWF.
* **gridstep**: granularity of the DAS in degrees.
* **update_frequency**: frequency at which new meteorological data is available in hours.
* **update_tzinfo**: IANA-compliant time zone base for the meteo data updates.

Additionally the user has to provide:

* **observatory**: observatory of interest, e.g. CTAO-North.
* **timestamp**: a timestamp within the night of interest. CalibPipe retrieves the date from the provided timestamp and calculates the astronomical dusk and dawn for the observatory of interest (taking into account its geographical coordinates and altitude above sea level) in order to form the data request. If the user provide a timestamp corresponding to daytime, they will get an error message.

Please find below an example configuration.

.. literalinclude:: atmosphere/configuration/create_molecular_density_profile.yaml
  :language: YAML

----------------------------------
Select reference atmospheric model
----------------------------------

With the help of the produced MDP we can select the reference seasonal atmospheric model that matches best with the atmospheric conditions over an observatory site at a given night. The selection is based on the molecular number density at 15km above sea level. In order to run this workflow the user has to provide an observatory site, a timestamp and to select a meteo_data_handler, similarly as above.

Please find below an example configuration.

.. literalinclude:: atmosphere/configuration/select_reference_atmospheric_model.yaml
  :language: YAML

-------------------------
Produce atmospheric model
-------------------------

A molecular atmospheric model consists of a molecular profile (input to Corsika, dictates the shower development & Cherenkov light creation) and a Molecular Extinction Profile (MEP) which is an input to sim_telarray and provides the light extinction profile due to molecular scattering or absorption. Currently only the Rayleigh scattering contribution is fully implemented. In order to run this tool the user has to provide to the same fields as above.

Please find below an example configuration.

.. literalinclude:: atmosphere/configuration/create_molecular_atmospheric_model.yaml
  :language: YAML
