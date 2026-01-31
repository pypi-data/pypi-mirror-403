"""Utility module to manage observatory data."""

# Python built-in imports
from calendar import month_abbr, monthrange
from datetime import date, datetime, timedelta
from enum import Enum
from functools import cached_property

# Third-party imports
import astral
import astropy.units as u
from astral.sun import sun
from astropy.coordinates import Latitude, Longitude

# CTA-related imports
from ctapipe.core.component import Component
from ctapipe.core.traits import (
    CaselessStrEnum,
    Float,
    Int,
    List,
)
from traitlets.config import Config

# Internal imports
from .observatory_containers import ObservatoryContainer, SeasonContainer


class SeasonAlias(Enum):
    """Seasons aliases."""

    SUMMER = "SUMMER"
    WINTER = "WINTER"
    SPRING = "INTERMEDIATE"
    FALL = "INTERMEDIATE"
    INTERMEDIATE = "INTERMEDIATE"


class Season(Component):
    """Class, describing nature seasons."""

    name = CaselessStrEnum(
        values=["SPRING", "SUMMER", "FALL", "WINTER", "INTERMEDIATE"],
        help="Season name (e.g. summer)",
    ).tag(config=True)
    start_month = Int(help="Start month of the season", allow_none=False).tag(
        config=True
    )
    stop_month = Int(help="Stop month of the season", allow_none=False).tag(config=True)
    start_day = Int(
        default_value=None, help="Start day of the season", allow_none=True
    ).tag(config=True)
    stop_day = Int(
        default_value=None, help="Stop day of the season", allow_none=True
    ).tag(config=True)

    _leap_year = (
        2000  # Arbitrary leap year. Do not change unless you know what you're doing.
    )

    def __init__(self, config=None, parent=None, **kwargs):
        super().__init__(config=config, parent=parent, **kwargs)
        self.name = self.name.upper()
        start = date(
            year=self._leap_year, month=self.start_month, day=self.start_day or 1
        )
        stop = date(
            year=self._leap_year,
            month=self.stop_month,
            day=self.stop_day or monthrange(self._leap_year, self.stop_month)[1],
        )
        if start > stop:
            self.log.debug(
                "Season %s start date (%s) is greater than its stop date (%s), "
                "rolling back start date year...",
                self.name,
                start,
                stop,
            )
            try:
                start = start.replace(year=start.year - 1)
            except ValueError:
                self.log.warning(
                    "29/02 is used as the season start date, changing it to 28/02..."
                )
                start = start.replace(year=start.year - 1, day=start.day - 1)
            self._months = list(range(self.start_month, 13)) + list(
                range(1, self.stop_month + 1)
            )
            self._carry_on = True
        else:
            self._months = list(range(self.start_month, self.stop_month + 1))
            self._carry_on = False
        self._start = start
        self._stop = stop

    @staticmethod
    def cfg_from_record(record):
        """Return configuration dictionary from the DB record."""
        return {
            "Season": {
                "name": record["name"],
                "start_month": record["start"].month,
                "start_day": record["start"].day,
                "stop_month": record["stop"].month,
                "stop_day": record["stop"].day,
            }
        }

    @classmethod
    def from_record(cls, record):
        """Create Season object from the DB record or container ``as_dict()`` representation.

        Parameters
        ----------
        record : dict
            Dictionary representation of a SeasonContainer.
        """
        return cls(config=Config(cls.cfg_from_record(record)))

    def __contains__(self, timestamp):
        """Check whether a timestamp is within a season."""
        if isinstance(timestamp, datetime):
            timestamp = timestamp.date()
        cast_date = timestamp.replace(year=self._leap_year)
        if self._carry_on:
            if (cast_date.month == 2) and (cast_date.day == 29):
                cast_date_start = cast_date.replace(
                    year=self._leap_year - 1, day=cast_date.day - 1
                )
            else:
                cast_date_start = cast_date.replace(year=self._leap_year - 1)
            return self._start <= cast_date_start or cast_date <= self._stop
        return self._start <= cast_date <= self._stop

    def __repr__(self):
        """Return a string representation of the season."""
        return (
            f"Season {self.name}: "
            f"from {month_abbr[self.start[0]]}, {self.start[1]} "
            f"to {month_abbr[self.stop[0]]}, {self.stop[1]}."
        )

    @property
    def start(self):
        """
        Start of the season.

        Returns
        -------
        tuple(int, int)
            Season start (month, day).
        """
        return (self._start.month, self._start.day)

    @property
    def stop(self):
        """
        End of the season.

        Returns
        -------
        tuple(int, int)
            Season stop (month, day).
        """
        return (self._stop.month, self._stop.day)

    @property
    def months(self):
        """
        List of months in the season.

        Returns
        -------
        list(int)
            List of month numbers in the season.
        """
        return self._months

    @property
    def reference_dates(self):
        """
        Reference season start and stop dates based on internal leap year.

        Returns
        -------
        tuple(date, date)
            Tuple of datetime.date objects (start, stop).
        """
        return (self._start, self._stop)

    def container(self, observatory_name, observatory_version):
        """
        Season container.

        Parameters
        ----------
        observatory_name : str
            Name of the observatory, to which the season belongs.
        observatory_version : int
            Version of the observatory, to which the season belongs.

        Returns
        -------
        SeasonContainer
        """
        season_container = SeasonContainer(
            start=self.reference_dates[0],
            stop=self.reference_dates[1],
            name=self.name,
            alias=SeasonAlias[self.name.upper()].value,
            name_Observatory=observatory_name,
            version_Observatory=observatory_version,
        )
        season_container.validate()
        return season_container


