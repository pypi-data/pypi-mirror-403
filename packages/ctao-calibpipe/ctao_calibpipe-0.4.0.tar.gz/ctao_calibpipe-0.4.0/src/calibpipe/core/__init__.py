"""Provide core classes and methods for CalibPipe."""

from .common_metadata_containers import (
    ActivityReferenceMetadataContainer,
    ContactReferenceMetadataContainer,
    InstrumentReferenceMetadataContainer,
    ProcessReferenceMetadataContainer,
    ProductReferenceMetadataContainer,
    ReferenceMetadataContainer,
)
from .exceptions import (
    CalibrationStorageError,
    ConfigurationError,
    CorruptedInputDataError,
    DBStorageError,
    FileStorageError,
    InsufficientStatisticsError,
    IntermittentError,
    MissingInputDataError,
)

__all__ = [
    # exceptions
    "CorruptedInputDataError",
    "ConfigurationError",
    "MissingInputDataError",
    "InsufficientStatisticsError",
    "IntermittentError",
    "DBStorageError",
    "FileStorageError",
    "CalibrationStorageError",
    # common_metadata_containers
    "ReferenceMetadataContainer",
    "ProductReferenceMetadataContainer",
    "ContactReferenceMetadataContainer",
    "ProcessReferenceMetadataContainer",
    "ActivityReferenceMetadataContainer",
    "InstrumentReferenceMetadataContainer",
]
