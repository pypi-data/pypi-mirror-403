# Third-party imports  # noqa: D100
import astropy.units as u

# CTA-related imports
from ctapipe.core import Container, Field


class ObservatoryContainer(Container):
    """Observatory container."""

    name = Field(None, "Observatory name")
    latitude = Field(None, "Observatory latitude", unit=u.deg)
    longitude = Field(None, "Observatory longitude", unit=u.deg)
    elevation = Field(None, "Observatory elevation", unit=u.m)
    version = Field(None, "Observatory configuration version")


class SeasonContainer(Container):
    """Season container."""

    start = Field(None, "Season start timestamp")
    stop = Field(None, "Season stop timestamp")
    name = Field(None, "Season name")
    alias = Field(None, "Season alias")
    name_Observatory = Field(None, "Reference observatory name")  # noqa: N815
    version_Observatory = Field(None, "Reference observatory configuration version")  # noqa: N815
