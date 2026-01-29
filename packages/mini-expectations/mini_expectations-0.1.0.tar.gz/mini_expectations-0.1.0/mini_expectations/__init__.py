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

from .core import expect, ExpectationFailed

__all__ = ["expect", "ExpectationFailed"]


