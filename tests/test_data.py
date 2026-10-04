import pandas as pd
import pytest

KEYS = ["season", "round", "session", "part", "driver"]


@pytest.fixture(scope="module")
def df():
    return pd.read_parquet("data/clean/qualifying.parquet")


def test_all_seasons_present(df):
    assert sorted(df["season"].unique()) == list(range(2018, 2027))


def test_rows_per_season_reasonable(df):
    rows = df.groupby("season").size()
    assert rows.between(600, 1500).all(), rows.to_dict()


def test_rows_per_part_reasonable(df):
    rows = df.groupby(KEYS[:-1]).size()
    assert rows.between(5, 22).all(), rows[~rows.between(5, 22)].to_dict()


def test_no_missing_values(df):
    assert df.notna().all().all(), df.isna().sum().to_dict()


def test_lap_times_plausible(df):
    assert df["lap_time"].between(50, 140).all()


def test_one_row_per_driver_per_part(df):
    assert not df.duplicated(KEYS).any()
