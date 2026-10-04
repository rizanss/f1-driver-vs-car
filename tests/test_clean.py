import numpy as np
import pandas as pd

from src.clean import clean, no_time, outlier_lap, slow_lap, took_part, unify_teams, wet_part


def make_raw(rows):
    cols = ["round", "part", "driver", "lap_time", "n_laps", "wet_tyres"]
    df = pd.DataFrame(rows, columns=cols)
    return df.assign(season=2023, session="Q", event="Test GP", team="T", rainfall=False)


def test_took_part_keeps_q1_and_drivers_who_ran():
    df = make_raw([
        (1, "Q1", "AAA", np.nan, 0, False),
        (1, "Q2", "AAA", np.nan, 0, False),
        (1, "Q2", "BBB", np.nan, 3, False),
        (1, "Q3", "CCC", 90.0, 0, False),
    ])
    assert took_part(df).tolist() == [True, False, True, True]


def test_unify_teams_merges_force_india_2018_only():
    df = pd.DataFrame({
        "season": [2018, 2018, 2019],
        "team": ["Force India", "Racing Point", "Racing Point"],
    })
    assert unify_teams(df)["team"].tolist() == ["Force India", "Force India", "Racing Point"]


def test_wet_part_flags_whole_part():
    df = make_raw([
        (1, "Q1", "AAA", 90.0, 3, True),
        (1, "Q1", "BBB", 91.0, 3, False),
        (1, "Q2", "BBB", 90.5, 3, False),
        (2, "Q1", "BBB", 80.0, 3, False),
    ])
    assert wet_part(df).tolist() == [True, True, False, False]


def test_no_time():
    df = make_raw([(1, "Q1", "AAA", np.nan, 2, False), (1, "Q1", "BBB", 90.0, 2, False)])
    assert no_time(df).tolist() == [True, False]


def test_outlier_lap_uses_fastest_in_part():
    df = make_raw([
        (1, "Q1", "AAA", 100.0, 3, False),
        (1, "Q1", "SLO", 106.9, 3, False),
        (1, "Q1", "BAD", 107.5, 3, False),
        (1, "Q2", "BAD", 104.0, 3, False),
    ])
    assert outlier_lap(df).tolist() == [False, False, True, False]


def test_slow_lap_compares_against_drivers_own_best():
    df = make_raw([
        (1, "Q1", "AAA", 92.0, 3, False),
        (1, "Q2", "AAA", 90.0, 3, False),
        (1, "Q3", "AAA", 91.8, 3, False),
        (1, "Q1", "SLO", 95.0, 3, False),
        (2, "Q1", "AAA", 99.0, 3, False),
    ])
    assert slow_lap(df).tolist() == [True, False, False, False, False]


def test_clean_logs_first_matching_reason_and_skips_non_participants():
    raw = make_raw([
        (1, "Q1", "AAA", 90.0, 3, False),
        (1, "Q1", "BBB", np.nan, 2, False),
        (1, "Q2", "AAA", 93.0, 3, False),
        (1, "Q2", "BBB", np.nan, 0, False),
        (2, "Q1", "AAA", 100.0, 3, True),
        (2, "Q1", "BBB", np.nan, 1, False),
    ])
    df, dropped = clean(raw)
    assert df[["round", "part", "driver"]].values.tolist() == [[1, "Q1", "AAA"]]
    assert df["lap_time"].notna().all()
    assert dropped[["round", "driver", "reason"]].values.tolist() == [
        [2, "AAA", "wet"], [2, "BBB", "wet"], [1, "BBB", "no_time"], [1, "AAA", "slow_lap"],
    ]
