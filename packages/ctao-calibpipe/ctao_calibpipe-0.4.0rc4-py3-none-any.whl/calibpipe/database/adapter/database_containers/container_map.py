"""ContainerMap class."""

from ctapipe.core import Container

from ...interfaces.sql_table_info import SQLTableInfo


class ContainerMap:
    """
    Map CalibPipe and database containers.

    The correspondence must be set using the `register_container_pair()`
    method, called automatically for the built-in CalibPipe containers. Once
    set, this map allows us to quickly get the DB container associated
    to a CalilbPipe container (or contrary) to switch between the two worlds.
    """

    cp_container = Container

    db_container_info = SQLTableInfo
    cp_container_type = type[cp_container]

    _cp_containers: dict[db_container_info, cp_container_type] = {}
    _db_containers: dict[cp_container_type, db_container_info] = {}

    @staticmethod
    def map_to_cp_container(
        db_container: db_container_info,
    ) -> cp_container_type:
        """Return the CalibPipe container corresponding to a DB container."""
        return ContainerMap._cp_containers[db_container]

    @staticmethod
    def map_to_db_container(
        cp_container: cp_container_type,
    ) -> db_container_info:
        """Return the DB container corresponding to a CalibPipe container."""
        return ContainerMap._db_containers[cp_container]

    @staticmethod
    def get_cp_containers() -> list:
        """Return the list of registered CalibPipe containers."""
        return [*ContainerMap._db_containers]

    @staticmethod
    def register_container_pair(
        cp_container: cp_container_type, db_container: db_container_info
    ) -> None:
        """Associate a CalibPipe container and a DB container."""
        ContainerMap._cp_containers[db_container] = cp_container
        ContainerMap._db_containers[cp_container] = db_container

    @staticmethod
    def unregister_container_pair(
        cp_container: cp_container_type, db_container: db_container_info
    ) -> None:
        """Deassociate a CalibPipe container and a DB container."""
        ContainerMap._db_containers[cp_container].pop(db_container, None)
        ContainerMap._cp_containers[db_container].pop(cp_container, None)
