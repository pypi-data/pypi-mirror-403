"""Utilities for CalibPipe data."""

from datetime import datetime, timezone
from typing import Any

import astropy.units as u
import numpy as np  #  # noqa: F401
import sqlalchemy as sa
from astropy.table import QTable
from ctapipe.core import Container

from ...core.exceptions import DBStorageError
from ..adapter.adapter import Adapter
from ..adapter.database_containers.container_map import ContainerMap
from ..adapter.database_containers.table_version_manager import TableVersionManager
from ..connections import CalibPipeDatabase
from ..interfaces import sql_metadata


class TableHandler:
    """
    Handles tables in CalibPipe DataBase.

    The first method returns a valid insertion for a DB, made by the table instance
    and the values to be inserted. The second method just insert values in a DB,
    provided the DB connection, the table and the values.

    """

    @staticmethod
    def get_database_table_insertion(
        container: Container,
        version: str | None = None,
    ) -> tuple[sa.Table, dict[str, Any]]:
        """Return a valid insertion for a DB made by the table instance, and the values to insert."""
        table, kwargs = Adapter.to_postgres(container, version=version)
        if table is None:
            raise TypeError(f"Table cannot be created for {type(container)}.")
        return table, kwargs

    @staticmethod
    def insert_row_in_database(
        table: sa.Table,
        kwargs: dict[str, Any],
        connection: CalibPipeDatabase,
    ) -> None:
        """Insert values in a DB table as a row."""
        connection.execute(sa.insert(table).values(**kwargs))

    @staticmethod
    def read_table_from_database(
        container: Container,
        connection: CalibPipeDatabase,
        condition: str | None = None,
    ) -> QTable:
        """
        Read a table from the DB and return it as a QTable object.

        An optional argument `condition` shall have the following form:
        `c.<column_name> <operator> <value>`
        or a combination of thereof using `&` and `|` operators.
        In case of compound condition, every singleton must be contained in parentheses.
        """
        table = ContainerMap.map_to_db_container(container).get_table()
        if condition:
            query = table.select().where(
                eval(condition.replace("c.", "table.c."))  # pylint: disable=eval-used
            )
        else:
            query = table.select()
        rows = connection.execute(query).fetchall()
        if not rows:
            return QTable(
                names=table.columns.keys(),
                units=[
                    1 * u.Unit(c.comment) if c.comment else None for c in table.columns
                ],
            )
        return QTable(
            rows=rows,
            names=table.columns.keys(),
            units=[1 * u.Unit(c.comment) if c.comment else None for c in table.columns],
        )

    @staticmethod
    def get_compatible_version(
        version_table: sa.Table,
        table_name: str,
        version: str,
        connection: CalibPipeDatabase,
    ) -> str:
        """
        Get a compatible version for a certain table from the version table.

        If no compatible version of the table is available, the new version
        the table will be added to the version table.
        """
        version_major = version.split(".")[0]
        query = sa.select(version_table.c.version).where(
            version_table.c.version.like(f"{version_major}%"),
            version_table.c.name == table_name,
        )
        query_results = connection.execute(query).first()
        if query_results is None:
            vals = {
                "name": table_name,
                "version": version,
                "validity_start": datetime(2023, 1, 1, 0, 0, 1, tzinfo=timezone.utc),
                "validity_end": datetime(2023, 1, 1, 0, 0, 2, tzinfo=timezone.utc),
            }
            TableHandler.insert_row_in_database(
                version_table,
                vals,
                connection=connection,
            )
            return version
        comp_version = query_results[0]
        return comp_version

    @staticmethod
    def update_tables_info(
        table: sa.Table,
        version_table: sa.Table,
        table_name: str,
        comp_version: str,
        table_version: str,
        connection: CalibPipeDatabase,
    ) -> str:
        """
        Update the tables' info.

        Updated min and max timestamps are taken from the data table,
        and a check on version is performed to update the version table.
        Also, the name of the table is updated accordingly if version has changed.
        """
        msg = "DB tables have been updated successfully."
        query = sa.select(
            sa.func.min(table.c.validity_start).label("min_time"),
            sa.func.max(table.c.validity_end).label("max_time"),
        )
        results = connection.execute(query).first()

        if float(table_version.split(".")[1]) > float(comp_version.split(".")[1]):
            TableHandler.update_version_table(
                version_table,
                table_name,
                comp_version,
                table_version,
                results.min_time,
                results.max_time,
                connection,
            )
            TableHandler.update_table_name(table, table_version, connection)
            return (
                msg
                + f" Version has been updated from v{comp_version} to v{table_version}."
            )
        TableHandler.update_version_table(
            version_table,
            table_name,
            comp_version,
            comp_version,
            results.min_time,
            results.max_time,
            connection,
        )
        return msg

    @staticmethod
    def update_version_table(
        version_table: sa.Table,
        table_name: str,
        old_version: str,
        new_version: str,
        min_time: datetime,
        max_time: datetime,
        connection: CalibPipeDatabase,
    ) -> None:
        """Update the version of a table with the new version in the version table of the DB."""
        stmt = (
            sa.update(version_table)
            .where(
                version_table.c.name == table_name,
                version_table.c.version == old_version,
            )
            .values(version=new_version, validity_start=min_time, validity_end=max_time)
        )
        connection.execute(stmt)

    @staticmethod
    def update_table_name(
        table: sa.Table,
        version: str,
        connection: CalibPipeDatabase,
    ) -> None:
        """Update the name of a table with the new version."""
        new_table_name = TableVersionManager.update_version(table.name, version)
        stmt = sa.text(f"ALTER TABLE {table} RENAME TO {new_table_name};")
        connection.execute(stmt)

    @staticmethod
    def prepare_db_tables(containers, db_config):
        """
        Create and upload to the CalibPipe DB empty tables for selected calibration containers.

        Parameters
        ----------
        containers : list[Container]
            list of calibpipe containers or ContainerMeta instances
            that will be created as empty tables in the DB

        config_data : dict
            Calibpipe configuration with database connection configuration
        """
        try:
            with CalibPipeDatabase(**db_config) as connection:
                sql_metadata.reflect(bind=connection.engine, extend_existing=True)

                # Create empty main data tables
                for cp_container in containers:
                    if isinstance(cp_container, Container):
                        db_container = ContainerMap.map_to_db_container(
                            type(cp_container)
                        )
                    else:
                        db_container = ContainerMap.map_to_db_container(cp_container)
                    if not sa.inspect(connection.engine).has_table(
                        db_container.table_name
                    ):
                        db_container.get_table()
                sql_metadata.create_all(bind=connection.engine)
        except sa.exc.DatabaseError:
            raise DBStorageError("Issues with connection to the CalibPipe DB")

    @staticmethod
    def upload_data(
        calibpipe_data_container: Container,
        metadata: list[Container] | None,
        connection: CalibPipeDatabase,
    ) -> None:
        """
        Upload data and optional metadata to the database.

        This method uploads the provided data to the main database table and,
        if provided, associates the metadata with the inserted data row.

        Parameters
        ----------
        calibpipe_data_container : ctapipe.core.Container
            The data container with the data to be uploaded to the main table of the database.

        metadata : list[Container] or None
            Optional list of metadata containers to be uploaded. Should include
            a "ReferenceMetadataContainer" if metadata is provided.

        connection : CalibPipeDatabase
            An active database connection to the CalibPipe database.

        Raises
        ------
        DBStorageError
            If there are issues with the database connection.

        ValueError
            If the main table does not contain a single autoincremented primary key
            or if ReferenceMetadataContainer is missing when metadata is provided.
        """
        data_db_container = ContainerMap.map_to_db_container(
            type(calibpipe_data_container)
        )
        has_autoincrement_pk = any(
            col.autoincrement for col in data_db_container.get_table().c
        )
        is_single_pk = len(data_db_container.get_primary_keys()) == 1

        if not (has_autoincrement_pk and is_single_pk):
            raise ValueError(
                f"Table '{data_db_container.table_name}' "
                "doesn't contain a single autoincremented primary key."
            )

        pk_name = data_db_container.get_primary_keys()[0].name

        try:
            # Insert main data
            table, values = TableHandler.get_database_table_insertion(
                calibpipe_data_container
            )
            TableHandler.insert_row_in_database(table, values, connection)

            # No metadata to upload
            if not metadata:
                return

            # Get the last inserted primary key
            stmt = sa.select(table).order_by(sa.desc(table.c[pk_name])).limit(1)
            last_db_record = connection.execute(stmt).fetchone()
            data_pk_value = last_db_record._asdict()[pk_name]

            # Handle ReferenceMetadataContainer
            reference_meta_container = next(
                (
                    c
                    for c in metadata
                    if c.__class__.__name__ == "ReferenceMetadataContainer"
                ),
                None,
            )
            if reference_meta_container is None:
                raise ValueError("ReferenceMetadataContainer is required in metadata.")

            reference_meta_container.ID_optical_throughput = data_pk_value
            ref_table, ref_values = TableHandler.get_database_table_insertion(
                reference_meta_container
            )
            TableHandler.insert_row_in_database(ref_table, ref_values, connection)

            # Get ReferenceMetadata ID to link to other metadata
            stmt = sa.select(ref_table).order_by(sa.desc(ref_table.c.ID)).limit(1)
            metadata_id = connection.execute(stmt).fetchone().ID

            # Upload other metadata
            for container in metadata:
                if container.__class__.__name__ == "ReferenceMetadataContainer":
                    continue
                container.ID = metadata_id
                meta_table, meta_values = TableHandler.get_database_table_insertion(
                    container
                )
                TableHandler.insert_row_in_database(meta_table, meta_values, connection)

        except sa.exc.DatabaseError:
            raise DBStorageError("Issues with connection to the CalibPipe DB")
