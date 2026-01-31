"""
Type definitions for SQLAlchemy.

These type definitions allow us to define database fields and
containers being almost completely decoupled from SQLAlchemy
(without direct coupling).

In particular, SQLColumnInfo and SQLTableInfo use these generic
types and not the sqlalchemy types directly.

The NDArray type is defined explicitly to implemented the
serialization/deserialization np.ndarray <-> bytes and the
(optional) zlib compression/decompression on the byte data.

"""

import pickle
import zlib

import numpy as np
import sqlalchemy as sa
import sqlalchemy.sql.sqltypes
from sqlalchemy.dialects.postgresql import ARRAY, DOUBLE_PRECISION

ColumnType = sqlalchemy.sql.sqltypes.TypeEngine

Boolean: ColumnType = sa.Boolean

SmallInteger: ColumnType = sa.SmallInteger
Integer: ColumnType = sa.Integer
BigInteger: ColumnType = sa.BigInteger
Float: ColumnType = sa.Float
Double: ColumnType = DOUBLE_PRECISION
Numeric: ColumnType = sa.Numeric
Binary: ColumnType = sa.types.LargeBinary
String: ColumnType = sa.String

ArrayF1D: ColumnType = ARRAY(Float, dimensions=1)
ArrayF2D: ColumnType = ARRAY(Float, dimensions=2)
ArrayF3D: ColumnType = ARRAY(Float, dimensions=3)

Date: ColumnType = sa.Date
Time: ColumnType = sa.Time
DateTime: ColumnType = sa.DateTime


class NDArray(sa.types.TypeDecorator):  # pylint: disable=too-many-ancestors
    """
    Type for numpy.ndarray binding, include data compression.

    The array is stored as a compressed byte string in the database.
    The class implements the binding between the `np.ndarray` in the
    program memory and the byte string stored in the DB.

    Compression can be removed or modified, but the two process methods
    should be the opposite of each other for the binding to work.
    Ignoring the dialect parameter that is anyway not used, this means
    that the following assertion should always pass::

        db_arr: NDArray
        arr: np.ndarray
        arr_bytes: bytes = db_arr.process_bind_param(arr)
        recov_arr: np.ndarray = db_arr.process_result_value(arr_bytes)
        assert(arr == recov_arr)

    """

    impl = sa.types.LargeBinary  # Byte storage in the DB
    cache_ok: bool = True  # Results of process methods can be cached

    def process_bind_param(self, value: np.ndarray, dialect) -> bytes:
        """
        Serialize a np.ndarray into a byte object to store in the DB.

        The array is first serialized into bytes and compressed using
        the default zlib compression algorithm.
        """
        return zlib.compress(pickle.dumps(value))

    def process_result_value(self, value: bytes, dialect) -> np.ndarray:
        """
        Deserialize a np.ndarray from bytes read in the DB.

        The bytes are first decompressed and the array is loaded from
        the decompressed byte string.
        """
        return pickle.loads(zlib.decompress(value))

    def process_literal_param(self, value: np.ndarray, dialect) -> str:
        """Representation of the NDArray object."""
        return f"NDArray(shape={value.shape}, dtype={value.dtype})"

    @property
    def python_type(self) -> type:
        """Return the python type of the underlying object represented by the byte string."""
        return np.ndarray
