import pandas as pd
import pytest

from src import evaluate
from src.evaluate import decompose, drop_events, predict, top5_overlap


def test_drop_events_removes_whole_weekends_only():
    df = pd.DataFrame({"season": [2023, 2023, 2023, 2024], "round": [1, 1, 2, 1], "driver": ["A", "B", "A", "A"]})
    held_out = pd.DataFrame({"season": [2023], "round": [1]})
    assert drop_events(df, held_out)[["season", "round"]].values.tolist() == [[2023, 2], [2024, 1]]


def test_predict_is_the_full_effect_difference_in_the_same_season():
    effects = pd.Series([-0.3, 0.2, 0.1], index=pd.MultiIndex.from_tuples([("AAA", 2025), ("BBB", 2025), ("BBB", 2026)]))
    gaps = pd.DataFrame({"driver": ["AAA", "BBB"], "teammate": ["BBB", "AAA"], "season": [2025, 2025]}, index=[7, 9])
    prediction = predict(effects, gaps)
    assert prediction.index.tolist() == [7, 9]
    assert prediction.tolist() == pytest.approx([-0.5, 0.5])


def test_top5_overlap_counts_shared_drivers_per_season():
    ref = pd.DataFrame({"driver": list("ABCDEF"), "season": 2023, "rating": [6, 5, 4, 3, 2, 1]})
    var = ref.assign(rating=[6, 5, 4, 3, 1, 2])
    assert top5_overlap(ref, var).to_dict() == {2023: 4}


def make_reference():
    return {
        "drivers": [
            {"driver": "ALO", "season": 2022, "teams": ["Alpine"], "rating": 0.20},
            {"driver": "ALO", "season": 2023, "teams": ["Aston Martin"], "rating": 0.25},
        ],
        "cars": [
            {"team": "Alpine", "season": 2022, "rating": 0.1},
            {"team": "Aston Martin", "season": 2023, "rating": 0.6},
        ],
    }


def test_decompose_splits_a_team_switch_into_driver_and_car_change():
    case = decompose(make_reference(), "ALO", 2022, 2023)
    assert case["teams"] == ["Alpine", "Aston Martin"]
    assert case["driver_change"] == pytest.approx(0.05)
    assert case["car_change"] == pytest.approx(0.5)


def test_sanity_passes_only_when_dominant_part_matches(monkeypatch):
    monkeypatch.setattr(evaluate, "SWITCHES", [("ALO", 2022, 2023, "car")])
    assert evaluate.sanity(make_reference())["passed"]
    monkeypatch.setattr(evaluate, "SWITCHES", [("ALO", 2022, 2023, "driver")])
    assert not evaluate.sanity(make_reference())["passed"]
