import numpy as np
import pandas as pd
import pytest

from src.baseline import fit, predict, split_events, split_future, teammate_gaps


def make_clean(rows):
    df = pd.DataFrame(rows, columns=["season", "round", "part", "team", "driver", "lap_time"])
    return df.assign(session="Q")


def test_teammate_gaps_pairs_drivers_and_skips_solo_rows():
    df = make_clean([
        (2023, 1, "Q1", "A", "AAA", 90.0),
        (2023, 1, "Q1", "A", "BBB", 90.9),
        (2023, 1, "Q2", "A", "AAA", 89.0),
        (2023, 1, "Q1", "B", "CCC", 91.0),
    ])
    gaps = teammate_gaps(df).set_index("driver")
    assert sorted(gaps.index) == ["AAA", "BBB"]
    assert gaps.loc["AAA", "teammate"] == "BBB"
    assert gaps.loc["AAA", "gap"] == pytest.approx(100 * np.log(90.0 / 90.9))
    assert gaps.loc["BBB", "gap"] == pytest.approx(-gaps.loc["AAA", "gap"])


def test_fit_averages_gap_per_driver_season():
    gaps = pd.DataFrame({
        "driver": ["AAA", "AAA", "AAA"],
        "season": [2023, 2023, 2024],
        "gap": [-0.2, -0.4, 0.1],
    })
    assert fit(gaps)["rating"].tolist() == pytest.approx([-0.3, 0.1])


def test_predict_uses_latest_season_and_zero_for_unknown():
    ratings = pd.DataFrame({
        "driver": ["AAA", "AAA", "BBB"],
        "season": [2023, 2024, 2023],
        "rating": [-0.4, -0.2, 0.2],
    })
    test = pd.DataFrame({
        "driver": ["AAA", "AAA", "NEW"],
        "teammate": ["BBB", "BBB", "AAA"],
        "season": [2024, 2026, 2026],
    })
    assert predict(ratings, test).tolist() == pytest.approx([-0.2, -0.2, 0.1])


def test_split_events_keeps_whole_events_and_covers_every_season():
    gaps = pd.DataFrame([(s, r, p) for s in (2023, 2024) for r in range(1, 11) for p in ("Q1", "Q2")],
                        columns=["season", "round", "part"])
    train, test = split_events(gaps)
    train_events = set(map(tuple, train[["season", "round"]].values))
    test_events = set(map(tuple, test[["season", "round"]].values))
    assert not train_events & test_events
    assert len(test_events) == 4
    assert set(test["season"]) == {2023, 2024}


def test_split_future_holds_out_2026():
    gaps = pd.DataFrame({"season": [2024, 2025, 2026]})
    train, test = split_future(gaps)
    assert train["season"].tolist() == [2024, 2025]
    assert test["season"].tolist() == [2026]
