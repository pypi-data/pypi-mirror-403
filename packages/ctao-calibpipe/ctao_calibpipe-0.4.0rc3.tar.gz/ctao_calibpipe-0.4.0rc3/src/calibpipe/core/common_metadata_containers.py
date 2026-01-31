"""Common metadata containers."""

from ctapipe.core import Container, Field


class ReferenceMetadataContainer(Container):
    """
    Container to store reference metadata.

    Serves as a central node for other metadata containers.
    This is the essential metadata that must be attached
    to all data products to uniquely describe the data product.
    """

    version_atmospheric_model = Field(
        None,
        description="Atmospheric Model version value to serve as a foreign key",
        type=str,
    )
    version = Field(
        None,
        description="Version of the reference metadata schema used in the data product",
        type=int,
    )
    ID_optical_throughput = Field(
        None, description="Optical throughput ID to serve as a foreign key", type=int
    )


class ProductReferenceMetadataContainer(Container):
    """
    Container to store product-related reference metadata.

    Describes the details of the data product, including its type and links to the data model definition.
    """

    ID = Field(
        None,
        description="Autoincremented value to serve as primary/foreign key",
        type=int,
    )
    description = Field(
        None, description="Human-readable description of data product", type=str
    )
    creation_time = Field(
        None,
        description="Human-readable date and time of file creation, in ISO format, UTC",
        type=str,
    )
    product_id = Field(
        None,
        description="A fixed-id to identify this product, e.g. UUID or VFN",
        type=str,
    )
    data_category = Field(None, description="A,B,C", type=str)
    data_level = Field(None, description="R0, R1, DL0, DL1, etc", type=str)
    data_association = Field(
        None, description="CTAO, Site, Subarray, Telescope, etc", type=str
    )
    data_type = Field(None, description="Event, Monitoring, Service, etc", type=str)
    data_model_name = Field(
        None, description="Identifying name of the data model used", type=str
    )
    data_model_version = Field(
        None, description="Version of the data model used", type=str
    )
    data_model_url = Field(
        None,
        description="Link to definition of data model, if available, and preferably a DOI",
        type=str,
    )
    format = Field(None, description="File format of the data product", type=str)


class ContactReferenceMetadataContainer(Container):
    """
    Container to store contact reference metadata.

    Describes the person or institution that is responsible for this data product.
    """

    ID = Field(
        None,
        description="Autoincremented value to serve as primary/foreign key",
        type=int,
    )
    organization = Field(
        None,
        description="Organization to which this data product is associated",
        type=str,
    )
    name = Field(None, description="Name of contact within organization", type=str)
    email = Field(None, description="Contact email address", type=str)


class ProcessReferenceMetadataContainer(Container):
    """
    Container to store process reference metadata.

    Describes the top-level process
    to which the activity that generated this product belongs.
    """

    ID = Field(
        None,
        description="Autoincremented value to serve as primary/foreign key",
        type=int,
    )
    type = Field(None, description="General type of the process", type=str)
    subtype = Field(
        None,
        description="More specific class of the process if the class is not sufficient to describe it",
        type=str,
    )
    subtype_id = Field(
        None,
        description="Unique identifier of the process, e.g. if the type is observation this is the obs_id",
        type=str,
    )


class ActivityReferenceMetadataContainer(Container):
    """
    Container to store activity reference metadata.

    Describes the specific software
    or task that generated this particular data product.
    """

    ID = Field(
        None,
        description="Autoincremented value to serve as primary/foreign key",
        type=int,
    )
    activity_id = Field(
        None,
        description="Unique identifier of the instance of this activity, if software a UUID",
        type=str,
    )
    name = Field(
        None,
        description="Name of activity that produced this data product, e.g. the software/script name",
        type=str,
    )
    type = Field(None, description="General type of the activity", type=str)
    start = Field(
        None, description="Starting date/time of activity, in ISO format, UTC", type=str
    )
    end = Field(
        None, description="Ending date/time of activity, in ISO format, UTC", type=str
    )
    software_name = Field(
        None,
        description="Name of software framework/library that was used if the activity if it involved software",
        type=str,
    )
    software_version = Field(None, description="Version of software used", type=str)


class InstrumentReferenceMetadataContainer(Container):
    """
    Container to store instrument reference metadata.

    Describes the subset of CTAO Instrument Description to which this data product is associated,
    which could be e.g. a Sub-array, or a small part such as a photo-sensor.
    """

    ID = Field(
        None,
        description="Autoincremented value to serve as primary/foreign key",
        type=int,
    )
    site = Field(
        None,
        description="CTAO-South, CTAO-North, or other site associated with the data product",
        type=str,
    )
    type = Field(
        None,
        description=(
            "The specific type of instrument in the class. E.g. if class=camera, ",
            "the type might be CHEC, or if class=telescope, the type might be 'SST'",
        ),
        type=str,
    )
    subtype = Field(
        None,
        description="Sub-type of the instrument. For example if the type is MST, this might be 'NectarCAM' or 'FlashCAM'",
        type=str,
    )
    instrument_id = Field(
        None,
        description=(
            "The unique ID of the specific instrument in the class. Depending on the instrument class,"
            "this might be for example is a telescope id, nominal subarray name, camera_id, or part serial number"
        ),
        type=str,
    )
