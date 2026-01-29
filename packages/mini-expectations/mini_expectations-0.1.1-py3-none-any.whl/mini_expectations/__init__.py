"""
mini_expectations
------------------

A tiny, code-first data quality expectations library for pandas DataFrames.

Usage
-----
from mini_expectations import expect

expect(df).to_have_columns(["id", "amount"])
expect(df).to_have_no_nulls()

expect(df).column("amount").to_be_positive()
expect(df).column("email").to_match_regex(r".+@.+")

expect(df).row_count().to_be_between(1, 1_000_000)
"""

from pandas import DataFrame

from .core import (
    ColumnExpectations,
    DataFrameExpectations,
    ExpectationFailed,
    RowCountExpectation,
    expect as _expect,
)


def expect(df: DataFrame) -> DataFrameExpectations:
    """
    Typed public entry point for mini_expectations.

    This function simply forwards to the internal implementation in ``core.expect``,
    but provides an explicit return type so editors like VS Code / Pylance can
    offer full autocomplete on:

    - expect(df).<TAB>
    - expect(df).column("col").<TAB>
    """

    return _expect(df)


__all__ = [
    "expect",
    "ExpectationFailed",
    "DataFrameExpectations",
    "ColumnExpectations",
    "RowCountExpectation",
]


