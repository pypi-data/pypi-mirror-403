# Set up logging
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml
from astropy.table import QTable
from astropy.time import Time
from ctapipe.core import run_tool
from traitlets.config import Config

from calibpipe.core.exceptions import IntermittentError, MissingInputDataError
from calibpipe.tools.contemporary_mdp_producer import CreateMolecularDensityProfile
from calibpipe.tools.macobac_calculator import CalculateMACOBAC
from calibpipe.tools.molecular_atmospheric_model_producer import (
    CreateMolecularAtmosphericModel,
)
from calibpipe.tools.reference_atmospheric_model_selector import (
    SelectMolecularAtmosphericModel,
)


@pytest.mark.verifies_usecase("UC-120-1.2")
def test_calculate_macobac(tmp_path):
    config = Config()
    config.CalculateMACOBAC = Config()
    config.CalculateMACOBAC.output_file = str(tmp_path / "macobac.ecsv")

    with patch(
        "calibpipe.tools.macobac_calculator.CO2DataHandler",
        new_callable=MagicMock,
    ) as mock_class:
        mock_class.return_value.data_path = str(
            Path(__file__).parent.parent.parent
            / "data/atmosphere/molecular_atmosphere/"
        )
        tool = CalculateMACOBAC(config=config)
        run_tool(tool)

        output_file = Path(config.CalculateMACOBAC.output_file)
        assert output_file.exists(), "Output file was not created."

        result_table = QTable.read(output_file, format="ascii.ecsv")
        expected_co2_concentration = 419.3
        assert result_table["co2_concentration"][0].value == pytest.approx(
            expected_co2_concentration, abs=0.1
        ), (
            f"CO2 concentration does not match expected value ({result_table['co2_concentration'][0]} != {expected_co2_concentration})."
        )
        assert (
            result_table["estimation_date"][0]
            == Time(str(datetime.now(timezone.utc).date()), out_subfmt="date").iso
        ), "Estimation date does not match expected value."


@pytest.mark.db
@pytest.mark.verifies_usecase("UC-120-1.7")
@pytest.mark.verifies_usecase("UC-120-1.8")
def test_create_molecular_atmospheric_model(tmp_path):
    config_path = (
        Path(__file__).parent.parent.parent.parent.parent.parent
        / "docs/source/user_guide/atmosphere/configuration/create_molecular_atmospheric_model.yaml"
    )
    with open(config_path) as file:
        config = Config(yaml.load(file, Loader=yaml.SafeLoader))

    config.CreateMolecularAtmosphericModel.output_path = str(tmp_path)
    # Mock the necessary components
    with patch(
        # "calibpipe.tools.molecular_atmospheric_model_producer.MeteoDataHandler",
        "calibpipe.tools.atmospheric_base_tool.MeteoDataHandler",
        new_callable=MagicMock,
    ) as mock_meteo_handler_class:
        tool = CreateMolecularAtmosphericModel(config=config)
        # Test missing input data
        with pytest.raises(MissingInputDataError):
            run_tool(
                tool,
                argv=[
                    "-c",
                    str(
                        Path(__file__).parent.parent.parent.parent.parent.parent
                        / "docs/source/user_guide/utils/configuration/db_config.yaml"
                    ),
                    "--macobac12-table-path",
                    str(
                        Path(__file__).parent.parent.parent
                        / "data/atmosphere/molecular_atmosphere/macobac.ecsv"
                    ),
                ],
                raises=True,
            )

        # Now set up the mock data handler
        mock_meteo_handler = MagicMock()
        mock_meteo_handler_class.from_name.return_value = mock_meteo_handler
        mock_meteo_handler.data_path = str(
            Path(__file__).parent.parent.parent
            / "data/atmosphere/molecular_atmosphere/"
        )
        mock_meteo_handler.request_data.return_value = 0

        run_tool(
            tool,
            argv=[
                "-c",
                str(
                    Path(__file__).parent.parent.parent.parent.parent.parent
                    / "docs/source/user_guide/utils/configuration/db_config.yaml"
                ),
                "--macobac12-table-path",
                str(
                    Path(__file__).parent.parent.parent
                    / "data/atmosphere/molecular_atmosphere/macobac.ecsv"
                ),
            ],
            raises=True,
        )

        # Check if the output files were created
        output_profile = (
            Path(config.CreateMolecularAtmosphericModel.output_path)
            / "contemporary_atmospheric_profile.ascii.ecsv"
        )
        output_extinction = (
            Path(config.CreateMolecularAtmosphericModel.output_path)
            / "contemporary_rayleigh_extinction_profile.ascii.ecsv"
        )
        assert output_profile.exists(), (
            "Contemporary atmospheric profile file was not created."
        )
        assert output_extinction.exists(), (
            "Contemporary Rayleigh extinction profile file was not created."
        )

        # Read and validate the output files
        profile_table = QTable.read(output_profile, format="ascii.ecsv")
        extinction_table = QTable.read(output_extinction, format="ascii.ecsv")

        expected_profile_columns = [
            "altitude",
            "atmospheric_density",
            "atmospheric_thickness",
            "refractive_index_m_1",
            "temperature",
            "pressure",
            "partial_water_pressure",
        ]

        for column in expected_profile_columns:
            assert column in profile_table.colnames, (
                f"{column} column missing in profile table."
            )

        assert "altitude_max" in extinction_table.colnames, (
            "Altitude_max column missing in extinction table."
        )
        assert "altitude_min" in extinction_table.colnames, (
            "Altitude_min column missing in extinction table."
        )


