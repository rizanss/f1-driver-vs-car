from pathlib import Path

import numpy as np
import pandas as pd

CLEAN = Path("data/clean/qualifying.parquet")
TEAM_PART = ["season", "round", "session", "part", "team"]
EVENT = ["season", "round"]
TEST_FRACTION = 0.2
LAST_TRAIN_SEASON = 2025


def teammate_gaps(df: pd.DataFrame) -> pd.DataFrame:
    df = df.assign(y=100 * np.log(df["lap_time"]))
    pairs = df.merge(df[TEAM_PART + ["driver", "y"]], on=TEAM_PART, suffixes=("", "_mate"))
    pairs = pairs[pairs["driver"] != pairs["driver_mate"]].rename(columns={"driver_mate": "teammate"})
    return pairs.assign(gap=pairs["y"] - pairs["y_mate"]).drop(columns=["y", "y_mate"]).reset_index(drop=True)


def fit(gaps: pd.DataFrame) -> pd.DataFrame:
    return gaps.groupby(["driver", "season"], as_index=False)["gap"].mean().rename(columns={"gap": "rating"})


def latest_rating(ratings: pd.DataFrame, drivers: pd.Series, seasons: pd.Series) -> pd.Series:
    keys = pd.DataFrame({"driver": drivers, "season": seasons}).reset_index(names="row")
    merged = pd.merge_asof(keys.sort_values("season"), ratings.sort_values("season"), on="season", by="driver")
    return merged.set_index("row")["rating"].reindex(drivers.index).fillna(0.0)


def predict(ratings: pd.DataFrame, gaps: pd.DataFrame) -> pd.Series:
    own = latest_rating(ratings, gaps["driver"], gaps["season"])
    mate = latest_rating(ratings, gaps["teammate"], gaps["season"])
    return (own - mate) / 2


def split_events(gaps: pd.DataFrame, fraction: float = TEST_FRACTION, seed: int = 0):
    events = gaps[EVENT].drop_duplicates().groupby("season").sample(frac=fraction, random_state=seed)
    is_test = gaps.set_index(EVENT).index.isin(events.set_index(EVENT).index)
    return gaps[~is_test], gaps[is_test]


def split_future(gaps: pd.DataFrame):
    is_test = gaps["season"] > LAST_TRAIN_SEASON
    return gaps[~is_test], gaps[is_test]


def evaluate(train: pd.DataFrame, test: pd.DataFrame) -> dict:
    error = test["gap"] - predict(fit(train), test)
    return {"test_rows": len(test), "baseline_mae": error.abs().mean(), "zero_mae": test["gap"].abs().mean()}


def main() -> None:
    gaps = teammate_gaps(pd.read_parquet(CLEAN))
    results = pd.DataFrame({
        "random events": evaluate(*split_events(gaps)),
        "future (2026)": evaluate(*split_future(gaps)),
    }).T.astype({"test_rows": int})
    print(f"{len(gaps)} rows with a teammate in the same part\n")
    print(results.round(3).to_string())


if __name__ == "__main__":
    main()