from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np
from traitlets.config import Config

from calibpipe.utils.observatory import Observatory

cta_south_config = {
    "Observatory": {
        "name": "CTAO-South",
        "latitude": -24.6272,
        "longitude": -70.4039,
        "elevation": 2200,
        "seasons": [
            {
                "Season": {
                    "name": "summer",
                    "start_month": 11,
                    "start_day": 1,
                    "stop_month": 5,
                    "stop_day": 1,
                }
            },
            {
                "Season": {
                    "name": "winter",
                    "start_month": 5,
                    "start_day": 2,
                    "stop_month": 10,
                    "stop_day": 31,
                }
            },
        ],
    }
}

cta_south_obs = Observatory(Config(cta_south_config))

cta_north_config = {
    "Observatory": {
        "name": "CTAO-North",
        "latitude": 28.761795,
        "longitude": -17.890701,
        "elevation": 2150,
        "seasons": [
            {
                "Season": {
                    "name": "spring",
                    "start_month": 5,
                    "start_day": 1,
                    "stop_month": 6,
                    "stop_day": 20,
                }
            },
            {
                "Season": {
                    "name": "summer",
                    "start_month": 6,
                    "start_day": 21,
                    "stop_month": 10,
                    "stop_day": 4,
                }
            },
            {
                "Season": {
                    "name": "winter",
                    "start_month": 11,
                    "start_day": 16,
                    "stop_month": 4,
                }
            },
            {
                "Season": {
                    "name": "fall",
                    "start_month": 10,
                    "start_day": 5,
                    "stop_month": 11,
                    "stop_day": 15,
                }
            },
        ],
    }
}
cta_north_obs = Observatory(Config(cta_north_config))

dates = np.arange(
    datetime(2023, 1, 1, 2, tzinfo=ZoneInfo("UTC")),
    datetime(2023, 12, 31, 2, tzinfo=ZoneInfo("UTC")),
    timedelta(days=1),
).astype(datetime)


def get_dusk_and_dawn(tstamp):
    return cta_south_obs.get_astronomical_night(tstamp)


def test_astral():
    for t in dates:
        dusk, dawn = get_dusk_and_dawn(t)
        print("DATE", t, "DUSK", dusk, "DAWN", dawn)
        dt = dawn - dusk
        print("hours of data to be downloaded", dt)
        dt_max = timedelta(hours=18)
        assert dt < dt_max


test_astral()
