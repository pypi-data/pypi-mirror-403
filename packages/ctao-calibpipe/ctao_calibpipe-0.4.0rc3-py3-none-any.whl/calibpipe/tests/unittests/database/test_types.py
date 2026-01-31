"""Test sqlalchemy types."""

from calibpipe.database.interfaces.types import (
    BigInteger,
    Boolean,
    ColumnType,
    Date,
    DateTime,
    Double,
    Float,
    Integer,
    NDArray,
    Numeric,
    SmallInteger,
    String,
    Time,
)
from sqlalchemy.sql.type_api import TypeEngine


def test_types():
    """Test that types are instance of TypeEngine."""
    for type_ in [
        Boolean,
        SmallInteger,
        Integer,
        BigInteger,
        Float,
        Double,
        Numeric,
        String,
        Date,
        DateTime,
        Time,
        ColumnType,
        NDArray,
    ]:
        assert issubclass(type_, TypeEngine)
