# Python built-in imports
import importlib.resources
from copy import deepcopy
from datetime import date, datetime, timezone

import astropy.units as u
import numpy as np
import pytest
import sqlalchemy as sa

# Third-party imports
from astropy.coordinates import Latitude, Longitude
from astropy.table import Table
from sqlalchemy.exc import IntegrityError
from traitlets.config import Config

from calibpipe.database.adapter.database_containers import ContainerMap
from calibpipe.database.connections import CalibPipeDatabase
from calibpipe.database.interfaces import TableHandler
from calibpipe.tests.data import utils

# Internal imports
from calibpipe.utils.observatory import (
    Observatory,
    ObservatoryContainer,
    Season,
    SeasonContainer,
)


class TestSeason:
    # test season configuration shall contain new year to test the start>stop condition
    test_season_configuration = {
        "Season": {
            "name": "winter",
            "start_month": 11,
            "start_day": 16,
            "stop_month": 4,
            "stop_day": 30,
        }
    }

    @pytest.fixture
    def test_season(self):
        return Season(config=Config(self.test_season_configuration))

    def test_contains_timestamp(self, test_season):
        test_timestamp = datetime(
            year=2020, month=2, day=29, hour=0, minute=0, second=0, microsecond=0
        )
        assert test_timestamp in test_season
        test_date = date(year=2020, month=2, day=29)
        assert test_date in test_season
        test_date_begin = date(year=2020, month=11, day=16)
        test_date_end = date(year=2020, month=4, day=30)
        assert test_date_begin in test_season
        assert test_date_end in test_season
        test_date_out = date(year=2020, month=7, day=29)
        assert test_date_out not in test_season

    def test_properties(self, test_season):
        assert test_season.start == (11, 16)
        assert test_season.stop == (4, 30)
        assert test_season.months == [11, 12, 1, 2, 3, 4]
        assert test_season.reference_dates == (date(1999, 11, 16), date(2000, 4, 30))


