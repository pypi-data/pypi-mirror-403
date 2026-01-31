"""Meteorological data handling module."""

# Python built-in imports
import copy
import errno
import glob
import importlib.resources
import json
import math
import os
import shutil
import tarfile
import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

# Third-party imports
import astropy.units as u
import cdsapi
import molecularprofiles.utils.grib_utils as gu
import numpy as np
import rdams_client as rc
import requests
from astropy.coordinates import Latitude, Longitude, angular_separation

# CTA-related imports
from ctapipe.core.component import Component
from ctapipe.core.traits import (
    Float,
    Int,
    Path,
    Unicode,
)

from ..core.exceptions import IntermittentError

# Internal imports
from .templates import request_templates


class MeteoDataHandler(Component):
    """Abstract class for meteo data handling."""

    dataset = Unicode(
        default_value="ds083.2",
        help="Meteorological dataset name",
        allow_none=False,
    ).tag(config=True)
    gridstep = Float(default_value=1.0, help="Meteo data grid step in degrees").tag(
        config=True
    )
    update_frequency = Int(
        default_value=6,
        help="Frequency at which new meteorological data is available in hours",
    ).tag(config=True)
    update_tzinfo = Unicode(
        default_value="UTC",
        help="IANA-compliant time zone base for the meteo data updates",
    ).tag(config=True)
    data_path = Path(
        default_value="/tmp/meteo_data/",
        file_ok=False,
        help="Path where the meteorological data shall be stored",
    ).tag(config=True)
    timeout = Int(default_value=600, help="Request timeout limit in seconds").tag(
        config=True
    )

    def __init__(self, config=None, parent=None, das=None, **kwargs):
        super().__init__(config, parent, **kwargs)
        try:
            os.makedirs(self.data_path, exist_ok=True)
        except OSError as error:
            if error.errno != errno.EEXIST:
                raise
        if das is not None:
            self.request = json.loads(
                importlib.resources.files(request_templates)
                .joinpath(f"{das}.json")
                .read_text()
            )
        self.start = None
        self.stop = None

    def _untar(self):
        """Unpack compressed grib2 files."""
        tar_files = list(glob.glob(os.path.join(self.data_path, "*.tar")))
        for compressed_file in tar_files:
            with tarfile.open(compressed_file) as my_tar:
                my_tar.extractall(self.data_path)
            os.remove(compressed_file)

    def time_rounder(self, timestamp, up=None):
        """
        Round a given timestamp to the nearest DAS update timestamp.

        This function rounds the given timestamp to the nearest multiple of the DAS update frequency.
        The rounding is done with respect to a fixed epoch (2000-01-01 00:00:00 UTC).

        Parameters
        ----------
        timestamp : datetime.datetime
            The timestamp to be rounded.
        up : bool, optional
            If True, round up to the next nearest DAS update timestamp.
            If False, round down to the previous nearest DAS update timestamp.

        Returns
        -------
        datetime.datetime
            The rounded timestamp.
        """
        epoch = datetime(
            2000, 1, 1, 0, 0, 0, 0, tzinfo=ZoneInfo(self.update_tzinfo)
        ).astimezone(timezone.utc)
        multiple = timedelta(hours=self.update_frequency)
        low = ((timestamp - epoch) // multiple) * multiple
        high = low + multiple
        if up is True:
            return high + epoch
        if up is False:
            return low + epoch
        if abs((high + epoch) - timestamp) < abs(timestamp - (low + epoch)):
            return high + epoch
        return low + epoch

    def get_near_gridpoints(self, latitude, longitude):
        """
        Get closest meteorological data point and a grid box, surrounding the observatory.

        The interpolation grids of the meteorological systems
        is assumed to start at (0,0) and be defined w.r.t. WGS84.

        Parameters
        ----------
        latitude : astropy.coordinates.Latitude
            Latitude of the observatory location.
        longitude : astropy.coordinates.Longitude
            Longitude of the observatory location.

        Returns
        -------
        nearest_grid_point : tuple(float, float)
            Longitude and latitude of the nearest grid point.
        box_coordinates : list(tuple(float, float))
            List of coordinates (longitude, latitude) of four grid points forming a box
            around the observatory location.
        """
        lon = longitude.to_value(u.deg)
        lat = latitude.to_value(u.deg)
        box_coordinates = [
            (
                Longitude(
                    angle=math.floor(lon / self.gridstep) * self.gridstep,
                    unit=u.deg,
                    wrap_angle=180 * u.deg,
                ),
                Latitude(
                    angle=math.floor(lat / self.gridstep) * self.gridstep, unit=u.deg
                ),
            ),
            (
                Longitude(
                    angle=(math.floor(lon / self.gridstep) + 1) * self.gridstep,
                    unit=u.deg,
                    wrap_angle=180 * u.deg,
                ),
                Latitude(
                    angle=math.floor(lat / self.gridstep) * self.gridstep, unit=u.deg
                ),
            ),
            (
                Longitude(
                    angle=math.floor(lon / self.gridstep) * self.gridstep,
                    unit=u.deg,
                    wrap_angle=180 * u.deg,
                ),
                Latitude(
                    angle=(math.floor(lat / self.gridstep) + 1) * self.gridstep,
                    unit=u.deg,
                ),
            ),
            (
                Longitude(
                    angle=(math.floor(lon / self.gridstep) + 1) * self.gridstep,
                    unit=u.deg,
                    wrap_angle=180 * u.deg,
                ),
                Latitude(
                    angle=(math.floor(lat / self.gridstep) + 1) * self.gridstep,
                    unit=u.deg,
                ),
            ),
        ]

        distances = [
            angular_separation(longitude, latitude, *grid_point).to_value()
            for grid_point in box_coordinates
        ]

        nearest_grid_point = box_coordinates[np.argmin(distances)]

        return nearest_grid_point, box_coordinates

    def create_request(self, start, stop, latitude, longitude, nearest_point=True):
        """To be implemented in the child classes."""

    def request_data(self):
        """To be implemented in the child classes."""

    def merge_data(self):
        """Merge meteo data.

        Creates an ecsv file that contains an astropy.core.Table
        with the meteorological data from grib files,
        downloaded from DAS.
        """
        gu.convert_to_text(self.data_path)
        gu.merge_ecsv_files(self.data_path)

    def cleanup(self):
        """Remove temporary files."""
        shutil.rmtree(self.data_path)


class GDASDataHandler(MeteoDataHandler):
    """GDAS/NCAR meteorological data handler."""

    dataset = Unicode("ds083.2").tag(config=True)
    gridstep = Float(1.0).tag(config=True)
    update_frequency = Int(6).tag(config=True)

    def __init__(self, config=None, parent=None, **kwargs):
        super().__init__(config, parent, das="gdas", **kwargs)
        rc.setup_logging(self.log.level)

    def create_request(self, start, stop, latitude, longitude, nearest_point=True):
        """
        Create a request for GDAS data.

        Parameters
        ----------
        start : datetime.datetime
            The start time for the data request.
        stop : datetime.datetime
            The stop time for the data request.
        latitude : astropy.coordinates.Latitude
            Latitude of the location for which data is requested.
        longitude : astropy.coordinates.Longitude
            Longitude of the location for which data is requested.
        nearest_point : bool, optional
            If True, request data for the nearest grid point.
            If False, request data for a grid box surrounding the location.
            Default is True.
        """
        self.start = self.time_rounder(start, up=True)
        self.stop = self.time_rounder(stop, up=False)
        point, box = self.get_near_gridpoints(latitude, longitude)
        timeseries = (
            f"{self.start.strftime('%Y%m%d%H%M')}/to/{self.stop.strftime('%Y%m%d%H%M')}"
        )
        self.log.debug(timeseries)
        self.request.update({"dataset": self.dataset})
        self.request.update({"date": timeseries})
        if nearest_point:
            lon = point[0].to_value(unit=u.deg)
            lat = point[1].to_value(unit=u.deg)
            self.request.update({"nlat": lat})
            self.request.update({"slat": lat})
            self.request.update({"elon": lon})
            self.request.update({"wlon": lon})
        else:
            self.request.update({"nlat": box[3][1].to_value(unit=u.deg)})
            self.request.update({"slat": box[0][1].to_value(unit=u.deg)})
            self.request.update({"elon": box[3][0].to_value(unit=u.deg)})
            self.request.update({"wlon": box[0][0].to_value(unit=u.deg)})
        self.log.debug("Created DAS request:\n%s", json.dumps(self.request, indent=4))

    def _is_request_ready(self, request_id):
        """Check if a request is ready.

        Parameters
        ----------
        request_id: int
            Unique identification number of the request for GDAS data.

        Returns
        -------
        Boolean
        """
        start = time.time()
        while True:
            now = time.time()
            if (now - start) > self.timeout:
                self.log.error(
                    "Maximum waiting time for the request exceeded. Exiting..."
                )
                return False

            res = rc.get_status(request_id)
            try:
                request_status = res["data"]["status"]
            except KeyError as err:
                self.log.error("Can't get request status: %s", err)
                self.log.error("Response content: \n%s", res)
                rc.purge_request(request_id)
                return False
            if request_status == "Completed":
                return True
            time.sleep(10)  # Sleep ten seconds before retry

        return False

    def request_data(self):
        """Request GDAS data."""
        response = rc.submit_json(self.request)
        request_id = response.get("data", {}).get("request_id")
        if request_id is None:
            self.log.critical(
                "Request ID can't be retrieved, request can't be purged."
                "Manual intervention is required to purge the request!\n"
                "Response content:\n%s",
                json.dumps(response, indent=4),
            )
            self.log.warning("Activating exception scenario")
            return 1
        if response.get("http_response") != 200:
            self.log.error(
                "Request to GDAS failed with response code %s\nResponse content:\n%s\nRequest content:\n%s\n",
                response.get("http_response"),
                json.dumps(response, indent=4),
                json.dumps(self.request, indent=4),
            )
            self.log.error("Purging request")
            rc.purge_request(request_id)
            self.log.warning("Activating exception scenario")
            return 1

        self.log.debug("Response content:\n%s", json.dumps(response, indent=4))
        if self._is_request_ready(request_id):
            rc.download(request_id, f"{self.data_path}/")
            rc.purge_request(request_id)
            self._untar()
            self.merge_data()
            return 0
        rc.purge_request(request_id)
        self.log.warning("Activating exception scenario")
        return 1


class ECMWFDataHandler(MeteoDataHandler):
    """ECMWF/Copernicus meteorological data handler."""

    dataset = Unicode("reanalysis-era5-pressure-levels").tag(config=True)
    gridstep = Float(0.25).tag(config=True)
    update_frequency = Int(1).tag(config=True)

    def __init__(self, config=None, parent=None, **kwargs):
        super().__init__(config, parent, das="copernicus", **kwargs)
        self.requests = []

    def create_request(self, start, stop, latitude, longitude, nearest_point=False):
        """
        Create a request for ECMWF/Copernicus meteorological data.

        This method prepares a request for meteorological data from the ECMWF/Copernicus dataset
        for a specified time range and location. The request can be for the nearest grid point
        or a grid box surrounding the specified location.

        Parameters
        ----------
        start : datetime.datetime
            The start time for the data request.
        stop : datetime.datetime
            The stop time for the data request.
        latitude : astropy.coordinates.Latitude
            Latitude of the location for which data is requested.
        longitude : astropy.coordinates.Longitude
            Longitude of the location for which data is requested.
        nearest_point : bool, optional
            If True, request data for the nearest grid point.
            If False, request data for a grid box surrounding the location.
            Default is False.

        Returns
        -------
        None
        """
        self.start = self.time_rounder(start, up=True)
        self.stop = self.time_rounder(stop, up=False)
        point, box = self.get_near_gridpoints(latitude, longitude)
        area_of_interest = []
        if nearest_point:
            lon = point[0].to_value(unit=u.deg)
            lat = point[1].to_value(unit=u.deg)
            area_of_interest = [lat, lon, lat, lon]
        else:
            area_of_interest = [
                box[0][1].to_value(unit=u.deg),
                box[0][0].to_value(unit=u.deg),
                box[3][1].to_value(unit=u.deg),
                box[3][0].to_value(unit=u.deg),
            ]
        self.request.update({"area": area_of_interest})
        years = [str(self.start.year), str(self.stop.year)]
        months = [str(self.start.month), str(self.stop.month)]
        days = [str(self.start.day), str(self.stop.day)]
        if self.start.day == self.stop.day:
            hours = [
                [
                    f"{h:02d}:00"
                    for h in range(
                        self.start.hour, self.stop.hour + 1, self.update_frequency
                    )
                ]
            ]
        else:
            hours = [
                [
                    f"{h:02d}:00"
                    for h in range(self.start.hour, 24, self.update_frequency)
                ],
                [
                    f"{h:02d}:00"
                    for h in range(0, self.stop.hour + 1, self.update_frequency)
                ],
            ]
        for i in range(len(hours)):
            self.request.update({"year": years[i]})
            self.request.update({"month": months[i]})
            self.request.update({"day": days[i]})
            self.request.update({"time": hours[i]})
            self.requests.append(copy.deepcopy(self.request))

    def request_data(self):
        """Request ECMWF data.

        The data is requested from the ECMWF/Copernicus server using the cdsapi library.

        """
        client = cdsapi.Client()
        for i, request in enumerate(self.requests):
            self.log.debug(request)
            client.retrieve(
                self.dataset, request, f"{self.data_path}/copernicus_{i}.grib"
            )
        self.merge_data()
        return 0


class CO2DataHandler(MeteoDataHandler):
    """Mauna Loa CO2 data handler."""

    dataset = Unicode(
        "https://scrippsco2.ucsd.edu/assets/data/atmospheric/stations/in_situ_co2/monthly/monthly_in_situ_co2_mlo.csv"  # pylint: disable=line-too-long
    ).tag(config=True)

    def __init__(self, config=None, parent=None, **kwargs):
        super().__init__(config, parent, **kwargs)

    def request_data(self):
        """
        Request CO2 data from the Mauna Loa Observatory.

        Returns
        -------
        int
            Returns 0 on successful data retrieval.

        Raises
        ------
        IntermittentError
            If the request to the dataset URL times out.
        """
        try:
            response = requests.get(
                self.dataset, allow_redirects=True, timeout=self.timeout
            )
        except requests.exceptions.Timeout:
            raise IntermittentError(
                f"Keeling curve server {self.dataset} is not accessible"
            )
        with open(f"{self.data_path}/macobac.csv", "wb") as keeling_curve_file:
            keeling_curve_file.write(response.content)
        return 0
