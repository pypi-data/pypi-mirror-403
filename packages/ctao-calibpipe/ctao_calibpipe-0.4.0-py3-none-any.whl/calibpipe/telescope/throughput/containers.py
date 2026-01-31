"""Containers to keep optical throughput data and metadata."""

import numpy as np
from astropy.time import Time
from ctapipe.core import Container, Field

NAN_TIME = Time(0, format="mjd", scale="tai")


class OpticalThoughtputContainer(Container):
    """Optical throughput calibration coefficient and analysis results for a single telescope."""

    mean = Field(
        np.nan,
        "Mean optical throughput from the selected calibration method",
        type=np.float64,
        allow_none=False,
    )
    median = Field(
        np.nan,
        "Optical throughput from the selected calibration method",
        type=np.float64,
        allow_none=False,
    )
    std = Field(
        np.nan,
        "Optical throughput from the selected calibration method",
        type=np.float64,
        allow_none=False,
    )
    sem = Field(
        np.nan,
        "Standard error of the mean optical throughput from the selected calibration method",
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
        description="Starting timestamp of validity for the selected throughput.",
        type=Time,
        allow_none=False,
    )
    time_end = Field(
        NAN_TIME,
        description="Ending timestamp of validity for the selected throughput.",
        type=Time,
        allow_none=False,
    )
    obs_id = Field(
        -1,
        description="ID of the observation block for validity",
        type=np.int32,
        allow_none=False,
    )
    n_events = Field(
        0,
        description="Number of muon rings used to calculate the throughput",
        type=np.int64,
        allow_none=False,
    )
