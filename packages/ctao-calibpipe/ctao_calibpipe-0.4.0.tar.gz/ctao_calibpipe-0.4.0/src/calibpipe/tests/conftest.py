"""
Test configuration and fixtures for CalibPipe tests.

This module provides fixtures for managing test data from the DPPS test data repository,
using ctapipe's get_dataset_path utility with CalibPipe-specific defaults.

Set the CALIBPIPE_DATASET_URL environment variable to override the default URL:
https://minio-cta.zeuthen.desy.de/dpps-testdata-public/data/calibpipe-test-data/
"""

import shutil
import tempfile
from pathlib import Path

import pytest
from ctapipe.utils.datasets import get_dataset_path

# Default URL for CalibPipe test data
DEFAULT_CALIBPIPE_URL = (
    "https://minio-cta.zeuthen.desy.de/dpps-testdata-public/data/calibpipe-test-data/"
)

# Mapping from local file paths to server file paths (for historical compatibility)
FILE_PATH_MAPPING = {
    # Local path -> Server path
    "array/cross_calibration_test_dl2.h5": "cross_calibration_test_dl2.h5",
    "telescope/throughput/lst_muon_table.h5": "dl1_lst_muon_simulation.h5",
    "telescope/throughput/empty_muon_table.h5": "empty_muon_table.h5",
    "telescope/camera/flatfield_LST_dark.simtel.gz": "camera-calibration-test-data/flasher_LST_dark.simtel.gz",
    "telescope/camera/pedestal_LST_dark.simtel.gz": "camera-calibration-test-data/pedestals_LST_dark.simtel.gz",
    "telescope/camera/high_statsagg_sims_single_chunk.dl1.h5": "camera-calibration-test-data/high_statsagg_v2_sims_single_chunk.dl1.h5",
    "telescope/camera/high_statsagg_obslike_same_chunks.dl1.h5": "camera-calibration-test-data/high_statsagg_v2_obslike_same_chunks.dl1.h5",
    "telescope/camera/high_statsagg_obslike_different_chunks.dl1.h5": "camera-calibration-test-data/high_statsagg_v2_obslike_different_chunks.dl1.h5",
    # Muon test data files  - lst LaPalma
    "telescope/throughput/muon-_0deg_0deg_run000008___cta-prod6-2156m-LaPalma-lst-dark-ref-degraded-0.8.h5": "muon-test-data/muon-_0deg_0deg_run000008___cta-prod6-2156m-LaPalma-lst-dark-ref-degraded-0.8.h5",
    "telescope/throughput/muon-_0deg_0deg_run000008___cta-prod6-2156m-LaPalma-lst-dark-ref-degraded-0.81.h5": "muon-test-data/muon-_0deg_0deg_run000008___cta-prod6-2156m-LaPalma-lst-dark-ref-degraded-0.81.h5",
    "telescope/throughput/muon-_0deg_0deg_run000008___cta-prod6-2156m-LaPalma-lst-dark-ref-degraded-0.83.h5": "muon-test-data/muon-_0deg_0deg_run000008___cta-prod6-2156m-LaPalma-lst-dark-ref-degraded-0.83.h5",
    "telescope/throughput/muon+_0deg_0deg_run000012___cta-prod6-2156m-LaPalma-lst-dark-ref-degraded-0.8.h5": "muon-test-data/muon+_0deg_0deg_run000012___cta-prod6-2156m-LaPalma-lst-dark-ref-degraded-0.8.h5",
    "telescope/throughput/muon+_0deg_0deg_run000012___cta-prod6-2156m-LaPalma-lst-dark-ref-degraded-0.81.h5": "muon-test-data/muon+_0deg_0deg_run000012___cta-prod6-2156m-LaPalma-lst-dark-ref-degraded-0.81.h5",
    "telescope/throughput/muon+_0deg_0deg_run000012___cta-prod6-2156m-LaPalma-lst-dark-ref-degraded-0.83.h5": "muon-test-data/muon+_0deg_0deg_run000012___cta-prod6-2156m-LaPalma-lst-dark-ref-degraded-0.83.h5",
    # Muon test data files  - mst LaPalma (NC)
    "telescope/throughput/muon+_0deg_0deg_run000006___cta-prod6-2156m-LaPalma-mst-nc-dark-ref-degraded-0.83.h5": "muon-test-data/muon+_0deg_0deg_run000006___cta-prod6-2156m-LaPalma-mst-nc-dark-ref-degraded-0.83.h5",
    # Muon test data files  - mst Paranal (FC)
    "telescope/throughput/muon+_0deg_0deg_run000002___cta-prod6-2147m-Paranal-mst-fc-dark-ref-degraded-0.83.h5": "muon-test-data/muon+_0deg_0deg_run000002___cta-prod6-2147m-Paranal-mst-fc-dark-ref-degraded-0.83.h5",
    # DL0 muon test data files
    "telescope/throughput/muon-_37.35deg_0deg_run000004___cta-prod6-2156m-LaPalma-lst-dark-ref-degraded-0.8_summer.simtel.zst": "muon-test-data/muon-_37.35deg_0deg_run000004___cta-prod6-2156m-LaPalma-lst-dark-ref-degraded-0.8_summer.simtel.zst",
    "telescope/psf/muon+_37.35deg_0deg_run000012___cta-prod6-2156m-LaPalma-lst-dark-ref-degraded-0.8_summer.simtel.zst": "muon-test-data/muon+_37.35deg_0deg_run000012___cta-prod6-2156m-LaPalma-lst-dark-ref-degraded-0.8_summer.simtel.zst",
    # psf with muons
    "telescope/psf/muon-_20deg_0deg_run000002___cta-prod6-2156m-LaPalma-lst-dark.h5": "muon-test-data/psf/muon-_20deg_0deg_run000002___cta-prod6-2156m-LaPalma-lst-dark.h5",
    "telescope/psf/muon-_20deg_0deg_run000002___cta-prod6-2156m-LaPalma-lst-dark-align-deg-20p.h5": "muon-test-data/psf/muon-_20deg_0deg_run000002___cta-prod6-2156m-LaPalma-lst-dark-align-deg-20p.h5",
    "telescope/psf/muon-_20deg_0deg_run000002___cta-prod6-2156m-LaPalma-lst-dark-align-deg-50p.h5": "muon-test-data/psf/muon-_20deg_0deg_run000002___cta-prod6-2156m-LaPalma-lst-dark-align-deg-50p.h5",
}


