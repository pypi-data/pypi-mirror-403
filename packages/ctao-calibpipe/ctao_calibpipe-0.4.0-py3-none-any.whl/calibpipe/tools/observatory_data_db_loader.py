import sqlalchemy as sa  # noqa: D100

# CTA-related imports
from ctapipe.core.traits import List, Unicode
from traitlets.config import Config

# Internal imports
from calibpipe.database.connections import CalibPipeDatabase
from calibpipe.database.interfaces import TableHandler
from calibpipe.utils.observatory import Observatory

from .basic_tool_with_db import BasicToolWithDB


class UploadObservatoryData(BasicToolWithDB):
    """Upload observatory data to the calibpipe database."""

    name = Unicode("Upload observatory data")
    description = "Upload observatory data to the calibpipe database."

    observatories = List(help="List of observatories configurations", minlen=1).tag(
        config=True
    )

    classes = [
        Observatory,
    ]

    def setup(self):
        """Create Observatory objects from the configuration and register database configuration."""
        super().setup()
        self._observatories = [
            Observatory(config=Config(key))
            for key in self.config["UploadObservatoryData"]["observatories"]
        ]

    def start(self):
        """Create the database tables and insert the data."""
        containers = [
            container
            for observatory in self._observatories
            for container in observatory.containers
        ]
        # Check if the tables exist, if not create them
        with CalibPipeDatabase(
            **self.database_configuration,
        ) as connection:
            for container in containers:
                table, insertion = TableHandler.get_database_table_insertion(
                    container,
                )
                if not sa.inspect(connection.engine).has_table(table.name):
                    table.create(bind=connection.engine)
        # Insert the data
        with CalibPipeDatabase(
            **self.database_configuration,
        ) as connection:
            for container in containers:
                table, insertion = TableHandler.get_database_table_insertion(
                    container,
                )
                TableHandler.insert_row_in_database(table, insertion, connection)

    def finish(self):
        """No finishing actions needed."""


def main():
    """Run the app."""
    tool = UploadObservatoryData()
    tool.run()
