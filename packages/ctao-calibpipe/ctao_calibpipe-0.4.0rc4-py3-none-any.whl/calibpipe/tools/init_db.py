# CTA-related imports  # noqa: D100
from ctapipe.core.traits import Unicode

from ..database.adapter.database_containers import ContainerMap
from ..database.interfaces import TableHandler

# Internal imports
from .basic_tool_with_db import BasicToolWithDB


class CalibPipeDatabaseInitialization(BasicToolWithDB):
    """Tool to create empty data and metadata tables in the CalibPipe DB."""

    name = Unicode("CalibPipeDatabaseInitialization")
    description = "Populate an empty databased with empty tables."

    def setup(self):
        """Parse configuration, setup the database connection and fetch CalibPipe containers."""
        super().setup()
        self.containers = ContainerMap.get_cp_containers()

    def start(self):
        """Create tables in the database."""
        TableHandler.prepare_db_tables(self.containers, self.database_configuration)

    def finish(self):
        """Log created tables."""
        self.log.info(
            "Data tables for %s was created and uploaded to CalibPipe DB",
            [_.__name__ for _ in self.containers],
        )


def main():
    """Run the app."""
    tool = CalibPipeDatabaseInitialization()
    tool.run()