class TestObservatory:
    cta_north_cfg = {
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

    cta_south_cfg = {
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

    # CI testing configuration
    db_config = {
        "user": "TEST_CALIBPIPE_DB_USER",
        "password": "DUMMY_PSWD",
        "database": "TEST_CALIBPIPE_DB",
        "host": "postgres",
        "autocommit": True,
    }

    @pytest.fixture
    def cta_north(self):
        return Observatory(config=Config(self.cta_north_cfg))

    @pytest.fixture
    def cta_south(self):
        return Observatory(config=Config(self.cta_south_cfg))

    def test_check_seasons(self):
        test_cfg = deepcopy(self.cta_north_cfg)
        test_cfg["Observatory"]["seasons"][2]["Season"]["start_day"] = 17
        with pytest.raises(ValueError, match="The seasons don't cover a year"):
            _ = Observatory(config=Config(test_cfg))
        test_cfg["Observatory"]["seasons"][2]["Season"]["start_day"] = 16
        test_cfg["Observatory"]["seasons"][0]["Season"]["start_day"] = 2
        with pytest.raises(
            ValueError, match="The season coverage has gaps or overlaps!"
        ):
            _ = Observatory(config=Config(test_cfg))

    def test_properties(self, cta_north):
        assert cta_north.name == "CTAO-NORTH"
        assert cta_north.coordinates == (
            Latitude(
                angle=self.cta_north_cfg["Observatory"]["latitude"],
                unit=u.deg,
            ),
            Longitude(
                angle=self.cta_north_cfg["Observatory"]["longitude"],
                unit=u.deg,
                wrap_angle=180 * u.deg,
            ),
        )

    def test_get_astronomical_night(self, cta_north):
        test_timestamp = datetime(2020, 11, 22, 1, 0, 0, 0)
        test_dusk = datetime(2020, 11, 21, 19, 44, 47, 805822, tzinfo=timezone.utc)
        test_dawn = datetime(2020, 11, 22, 6, 10, 44, 48436, tzinfo=timezone.utc)
        assert cta_north.get_astronomical_night(test_timestamp) == (
            test_dusk,
            test_dawn,
        )
        test_timestamp_daytime = datetime(2020, 11, 22, 12, 0, 0, 0)
        with pytest.raises(
            ValueError, match=r"The provided timestamp .* corresponds to daytime"
        ):
            dusk, down = cta_north.get_astronomical_night(test_timestamp_daytime)

    def test_get_season_from_timestamp(self, cta_north):
        test_timestamp = datetime(2020, 11, 22, 1, 0, 0, 0)
        assert cta_north.get_season_from_timestamp(test_timestamp).upper() == "WINTER"

    def test_select_season_data(self, cta_north):
        test_data = Table.read(
            importlib.resources.files(utils).joinpath(
                "meteo_data_winter_and_summer.ecsv"
            )
        )
        summer_data = cta_north.select_season_data(test_data, "SUMMER")
        assert np.all(
            np.vectorize(lambda x: x.month)(summer_data["Timestamp"].to_datetime()) == 7
        )
        winter_data = cta_north.select_season_data(test_data, "WINTER")
        assert np.all(
            np.vectorize(lambda x: x.month)(winter_data["Timestamp"].to_datetime())
            == 12
        )

    @pytest.mark.db
    @pytest.mark.observatory
    def test_db_write(self, cta_north, cta_south):
        with CalibPipeDatabase(
            **self.db_config,
        ) as connection:
            table, insertion = TableHandler.get_database_table_insertion(
                cta_north.containers[0],  # Observatory table
            )

            # Check if the Observatory table exists, create one if needed
            if not sa.inspect(connection.engine).has_table(table.name):
                table.create(bind=connection.engine)

        with CalibPipeDatabase(
            **self.db_config,
        ) as connection:
            table, insertion = TableHandler.get_database_table_insertion(
                cta_north.containers[1],  # Season table
            )

            # Check if the Season table exists, create one if needed
            if not sa.inspect(connection.engine).has_table(table.name):
                table.create(bind=connection.engine)

        with CalibPipeDatabase(
            **self.db_config,
        ) as connection:
            for test_observatory in [cta_north, cta_south]:
                for container in test_observatory.containers:
                    table, insertion = TableHandler.get_database_table_insertion(
                        container,
                    )
                    try:
                        TableHandler.insert_row_in_database(
                            table, insertion, connection
                        )
                    except IntegrityError as e:
                        if "duplicate key value violates unique constraint" in str(e):
                            connection.session.rollback()  # Unique constraint violation is expected in some tests due to previous DB setup
                        else:
                            raise e

    @pytest.mark.db
    @pytest.mark.observatory
    def test_db_read_raw(self):
        observatory_table = ContainerMap.map_to_db_container(
            ObservatoryContainer
        ).get_table()
        season_table = ContainerMap.map_to_db_container(SeasonContainer).get_table()
        query_observatory = observatory_table.select().where(
            observatory_table.c.name == "CTAO-NORTH"
        )
        query_season = season_table.select().where(
            season_table.c.name_Observatory == "CTAO-NORTH"
        )
        with CalibPipeDatabase(
            **self.db_config,
        ) as connection:
            read_observatory = connection.execute(query_observatory).fetchall()
            assert len(read_observatory) == 1
            read_season = connection.execute(query_season).fetchall()
            assert len(read_season) == 4

    @pytest.mark.db
    @pytest.mark.observatory
    def test_db_table_read_simple(self):
        with CalibPipeDatabase(
            **self.db_config,
        ) as connection:
            observatory_qtable = TableHandler.read_table_from_database(
                container=ObservatoryContainer,
                connection=connection,
            )
            # DEBUG purposes only. Use pytest -s -v in order to see this printout
            print(observatory_qtable)

    @pytest.mark.db
    @pytest.mark.observatory
    def test_db_table_read_conditional(self):
        with CalibPipeDatabase(
            **self.db_config,
        ) as connection:
            season_qtable = TableHandler.read_table_from_database(
                container=SeasonContainer,
                connection=connection,
                condition="(c.name_Observatory == 'CTAO-NORTH') & (c.alias == 'INTERMEDIATE')",
            )
            # DEBUG purposes only. Use pytest -s -v in order to see this printout
            print(season_qtable)
