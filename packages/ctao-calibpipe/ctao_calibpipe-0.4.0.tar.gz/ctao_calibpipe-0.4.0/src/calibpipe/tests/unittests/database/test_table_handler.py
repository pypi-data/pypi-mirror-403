# Import the necessary modules and classes for testing
import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import astropy.units as u
import pytest
import yaml
from traitlets.config import Config

from calibpipe.core.common_metadata_containers import (
    ContactReferenceMetadataContainer,
    ProductReferenceMetadataContainer,
    ReferenceMetadataContainer,
)
from calibpipe.database.adapter import Adapter
from calibpipe.database.connections import CalibPipeDatabase
from calibpipe.database.interfaces import TableHandler
from calibpipe.telescope.throughput.containers import OpticalThoughtputContainer
from calibpipe.utils.observatory import (
    Observatory,
)


@pytest.fixture
def mock_connection():
    """
    Fixture to create a mock database connection.
    """
    connection = MagicMock(spec=CalibPipeDatabase)
    return connection


# Fixture to provide a database connection
@pytest.fixture
def test_config():
    # Setup and connect to the test database
    config_path = Path(__file__).parent.joinpath(
        "../../../../../docs/source/user_guide/utils/configuration/"
    )
    with open(config_path.joinpath("upload_observatory_data_db.yaml")) as yaml_file:
        config_data = yaml.safe_load(yaml_file)
    config_data = config_data["UploadObservatoryData"]

    with open(config_path.joinpath("db_config.yaml")) as yaml_file:
        config_data |= yaml.safe_load(yaml_file)
    return config_data


@pytest.fixture
def test_container(test_config):
    return Observatory(config=Config(test_config["observatories"][0])).containers[0]


# Test cases for TableHandler class and other functions in the module
class TestTableHandler:
    # Test get_database_table_insertion method
    @pytest.mark.db
    def test_get_database_table_insertion(self, test_container):
        # Prepare a mock container and call the method
        table, kwargs = TableHandler.get_database_table_insertion(test_container)

        # Assert that the table and kwargs are not None
        assert table is not None
        assert kwargs is not None

    # Test read_table_from_database method
    @pytest.mark.db
    def test_read_table_from_database(self, test_container, test_config):
        TableHandler.prepare_db_tables(
            [
                test_container,
            ],
            test_config["database_configuration"],
        )
        condition = "c.elevation == 3000"
        with CalibPipeDatabase(**test_config["database_configuration"]) as connection:
            qtable = TableHandler.read_table_from_database(
                type(test_container), connection, condition
            )

        # Assert that qtable is not None and has the expected columns
        assert qtable is not None
        assert "elevation" in qtable.colnames
        assert qtable["elevation"].unit == u.m


def test_upload_data(mock_connection):
    """
    Test the upload_data function to ensure it correctly uploads data and metadata.
    """
    # Use OpticalThoughtputContainer as the data container
    data = OpticalThoughtputContainer(
        mean=0.95,
        median=0.90,
        std=0.02,
        sem=0.001,
        method="muon analysis",
        time_start=datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc),
        time_end=datetime.datetime(2025, 12, 31, tzinfo=datetime.timezone.utc),
        obs_id=12345,
    )

    # Mock metadata containers
    reference_metadata = ReferenceMetadataContainer(
        version_atmospheric_model="1.0",
        version=1,
        ID_optical_throughput=None,  # Will be set during the upload
    )
    product_metadata = ProductReferenceMetadataContainer(
        description="Test product",
        creation_time="2025-04-08T12:00:00Z",
        product_id="12345",
    )
    contact_metadata = ContactReferenceMetadataContainer(
        organization="Test Organization",
        name="Test User",
        email="test@example.com",
    )

    # Combine metadata into a list
    metadata = [reference_metadata, product_metadata, contact_metadata]

    # Mock database behavior
    mock_connection.execute.return_value.fetchone.return_value = MagicMock(
        _asdict=lambda: {"ID": 1}
    )

    # Patch the insert_row_in_database method
    with patch(
        "calibpipe.database.interfaces.table_handler.TableHandler.insert_row_in_database",
    ) as mock_insert:
        # Call the upload_data function
        TableHandler.upload_data(data, metadata, mock_connection)

        # Assertions to verify correct behavior
        # Verify that the main data was inserted
        data_table, data_kwargs = Adapter.to_postgres(data)

        calls = mock_insert.call_args_list

        # Check that a call was made with the expected table and connection
        assert any(
            call_args[0][0] == data_table
            and call_args[0][2] == mock_connection
            and call_args[0][1]["mean"] == 0.95
            for call_args in calls
        ), "Expected call to insert_row_in_database not found."

        ref_table, ref_kwargs = Adapter.to_postgres(reference_metadata)

        assert any(
            call_args[0][0] == ref_table
            and call_args[0][2] == mock_connection
            and call_args[0][1]["version_atmospheric_model"] == "1.0"
            for call_args in calls
        ), "Expected call to insert_row_in_database not found."

        for container in metadata[1:]:
            meta_table, meta_kwargs = Adapter.to_postgres(container)
            assert any(
                call_args[0][0] == meta_table and call_args[0][2] == mock_connection
                for call_args in calls
            ), "Expected call to insert_row_in_database not found."
