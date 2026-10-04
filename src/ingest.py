import sys
import time
from pathlib import Path

import fastf1
import pandas as pd
from fastf1.exceptions import DataNotLoadedError, RateLimitExceededError

RAW = Path("data/raw")
SEASONS = range(2018, 2027)
PARTS = ("Q1", "Q2", "Q3")
WET = ("INTERMEDIATE", "WET")
COLUMNS = [
    "season", "round", "event", "session", "part", "driver", "team",
    "position", "lap_time", "n_laps", "wet_tyres", "rainfall",
]


def is_qualifying(year: int, name: str) -> bool:
    if name == "Sprint Qualifying":
        return year >= 2024
    return name in ("Qualifying", "Sprint Shootout")


def qualifying_sessions(schedule: pd.DataFrame, year: int, today: pd.Timestamp) -> list[tuple[int, str]]:
    done = schedule[(schedule["RoundNumber"] > 0) & (schedule["EventDate"] < today)]
    return [
        (int(event["RoundNumber"]), event[f"Session{i}"])
        for _, event in done.iterrows()
        for i in range(1, 6)
        if is_qualifying(year, event[f"Session{i}"])
    ]


def part_rows(results: pd.DataFrame, part: str, laps: pd.DataFrame | None, weather: pd.DataFrame) -> pd.DataFrame:
    lap_time = results[part]
    if lap_time.isna().all() and laps is not None:
        valid = laps[laps["Deleted"].ne(True)]
        lap_time = results["Abbreviation"].map(valid.groupby("Driver")["LapTime"].min())
    rows = pd.DataFrame({
        "driver": results["Abbreviation"],
        "team": results["TeamName"],
        "position": results["Position"].astype(float),
        "part": part,
        "lap_time": lap_time.dt.total_seconds(),
    }).reset_index(drop=True)
    if laps is None:
        return rows.assign(n_laps=0, wet_tyres=False, rainfall=False)

    wet_drivers = laps.loc[laps["Compound"].isin(WET), "Driver"]
    in_part = weather["Time"].between(laps["LapStartTime"].min(), laps["Time"].max())
    return rows.assign(
        n_laps=rows["driver"].map(laps["Driver"].value_counts()).fillna(0).astype(int),
        wet_tyres=rows["driver"].isin(wet_drivers),
        rainfall=bool(weather.loc[in_part, "Rainfall"].any()),
    )


def load_session(year: int, rnd: int, name: str):
    while True:
        try:
            session = fastf1.get_session(year, rnd, name)
            session.load(telemetry=False)
            return session
        except RateLimitExceededError:
            print("  rate limit reached, waiting 5 min", flush=True)
            time.sleep(300)


def ingest_season(year: int) -> tuple[pd.DataFrame, list[str]]:
    schedule = fastf1.get_event_schedule(year, include_testing=False)
    frames, failed = [], []
    for rnd, name in qualifying_sessions(schedule, year, pd.Timestamp.now().normalize()):
        session = load_session(year, rnd, name)
        try:
            parts = session.laps.split_qualifying_sessions()
            rows = pd.concat(
                [part_rows(session.results, p, laps, session.weather_data) for p, laps in zip(PARTS, parts)],
                ignore_index=True,
            )
        except (DataNotLoadedError, ValueError) as exc:
            print(f"  failed {year} R{rnd} {name}: {exc}", flush=True)
            failed.append(f"R{rnd} {name}")
            continue
        session_code = "Q" if name == "Qualifying" else "SQ"
        frames.append(rows.assign(season=year, round=rnd, event=session.event["EventName"], session=session_code))
    return pd.concat(frames, ignore_index=True)[COLUMNS], failed


def main(years) -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    fastf1.Cache.enable_cache(str(RAW))
    fastf1.set_log_level("WARNING")
    current_year = pd.Timestamp.now().year
    for year in years:
        path = RAW / f"qualifying_{year}.parquet"
        if path.exists() and year < current_year:
            print(f"{year}: cached", flush=True)
            continue
        df, failed = ingest_season(year)
        if failed:
            print(f"{year}: not saved, rerun to retry {failed}", flush=True)
            continue
        df.to_parquet(path, index=False)
        n_sessions = df[["round", "session"]].drop_duplicates().shape[0]
        print(f"{year}: {n_sessions} sessions, {len(df)} rows", flush=True)


if __name__ == "__main__":
    main([int(y) for y in sys.argv[1:]] or SEASONS)
