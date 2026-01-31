"""Interface to connect to the calibration DB stored in a SQL DB."""

import sqlalchemy as sa
from sqlalchemy.engine import Engine, Result
from sqlalchemy.orm import Session


class SQLConnection:
    """
    Interface to communicate with a SQL database.

    Once an uri (`str`) has been generated, the connection can be
    open in a context to ensure proper closing (and commit if
    required)::

        uri: str = get_postgres_uri(user='api-owner', database='calibration')
        with SQLConnection(uri=uri, autocommit=True) as connection:
            # e.g.
            # connection.execute(...)

    Attributes
    ----------
    autocommit: bool
        Tell if the database changes must be committed automatically
        when closing the connection (can be done manually by calling
        the :meth:`commit` method).

    uri: str
        Uri used to connect to the database. This attribute is not
        used anymore once the connection is open.

    engine: sqlalchemy.engine.Engine
        Engine used for the database connection. It can be of several
        kinds, the default one is `postgres + psycopg`. The engine
        is automatically connected at the initialization step.

    session: sqlalchemy.orm.Session
        Session (use the :attr:`engine`) used to execute
        queries to the database.
    """

    def __init__(self, uri: str, autocommit: bool = False) -> None:
        """
        Initialize the session and engine, connect to the database.

        Parameters
        ----------
        uri: str
            uri to connect to the database. See the
            :func:`calibpipe.database.connections.get_postgres_uri`
            to generate the uri connecting to a Postgres database.

        autocommit: bool, optional (default=False)
            Determines if the connection commits changes when the
            :meth:`__exit__`
            method is called. If set to `False` (default), changes will not be
            committed and it is necessary to call :meth:`commit` after
            modifications have been done.
        """
        self.autocommit = autocommit
        self.uri: str = uri
        self.engine: Engine = sa.create_engine(self.uri, echo=True, future=True)
        self.engine.connect()
        self.session: Session = Session(self.engine)

    def __enter__(self) -> "SQLConnection":
        """Enter a new context."""
        return self

    def __exit__(self, *args) -> None:
        """
        Exit the context and close the connection.

        This method simply call `close()`.
        """
        self.close()

    def close(self) -> None:
        """
        Close the session.

        If the autocommit attribute is True, changes are committed before
        closing the connection.
        """
        if self.session:
            if self.autocommit:
                self.commit()
            self.session.close()

    def commit(self) -> None:
        """Commit changes to the database."""
        self.session.commit()

    def execute(self, *args) -> Result:
        """
        Execute a query in the SQL session.

        This methods forwards the arguments to the
        :meth:`sqlalchemy.orm.Session.execute` method of
        :attr:`session`.
        Refer to the documentation of `sqlalchemy` to use queries.
        """
        return self.session.execute(*args)
