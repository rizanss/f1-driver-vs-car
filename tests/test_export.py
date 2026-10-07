import numpy as np
import pandas as pd
import pytest
import xarray as xr

from src.export import by_era, car_share, draws, has_photo, pole_laps, records


def frame(rows: dict, key: str) -> pd.DataFrame:
    index = pd.MultiIndex.from_tuples(rows.keys(), names=[key, "season"])
    return pd.DataFrame(list(rows.values()), index=index)


def test_draws_flips_sign_and_splits_labels():
    da = xr.DataArray(
        np.arange(8.0).reshape(1, 4, 2), dims=("chain", "draw", "team_season"),
        coords={"team_season": ["Alfa Romeo Racing 2019", "Haas 2020"]},
    )
    x = draws(da, "team")
    assert x.index.tolist() == [("Alfa Romeo Racing", 2019), ("Haas", 2020)]
    assert x.loc[("Haas", 2020)].tolist() == [-1.0, -3.0, -5.0, -7.0]


def test_car_share_is_car_variance_over_total_per_season_and_draw():
    cars = frame({("A", 2020): [1, 2], ("B", 2020): [-1, -2]}, "team")
    drivers = frame({("X", 2020): [1, 1], ("Y", 2020): [-1, -1], ("Z", 2020): [0, 0]}, "driver")
    share = car_share(drivers, cars)
    assert share.loc[2020].tolist() == pytest.approx([1 / (1 + 2 / 3), 4 / (4 + 2 / 3)])


def test_by_era_averages_seasons_within_each_draw():
    share = pd.DataFrame([[0.2, 0.4]] * 4 + [[0.6, 0.8]] * 4 + [[0.9, 1.0]], index=range(2018, 2027))
    eras = by_era(share)
    assert eras.index.tolist() == ["2018-2021", "2022-2025", "2026"]
    assert eras.values == pytest.approx(np.array([[0.2, 0.4], [0.6, 0.8], [0.9, 1.0]]))


def test_pole_laps_is_median_of_fastest_lap_per_session():
    df = pd.DataFrame({
        "season": [2024] * 5, "round": [1, 1, 2, 3, 3], "session": ["Q", "Q", "Q", "Q", "SQ"],
        "lap_time": [90.0, 89.0, 80.0, 100.0, 101.0],
    })
    assert pole_laps(df).to_dict() == {2024: 94.5}


def test_records_rounds_draws_and_uses_plain_ints():
    out = records(frame({("VER", 2023): [0.12345, -0.5]}, "driver"))
    assert out == [{"driver": "VER", "season": 2023, "draws": [0.123, -0.5]}]
    assert type(out[0]["season"]) is int


def test_has_photo_rejects_missing_urls():
    assert has_photo("https://media.formula1.com/x/1col/image.png")
    assert not has_photo("None")
    assert not has_photo(float("nan"))
