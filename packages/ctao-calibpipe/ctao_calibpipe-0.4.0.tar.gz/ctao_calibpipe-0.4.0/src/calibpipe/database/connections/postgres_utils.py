"""Adapter for psycopg types and database uri."""

from typing import Any

import numpy as np
from psycopg import adapters
from psycopg.adapt import Buffer, Dumper
from psycopg.errors import DataError
from psycopg.postgres import types as _types
from psycopg.types.bool import BoolDumper
from psycopg.types.numeric import Float4Dumper, FloatDumper


def get_postgres_uri(
    user: str,
    database: str,
    passwd: str,
    host: str = "postgres",
    port: str | None = None,
) -> str:
    """Generate a valid uri to connect to the postgres+psycopg database."""
    port_str = f":{port}" if port else ""
    return f"postgresql+psycopg://{user}:{passwd}@{host}{port_str}/{database}"


# np.int dumpers
class _NPIntDumper(Dumper):
    def dump(self, obj: Any) -> Buffer:
        t = type(obj)
        allowed_types = [
            np.int8,
            np.int16,
            np.int32,
            np.int64,
            np.longlong,
            np.uint8,
            np.uint16,
            np.uint32,
            np.uint64,
            np.ulonglong,
        ]
        if t not in allowed_types:
            raise DataError(f"Numpy integer expected, got {type(obj).__name__!r}")
        return str(obj).encode()


class NPInt16Dumper(_NPIntDumper):
    """Numpy int16 dumper."""

    oid = _types["int2"].oid


class NPInt32Dumper(_NPIntDumper):
    """Numpy int32 dumper."""

    oid = _types["int4"].oid


class NPInt64Dumper(_NPIntDumper):
    """Numpy int64 dumper."""

    oid = _types["int8"].oid


class NPNumericDumper(_NPIntDumper):
    """Numpy numeric dumper."""

    oid = _types["numeric"].oid


def adapt_psycopg() -> None:
    # pylint: disable=line-too-long
    """
    Adapt numpy numerical types for psycopg3.

    .. note::
        Required for psycopg3 < 3.2. Until the pyscopg-3.2.0 is released, we borrow their code.
        See `this PR <https://github.com/psycopg/psycopg/pull/332/files#diff-6d04f11a711cbef8ea32bd1479af4a79b402e213559d8b66359a6b871c5bdd28>`_ for details
    """
    # pylint: enable=line-too-long
    adapters.register_dumper("numpy.int8", NPInt16Dumper)
    adapters.register_dumper("numpy.int16", NPInt16Dumper)
    adapters.register_dumper("numpy.int32", NPInt32Dumper)
    adapters.register_dumper("numpy.int64", NPInt64Dumper)
    adapters.register_dumper("numpy.longlong", NPInt64Dumper)
    adapters.register_dumper("numpy.bool_", BoolDumper)
    adapters.register_dumper("numpy.uint8", NPInt16Dumper)
    adapters.register_dumper("numpy.uint16", NPInt32Dumper)
    adapters.register_dumper("numpy.uint32", NPInt64Dumper)
    adapters.register_dumper("numpy.uint64", NPNumericDumper)
    adapters.register_dumper("numpy.ulonglong", NPNumericDumper)
    adapters.register_dumper("numpy.float16", Float4Dumper)
    adapters.register_dumper("numpy.float32", Float4Dumper)
    adapters.register_dumper("numpy.float64", FloatDumper)


adapt_psycopg()
