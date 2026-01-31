"""
Calibpipe-specific exceptions.

Exit code values are following the ICD_.

.. _ICD: https://gitlab.cta-observatory.org/cta-computing/dpps/dpps-project-management/icd-pipelines-workload/-/jobs/artifacts/main/raw/build/pipelines-workload.pdf?job=build
"""


class CalibrationError(Exception):
    """Base class for all CalibPipe exceptions."""

    exit_code = 1


class IntermittentError(CalibrationError):
    """Indicate an intermittent known issue that might be resolved by re-submitting the job."""

    exit_code = 100

    def __init__(self, message="Intermittent runtime error."):
        super().__init__(message)


class CorruptedInputDataError(CalibrationError):
    """Raise when the input data file is available but cannot be correctly processed."""

    exit_code = 104  # Activate an alternative scenario

    def __init__(self, message="Input data is corrupted."):
        super().__init__(message)


class MissingInputDataError(CalibrationError):
    """Raise when expected input data is missing."""

    exit_code = 105  # Activate an alternative scenario

    def __init__(self, message="Input data is missing."):
        super().__init__(message)


class InsufficientStatisticsError(CalibrationError):
    """Raise when data quality is found to be insufficient after processing."""

    exit_code = 106  # Activate an alternative scenario

    def __init__(self, message="Quality of input data is not sufficient."):
        super().__init__(message)


class ConfigurationError(CalibrationError):
    """Raise for issues with the configuration files."""

    exit_code = 101  # Configuration problem exit code due to IOError

    def __init__(self, message="Problem with the input configuration file.", *args):
        if args:
            message = message % args
        super().__init__(message)


class CalibrationStorageError(CalibrationError):
    """Raise for database/ECSV table storage related exceptions."""

    exit_code = 102  # Runtime error exit code due to IOError

    def __init__(self, message="Calibration coefficient cannot be stored."):
        super().__init__(message)


class DBStorageError(CalibrationStorageError):
    """Raise for issues with data storage in the database."""

    exit_code = 102  # Runtime error exit code due to IOError

    def __init__(self, message="Storage in the database cannot be performed."):
        super().__init__(message)


class FileStorageError(CalibrationStorageError):
    """Raise for issues with data storage in ECSV files."""

    exit_code = 102  # Runtime error exit code due to IOError

    def __init__(self, message="Storage in the output file cannot be performed."):
        super().__init__(message)