@pytest.mark.db
@pytest.mark.verifies_usecase("UC-120-1.6")
def test_create_molecular_density_profile(tmp_path):
    config_path = (
        Path(__file__).parent.parent.parent.parent.parent.parent
        / "docs/source/user_guide/atmosphere/configuration/create_molecular_density_profile.yaml"
    )
    with open(config_path) as file:
        config = Config(yaml.load(file, Loader=yaml.SafeLoader))

    config.CreateMolecularDensityProfile.output_path = str(tmp_path)
    # Mock the necessary components
    with patch(
        "calibpipe.tools.atmospheric_base_tool.MeteoDataHandler",
        new_callable=MagicMock,
    ) as mock_meteo_handler_class:
        tool = CreateMolecularDensityProfile(config=config)
        # Test missing input data
        with pytest.raises(MissingInputDataError):
            run_tool(
                tool,
                argv=[
                    "-c",
                    str(
                        Path(__file__).parent.parent.parent.parent.parent.parent
                        / "docs/source/user_guide/utils/configuration/db_config.yaml"
                    ),
                ],
                raises=True,
            )

        # Now set up the mock data handler
        mock_meteo_handler = MagicMock()
        mock_meteo_handler_class.from_name.return_value = mock_meteo_handler
        mock_meteo_handler.data_path = str(
            Path(__file__).parent.parent.parent
            / "data/atmosphere/molecular_atmosphere/"
        )
        mock_meteo_handler.request_data.return_value = 0

        run_tool(
            tool,
            argv=[
                "-c",
                str(
                    Path(__file__).parent.parent.parent.parent.parent.parent
                    / "docs/source/user_guide/utils/configuration/db_config.yaml"
                ),
            ],
            raises=True,
        )

        # Check if the output file was created
        output_file = (
            Path(config.CreateMolecularDensityProfile.output_path)
            / "contemporary_molecular_density_profile.ascii.ecsv"
        )
        assert output_file.exists(), (
            "Contemporary molecular density profile file was not created."
        )

        # Read and validate the output file
        mdp_table = QTable.read(output_file, format="ascii.ecsv")

        expected_columns = [
            "altitude",
            "number density",
        ]

        for column in expected_columns:
            assert column in mdp_table.colnames, (
                f"{column} column missing in molecular density profile table."
            )


@pytest.mark.db
@pytest.mark.verifies_usecase("UC-120-1.3")
def test_select_molecular_atmospheric_model(tmp_path):
    config_path = (
        Path(__file__).parent.parent.parent.parent.parent.parent
        / "docs/source/user_guide/atmosphere/configuration/select_reference_atmospheric_model.yaml"
    )
    with open(config_path) as file:
        config = Config(yaml.load(file, Loader=yaml.SafeLoader))

    config.SelectMolecularAtmosphericModel.output_path = str(tmp_path)
    # Mock the necessary components
    with patch(
        "calibpipe.tools.atmospheric_base_tool.MeteoDataHandler",
        new_callable=MagicMock,
    ) as mock_meteo_handler_class:
        tool = SelectMolecularAtmosphericModel(config=config)

        # Mock database and data handler behavior
        mock_meteo_handler = MagicMock()
        mock_meteo_handler_class.from_name.return_value = mock_meteo_handler
        mock_meteo_handler.data_path = str(
            Path(__file__).parent.parent.parent
            / "data/atmosphere/molecular_atmosphere/"
        )

        # Test missing input data
        mock_meteo_handler.request_data.return_value = 1

        with pytest.raises(IntermittentError):
            run_tool(
                tool,
                argv=[
                    "-c",
                    str(
                        Path(__file__).parent.parent.parent.parent.parent.parent
                        / "docs/source/user_guide/utils/configuration/db_config.yaml"
                    ),
                ],
                raises=True,
            )

        # Check if the output files were created
        output_profile = (
            Path(config.SelectMolecularAtmosphericModel.output_path)
            / "selected_atmospheric_profile.ascii.ecsv"
        )
        output_extinction = (
            Path(config.SelectMolecularAtmosphericModel.output_path)
            / "selected_rayleigh_extinction_profile.ascii.ecsv"
        )
        assert output_profile.exists(), (
            "Selected atmospheric profile file was not created."
        )
        assert output_extinction.exists(), (
            "Selected Rayleigh extinction profile file was not created."
        )

        # Read and validate the output files
        profile_table = QTable.read(output_profile, format="ascii.ecsv")
        extinction_table = QTable.read(output_extinction, format="ascii.ecsv")

        expected_profile_columns = [
            "altitude",
            "atmospheric_density",
            "atmospheric_thickness",
            "refractive_index_m_1",
            "temperature",
            "pressure",
            "partial_water_pressure",
        ]

        for column in expected_profile_columns:
            assert column in profile_table.colnames, (
                f"{column} column missing in profile table."
            )

        expected_extinction_columns = ["altitude_min", "altitude_max"]
        expected_extinction_columns.extend([f"{i}.0 nm" for i in range(200, 1000)])

        for column in expected_extinction_columns:
            assert column in extinction_table.colnames, (
                f"{column} column missing in extinction table."
            )
            if "altitude" in column:
                assert extinction_table[column].unit == "km", (
                    f"Column {column} unit does not match expected unit."
                )
            assert extinction_table[column].ndim == 1, (
                f"Column {column} does not have the expected number of dimensions."
            )