# Test data files available in the CalibPipe test data repository (local paths)
TEST_FILES = list(FILE_PATH_MAPPING.keys())


@pytest.fixture
def cut_value_h0():
    """H0 cut value for PSF tests."""
    return 5


@pytest.fixture
def cut_value_h1():
    """H1 cut value for PSF tests."""
    return 0.1


@pytest.fixture
def separation_power_cut():
    """Separation power cut value for PSF tests."""
    return 0.01


@pytest.fixture(scope="session")
def calibpipe_test_data_dir():
    """
    Fixture providing the base test data directory.

    This creates a temporary directory structure for test data
    and ensures all required test files are downloaded using ctapipe's get_dataset_path
    with CalibPipe-specific URL defaults.

    Uses CALIBPIPE_DATASET_URL environment variable if set, otherwise defaults to:
    https://minio-cta.zeuthen.desy.de/dpps-testdata-public/data/calibpipe-test-data/
    """
    test_data_dir = Path(tempfile.mkdtemp(prefix="calibpipe_test_data_"))

    try:
        # Create directory structure
        (test_data_dir / "array").mkdir()
        (test_data_dir / "telescope" / "throughput").mkdir(parents=True)
        (test_data_dir / "telescope" / "psf").mkdir(parents=True)
        (test_data_dir / "telescope" / "camera").mkdir(parents=True)

        # Download and copy required files
        for local_path, server_path in FILE_PATH_MAPPING.items():
            # Download using the server path
            cached_file = get_dataset_path(server_path, url=DEFAULT_CALIBPIPE_URL)
            # Place in the local directory structure
            target_file = test_data_dir / local_path
            shutil.copy2(cached_file, target_file)

        yield test_data_dir

    finally:
        # Clean up
        shutil.rmtree(test_data_dir, ignore_errors=True)


