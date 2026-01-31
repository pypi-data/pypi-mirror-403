"""Containers to keep atmospheric data and metadata."""

# Python built-in imports
import datetime

# Third-party imports
import astropy.units as u
import numpy as np
from astropy.units.cds import ppm

# CTA-related imports
from ctapipe.core import Container, Field

REFERENCE_ATMOSPHERIC_MODEL_VER_DESC = "Atmospheric model version"


class AtmosphericModelContainer(Container):
    """Container for the atmospheric models."""

    start = Field(None, "Start of use timestamp")
    stop = Field(None, "End of use timestamp")
    version = Field(None, REFERENCE_ATMOSPHERIC_MODEL_VER_DESC, allow_none=False)
    current = Field(
        True, "Boolean flag showing whether a given model is currently in use"
    )
    season = Field(None, "Season alias")
    name_Observatory = Field(None, "Reference observatory name")  # noqa: N815
    version_Observatory = Field(None, "Reference observatory configuration version")  # noqa: N815


class MacobacContainer(Container):
    """Container for 12 months average CO2 background concentration."""

    co2_concentration = Field(
        np.nan * ppm, "12 months average CO2 background concentration", unit=ppm
    )
    estimation_date = Field(
        None, "Date of MACOBAC estimation", type=datetime.date, allow_none=False
    )
    version = Field("0.0.0", REFERENCE_ATMOSPHERIC_MODEL_VER_DESC)


class MolecularAtmosphericProfileMetaContainer(Container):
    """
    Container for molecular atmospheric metadata.

    Container that stores the metadata associated
    to the molecular atmospheric part of the model.
    """

    data_assimilation_system = Field("", "Data assimilation system")
    dataset = Field("", "Dataset of the given data assimilation system")
    description = Field("", "Optional description field")
    version = Field(None, REFERENCE_ATMOSPHERIC_MODEL_VER_DESC, allow_none=False)


class MolecularAtmosphericProfileContainer(Container):
    """Container for molecular atmospheric profile."""

    altitude = Field(None, "Altitude", unit=u.km, ndim=1)
    pressure = Field(None, "Pressure", unit=u.hPa, ndim=1)
    temperature = Field(None, "Temperature", unit=u.K, ndim=1)
    partial_water_pressure = Field(
        None,
        "Partial water vapor pressure, expressed as a fraction of the total pressure",
        ndim=1,
    )
    refractive_index_m_1 = Field(None, "Refractive index N-1", ndim=1)
    atmospheric_density = Field(
        None, "Atmospheric density", unit=u.g / (u.cm**3), ndim=1
    )
    atmospheric_thickness = Field(
        None, "Atmospheric thickness", unit=u.g / (u.cm**2), ndim=1
    )
    version = Field(None, REFERENCE_ATMOSPHERIC_MODEL_VER_DESC, allow_none=False)


class MolecularDensityContainer(Container):
    """Container for molecular density profile."""

    season = Field(None, "Atmospheric model season alias.", ndim=1)
    density = Field(None, "Molecular number density", unit=1 / (u.cm**3))
    version = Field(None, REFERENCE_ATMOSPHERIC_MODEL_VER_DESC, allow_none=False)


class RayleighExtinctionContainer(Container):
    """Container for Rayleigh extinction profile."""

    wavelength = Field(None, "Wavelength", unit=u.nm, ndim=1, allow_none=False)
    altitude = Field(None, "Altitude", unit=u.km, ndim=2, allow_none=False)
    AOD = Field(None, "Absolute Optical Depth (AOD)", ndim=2, allow_none=False)
    version = Field(None, REFERENCE_ATMOSPHERIC_MODEL_VER_DESC, allow_none=False)


class SelectedAtmosphericModelContainer(Container):
    """Container for atmosphere model selection."""

    date = Field(
        None, "Date of reference model selection.", type=datetime.date, allow_none=False
    )
    version = Field(None, REFERENCE_ATMOSPHERIC_MODEL_VER_DESC, allow_none=False)
    season = Field(None, "Atmospheric model season alias.", ndim=1)
    site = Field(None, "Observation site name", type=str, allow_none=False)
    provenance = Field(
        None,
        "Model data provenance. Can be `timestamp`, `GDAS` or `ECMWF`.",
        type=str,
        allow_none=False,
    )
