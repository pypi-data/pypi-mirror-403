"""CalibPipeDatabase class."""

from .postgres_utils import (
    get_postgres_uri,
)
from .sql_connection import SQLConnection


class CalibPipeDatabase(SQLConnection):
    """
    CalibPipeDatabase connection. For now `SQLConnection` (`PostgreSQL+psycopg`).

    This class simply creates a valid URI from named parameters to create the
    particular instance of DB used for CalibPipe data and provides no additional
    interface.

    A few built-in queries can be found in the module
    :mod:`queries<calibpipe.database.interfaces.queries>`.

    Attributes
    ----------
    user: str
        Username used to connect to the database.

    database: str
        Name of the database with which the connection must be established.

    password: str
        Password for the given user.

    host: str, default=`localhost`
        Database host.

    port: Optional[int], default=None
        Database port.

    autocommit: bool, default=False
        Tell if the modifications to the DB must be committed automatically when the
        connection closes. Default is `False`, in this case the `commit()` method
        has to be called explicitly.

    """

    def __init__(
        self,
        user: str,
        database: str,
        password: str,
        host: str = "localhost",
        port: int | None = None,
        autocommit: bool = False,
    ) -> None:
        """Initialize the database connection."""
        uri = get_postgres_uri(
            user=user, database=database, passwd=password, host=host, port=port
        )
        super().__init__(
            uri=uri,
            autocommit=autocommit,
        )
