import pandas as pd
import pytest

from src.network import CLEAN, build_graph, to_json, to_lineage, year_label


def test_every_team_in_clean_data_has_lineage():
    to_lineage(pd.read_parquet(CLEAN)["team"])


def test_to_lineage_rejects_unknown_team():
    with pytest.raises(ValueError, match="Brawn"):
        to_lineage(pd.Series(["Ferrari", "Brawn"]))


def test_build_graph_merges_renamed_teams():
    df = pd.DataFrame({
        "driver": ["GAS", "GAS", "GAS", "GAS", "VER"],
        "team": ["Toro Rosso", "Red Bull Racing", "Toro Rosso", "AlphaTauri", "Red Bull Racing"],
        "season": [2018, 2019, 2019, 2020, 2019],
    })
    G = build_graph(df)
    assert G.edges["GAS", "Racing Bulls"]["seasons"] == [2018, 2019, 2020]
    assert G.edges["GAS", "Red Bull"]["seasons"] == [2019]
    assert G.nodes["Red Bull"]["kind"] == "team"
    assert G.degree("Red Bull") == 2


def test_to_json_links_drivers_to_teams_with_raw_names():
    df = pd.DataFrame({"driver": ["GAS", "GAS"], "team": ["Toro Rosso", "Red Bull Racing"], "season": [2018, 2019]})
    out = to_json(build_graph(df))
    assert out["drivers"] == [{"id": "GAS"}]
    assert {(l["source"], l["target"]) for l in out["links"]} == {("GAS", "Racing Bulls"), ("GAS", "Red Bull")}
    red_bull = next(t for t in out["teams"] if t["id"] == "Red Bull")
    assert red_bull["names"] == ["Red Bull", "Red Bull Racing"]
    assert red_bull["color"].startswith("#")


def test_year_label_collapses_consecutive_seasons():
    assert year_label([2018, 2019, 2020, 2022]) == "18–20, 22"
    assert year_label([2021]) == "21"
