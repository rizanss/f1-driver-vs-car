from pathlib import Path

import pandas as pd

RAW = Path("data/raw")
CLEAN = Path("data/clean")
PART_KEYS = ["season", "round", "session", "part"]
DRIVER_SESSION_KEYS = ["season", "round", "session", "driver"]
SLOW = 1.02
OUTLIER = 1.07
COLUMNS = ["season", "round", "event", "session", "part", "driver", "team", "lap_time"]


def took_part(df: pd.DataFrame) -> pd.Series:
    return (df["part"] == "Q1") | df["lap_time"].notna() | (df["n_laps"] > 0)


def wet_part(df: pd.DataFrame) -> pd.Series:
    return df.groupby(PART_KEYS)["wet_tyres"].transform("any")


def no_time(df: pd.DataFrame) -> pd.Series:
    return df["lap_time"].isna()


def outlier_lap(df: pd.DataFrame) -> pd.Series:
    fastest = df.groupby(PART_KEYS)["lap_time"].transform("min")
    return df["lap_time"] > OUTLIER * fastest


def slow_lap(df: pd.DataFrame) -> pd.Series:
    best = df.groupby(DRIVER_SESSION_KEYS)["lap_time"].transform("min")
    return df["lap_time"] > SLOW * best


RULES = {"wet": wet_part, "no_time": no_time, "over_107pct": outlier_lap, "slow_lap": slow_lap}


def clean(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = raw[took_part(raw)]
    dropped = []
    for reason, rule in RULES.items():
        mask = rule(df)
        dropped.append(df[mask].assign(reason=reason))
        df = df[~mask]
    return df[COLUMNS].reset_index(drop=True), pd.concat(dropped, ignore_index=True)


def main() -> None:
    raw = pd.concat([pd.read_parquet(p) for p in sorted(RAW.glob("qualifying_*.parquet"))], ignore_index=True)
    df, dropped = clean(raw)
    CLEAN.mkdir(parents=True, exist_ok=True)
    df.to_parquet(CLEAN / "qualifying.parquet", index=False)
    dropped.to_csv(CLEAN / "dropped.csv", index=False, encoding="utf-8-sig")

    summary = pd.crosstab(dropped["season"], dropped["reason"]).join(df.groupby("season").size().rename("kept"))
    print(summary.to_string())
    rain_only = raw[raw["rainfall"] & ~wet_part(raw)].drop_duplicates(PART_KEYS)
    print(f"\nrain flag without wet tyres (kept, check manually): {len(rain_only)} parts")
    print(rain_only[["season", "round", "event", "session", "part"]].to_string(index=False))


if __name__ == "__main__":
    main()
