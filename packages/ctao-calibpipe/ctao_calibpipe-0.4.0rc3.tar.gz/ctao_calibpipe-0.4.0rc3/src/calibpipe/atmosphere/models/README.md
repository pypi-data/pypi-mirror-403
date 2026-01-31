In this directory, we store (mockup) reference atmospheric models. Those models are
- reference MDPs
- reference atmospheric models (Corsika simulation inputs)
- reference ozone profiles

For the moment we have created only the MDPs (more urgent for DPPS release 0). The models were created using the dataset "ERA5 monthly averaged data on pressure levels from 1959 to present" provided by the Copernicus service. This choice should be confirmed.
We provide an example script, Reference_MDP_calculator.py, that produces an MDP for La Palma, intermediate season. This script is made to be run in Climate Data Store (CDS) server toolbox. It loads the data in the CDS cache, analyses them, and produces a list of scaled molecular number densities per altitude level.

Some notes concerning the mockup reference MDPs:
1. How many years worth of data do we need to process? Currently, we process only one year (2022). The processing time in the CDS toolbox is a few minutes. The queue time varies, and is independent of the requested data, but usually doesn't exceed a few minutes also. However, the climate normals are 30 years long.
2. The current requests are downloading and averaging the data from a few grid points, e.g. 5 grid points for La Palma. Shall we restrict to the closest one, as stated in the requirements support document? However, this document was written with different datasets in mind.
3. The MDPs have been created with nighttime data, however, we considered the same nighttime for the whole year. That's wrong, but probably good enough for mockup MDPs. It can be corrected rather easily.
4. Seasons definition: as the requirement support document states, we considered two seasons for Atacama and three for La Palma. Their definition is somewhat reasonable, but of course, it needs to be verified.
5. Atmospheric scale height: the issue is described [here](https://gitlab.cta-observatory.org/cta-array-elements/ccf/mdps/-/issues/24): in order to resolve it, we need to find the mean atmospheric temperature over the two observatories for every season in question. Or simply calculate it using climatological data.
