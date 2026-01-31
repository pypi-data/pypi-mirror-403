"""Adapter class."""

from typing import Any

import astropy.units
import sqlalchemy as sa

from .database_containers.container_map import ContainerMap
from .database_containers.table_version_manager import TableVersionManager


class Adapter:
    """
    Adapt CalibPipe containers into DB objects.

    The main method is to_postgres(), converting a CalibPipe container
    to a tuple containing the objects required to interact with the
    corresponding data in the database.
    """

    @staticmethod
    def to_postgres(
        container: ContainerMap.cp_container, version: str | None = None
    ) -> tuple[sa.Table, dict[str, Any]] | None:
        """
        Convert a CalibPipe container in DB data that can be inserted or queried.

        Parameters
        ----------
        container: ContainerMap.cp_container
            CalibPipe container (containing data) to convert to DB-level data

        version: str
            Software version corresponding to the data

        Returns
        -------
        Optional[tuple[sa.Table, dict[str, Any]]]
            None if no DB table information is associated to the container.
            A tuple containing the SQL table corresponding to the container,
            and a dictionary with the valued attributes contained in the
            CalibPipe container.
        """
        try:
            table_info = ContainerMap.map_to_db_container(type(container))
            table = TableVersionManager.apply_version(
                table_info=table_info, version=version
            )
            return table, Adapter.get_db_kwargs(container, table_info)
        except KeyError:
            return None

    @staticmethod
    def get_db_kwargs(
        container: ContainerMap.cp_container,
        table_info: ContainerMap.db_container_info,
    ) -> dict[str, Any]:
        """Get kwargs required to insert a row from a CalibPipe container."""
        return {
            name: Adapter._remove_astropy_unit(value, col.unit)
            for (name, value), col in zip(container.items(), table_info.columns)
        }

    @staticmethod
    def _remove_astropy_unit(value, unit):
        """
        Remove the astropy unit from a value if necessary.

        Astropy units cannot be stored in a database, or at least not
        in a single field. Units are therefore removed and the value is
        converted to either units from the column description
        or to SI units for consistency.
        """
        if isinstance(value, astropy.units.Quantity):
            if unit is not None:
                return (
                    value.decompose().to(unit).value
                )  # Value only, in the units from column description
            return value.decompose().value  # Value only, in S.I. units
        return value
