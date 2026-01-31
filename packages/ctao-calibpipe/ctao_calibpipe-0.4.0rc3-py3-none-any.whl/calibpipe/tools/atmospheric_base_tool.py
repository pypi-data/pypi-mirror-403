from datetime import datetime  # noqa: D100

from ctapipe.core.traits import (
    AstroTime,
    CaselessStrEnum,
    Dict,
    Integer,
    Path,
    Unicode,
)

from ..atmosphere.meteo_data_handlers import (
    MeteoDataHandler,
)
from .basic_tool_with_db import BasicToolWithDB


class AtmosphericBaseTool(BasicToolWithDB):
    """Basic tool for atmospheric data processing."""

    meteo_data_handler = CaselessStrEnum(
        values=["GDASDataHandler", "ECMWFDataHandler"],
        default_value="ECMWFDataHandler",
        help="Meteorological data handler name",
    ).tag(config=True)

    observatory = Dict(
        per_key_traits={
            "name": Unicode(),
            "version": Integer(),
        },
        default_value={
            "name": "CTAO-NORTH",
            "version": 1,
        },
        help="Observatory name and configuration version",
    ).tag(config=True)

    timestamp = AstroTime(
        allow_none=False,
        help="A timestamp used to retrieve meteorological data. "
        "Should correspond to a night time of the observatory. ",
    ).tag(config=True)

    output_path = Path(
        "./",
        help="Path to the output folder where the atmospheric model files will be saved",
        allow_none=False,
        directory_ok=True,
        file_ok=False,
    ).tag(config=True)

    output_format = Unicode(
        "ascii.ecsv",
        help="Output files format",
        allow_none=False,
    ).tag(config=True)

    DEFAULT_METEO_COLUMNS = [
        "Pressure",
        "Altitude",
        "Density",
        "Temperature",
        "Wind Speed",
        "Wind Direction",
        "Relative humidity",
        "Exponential Density",
    ]

    classes = [MeteoDataHandler]

    def setup(self):
        """Set up the tool."""
        super().setup()
        self.data_handler = MeteoDataHandler.from_name(
            self.meteo_data_handler, parent=self
        )
        self._timestamp = datetime.fromisoformat(self.timestamp.iso)
