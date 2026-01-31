"""Containers to keep optical PSF data and metadata."""

import numpy as np
from astropy.time import Time
from ctapipe.core import Container, Field

NAN_TIME = Time(0, format="mjd", scale="tai")


class OpticalPSFContainer(Container):
    """Optical throughput calibration coefficient and analysis results for a single telescope."""

    slope = Field(
        np.nan,
        "Slope of the optical PSF from fitting the ring width as a function of the ring radius",
        type=np.float64,
        allow_none=False,
    )
    intercept = Field(
        np.nan,
        "Intercept of the optical PSF from fitting the ring width as a function of the ring radius",
        type=np.float64,
        allow_none=False,
    )
    slope_err = Field(
        np.nan,
        "Error of the slope",
        type=np.float64,
        allow_none=False,
    )
    intercept_err = Field(
        np.nan,
        "Error of the intercept",
        type=np.float64,
        allow_none=False,
    )
    chi2 = Field(
        np.nan,
        "Chi2 of the fit",
        type=np.float64,
        allow_none=False,
    )
    method = Field(
        "None",
        "Calibration method used",
        type=str,
        allow_none=False,
    )
    time_start = Field(
        NAN_TIME,
        description="Starting timestamp of validity for the PSF",
        type=Time,
        allow_none=False,
    )
    time_end = Field(
        NAN_TIME,
        description="Ending timestamp of validity for the PSF",
        type=Time,
        allow_none=False,
    )
    obs_id = Field(
        -1,
        description="ID of the observation block for validity",
        type=np.int32,
        allow_none=False,
    )