@pytest.fixture(scope="session")
def cross_calibration_dl2_file(calibpipe_test_data_dir):
    """Fixture providing the cross-calibration DL2 test file."""
    return calibpipe_test_data_dir / "array" / "cross_calibration_test_dl2.h5"


@pytest.fixture(scope="session")
def lst_muon_table_file(calibpipe_test_data_dir):
    """Fixture providing the LST muon table test file."""
    return calibpipe_test_data_dir / "telescope" / "throughput" / "lst_muon_table.h5"


@pytest.fixture(scope="session")
def empty_muon_table_file(calibpipe_test_data_dir):
    """Fixture providing the empty muon table test file."""
    return calibpipe_test_data_dir / "telescope" / "throughput" / "empty_muon_table.h5"


# lst
@pytest.fixture(scope="session")
def muon_minus_r80_file(calibpipe_test_data_dir):
    """Fixture providing the μ- muon test file with reflectivity 0.8."""
    return (
        calibpipe_test_data_dir
        / "telescope"
        / "throughput"
        / "muon-_0deg_0deg_run000008___cta-prod6-2156m-LaPalma-lst-dark-ref-degraded-0.8.h5"
    )


@pytest.fixture(scope="session")
def muon_minus_r81_file(calibpipe_test_data_dir):
    """Fixture providing the μ- muon test file with reflectivity 0.81."""
    return (
        calibpipe_test_data_dir
        / "telescope"
        / "throughput"
        / "muon-_0deg_0deg_run000008___cta-prod6-2156m-LaPalma-lst-dark-ref-degraded-0.81.h5"
    )


@pytest.fixture(scope="session")
def muon_minus_r83_file(calibpipe_test_data_dir):
    """Fixture providing the μ- muon test file with reflectivity 0.83."""
    return (
        calibpipe_test_data_dir
        / "telescope"
        / "throughput"
        / "muon-_0deg_0deg_run000008___cta-prod6-2156m-LaPalma-lst-dark-ref-degraded-0.83.h5"
    )


@pytest.fixture(scope="session")
def muon_plus_r80_file(calibpipe_test_data_dir):
    """Fixture providing the μ+ muon test file with reflectivity 0.8."""
    return (
        calibpipe_test_data_dir
        / "telescope"
        / "throughput"
        / "muon+_0deg_0deg_run000012___cta-prod6-2156m-LaPalma-lst-dark-ref-degraded-0.8.h5"
    )


@pytest.fixture(scope="session")
def muon_plus_r81_file(calibpipe_test_data_dir):
    """Fixture providing the μ+ muon test file with reflectivity 0.81."""
    return (
        calibpipe_test_data_dir
        / "telescope"
        / "throughput"
        / "muon+_0deg_0deg_run000012___cta-prod6-2156m-LaPalma-lst-dark-ref-degraded-0.81.h5"
    )


@pytest.fixture(scope="session")
def muon_plus_r83_file(calibpipe_test_data_dir):
    """Fixture providing the μ+ muon test file with reflectivity 0.83."""
    return (
        calibpipe_test_data_dir
        / "telescope"
        / "throughput"
        / "muon+_0deg_0deg_run000012___cta-prod6-2156m-LaPalma-lst-dark-ref-degraded-0.83.h5"
    )


# mst nc
@pytest.fixture(scope="session")
def muon_mst_nc_file(calibpipe_test_data_dir):
    """Fixture providing the μ+ muon test file with reflectivity 0.83. (MST-NC)"""
    return (
        calibpipe_test_data_dir
        / "telescope"
        / "throughput"
        / "muon+_0deg_0deg_run000006___cta-prod6-2156m-LaPalma-mst-nc-dark-ref-degraded-0.83.h5"
    )


# mst fc
@pytest.fixture(scope="session")
def muon_mst_fc_file(calibpipe_test_data_dir):
    """Fixture providing the μ+ muon test file with reflectivity 0.83. (MST-FC)"""
    return (
        calibpipe_test_data_dir
        / "telescope"
        / "throughput"
        / "muon+_0deg_0deg_run000002___cta-prod6-2147m-Paranal-mst-fc-dark-ref-degraded-0.83.h5"
    )


