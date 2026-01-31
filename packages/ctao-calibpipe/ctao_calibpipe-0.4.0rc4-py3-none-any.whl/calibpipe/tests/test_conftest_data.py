"""
Test for CalibPipe test data download and caching functionality.

This test verifies that all test files can be downloaded and cached properly
using the conftest.py infrastructure.
"""

from ctapipe.utils.datasets import get_dataset_path

from calibpipe.tests.conftest import (
    DEFAULT_CALIBPIPE_URL,
    FILE_PATH_MAPPING,
    TEST_FILES,
)


class TestCalibPipeTestData:
    """Test class for CalibPipe test data functionality."""

    def test_download_all_test_files(self):
        """
        Test that all test files in TEST_FILES can be downloaded and cached.

        This test will:
        1. Download each file listed in TEST_FILES
        2. Verify the file exists after download
        3. Verify the file has non-zero size
        4. Test that subsequent calls use the cached version
        """
        downloaded_files = {}

        for file_path in TEST_FILES:
            print(f"Downloading and testing: {file_path}")

            # Get the server path from the mapping and download
            server_path = FILE_PATH_MAPPING[file_path]
            cached_file = get_dataset_path(server_path, url=DEFAULT_CALIBPIPE_URL)

            # Verify the file exists
            assert cached_file.exists(), (
                f"Downloaded file does not exist: {cached_file}"
            )

            # Verify the file has content
            file_size = cached_file.stat().st_size
            assert file_size > 0, (
                f"Downloaded file is empty: {cached_file} (size: {file_size})"
            )

            # Store for further verification
            downloaded_files[file_path] = {"path": cached_file, "size": file_size}

            print(f"  ✓ Downloaded to: {cached_file}")
            print(f"  ✓ File size: {file_size:,} bytes")

        # Test that all files are accessible
        assert len(downloaded_files) == len(TEST_FILES), (
            f"Expected {len(TEST_FILES)} files, got {len(downloaded_files)}"
        )

        print(
            f"\n✓ Successfully downloaded and verified {len(downloaded_files)} test files"
        )

        # Test caching by downloading again and ensuring we get the same paths
        print("\nTesting cache functionality...")
        for file_path in TEST_FILES[:3]:  # Test first 3 files for caching
            server_path = FILE_PATH_MAPPING[file_path]
            cached_file_again = get_dataset_path(server_path, url=DEFAULT_CALIBPIPE_URL)
            original_file = downloaded_files[file_path]["path"]

            assert cached_file_again == original_file, (
                f"Cache miss: got different path for {file_path}"
            )
            print(f"  ✓ Cache hit for: {file_path}")

        print("✓ Cache functionality verified")

    def test_specific_file_types(self):
        """Test specific file types and their expected characteristics."""

        # Test HDF5 files
        h5_files = [f for f in TEST_FILES if f.endswith(".h5")]
        for h5_file in h5_files:
            server_path = FILE_PATH_MAPPING[h5_file]
            cached_file = get_dataset_path(server_path, url=DEFAULT_CALIBPIPE_URL)

            # HDF5 files should have the HDF5 signature
            with open(cached_file, "rb") as f:
                header = f.read(8)
                assert header.startswith(b"\x89HDF"), (
                    f"File {h5_file} does not appear to be a valid HDF5 file"
                )

            print(f"  ✓ Verified HDF5 format: {h5_file}")

        # Test gzipped files
        gz_files = [f for f in TEST_FILES if f.endswith(".gz")]
        for gz_file in gz_files:
            server_path = FILE_PATH_MAPPING[gz_file]
            cached_file = get_dataset_path(server_path, url=DEFAULT_CALIBPIPE_URL)

            # Gzipped files should have the gzip magic number
            with open(cached_file, "rb") as f:
                header = f.read(2)
                assert header == b"\x1f\x8b", (
                    f"File {gz_file} does not appear to be a valid gzip file"
                )

            print(f"  ✓ Verified gzip format: {gz_file}")

    def test_file_categories(self):
        """Test that files are properly categorized by their directory structure."""

        categories = {"array": [], "telescope/throughput": [], "telescope/camera": []}

        for file_path in TEST_FILES:
            if file_path.startswith("array/"):
                categories["array"].append(file_path)
            elif file_path.startswith("telescope/throughput/"):
                categories["telescope/throughput"].append(file_path)
            elif file_path.startswith("telescope/camera/"):
                categories["telescope/camera"].append(file_path)

        # Verify we have files in each category
        assert len(categories["array"]) > 0, "No array test files found"
        assert len(categories["telescope/throughput"]) > 0, (
            "No throughput test files found"
        )
        assert len(categories["telescope/camera"]) > 0, "No camera test files found"

        print(f"✓ Array files: {len(categories['array'])}")
        print(f"✓ Throughput files: {len(categories['telescope/throughput'])}")
        print(f"✓ Camera files: {len(categories['telescope/camera'])}")

    def test_fixtures_work(
        self,
        cross_calibration_dl2_file,
        lst_muon_table_file,
        flatfield_file,
        pedestal_file,
    ):
        """Test that the pytest fixtures work correctly."""

        test_fixtures = [
            ("cross_calibration_dl2_file", cross_calibration_dl2_file),
            ("lst_muon_table_file", lst_muon_table_file),
            ("flatfield_file", flatfield_file),
            ("pedestal_file", pedestal_file),
        ]

        for fixture_name, fixture_path in test_fixtures:
            assert fixture_path.exists(), (
                f"Fixture {fixture_name} does not exist: {fixture_path}"
            )
            assert fixture_path.stat().st_size > 0, f"Fixture {fixture_name} is empty"
            print(f"  ✓ Fixture {fixture_name}: {fixture_path}")

        print("✓ All fixtures are working correctly")

    def test_parametrized_fixture(self, calibpipe_dl1_file):
        """Test the parametrized fixture for DL1 files."""
        assert calibpipe_dl1_file.exists(), (
            f"Parametrized DL1 file does not exist: {calibpipe_dl1_file}"
        )
        assert calibpipe_dl1_file.stat().st_size > 0, (
            f"Parametrized DL1 file is empty: {calibpipe_dl1_file}"
        )

        # Check that the filename contains one of the expected modes
        filename = calibpipe_dl1_file.name
        expected_modes = ["single_chunk", "same_chunks", "different_chunks"]
        assert any(mode in filename for mode in expected_modes), (
            f"DL1 filename {filename} doesn't contain expected mode"
        )

        print(f"  ✓ Parametrized DL1 file: {calibpipe_dl1_file}")


if __name__ == "__main__":
    # Allow running this test directly for quick verification
    import sys

    print("Running CalibPipe test data download verification...")
    print(f"Test data URL: {DEFAULT_CALIBPIPE_URL}")
    print(f"Number of test files: {len(TEST_FILES)}")
    print("=" * 60)

    test_instance = TestCalibPipeTestData()

    try:
        test_instance.test_download_all_test_files()
        test_instance.test_specific_file_types()
        test_instance.test_file_categories()
        print("\n" + "=" * 60)
        print(
            "✅ All tests passed! Test data download and caching is working correctly."
        )
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
