#!/usr/bin/env python3
"""
Test calibpipe-produce-camcalib-test-data tool
"""

from pathlib import Path

from ctapipe.core import run_tool

from calibpipe.tools.camcalib_test_data import CamCalibTestDataTool

# Get the path to the configuration files
CONFIG_PATH = Path(__file__).parent.joinpath(
    "../../../../../../docs/source/user_guide/telescope/camera/configuration/"
)


def test_produce_camcalib_test_data(pedestal_file, flatfield_file, tmp_path):
    """Test the calibpipe-produce-camcalib-test-data tool"""
    # Run the tool with the configuration and the input files
    assert (
        run_tool(
            CamCalibTestDataTool(),
            argv=[
                f"--CamCalibTestDataTool.pedestal_input_url={pedestal_file}",
                f"--CamCalibTestDataTool.flatfield_input_url={flatfield_file}",
                f"--CamCalibTestDataTool.output_dir={tmp_path}",
                f"--CamCalibTestDataTool.process_pedestal_config={CONFIG_PATH.joinpath('ctapipe_process_pedestal.yaml')}",
                f"--CamCalibTestDataTool.process_flatfield_config={CONFIG_PATH.joinpath('ctapipe_process_flatfield.yaml')}",
                f"--CamCalibTestDataTool.agg_stats_sky_pedestal_image_config={CONFIG_PATH.joinpath('ctapipe_calculate_pixel_stats_sky_pedestal_image.yaml')}",
                f"--CamCalibTestDataTool.agg_stats_flatfield_image_config={CONFIG_PATH.joinpath('ctapipe_calculate_pixel_stats_flatfield_image.yaml')}",
                f"--CamCalibTestDataTool.agg_stats_flatfield_peak_time_config={CONFIG_PATH.joinpath('ctapipe_calculate_pixel_stats_flatfield_peak_time.yaml')}",
            ],
            cwd=tmp_path,
            raises=True,
        )
        == 0
    )
