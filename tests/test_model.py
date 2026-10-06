import json
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from src.model import build_model, center_matrix, encode, ratings, seasons_since, second_season, walk_matrix, zero_sum_basis


def make_drivers():
    return pd.DataFrame({"driver": ["ALO", "ALO", "ALO", "VER"], "season": [2018, 2021, 2022, 2021]})


def test_encode_returns_sorted_table_and_matching_codes():
    df = pd.DataFrame({"team": ["B", "A", "B"], "season": [2023, 2023, 2022]})
    table, codes = encode(df, ["team", "season"])
    assert table.values.tolist() == [["A", 2023], ["B", 2022], ["B", 2023]]
    assert codes.tolist() == [2, 0, 1]


def test_center_matrix_zeroes_the_mean_within_each_group():
    groups = np.array([2023, 2023, 2023, 2024, 2024])
    centered = center_matrix(groups) @ np.array([1.0, 2.0, 6.0, -1.0, 5.0])
    assert centered[:3].sum() == pytest.approx(0)
    assert centered[3:].sum() == pytest.approx(0)
    assert centered.tolist() == pytest.approx([-2.0, -1.0, 3.0, -3.0, 3.0])


def test_zero_sum_basis_is_orthonormal_and_sums_to_zero_per_group():
    groups = np.array([2023, 2023, 2023, 2024, 2024])
    basis = zero_sum_basis(groups)
    assert basis.shape == (5, 3)
    assert basis.T @ basis == pytest.approx(np.eye(3))
    assert basis[:3].sum(axis=0) == pytest.approx(0)
    assert basis[3:].sum(axis=0) == pytest.approx(0)


def test_walk_matrix_accumulates_steps_within_each_driver():
    steps = np.array([1.0, 0.5, -0.2, 3.0])
    assert (walk_matrix(make_drivers()) @ steps).tolist() == pytest.approx([1.0, 1.5, 1.3, 3.0])


def test_seasons_since_counts_missed_seasons():
    gap = seasons_since(make_drivers())
    assert gap.isna().tolist() == [True, False, False, True]
    assert gap.dropna().tolist() == [3, 1]


def test_second_season_flags_only_drivers_who_debuted_in_the_data():
    drivers = pd.DataFrame({"driver": ["ALO", "ALO", "PIA", "PIA", "PIA"], "season": [2018, 2019, 2023, 2024, 2025]})
    assert second_season(drivers).tolist() == [0, 0, 0, 1, 0]


def test_ratings_flip_sign_and_list_teams_per_driver_season():
    df = pd.DataFrame({
        "season": [2024, 2024, 2024],
        "driver": ["BEA", "BEA", "LEC"],
        "team": ["Ferrari", "Haas F1 Team", "Ferrari"],
    })
    draws = np.arange(1.0, 101.0).reshape(1, 100)
    posterior = xr.Dataset({
        "beta": (("chain", "draw", "driver_season"), np.stack([draws, -draws], axis=-1)),
        "gamma": (("chain", "draw", "team_season"), np.stack([draws, -draws], axis=-1)),
    })
    result = ratings(SimpleNamespace(posterior=posterior), df)
    bea, lec = result["drivers"]
    assert bea["driver"] == "BEA" and bea["teams"] == ["Ferrari", "Haas F1 Team"]
    assert bea["rating"] == pytest.approx(-50.5)
    assert bea["q05"] < bea["rating"] < bea["q95"]
    assert lec["rating"] == pytest.approx(50.5)
    assert [c["team"] for c in result["cars"]] == ["Ferrari", "Haas F1 Team"]
    json.dumps(result)


def test_build_model_has_one_effect_per_driver_season_and_team_season():
    df = pd.DataFrame({
        "season": [2023] * 4 + [2024] * 4,
        "round": 1, "session": "Q", "part": "Q1",
        "driver": ["AAA", "BBB", "CCC", "DDD"] * 2,
        "team": ["X", "X", "Y", "Y"] * 2,
        "lap_time": [90.0, 90.2, 90.5, 90.6, 89.0, 89.3, 89.4, 89.8],
    })
    model = build_model(df)
    assert len(model.coords["driver_season"]) == 8
    assert len(model.coords["team_season"]) == 4
    assert np.isfinite(model.compile_logp()(model.initial_point()))


def test_build_model_adds_forecast_driver_seasons_without_data():
    df = pd.DataFrame({
        "season": 2023, "round": 1, "session": "Q", "part": "Q1",
        "driver": ["AAA", "BBB"], "team": "X", "lap_time": [90.0, 90.2],
    })
    model = build_model(df, forecast=pd.DataFrame({"driver": ["AAA", "CCC"], "season": [2024, 2024]}))
    assert model.coords["driver_season"] == ("AAA 2023", "AAA 2024", "BBB 2023", "CCC 2024")
    assert np.isfinite(model.compile_logp()(model.initial_point()))
