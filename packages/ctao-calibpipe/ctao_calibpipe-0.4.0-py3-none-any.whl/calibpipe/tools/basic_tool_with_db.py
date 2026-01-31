# CTA-related imports  # noqa: D100
from ctapipe.core import Tool
from ctapipe.core.traits import Bool, Dict, Integer, Unicode


class BasicToolWithDB(Tool):
    """Basic tool with database connection."""

    name = Unicode("BasicToolWithDB")
    description = "Basic tool with database connection."

    database_configuration = Dict(
        per_key_traits={
            "user": Unicode(),
            "password": Unicode(),
            "database": Unicode(),
            "host": Unicode(),
            "port": Integer(allow_none=True),
            "autocommit": Bool(),
        },
        default_value={
            "user": "TEST_CALIBPIPE_DB_USER",
            "password": "DUMMY_PSWRD",
            "database": "TEST_CALIBPIPE_DB",
            "host": "localhost",
            "port": 5432,
            "autocommit": True,
        },
        help="Database configuration",
    ).tag(config=True)

    def setup(self):
        """Set up the database connection."""
        if (
            "database_configuration" in self.config
            and "database_configuration" not in self.config[self.name]
        ):
            self.database_configuration = self.config["database_configuration"]
