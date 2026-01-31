"""
Contain database containers for CalibPipe and the table version manager.

All CalibPipe data is defined at the database level
in this sub-package. In particular, a `SQLTableInformation` can be
found for each CalibPipe container.

In addition, two utilities are present here to ease the use of DB
containers:

- `TableVersionManager`: Creates tables objects specific to a version number
  (needed for CalibPipe data).
- `ContainerMap`: Maps CalibPipe containers (ultimately `ctapipe.core.container`)
  to database table information. The mapping is built-in,
  and allows users to quickly access the DB container
  corresponding to a CalibPipe container (or the contrary).

"""

from .atmosphere import (
    atmospheric_model_sql_info,
    macobac_sql_info,
    map_meta_sql_info,
    map_sql_info,
    mdp_sql_info,
    rayleigh_extinction_sql_info,
    selected_model_sql_info,
)
from .common_metadata import (
    activity_reference_metadata_sql_info,
    contact_reference_metadata_sql_info,
    instrument_reference_metadata_sql_info,
    process_reference_metadata_sql_info,
    product_reference_metadata_sql_info,
    reference_metadata_sql_info,
)
from .container_map import ContainerMap
from .observatory import observatory_sql_info, season_sql_info
from .table_version_manager import TableVersionManager
from .throughput import optical_throughput_sql_info
from .version_control import version_control_sql_info

__all__ = [
    "atmospheric_model_sql_info",
    "map_meta_sql_info",
    "map_sql_info",
    "mdp_sql_info",
    "macobac_sql_info",
    "selected_model_sql_info",
    "observatory_sql_info",
    "rayleigh_extinction_sql_info",
    "season_sql_info",
    "version_control_sql_info",
    "TableVersionManager",
    "ContainerMap",
    "reference_metadata_sql_info",
    "product_reference_metadata_sql_info",
    "contact_reference_metadata_sql_info",
    "activity_reference_metadata_sql_info",
    "process_reference_metadata_sql_info",
    "instrument_reference_metadata_sql_info",
    "optical_throughput_sql_info",
]
