import re

import pandas as pd
import pytest

from mini_expectations import ExpectationFailed, expect


def make_sample_df():
    return pd.DataFrame(
        {
            "id": [1, 2, 3],
            "amount": [10.0, 20.5, 0.1],
            "email": ["a@example.com", "b@example.com", "c@example.com"],
        }
    )


def test_basic_dataframe_expectations_pass():
    df = make_sample_df()

    # Should not raise
    expect(df).to_have_columns(["id", "amount"])
    expect(df).to_have_no_nulls()


def test_column_navigation_and_expectations_pass():
    df = make_sample_df()

    expect(df).column("amount").to_be_positive()
    expect(df).column("email").to_match_regex(r".+@.+")
    expect(df).column("id").to_be_unique()
    expect(df).column("amount").to_be_between(0, 100)
    expect(df).column("email").to_be_in_set(
        ["a@example.com", "b@example.com", "c@example.com"]
    )
    expect(df).column("id").to_have_no_nulls()


def test_row_count_expectation_pass():
    df = make_sample_df()

    expect(df).row_count().to_be_between(1, 10)


def test_missing_column_raises_clear_error():
    df = make_sample_df()

    with pytest.raises(ExpectationFailed) as excinfo:
        expect(df).to_have_columns(["id", "missing"])

    msg = str(excinfo.value)
    assert "missing" in msg
    assert "Available columns" in msg


def test_nulls_raise_clear_error():
    df = make_sample_df()
    df.loc[0, "email"] = None

    with pytest.raises(ExpectationFailed) as excinfo:
        expect(df).to_have_no_nulls()

    msg = str(excinfo.value)
    assert "null values" in msg
    assert "email" in msg


def test_positive_expectation_failure_message():
    df = make_sample_df()
    df.loc[1, "amount"] = -5

    with pytest.raises(ExpectationFailed) as excinfo:
        expect(df).column("amount").to_be_positive()

    msg = str(excinfo.value)
    assert "strictly positive" in msg
    assert "amount" in msg
    assert "failing rows" in msg


def test_regex_expectation_failure_message():
    df = make_sample_df()
    df.loc[1, "email"] = "not-an-email"

    with pytest.raises(ExpectationFailed) as excinfo:
        expect(df).column("email").to_match_regex(r".+@.+")

    msg = str(excinfo.value)
    assert re.search("not-an-email", msg)


def test_row_count_out_of_range_raises():
    df = make_sample_df()

    with pytest.raises(ExpectationFailed) as excinfo:
        expect(df).row_count().to_be_between(10, 20)

    msg = str(excinfo.value)
    assert "row count" in msg


def test_dataframe_unique_column_expectation():
    df = make_sample_df()
    expect(df).to_have_unique_column("id")

    df_dup = make_sample_df()
    df_dup.loc[1, "id"] = 1

    with pytest.raises(ExpectationFailed) as excinfo:
        expect(df_dup).to_have_unique_column("id")

    msg = str(excinfo.value)
    assert "unique" in msg
    assert "duplicated" in msg


def test_column_set_and_range_expectation_failures():
    df = make_sample_df()
    df.loc[0, "amount"] = -1
    df.loc[1, "email"] = "other@example.com"

    with pytest.raises(ExpectationFailed) as excinfo_range:
        expect(df).column("amount").to_be_between(0, 100)

    assert "between 0 and 100" in str(excinfo_range.value)

    with pytest.raises(ExpectationFailed) as excinfo_set:
        expect(df).column("email").to_be_in_set(["a@example.com"])

    assert "to be in" in str(excinfo_set.value)


def test_column_no_nulls_failure():
    df = make_sample_df()
    df.loc[0, "id"] = None

    with pytest.raises(ExpectationFailed) as excinfo:
        expect(df).column("id").to_have_no_nulls()

    msg = str(excinfo.value)
    assert "no null values" in msg


