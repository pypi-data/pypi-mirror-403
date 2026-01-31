from copy import deepcopy
from pathlib import Path

import pytest
import yaml
from ctapipe.core import run_tool
from traitlets.config import Config

from calibpipe.tools.atmospheric_model_db_loader import UploadAtmosphericModel
from calibpipe.tools.init_db import CalibPipeDatabaseInitialization
from calibpipe.tools.observatory_data_db_loader import UploadObservatoryData


@pytest.mark.db
@pytest.mark.order(1)
def test_init_database():
    """
    Fixture to initialize the database and upload required data.
    This runs before any other database-related tests.
    """
    # Paths to configuration files
    db_config_path = (
        Path(__file__).parent.parent.parent.parent.parent
        / "docs/source/user_guide/utils/configuration/db_config.yaml"
    )

    # Initialize the database
    with open(db_config_path) as file:
        db_config = Config(yaml.load(file, Loader=yaml.SafeLoader))
    tool = CalibPipeDatabaseInitialization(config=db_config)
    run_tool(tool)


@pytest.mark.db
@pytest.mark.order(2)
def test_upload_observatory():
    db_config_path = (
        Path(__file__).parent.parent.parent.parent.parent
        / "docs/source/user_guide/utils/configuration/db_config.yaml"
    )
    with open(db_config_path) as file:
        db_config = Config(yaml.load(file, Loader=yaml.SafeLoader))

    observatory_data_config_path = (
        Path(__file__).parent.parent.parent.parent.parent
        / "docs/source/user_guide/utils/configuration/upload_observatory_data_db.yaml"
    )
    # Upload observatory data
    config = deepcopy(db_config)
    with open(observatory_data_config_path) as file:
        observatory_data_config = Config(yaml.load(file, Loader=yaml.SafeLoader))
    config.update(observatory_data_config)
    tool = UploadObservatoryData(config=config)
    run_tool(tool)


@pytest.mark.db
@pytest.mark.order(3)
def test_upload_atmospheric_models():
    db_config_path = (
        Path(__file__).parent.parent.parent.parent.parent
        / "docs/source/user_guide/utils/configuration/db_config.yaml"
    )

    with open(db_config_path) as file:
        db_config = Config(yaml.load(file, Loader=yaml.SafeLoader))

    atmospheric_model_configs = list(
        Path(__file__).parent.parent.parent.parent.parent.glob(
            "docs/source/user_guide/utils/configuration/upload_atmospheric*.yaml"
        )
    )
    # Upload atmospheric model data
    for config_path in atmospheric_model_configs:
        config = deepcopy(db_config)
        with open(config_path) as file:
            atmospheric_model_config = Config(yaml.load(file, Loader=yaml.SafeLoader))
        config.update(atmospheric_model_config)
        tool = UploadAtmosphericModel(config=config)
        run_tool(tool)