class Observatory(Component):
    """Class, defining an observatory object."""

    name = CaselessStrEnum(
        values=["CTAO-NORTH", "CTAO-SOUTH"],
        default_value="CTAO-NORTH",
        help="Observatory name",
    ).tag(config=True)
    latitude = Float(
        default_value=28.7636, help="Observatory latitude in degrees", allow_none=False
    ).tag(config=True)
    longitude = Float(
        default_value=17.8947, help="Observatory longitude in degrees", allow_none=False
    ).tag(config=True)
    elevation = Int(
        default_value=2158, help="Observatory elevation in meters", allow_none=False
    ).tag(config=True)
    seasons = List(help="Observatory meteorological seasons", minlen=2).tag(config=True)
    version = Int(default_value=1, help="Observatory configuration version").tag(
        config=True
    )

    def __init__(self, config=None, parent=None, **kwargs):
        super().__init__(config=config, parent=parent, **kwargs)
        self.name = self.name.upper()
        self._longitude = Longitude(
            angle=self.longitude, unit=u.deg, wrap_angle=180 * u.deg
        )
        self._latitude = Latitude(angle=self.latitude, unit=u.deg)
        self._elevation = self.elevation * u.m
        self._seasons = [
            Season(config=Config(key))
            for key in self.get_current_config()["Observatory"]["seasons"]
        ]
        self.__check_seasons()
        self.seasons_dict = {season.name: season for season in self._seasons}

    @classmethod
    def from_db(cls, database_configuration, site, version):
        """Create Observatory object from the DB record."""
        from ..database.connections import CalibPipeDatabase
        from ..database.interfaces import TableHandler

        with CalibPipeDatabase(
            **database_configuration,
        ) as connection:
            observatory_table = TableHandler.read_table_from_database(
                ObservatoryContainer,
                connection,
                condition=f"(c.name == '{site.upper()}') & (c.version == {version})",
            )
            if len(observatory_table) == 0:
                raise ValueError(
                    f"There's no DB record for observatory {site} v{version}"
                )
            if len(observatory_table) > 1:
                raise ValueError(
                    f"There're multiple DB records for observatory {site} v{version}"
                )
            seasons_table = TableHandler.read_table_from_database(
                SeasonContainer,
                connection,
                condition=f"(c.name_Observatory == '{site.upper()}') & (c.version_Observatory == {version})",
            )
        observatory_record = observatory_table.to_pandas().to_dict(orient="records")[0]
        seasons_records = seasons_table.to_pandas().to_dict(orient="records")
        seasons_cfg = [Season.cfg_from_record(rec) for rec in seasons_records]
        config_dict = {
            "Observatory": {
                "name": observatory_record["name"],
                "latitude": observatory_record["latitude"],
                "longitude": observatory_record["longitude"],
                "elevation": int(observatory_record["elevation"]),
                "seasons": seasons_cfg,
            }
        }

        return cls(config=Config(config_dict))

    def __check_seasons(self):
        """
        Check if provided seasons provide no-gaps and no-overlaps full coverage of a year.

        Raises
        ------
        ValueError
            If the seasons overlap, if there's a gap between the seasons or they don't cover a year.
        """
        dates = sorted(
            [season.reference_dates for season in self._seasons], key=lambda x: x[0]
        )
        # check that there's one year between the first start and last end
        if dates[0][0] + timedelta(days=365) != dates[-1][1]:
            raise ValueError("The seasons don't cover a year")
        diffs = [j[0] - i[1] for i, j in zip(dates[:-1], dates[1:])]
        if not all(x == timedelta(days=1) for x in diffs):
            raise ValueError("The season coverage has gaps or overlaps!")

    @property
    def coordinates(self):
        """
        Observatory coordinates.

        Returns
        -------
        astropy.coordinates.Latitude
            Observatory's latitude.
        astropy.coordinates.Longitude
            Observatory's longitude.
        """
        return self._latitude, self._longitude

    @cached_property
    def containers(self):
        """
        Observatory containers.

        Returns
        -------
        tuple(ObservatoryContainer, SeasonContainer)
            Containers with observatory and season configuration data
            used to store the observatory configuration in the DB.
        """
        obs_container = ObservatoryContainer(
            name=self.name,
            latitude=self._latitude,
            longitude=self._longitude,
            elevation=self._elevation,
            version=self.version,
        )
        obs_container.validate()
        season_containers = [
            season.container(self.name, self.version) for season in self._seasons
        ]
        return (obs_container, *season_containers)

    def select_season_data(self, data, season_name):
        """
        Select data that belongs to a given season.

        Parameters
        ----------
        data : astropy.table.Table
            Astropy table with meteorological data. Must contain 'Timestamp' column with ``astropy.time.Time``
        season_name : str
            Season name.

        Returns
        -------
        astropy.table.Table
            Selected data table according to provided season.
        """
        if season_name.upper() not in self.seasons_dict.keys():
            self.log.error(
                "Requested season (%s) is not defined for the observatory %s\n"
                "%s's seasons:\n%s",
                season_name,
                self.name,
                self.name,
                self.seasons_dict.keys(),
            )
            raise RuntimeError(
                f"{season_name} is not present in {self.name}'s seasons."
            )
        mask = [
            ts.date() in self.seasons_dict[season_name.upper()]
            for ts in data["Timestamp"].tt.datetime
        ]
        return data[mask]

    def get_astronomical_night(self, timestamp):
        """
        Calculate astronomical night.

        Calculates the astronomical dusk and dawn (i.e. when the Sun is 18deg below the
        horizon) for this observatory around a given timestamp. Returned values represent
        the UTC timestamps of dusk and dawn.

        Parameters
        ----------
        timestamp: datetime
            The date for which we want to request for data.

        Returns
        -------
        tuple(datetime, datetime)
            The astronomical dusk and dawn.

        Raises
        ------
        ValueError
            If the provided timestamp corresponds to daytime.
        """
        observer = astral.Observer(
            latitude=self.coordinates[0].to_value(u.deg),
            longitude=self.coordinates[1].to_value(u.deg),
            elevation=self._elevation.to_value(u.m),
        )
        try:
            sun_today = sun(
                observer, date=timestamp, dawn_dusk_depression=18
            )  # corresponds to astronomical dusk/dawn
        except ValueError:
            sun_today = sun(
                observer, date=timestamp - timedelta(days=1), dawn_dusk_depression=18
            )
            return sun_today["dusk"], sun_today["dawn"] + timedelta(days=1)

        if (timestamp.time() < sun_today["dusk"].time()) and (
            timestamp.time() > sun_today["dawn"].time()
        ):
            self.log.error(
                "The provided timestamp %s corresponds to daytime.", timestamp
            )
            raise ValueError(
                f"The provided timestamp {timestamp} corresponds to daytime."
            )
        if sun_today["dusk"].hour < 12 and (
            (
                (timestamp.time() > sun_today["dusk"].time())
                and (timestamp.time() > sun_today["dawn"].time())
            )
            or (
                (timestamp.time() < sun_today["dusk"].time())
                and (timestamp.time() < sun_today["dawn"].time())
            )
        ):
            self.log.error(
                "The provided timestamp %s corresponds to daytime.", timestamp
            )
            raise ValueError(
                f"The provided timestamp {timestamp} corresponds to daytime."
            )

        if timestamp.hour < sun_today["dusk"].hour:
            sun_yesterday = sun(
                observer,
                date=timestamp - timedelta(days=1),
                dawn_dusk_depression=18,
            )
            if (sun_today["dawn"] - sun_yesterday["dusk"]) > timedelta(days=1):
                return sun_yesterday["dusk"] + timedelta(days=1), sun_today["dawn"]
            return sun_yesterday["dusk"], sun_today["dawn"]

        if timestamp.hour > sun_today["dawn"].hour:
            sun_tomorrow = sun(
                observer,
                date=timestamp + timedelta(days=1),
                dawn_dusk_depression=18,
            )
            return sun_today["dusk"], sun_tomorrow["dawn"]
        return (sun_today["dusk"], sun_today["dawn"])

    def get_season_from_timestamp(self, timestamp):
        """Get the name of the season corresponding to the timestamp.

        Parameters
        ----------
        timestamp : datetime

        Returns
        -------
        str
            Season name.
        """
        for season in self._seasons:
            if timestamp in season:
                return season.name