# lst PSF
@pytest.fixture(scope="session")
def muon_lst_psf_mu_minus_nominal_mirror_alignment_file(calibpipe_test_data_dir):
    """Fixture providing the μ- muon test file for psf measurements with nominal mirror alignment"""
    return (
        calibpipe_test_data_dir
        / "telescope"
        / "psf"
        / "muon-_20deg_0deg_run000002___cta-prod6-2156m-LaPalma-lst-dark.h5"
    )


@pytest.fixture(scope="session")
def muon_lst_psf_mu_minus_20p_degraded_mirror_alignment_file(calibpipe_test_data_dir):
    """Fixture providing the μ- muon test file for psf measurements with 20 percent degraded mirror alignment"""
    return (
        calibpipe_test_data_dir
        / "telescope"
        / "psf"
        / "muon-_20deg_0deg_run000002___cta-prod6-2156m-LaPalma-lst-dark-align-deg-20p.h5"
    )


@pytest.fixture(scope="session")
def muon_lst_psf_mu_minus_50p_degraded_mirror_alignment_file(calibpipe_test_data_dir):
    """Fixture providing the μ- muon test file for psf measurements with 50 percent degraded mirror alignment"""
    return (
        calibpipe_test_data_dir
        / "telescope"
        / "psf"
        / "muon-_20deg_0deg_run000002___cta-prod6-2156m-LaPalma-lst-dark-align-deg-50p.h5"
    )


@pytest.fixture(scope="session")
def muon_test_files(
    muon_minus_r80_file,
    muon_minus_r81_file,
    muon_minus_r83_file,
    muon_plus_r80_file,
    muon_plus_r81_file,
    muon_plus_r83_file,
):
    """Fixture providing a dictionary of all muon test files organized by particle type and reflectivity (lst)."""
    return {
        "μ-": {
            "0.80": muon_minus_r80_file,
            "0.81": muon_minus_r81_file,
            "0.83": muon_minus_r83_file,
        },
        "μ+": {
            "0.80": muon_plus_r80_file,
            "0.81": muon_plus_r81_file,
            "0.83": muon_plus_r83_file,
        },
    }


@pytest.fixture(scope="session")
def flatfield_file(calibpipe_test_data_dir):
    """Fixture providing the flatfield calibration test file."""
    return (
        calibpipe_test_data_dir
        / "telescope"
        / "camera"
        / "flatfield_LST_dark.simtel.gz"
    )


@pytest.fixture(scope="session")
def pedestal_file(calibpipe_test_data_dir):
    """Fixture providing the pedestal calibration test file."""
    return (
        calibpipe_test_data_dir / "telescope" / "camera" / "pedestal_LST_dark.simtel.gz"
    )


@pytest.fixture(scope="session")
def muon_simtel_file(calibpipe_test_data_dir):
    """Fixture providing the pedestal calibration test file."""
    return (
        calibpipe_test_data_dir
        / "telescope"
        / "throughput"
        / "muon-_37.35deg_0deg_run000004___cta-prod6-2156m-LaPalma-lst-dark-ref-degraded-0.8_summer.simtel.zst"
    )


@pytest.fixture(scope="session")
def muon_simtel_file_psf(calibpipe_test_data_dir):
    """Fixture providing the pedestal calibration test file."""
    return (
        calibpipe_test_data_dir
        / "telescope"
        / "psf"
        / "muon+_37.35deg_0deg_run000012___cta-prod6-2156m-LaPalma-lst-dark-ref-degraded-0.8_summer.simtel.zst"
    )


@pytest.fixture(
    scope="session",
    params=["sims_single_chunk", "obslike_same_chunks", "obslike_different_chunks"],
)
def calibpipe_dl1_file(request, calibpipe_test_data_dir):
    """Fixture providing calibpipe DL1 test files with different chunking modes."""
    mode = request.param
    filename = f"high_statsagg_{mode}.dl1.h5"
    return calibpipe_test_data_dir / "telescope" / "camera" / filename


@pytest.fixture
def tmp_test_data_dir():
    """
    Fixture providing a temporary directory for test data.

    This is useful for tests that need to create temporary files
    or modify test data without affecting the cached versions.
    """
    tmp_dir = Path(tempfile.mkdtemp(prefix="calibpipe_tmp_test_"))
    try:
        yield tmp_dir
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
