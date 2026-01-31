from datetime import datetime

import astropy.units as u
import pytest
from traitlets.config import Config

from calibpipe.atmosphere.meteo_data_handlers import (
    CO2DataHandler,
    ECMWFDataHandler,
    GDASDataHandler,
)
from calibpipe.utils.observatory import Observatory

co2_file_path = "./"


class TestMeteoDataHandler:
    @pytest.fixture
    def setup_macobac(self):
        macobac = CO2DataHandler()
        return macobac

    @pytest.fixture
    def setup_cta_north(self):
        cta_north = {
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
        return cta_north

    @pytest.fixture
    def setup_cta_south(self):
        cta_south = {
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
        return cta_south

    @pytest.fixture
    def setup_ecmwf_handler(self):
        ecmwf_data_handler = ECMWFDataHandler()
        return ecmwf_data_handler

    @pytest.fixture
    def setup_gdas_handler(self):
        gdas_data_handler = GDASDataHandler()
        return gdas_data_handler

    @pytest.fixture
    def setup_south_observatory(self, setup_cta_south):
        south_observatory = Observatory(config=Config(setup_cta_south))
        return south_observatory

    @pytest.fixture
    def setup_north_observatory(self, setup_cta_north):
        north_observatory = Observatory(config=Config(setup_cta_north))
        return north_observatory

    @pytest.mark.ecmwf
    @pytest.mark.verifies_usecase("UC-120-1.5")
    @pytest.mark.verifies_usecase("UC-120-1.10")
    def test_request_ecmwf_north(
        self, setup_north_observatory, setup_ecmwf_handler, setup_cta_north
    ):
        """Test if the ECMWF requested is reconstructed correctly"""
        timestamp = datetime(2023, 1, 20, 2, 0, 0, 0)
        dusk, dawn = setup_north_observatory.get_astronomical_night(timestamp)
        setup_ecmwf_handler.create_request(
            start=dusk,
            stop=dawn,
            latitude=setup_cta_north["Observatory"]["latitude"] * u.deg,
            longitude=setup_cta_north["Observatory"]["longitude"] * u.deg,
        )
        assert setup_ecmwf_handler.requests == [
            {
                "product_type": "reanalysis",
                "variable": [
                    "divergence",
                    "geopotential",
                    "ozone_mass_mixing_ratio",
                    "potential_vorticity",
                    "relative_humidity",
                    "temperature",
                    "u_component_of_wind",
                    "v_component_of_wind",
                    "vertical_velocity",
                ],
                "pressure_level": [
                    "1",
                    "2",
                    "3",
                    "5",
                    "7",
                    "10",
                    "20",
                    "30",
                    "50",
                    "70",
                    "100",
                    "125",
                    "150",
                    "175",
                    "200",
                    "225",
                    "250",
                    "300",
                    "350",
                    "400",
                    "450",
                    "500",
                    "550",
                    "600",
                    "650",
                    "700",
                    "750",
                    "775",
                    "800",
                    "825",
                    "850",
                    "875",
                    "900",
                    "925",
                    "950",
                    "975",
                    "1000",
                ],
                "year": "2023",
                "month": "1",
                "day": "19",
                "time": ["21:00", "22:00", "23:00"],
                "area": [28.75, -18.0, 29.0, -17.75],
                "format": "grib",
            },
            {
                "product_type": "reanalysis",
                "variable": [
                    "divergence",
                    "geopotential",
                    "ozone_mass_mixing_ratio",
                    "potential_vorticity",
                    "relative_humidity",
                    "temperature",
                    "u_component_of_wind",
                    "v_component_of_wind",
                    "vertical_velocity",
                ],
                "pressure_level": [
                    "1",
                    "2",
                    "3",
                    "5",
                    "7",
                    "10",
                    "20",
                    "30",
                    "50",
                    "70",
                    "100",
                    "125",
                    "150",
                    "175",
                    "200",
                    "225",
                    "250",
                    "300",
                    "350",
                    "400",
                    "450",
                    "500",
                    "550",
                    "600",
                    "650",
                    "700",
                    "750",
                    "775",
                    "800",
                    "825",
                    "850",
                    "875",
                    "900",
                    "925",
                    "950",
                    "975",
                    "1000",
                ],
                "year": "2023",
                "month": "1",
                "day": "20",
                "time": ["00:00", "01:00", "02:00", "03:00", "04:00", "05:00", "06:00"],
                "area": [28.75, -18.0, 29.0, -17.75],
                "format": "grib",
            },
        ]

    @pytest.mark.ecmwf
    @pytest.mark.verifies_usecase("UC-120-1.5")
    @pytest.mark.verifies_usecase("UC-120-1.10")
    def test_request_ecmwf_south(
        self, setup_south_observatory, setup_ecmwf_handler, setup_cta_south
    ):
        """Test if the ECMWF requested is reconstructed correctly"""
        timestamp = datetime(2023, 1, 20, 2, 0, 0, 0)
        dusk, dawn = setup_south_observatory.get_astronomical_night(timestamp)
        setup_ecmwf_handler.create_request(
            start=dusk,
            stop=dawn,
            latitude=setup_cta_south["Observatory"]["latitude"] * u.deg,
            longitude=setup_cta_south["Observatory"]["longitude"] * u.deg,
        )
        assert setup_ecmwf_handler.requests == [
            {
                "product_type": "reanalysis",
                "variable": [
                    "divergence",
                    "geopotential",
                    "ozone_mass_mixing_ratio",
                    "potential_vorticity",
                    "relative_humidity",
                    "temperature",
                    "u_component_of_wind",
                    "v_component_of_wind",
                    "vertical_velocity",
                ],
                "pressure_level": [
                    "1",
                    "2",
                    "3",
                    "5",
                    "7",
                    "10",
                    "20",
                    "30",
                    "50",
                    "70",
                    "100",
                    "125",
                    "150",
                    "175",
                    "200",
                    "225",
                    "250",
                    "300",
                    "350",
                    "400",
                    "450",
                    "500",
                    "550",
                    "600",
                    "650",
                    "700",
                    "750",
                    "775",
                    "800",
                    "825",
                    "850",
                    "875",
                    "900",
                    "925",
                    "950",
                    "975",
                    "1000",
                ],
                "year": "2023",
                "month": "1",
                "day": "20",
                "time": [
                    "02:00",
                    "03:00",
                    "04:00",
                    "05:00",
                    "06:00",
                    "07:00",
                    "08:00",
                ],
                "area": [-24.75, -70.5, -24.5, -70.25],
                "format": "grib",
            }
        ]

    # Testing boundary conditions for Copernicus requests
    # Starting with leap years
    @pytest.mark.ecmwf
    @pytest.mark.verifies_usecase("UC-120-1.5")
    @pytest.mark.verifies_usecase("UC-120-1.10")
    def test_request_ecmwf_leap_year(
        self, setup_north_observatory, setup_ecmwf_handler, setup_cta_north
    ):
        """Test if the ECMWF requested is reconstructed correctly"""
        timestamp = datetime(2020, 2, 28, 23, 56, 28, 0)
        dusk, dawn = setup_north_observatory.get_astronomical_night(timestamp)
        setup_ecmwf_handler.create_request(
            start=dusk,
            stop=dawn,
            latitude=setup_cta_north["Observatory"]["latitude"] * u.deg,
            longitude=setup_cta_north["Observatory"]["longitude"] * u.deg,
        )
        assert setup_ecmwf_handler.requests == [
            {
                "product_type": "reanalysis",
                "variable": [
                    "divergence",
                    "geopotential",
                    "ozone_mass_mixing_ratio",
                    "potential_vorticity",
                    "relative_humidity",
                    "temperature",
                    "u_component_of_wind",
                    "v_component_of_wind",
                    "vertical_velocity",
                ],
                "pressure_level": [
                    "1",
                    "2",
                    "3",
                    "5",
                    "7",
                    "10",
                    "20",
                    "30",
                    "50",
                    "70",
                    "100",
                    "125",
                    "150",
                    "175",
                    "200",
                    "225",
                    "250",
                    "300",
                    "350",
                    "400",
                    "450",
                    "500",
                    "550",
                    "600",
                    "650",
                    "700",
                    "750",
                    "775",
                    "800",
                    "825",
                    "850",
                    "875",
                    "900",
                    "925",
                    "950",
                    "975",
                    "1000",
                ],
                "year": "2020",
                "month": "2",
                "day": "28",
                "time": ["21:00", "22:00", "23:00"],
                "area": [28.75, -18.0, 29.0, -17.75],
                "format": "grib",
            },
            {
                "product_type": "reanalysis",
                "variable": [
                    "divergence",
                    "geopotential",
                    "ozone_mass_mixing_ratio",
                    "potential_vorticity",
                    "relative_humidity",
                    "temperature",
                    "u_component_of_wind",
                    "v_component_of_wind",
                    "vertical_velocity",
                ],
                "pressure_level": [
                    "1",
                    "2",
                    "3",
                    "5",
                    "7",
                    "10",
                    "20",
                    "30",
                    "50",
                    "70",
                    "100",
                    "125",
                    "150",
                    "175",
                    "200",
                    "225",
                    "250",
                    "300",
                    "350",
                    "400",
                    "450",
                    "500",
                    "550",
                    "600",
                    "650",
                    "700",
                    "750",
                    "775",
                    "800",
                    "825",
                    "850",
                    "875",
                    "900",
                    "925",
                    "950",
                    "975",
                    "1000",
                ],
                "year": "2020",
                "month": "2",
                "day": "29",
                "time": ["00:00", "01:00", "02:00", "03:00", "04:00", "05:00", "06:00"],
                "area": [28.75, -18.0, 29.0, -17.75],
                "format": "grib",
            },
        ]

    # Continuing with new years eve where all (day, month and year) are changing
    @pytest.mark.ecmwf
    @pytest.mark.verifies_usecase("UC-120-1.5")
    @pytest.mark.verifies_usecase("UC-120-1.10")
    def test_request_ecmwf_new_year(
        self, setup_north_observatory, setup_ecmwf_handler, setup_cta_north
    ):
        """Test if the ECMWF requested is reconstructed correctly"""
        timestamp = datetime(2023, 1, 1, 0, 0, 0, 0)
        dusk, dawn = setup_north_observatory.get_astronomical_night(timestamp)
        setup_ecmwf_handler.create_request(
            start=dusk,
            stop=dawn,
            latitude=setup_cta_north["Observatory"]["latitude"] * u.deg,
            longitude=setup_cta_north["Observatory"]["longitude"] * u.deg,
        )
        assert setup_ecmwf_handler.requests == [
            {
                "product_type": "reanalysis",
                "variable": [
                    "divergence",
                    "geopotential",
                    "ozone_mass_mixing_ratio",
                    "potential_vorticity",
                    "relative_humidity",
                    "temperature",
                    "u_component_of_wind",
                    "v_component_of_wind",
                    "vertical_velocity",
                ],
                "pressure_level": [
                    "1",
                    "2",
                    "3",
                    "5",
                    "7",
                    "10",
                    "20",
                    "30",
                    "50",
                    "70",
                    "100",
                    "125",
                    "150",
                    "175",
                    "200",
                    "225",
                    "250",
                    "300",
                    "350",
                    "400",
                    "450",
                    "500",
                    "550",
                    "600",
                    "650",
                    "700",
                    "750",
                    "775",
                    "800",
                    "825",
                    "850",
                    "875",
                    "900",
                    "925",
                    "950",
                    "975",
                    "1000",
                ],
                "year": "2022",
                "month": "12",
                "day": "31",
                "time": ["20:00", "21:00", "22:00", "23:00"],
                "area": [28.75, -18.0, 29.0, -17.75],
                "format": "grib",
            },
            {
                "product_type": "reanalysis",
                "variable": [
                    "divergence",
                    "geopotential",
                    "ozone_mass_mixing_ratio",
                    "potential_vorticity",
                    "relative_humidity",
                    "temperature",
                    "u_component_of_wind",
                    "v_component_of_wind",
                    "vertical_velocity",
                ],
                "pressure_level": [
                    "1",
                    "2",
                    "3",
                    "5",
                    "7",
                    "10",
                    "20",
                    "30",
                    "50",
                    "70",
                    "100",
                    "125",
                    "150",
                    "175",
                    "200",
                    "225",
                    "250",
                    "300",
                    "350",
                    "400",
                    "450",
                    "500",
                    "550",
                    "600",
                    "650",
                    "700",
                    "750",
                    "775",
                    "800",
                    "825",
                    "850",
                    "875",
                    "900",
                    "925",
                    "950",
                    "975",
                    "1000",
                ],
                "year": "2023",
                "month": "1",
                "day": "1",
                "time": ["00:00", "01:00", "02:00", "03:00", "04:00", "05:00", "06:00"],
                "area": [28.75, -18.0, 29.0, -17.75],
                "format": "grib",
            },
        ]

    # Continuing with new years eve where all (day, month and year) are changing
    @pytest.mark.ecmwf
    @pytest.mark.verifies_usecase("UC-120-1.5")
    @pytest.mark.verifies_usecase("UC-120-1.10")
    def test_request_ecmwf_day_without_dusk(
        self, setup_south_observatory, setup_ecmwf_handler, setup_cta_south
    ):
        """Test if the ECMWF requested is reconstructed correctly"""
        timestamp = datetime(2023, 9, 22, 2, 0, 0, 0)
        dusk, dawn = setup_south_observatory.get_astronomical_night(timestamp)
        setup_ecmwf_handler.create_request(
            start=dusk,
            stop=dawn,
            latitude=setup_cta_south["Observatory"]["latitude"] * u.deg,
            longitude=setup_cta_south["Observatory"]["longitude"] * u.deg,
        )
        assert setup_ecmwf_handler.requests == [
            {
                "product_type": "reanalysis",
                "variable": [
                    "divergence",
                    "geopotential",
                    "ozone_mass_mixing_ratio",
                    "potential_vorticity",
                    "relative_humidity",
                    "temperature",
                    "u_component_of_wind",
                    "v_component_of_wind",
                    "vertical_velocity",
                ],
                "pressure_level": [
                    "1",
                    "2",
                    "3",
                    "5",
                    "7",
                    "10",
                    "20",
                    "30",
                    "50",
                    "70",
                    "100",
                    "125",
                    "150",
                    "175",
                    "200",
                    "225",
                    "250",
                    "300",
                    "350",
                    "400",
                    "450",
                    "500",
                    "550",
                    "600",
                    "650",
                    "700",
                    "750",
                    "775",
                    "800",
                    "825",
                    "850",
                    "875",
                    "900",
                    "925",
                    "950",
                    "975",
                    "1000",
                ],
                "year": "2023",
                "month": "9",
                "day": "22",
                "time": [
                    "00:00",
                    "01:00",
                    "02:00",
                    "03:00",
                    "04:00",
                    "05:00",
                    "06:00",
                    "07:00",
                    "08:00",
                    "09:00",
                ],
                "area": [-24.75, -70.5, -24.5, -70.25],
                "format": "grib",
            }
        ]

    @pytest.mark.verifies_usecase("UC-120-1.5")
    @pytest.mark.verifies_usecase("UC-120-1.10")
    def test_keeling_curve_download(self, setup_macobac):
        setup_macobac.data_path = co2_file_path
        assert setup_macobac.request_data() == 0

    @pytest.mark.gdas
    @pytest.mark.verifies_usecase("UC-120-1.5")
    def test_request_gdas_creation(
        self, setup_south_observatory, setup_gdas_handler, setup_cta_south
    ):
        """Test correct GDAS request creation"""
        timestamp = datetime(2023, 1, 20, 2, 0, 0, 0)
        dusk, dawn = setup_south_observatory.get_astronomical_night(timestamp)
        setup_gdas_handler.create_request(
            start=dusk,
            stop=dawn,
            latitude=setup_cta_south["Observatory"]["latitude"] * u.deg,
            longitude=setup_cta_south["Observatory"]["longitude"] * u.deg,
        )
        assert setup_gdas_handler.request == {
            "dataset": "ds083.2",
            "date": "202301200600/to/202301200600",
            "datetype": "init",
            "param": "HGT/PRES/TMP/R H/P WAT/A PCP/U GRD/V GRD/T CDC/LANDN/TOZNE",
            "level": "ISBL:1000/975/950/925/900/850/800/750/700/650/600/550/500/450/400/350/300/250/200/150/100/50/20",
            "nlat": -25.0,
            "slat": -25.0,
            "elon": -70.0,
            "wlon": -70.0,
            "product": "Analysis",
        }

    @pytest.mark.gdas
    @pytest.mark.xfail(
        reason="GDAS is rather unstable. Functionality is tested manually"
    )
    @pytest.mark.verifies_usecase("UC-120-1.5")
    def test_gdas_data_retrieval(
        self, setup_north_observatory, setup_gdas_handler, setup_cta_north
    ):
        """Test GDAS data retrieval"""
        timestamp = datetime(2023, 1, 20, 2, 0, 0, 0)
        dusk, dawn = setup_north_observatory.get_astronomical_night(timestamp)
        setup_gdas_handler.create_request(
            start=dusk,
            stop=dawn,
            latitude=setup_cta_north["Observatory"]["latitude"] * u.deg,
            longitude=setup_cta_north["Observatory"]["longitude"] * u.deg,
        )
        assert setup_gdas_handler.request_data() == 0

    @pytest.mark.ecmwf
    @pytest.mark.verifies_usecase("UC-120-1.5")
    @pytest.mark.verifies_usecase("UC-120-1.10")
    def test_ecmwf_data_retrieval(
        self, setup_south_observatory, setup_ecmwf_handler, setup_cta_south
    ):
        """Test ECMWF data retrieval"""
        timestamp = datetime(2023, 1, 20, 2, 0, 0, 0)
        dusk, dawn = setup_south_observatory.get_astronomical_night(timestamp)
        setup_ecmwf_handler.create_request(
            start=dusk,
            stop=dawn,
            latitude=setup_cta_south["Observatory"]["latitude"] * u.deg,
            longitude=setup_cta_south["Observatory"]["longitude"] * u.deg,
        )
        assert setup_ecmwf_handler.request_data() == 0
