"""
Core implementation for mini_expectations.

Design:
- Single entry point: expect(df) -> DataFrameExpectations
- DataFrame-level and Column-level expectation classes
- Shared ExpectationFailed exception
- Simple, chainable, pandas-only API
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

import pandas as pd


class ExpectationFailed(AssertionError):
    """
    Raised when an expectation about a DataFrame or Series is not met.

    This fails fast and includes a human-readable message describing
    what was expected and what was actually observed.
    """


@dataclass
class DataFrameExpectations:
    """Expectations that operate on a whole pandas DataFrame."""

    df: pd.DataFrame

    # ---- navigation ----
    def column(self, name: str) -> "ColumnExpectations":
        if name not in self.df.columns:
            raise ExpectationFailed(
                f"Expected DataFrame to have column '{name}', "
                f"but available columns are: {list(self.df.columns)}"
            )
        return ColumnExpectations(self.df[name], column_name=name)

    def row_count(self) -> "RowCountExpectation":
        return RowCountExpectation(len(self.df))

    # ---- dataframe-level expectations ----
    def to_have_columns(self, columns: Iterable[str]) -> "DataFrameExpectations":
        missing = [c for c in columns if c not in self.df.columns]
        if missing:
            raise ExpectationFailed(
                f"Expected DataFrame to have columns {list(columns)}, "
                f"but the following are missing: {missing}. "
                f"Available columns: {list(self.df.columns)}"
            )
        return self

    def to_have_no_nulls(
        self, subset: Optional[Iterable[str]] = None
    ) -> "DataFrameExpectations":
        """
        Expect that there are no null values in the DataFrame (or subset of columns).
        """
        df = self.df
        if subset is not None:
            missing_subset = [c for c in subset if c not in df.columns]
            if missing_subset:
                raise ExpectationFailed(
                    f"Subset columns {missing_subset} not found in DataFrame. "
                    f"Available columns: {list(df.columns)}"
                )
            df = df[list(subset)]

        null_mask = df.isnull()
        if null_mask.values.any():
            # Build a compact description of where nulls are
            cols_with_nulls = [
                col for col in df.columns if null_mask[col].any()  # type: ignore[index]
            ]
            counts = {col: int(null_mask[col].sum()) for col in cols_with_nulls}  # type: ignore[index]
            raise ExpectationFailed(
                "Expected DataFrame to have no null values"
                + (f" in columns {list(subset)}" if subset is not None else "")
                + f", but found nulls in columns {cols_with_nulls} "
                f"with counts {counts}."
            )

        return self

    def to_have_unique_column(self, column: str) -> "DataFrameExpectations":
        """
        Expect that a specific column exists and is unique (no duplicates, no nulls).
        """
        if column not in self.df.columns:
            raise ExpectationFailed(
                f"Expected DataFrame to have column '{column}' for uniqueness check, "
                f"but available columns are: {list(self.df.columns)}"
            )

        s = self.df[column]
        if s.isnull().any():
            raise ExpectationFailed(
                f"Expected column '{column}' to be unique with no nulls, "
                f"but found {int(s.isnull().sum())} null values."
            )

        duplicated_mask = s.duplicated(keep=False)
        if duplicated_mask.any():
            duplicated_values = s[duplicated_mask].drop_duplicates().tolist()
            count_duplicates = int(duplicated_mask.sum())
            raise ExpectationFailed(
                f"Expected column '{column}' to contain only unique values, "
                f"but found {count_duplicates} duplicated rows. "
                f"Example duplicated values: {duplicated_values[:5]}."
            )

        return self


@dataclass
class ColumnExpectations:
    """Expectations that operate on a single pandas Series (column)."""

    series: pd.Series
    column_name: str

    def to_be_positive(self, strictly: bool = True) -> "ColumnExpectations":
        """
        Expect that all values in the column are positive.

        By default this is strictly positive (> 0). If strictly=False, zero
        values are allowed (>= 0).
        """
        s = self.series
        if not pd.api.types.is_numeric_dtype(s):
            raise ExpectationFailed(
                f"Expected column '{self.column_name}' to be numeric for positivity check, "
                f"but got dtype {s.dtype}."
            )

        if strictly:
            failing_mask = ~(s > 0)
            description = "strictly positive (> 0)"
        else:
            failing_mask = ~(s >= 0)
            description = "non-negative (>= 0)"

        if failing_mask.any():
            failing_indices = list(s.index[failing_mask])
            sample_values = s[failing_mask].head(5).tolist()
            raise ExpectationFailed(
                f"Expected all values in column '{self.column_name}' to be {description}, "
                f"but found {failing_mask.sum()} failing rows. "
                f"Example indices: {failing_indices[:5]}, values: {sample_values}."
            )

        return self

    def to_match_regex(self, pattern: str) -> "ColumnExpectations":
        """
        Expect that all non-null string values in the column match a regex pattern.
        """
        s = self.series
        # Convert to string but keep nulls as-is
        non_null = s.dropna()
        as_str = non_null.astype(str)
        matches = as_str.str.match(pattern)

        if not matches.all():
            failing = as_str[~matches]
            failing_indices = list(failing.index)
            sample_values = failing.head(5).tolist()
            raise ExpectationFailed(
                f"Expected all non-null values in column '{self.column_name}' "
                f"to match regex pattern {pattern!r}, but found "
                f"{len(failing)} non-matching rows. "
                f"Example indices: {failing_indices[:5]}, values: {sample_values}."
            )

        return self

    def to_be_unique(self) -> "ColumnExpectations":
        """
        Expect that all non-null values in the column are unique.
        """
        s = self.series
        non_null = s.dropna()
        duplicated_mask = non_null.duplicated(keep=False)

        if duplicated_mask.any():
            duplicated = non_null[duplicated_mask]
            duplicated_values = duplicated.drop_duplicates().tolist()
            raise ExpectationFailed(
                f"Expected column '{self.column_name}' to have unique values "
                f"(ignoring nulls), but found {int(duplicated_mask.sum())} "
                f"duplicated rows. Example duplicated values: {duplicated_values[:5]}."
            )

        return self

    def to_be_between(
        self, min_value, max_value, inclusive: bool = True
    ) -> "ColumnExpectations":
        """
        Expect that all non-null numeric values are between min_value and max_value.
        """
        s = self.series
        if not pd.api.types.is_numeric_dtype(s):
            raise ExpectationFailed(
                f"Expected column '{self.column_name}' to be numeric for range check, "
                f"but got dtype {s.dtype}."
            )

        non_null = s.dropna()
        if inclusive:
            failing_mask = ~((non_null >= min_value) & (non_null <= max_value))
            description = f"between {min_value} and {max_value} inclusive"
        else:
            failing_mask = ~((non_null > min_value) & (non_null < max_value))
            description = f"between {min_value} and {max_value} exclusive"

        if failing_mask.any():
            failing_indices = list(non_null.index[failing_mask])
            sample_values = non_null[failing_mask].head(5).tolist()
            raise ExpectationFailed(
                f"Expected all non-null values in column '{self.column_name}' to be "
                f"{description}, but found {failing_mask.sum()} failing rows. "
                f"Example indices: {failing_indices[:5]}, values: {sample_values}."
            )

        return self

    def to_be_in_set(self, allowed_values) -> "ColumnExpectations":
        """
        Expect that all non-null values are drawn from a given set of allowed values.
        """
        s = self.series
        non_null = s.dropna()
        allowed = set(allowed_values)

        failing_mask = ~non_null.isin(allowed)
        if failing_mask.any():
            failing_values = non_null[failing_mask].drop_duplicates().tolist()
            raise ExpectationFailed(
                f"Expected all non-null values in column '{self.column_name}' to be in "
                f"{sorted(allowed)}, but found {failing_mask.sum()} values outside "
                f"this set. Example offending values: {failing_values[:5]}."
            )

        return self

    def to_have_no_nulls(self) -> "ColumnExpectations":
        """
        Expect that the column contains no null values.
        """
        s = self.series
        null_mask = s.isnull()
        if null_mask.any():
            count_nulls = int(null_mask.sum())
            failing_indices = list(s.index[null_mask])[:5]
            raise ExpectationFailed(
                f"Expected column '{self.column_name}' to contain no null values, "
                f"but found {count_nulls} nulls. Example indices: {failing_indices}."
            )

        return self


@dataclass
class RowCountExpectation:
    """Simple wrapper around row count to allow chaining row_count().to_be_between()."""

    count: int

    def to_be_between(self, min_value: int, max_value: int) -> "RowCountExpectation":
        if min_value > max_value:
            raise ValueError(
                f"min_value ({min_value}) cannot be greater than max_value ({max_value})."
            )

        if not (min_value <= self.count <= max_value):
            raise ExpectationFailed(
                f"Expected row count to be between {min_value} and {max_value} "
                f"(inclusive), but got {self.count}."
            )

        return self


def expect(df: pd.DataFrame) -> DataFrameExpectations:
    """
    Entry point for mini_expectations.

    Parameters
    ----------
    df : pandas.DataFrame
        The DataFrame under test.

    Returns
    -------
    DataFrameExpectations
        An object exposing DataFrame-level and navigational expectations.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            f"mini_expectations.expect() expects a pandas DataFrame, "
            f"but got object of type {type(df).__name__}."
        )
    return DataFrameExpectations(df=df)


