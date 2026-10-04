import pandas as pd

from src.ingest import is_qualifying, part_rows, qualifying_sessions

td = pd.to_timedelta


def test_sprint_qualifying_only_from_2024():
    assert not is_qualifying(2021, "Sprint Qualifying")
    assert is_qualifying(2024, "Sprint Qualifying")
    assert is_qualifying(2023, "Sprint Shootout")
    assert is_qualifying(2018, "Qualifying")
    assert not is_qualifying(2022, "Sprint")


def test_qualifying_sessions_skips_testing_and_future_events():
    normal = ["Practice 1", "Practice 2", "Practice 3", "Qualifying", "Race"]
    sprint = ["Practice 1", "Sprint Qualifying", "Sprint", "Qualifying", "Race"]
    testing = ["Practice 1", "Practice 2", "Practice 3", "None", "None"]
    events = [(0, "2024-02-23", testing), (1, "2024-03-02", normal), (2, "2024-04-21", sprint), (3, "2024-12-08", normal)]
    schedule = pd.DataFrame(
        [{"RoundNumber": r, "EventDate": pd.Timestamp(d), **{f"Session{i + 1}": s for i, s in enumerate(names)}}
         for r, d, names in events]
    )
    sessions = qualifying_sessions(schedule, 2024, pd.Timestamp("2024-06-01"))
    assert sessions == [(1, "Qualifying"), (2, "Sprint Qualifying"), (2, "Qualifying")]


def make_results():
    return pd.DataFrame({
        "Abbreviation": ["AAA", "BBB", "CCC"],
        "TeamName": ["T1", "T1", "T2"],
        "Position": [1, 2, 3],
        "Q1": td(["90s", "91s", None]),
    })


def test_part_rows_counts_laps_and_flags_wet_tyres():
    laps = pd.DataFrame({
        "Driver": ["AAA", "AAA", "BBB"],
        "Compound": ["SOFT", "SOFT", "INTERMEDIATE"],
        "LapStartTime": td(["10min", "12min", "11min"]),
        "Time": td(["11min", "13min", "12min"]),
    })
    weather = pd.DataFrame({"Time": td(["5min", "12min", "30min"]), "Rainfall": [False, True, False]})
    rows = part_rows(make_results(), "Q1", laps, weather)
    assert rows["lap_time"].tolist()[:2] == [90.0, 91.0]
    assert rows["lap_time"].isna().tolist() == [False, False, True]
    assert rows["n_laps"].tolist() == [2, 1, 0]
    assert rows["wet_tyres"].tolist() == [False, True, False]
    assert rows["rainfall"].all()


def test_part_rows_rainfall_only_inside_part_window():
    laps = pd.DataFrame({
        "Driver": ["AAA"], "Compound": ["SOFT"],
        "LapStartTime": td(["10min"]), "Time": td(["11min"]),
    })
    weather = pd.DataFrame({"Time": td(["5min", "30min"]), "Rainfall": [True, True]})
    assert not part_rows(make_results(), "Q1", laps, weather)["rainfall"].any()


def test_part_rows_falls_back_to_valid_laps_when_official_times_missing():
    results = make_results().assign(Q1=pd.NaT)
    laps = pd.DataFrame({
        "Driver": ["AAA", "AAA", "BBB"],
        "LapTime": td(["89s", "90s", "92s"]),
        "Deleted": [True, False, False],
        "Compound": ["SOFT"] * 3,
        "LapStartTime": td(["10min", "12min", "11min"]),
        "Time": td(["11min", "13min", "12min"]),
    })
    weather = pd.DataFrame({"Time": td(["5min"]), "Rainfall": [False]})
    rows = part_rows(results, "Q1", laps, weather)
    assert rows["lap_time"].tolist()[:2] == [90.0, 92.0]
    assert pd.isna(rows["lap_time"].iloc[2])


def test_part_rows_cancelled_part():
    weather = pd.DataFrame({"Time": td(["5min"]), "Rainfall": [True]})
    rows = part_rows(make_results(), "Q1", None, weather)
    assert rows["n_laps"].eq(0).all()
    assert not rows["wet_tyres"].any() and not rows["rainfall"].any()
