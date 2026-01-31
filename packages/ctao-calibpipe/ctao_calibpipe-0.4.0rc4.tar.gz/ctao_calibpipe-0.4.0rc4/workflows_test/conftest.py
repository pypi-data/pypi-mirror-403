"""Fixtures for workflow tests."""

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from calibpipe.tests.conftest import *  # noqa: D100, F403

# Import WorkflowGroup from test module - add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent))
from test_run_workflows import WorkflowGroup


@pytest.fixture
def muon_psf_config_factory(muon_simtel_file_psf):
    """Create muon psf calibration workflow configurations."""

    def _muon_psf_config(uc_id, base_path, **kwargs):
        # Append specific to muon psf and throughput configuration path
        config_path = base_path / "telescope/psf/configuration"
        config_path_throughput = base_path / "telescope/throughput/configuration"

        # Default config uses single files
        config = {
            "dl0_input_data": [{"class": "File", "path": str(muon_simtel_file_psf)}],
            "process_config": [
                {
                    "class": "File",
                    "path": str(
                        config_path_throughput / "ctapipe_process_muon_image.yaml"
                    ),
                },
                {
                    "class": "File",
                    "path": str(
                        config_path_throughput / "ctapipe_process_muon_fitter.yaml"
                    ),
                },
            ],
            "output_filename": "muon_psf_results.dl1.h5",
            "psf_muon_config": {
                "class": "File",
                "path": str(config_path / "psf_muon_configuration.yaml"),
            },
            "log-level": "INFO",
            "provenance_log_filename": "optical_psf.provenance.log",
        }

        # Allow overriding any config values
        config.update(kwargs)

        # Replace placeholder paths with actual fixture file paths
        def _replace_placeholders(obj):
            if isinstance(obj, dict):
                return {k: _replace_placeholders(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [_replace_placeholders(item) for item in obj]
            elif isinstance(obj, str):
                replacements = {
                    "DL0_MUON_FILE": str(muon_simtel_file_psf),
                }
                return replacements.get(obj, obj)
            else:
                return obj

        config = _replace_placeholders(config)
        return config

    return _muon_psf_config


@pytest.fixture
def muon_throughput_config_factory(muon_simtel_file):
    """Create muon throughput calibration workflow configurations."""

    def _muon_throughput_config(uc_id, base_path, **kwargs):
        # Append specific to muon throughput configuration path
        config_path = base_path / "telescope/throughput/configuration"

        # Default config uses single files
        config = {
            "dl0_input_data": [{"class": "File", "path": str(muon_simtel_file)}],
            "process_config": [
                {
                    "class": "File",
                    "path": str(config_path / "ctapipe_process_muon_image.yaml"),
                },
                {
                    "class": "File",
                    "path": str(config_path / "ctapipe_process_muon_fitter.yaml"),
                },
            ],
            "output_filename": "muon_throughput_results.dl1.h5",
            "throughput_muon_config": {
                "class": "File",
                "path": str(config_path / "throughput_muon_configuration.yaml"),
            },
            "log-level": "INFO",
            "provenance_log_filename": "optical_throughput.provenance.log",
        }

        # Allow overriding any config values
        config.update(kwargs)

        # Replace placeholder paths with actual fixture file paths
        def _replace_placeholders(obj):
            if isinstance(obj, dict):
                return {k: _replace_placeholders(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [_replace_placeholders(item) for item in obj]
            elif isinstance(obj, str):
                replacements = {
                    "DL0_MUON_FILE": str(muon_simtel_file),
                }
                return replacements.get(obj, obj)
            else:
                return obj

        config = _replace_placeholders(config)
        return config

    return _muon_throughput_config


@pytest.fixture
def camera_config_factory(flatfield_file, pedestal_file):
    """Create camera calibration workflow configurations."""

    def _make_camera_config(uc_id, base_path, **kwargs):
        # Append camera-specific configuration path
        config_path = base_path / "telescope/camera/configuration"

        # Default config uses single files
        config = {
            "dl0_pedestal_data": [{"class": "File", "path": str(pedestal_file)}],
            "dl0_flatfield_data": [{"class": "File", "path": str(flatfield_file)}],
            "ped_process_config": [
                {
                    "class": "File",
                    "path": str(config_path / "ctapipe_process_pedestal.yaml"),
                }
            ],
            "ff_process_config": [
                {
                    "class": "File",
                    "path": str(config_path / "ctapipe_process_flatfield.yaml"),
                }
            ],
            "ped_img_pix_stats_config": {
                "class": "File",
                "path": str(
                    config_path
                    / "ctapipe_calculate_pixel_stats_sky_pedestal_image.yaml"
                ),
            },
            "ff_img_pix_stats_config": {
                "class": "File",
                "path": str(
                    config_path / "ctapipe_calculate_pixel_stats_flatfield_image.yaml"
                ),
            },
            "ff_time_pix_stats_config": {
                "class": "File",
                "path": str(
                    config_path
                    / "ctapipe_calculate_pixel_stats_flatfield_peak_time.yaml"
                ),
            },
            "merge_config": {
                "class": "File",
                "path": str(base_path / "telescope/ctapipe_merge.yaml"),
            },
            "coeffs_camcalib_config": {
                "class": "File",
                "path": str(
                    config_path / "calibpipe_calculate_camcalib_coefficients.yaml"
                ),
            },
            "output_filename": "camera_calibration.mon.dl1.h5",
            "log-level": "INFO",
            "provenance_log_filename": "camera_calibration.provenance.log",
        }

        # Allow overriding any config values
        config.update(kwargs)

        # Replace placeholder paths with actual fixture file paths
        def _replace_placeholders(obj):
            if isinstance(obj, dict):
                return {k: _replace_placeholders(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [_replace_placeholders(item) for item in obj]
            elif isinstance(obj, str):
                replacements = {
                    "PEDESTAL_FILE_1": str(pedestal_file),
                    "PEDESTAL_FILE_2": str(
                        pedestal_file
                    ),  # Use same file for both for now
                    "FLATFIELD_FILE_1": str(flatfield_file),
                    "FLATFIELD_FILE_2": str(
                        flatfield_file
                    ),  # Use same file for both for now
                }
                return replacements.get(obj, obj)
            else:
                return obj

        config = _replace_placeholders(config)
        return config

    return _make_camera_config


@pytest.fixture
def atmosphere_config_factory():
    """Create atmosphere workflow configuration factory."""

    def _make_atmosphere_config(uc_id, base_path, **kwargs):
        # Append atmosphere-specific configuration paths
        atmosphere_config_path = base_path / "atmosphere/configuration"
        utils_config_path = base_path / "utils/configuration"

        if uc_id == "1.2":
            config = {
                "log-level": "INFO",
                "configuration": {
                    "class": "File",
                    "path": str(atmosphere_config_path / "calculate_macobac.yaml"),
                },
                "provenance_log_filename": "calibpipe-calculate-macobac.provenance.log",
            }
        elif uc_id == "1.3":
            # Configuration for select reference atmospheric model
            rdams_token = Path(__file__).parent / "../rdams_token.txt"

            config = {
                "log-level": "INFO",
                "credentials": {
                    "class": "File",
                    "path": str(rdams_token),
                },
                "configuration": [
                    {
                        "class": "File",
                        "path": str(
                            atmosphere_config_path
                            / "select_reference_atmospheric_model.yaml"
                        ),
                    },
                    {
                        "class": "File",
                        "path": str(utils_config_path / "db_config.yaml"),
                    },
                ],
                "provenance_log_filename": "calibpipe-select-reference-atmospheric-model.provenance.log",
            }
        elif uc_id == "1.7":
            # Configuration for create contemporary atmospheric model
            cdsapi_credentials = Path(__file__).parent / "../.cdsapirc"
            macobac_table_path = (
                Path(__file__).parent
                / "../src/calibpipe/tests/data/atmosphere/molecular_atmosphere/macobac.ecsv"
            )

            config = {
                "log-level": "INFO",
                "credentials": {
                    "class": "File",
                    "path": str(cdsapi_credentials),
                },
                "configuration": [
                    {
                        "class": "File",
                        "path": str(
                            atmosphere_config_path
                            / "create_molecular_atmospheric_model.yaml"
                        ),
                    },
                    {
                        "class": "File",
                        "path": str(utils_config_path / "db_config.yaml"),
                    },
                ],
                "macobac_table": {
                    "class": "File",
                    "path": str(macobac_table_path),
                },
                "provenance_log_filename": "calibpipe-create-molecular-atmospheric-model.provenance.log",
            }
        else:
            raise ValueError(f"Unknown atmosphere UC ID: {uc_id}")

        # Allow overriding any config values
        config.update(kwargs)
        return config

    return _make_atmosphere_config


@pytest.fixture
def workflow_config_factory(
    camera_config_factory,
    atmosphere_config_factory,
    muon_throughput_config_factory,
    muon_psf_config_factory,
):
    """Create workflow configuration files using factories."""

    def _make_workflow_config(group, uc_id, tmp_path, base_path, **config_overrides):
        # Find workflow file
        path_to_workflows = Path(__file__).parent / "../workflows"
        workflow_pattern = f"uc-120-{uc_id}*.cwl"
        workflow_file_path = path_to_workflows / group.value

        try:
            workflow_file = next(workflow_file_path.glob(workflow_pattern))
        except StopIteration:
            pytest.fail(
                f"No matching workflow file found for pattern {workflow_pattern} "
                f"in {workflow_file_path}."
            )

        # Generate CWL template
        try:
            make_tpl = subprocess.run(
                ["cwltool", "--make-template", str(workflow_file)],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            pytest.fail(
                f"cwltool --make-template failed for {workflow_file}: {e.stderr}"
            )

        # Parse template
        template = yaml.safe_load(make_tpl.stdout) or {}

        # Create config based on workflow group using factories
        if group == WorkflowGroup.CAMERA:
            config_values = camera_config_factory(uc_id, base_path, **config_overrides)
        elif group == WorkflowGroup.ATMOSPHERE:
            config_values = atmosphere_config_factory(
                uc_id, base_path, **config_overrides
            )
        elif group == WorkflowGroup.MUONTHROUGHPUT:
            config_values = muon_throughput_config_factory(
                uc_id, base_path, **config_overrides
            )
        elif group == WorkflowGroup.MUONPSF:
            config_values = muon_psf_config_factory(
                uc_id, base_path, **config_overrides
            )
        else:
            raise ValueError(f"Unknown workflow group: {group}")

        # Merge template with fixture-based config
        populated = dict(template)
        for k, v in config_values.items():
            populated[k] = v

        # Write to temporary file
        config_path = tmp_path / f"uc-120-{uc_id}.yml"
        config_path.write_text(yaml.safe_dump(populated))

        return config_path

    return _make_workflow_config


@pytest.fixture
def workflow_config(request, tmp_path, workflow_config_factory):
    """Generate workflow config for parameterized tests with optional kwargs."""
    group, uc_id, base_path, config_kwargs = (
        request.node.callspec.params["group"],
        request.node.callspec.params["id"],
        request.node.callspec.params["base_path"],
        request.node.callspec.params["config_kwargs"],
    )
    return workflow_config_factory(group, uc_id, tmp_path, base_path, **config_kwargs)
