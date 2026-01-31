import subprocess
from enum import Enum
from pathlib import Path

import pytest


class WorkflowGroup(Enum):
    ATMOSPHERE = "atmosphere"
    CAMERA = "telescope/camera"
    MUONTHROUGHPUT = "telescope/throughput"
    MUONPSF = "telescope/psf"
    # Add other groups as needed


def run_cwl(workflow, config=None):
    command = ["cwltool", workflow]
    if config is not None:
        command.append(config)
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        return result.stderr
    except subprocess.CalledProcessError as e:
        return e.stderr


# Common base path for all configuration files
DEFAULT_CONFIG_BASE_PATH = Path(__file__).parent / "../docs/source/user_guide"

# Define your test cases declaratively
# Test case parameters: (group, id, base_path, config_kwargs)
# - group: WorkflowGroup enum (ATMOSPHERE or CAMERA)
# - id: Use case identifier string (e.g., "1.2", "1.3", "2.2", "2.10", "2.20")
# - base_path: Path to user_guide directory (fixtures will add their specific subdirectories)
# - config_kwargs: Dictionary of configuration overrides
USECASE_PARAMS = [
    (WorkflowGroup.ATMOSPHERE, "1.2", DEFAULT_CONFIG_BASE_PATH, {}),
    (WorkflowGroup.ATMOSPHERE, "1.3", DEFAULT_CONFIG_BASE_PATH, {}),
    (WorkflowGroup.ATMOSPHERE, "1.7", DEFAULT_CONFIG_BASE_PATH, {}),
    # Camera workflow with single files (default)
    (WorkflowGroup.CAMERA, "2.20", DEFAULT_CONFIG_BASE_PATH, {}),
    # Camera workflow with multiple files
    (
        WorkflowGroup.CAMERA,
        "2.20",
        DEFAULT_CONFIG_BASE_PATH,
        {
            "dl0_pedestal_data": [
                {"class": "File", "path": "PEDESTAL_FILE_1"},
                {"class": "File", "path": "PEDESTAL_FILE_2"},
            ],
            "dl0_flatfield_data": [
                {"class": "File", "path": "FLATFIELD_FILE_1"},
                {"class": "File", "path": "FLATFIELD_FILE_2"},
            ],
        },
    ),
    # Muon throughput calibration workflow with one files
    (
        WorkflowGroup.MUONTHROUGHPUT,
        "2.2",
        DEFAULT_CONFIG_BASE_PATH,
        {
            "dl0_input_data": [
                {"class": "File", "path": "DL0_MUON_FILE"},
            ],
        },
    ),
    # Muon psf measurements workflow with one files
    (
        WorkflowGroup.MUONPSF,
        "2.10",
        DEFAULT_CONFIG_BASE_PATH,
        {
            "dl0_input_data": [
                {"class": "File", "path": "DL0_MUON_FILE"},
            ],
        },
    ),
]


@pytest.mark.integration
@pytest.mark.parametrize(
    ("group", "id", "base_path", "config_kwargs"),
    [
        pytest.param(
            g, i, base_path, kwargs, marks=pytest.mark.verifies_usecase(f"UC-120-{i}")
        )
        for g, i, base_path, kwargs in USECASE_PARAMS
    ],
)
def test_run_cwl(group, id, base_path, config_kwargs, workflow_config):
    path_to_workflows = Path(__file__).parent / "../workflows"

    # Use glob to find the workflow file
    workflow_pattern = f"uc-120-{id}*.cwl"
    workflow_file_path = path_to_workflows / group.value

    try:
        workflow_file = next(workflow_file_path.glob(workflow_pattern))
    except StopIteration:
        pytest.fail(
            f"No matching workflow file found for pattern {workflow_pattern} "
            f"in {workflow_file_path}."
        )

    # Use the populated config from the fixture
    output = run_cwl(workflow_file, workflow_config)
    assert (
        "Final process status is success" in output
        or "Final process status is temporaryFail" in output
    )
    if "Final process status is temporaryFail" in output:
        assert "exited with status: 100" in output
