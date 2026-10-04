from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from matplotlib.colors import to_rgb

CLEAN = Path("data/clean/qualifying.parquet")
FIGURE = Path("outputs/figures/driver_network.png")

TEAMS = {
    "Williams": ("#64C4FF", ""),
    "Racing Bulls": ("#6692FF", "Toro Rosso\nAlphaTauri · RB"),
    "Red Bull": ("#1E3A8A", ""),
    "McLaren": ("#FF8000", ""),
    "Alpine": ("#FF87BC", "Renault"),
    "Aston Martin": ("#229971", "Force India\nRacing Point"),
    "Haas": ("#9CA3AF", ""),
    "Ferrari": ("#E8002D", ""),
    "Audi": ("#52E252", "Sauber · Alfa Romeo\nKick Sauber"),
    "Cadillac": ("#1F1F1F", ""),
    "Mercedes": ("#27F4D2", ""),
}
LINEAGE = {
    "Red Bull Racing": "Red Bull",
    "Toro Rosso": "Racing Bulls",
    "AlphaTauri": "Racing Bulls",
    "RB": "Racing Bulls",
    "Force India": "Aston Martin",
    "Racing Point": "Aston Martin",
    "Renault": "Alpine",
    "Haas F1 Team": "Haas",
    "Sauber": "Audi",
    "Alfa Romeo Racing": "Audi",
    "Alfa Romeo": "Audi",
    "Kick Sauber": "Audi",
}


def to_lineage(teams: pd.Series) -> pd.Series:
    lineage = teams.replace(LINEAGE)
    unknown = set(lineage) - set(TEAMS)
    if unknown:
        raise ValueError(f"teams without lineage: {sorted(unknown)}")
    return lineage


def build_graph(df: pd.DataFrame) -> nx.Graph:
    stints = (
        df.assign(team=to_lineage(df["team"]))
        .groupby(["driver", "team"])["season"]
        .agg(lambda s: sorted(s.unique().tolist()))
    )
    G = nx.Graph()
    for (driver, team), seasons in stints.items():
        G.add_node(driver, kind="driver")
        G.add_node(team, kind="team")
        G.add_edge(driver, team, seasons=seasons)
    return G


def year_label(seasons: list[int]) -> str:
    runs = []
    for s in seasons:
        if runs and s == runs[-1][-1] + 1:
            runs[-1].append(s)
        else:
            runs.append([s])
    return ", ".join(f"{r[0] % 100}" + (f"–{r[-1] % 100}" if len(r) > 1 else "") for r in runs)


def separate(pos: dict, movable: list, team_gap: float = 0.25, driver_gap: float = 0.12) -> None:
    for _ in range(100):
        for d in movable:
            for n, p in pos.items():
                delta = pos[d] - p
                dist = np.hypot(*delta)
                gap = team_gap if n in TEAMS else driver_gap
                if n != d and dist < gap:
                    pos[d] = p + (delta / dist if dist else np.array([0.0, 1.0])) * gap


def layout(G: nx.Graph) -> dict:
    teams = [t for t in TEAMS if t in G]
    angles = np.pi / 2 - np.linspace(0, 2 * np.pi, len(teams), endpoint=False)
    pos = {t: np.array([np.cos(a), np.sin(a)]) for t, a in zip(teams, angles)}

    movers = sorted(n for n, k in G.nodes(data="kind") if k == "driver" and G.degree(n) > 1)
    for d in movers:
        weights = [len(G.edges[d, t]["seasons"]) for t in G[d]]
        pos[d] = 0.8 * np.average([pos[t] for t in G[d]], axis=0, weights=weights)
    separate(pos, movers)

    rng = np.random.default_rng(0)
    for n in G:
        if n not in pos:
            pos[n] = 1.25 * pos[next(iter(G[n]))] + rng.normal(0, 0.05, 2)
    return nx.spring_layout(G, pos=pos, fixed=teams + movers, k=0.2, iterations=300, seed=0)


def draw(G: nx.Graph, path: Path) -> None:
    pos = layout(G)
    teams = [n for n, k in G.nodes(data="kind") if k == "team"]
    drivers = [n for n, k in G.nodes(data="kind") if k == "driver"]
    edges = [(d, t) if t in TEAMS else (t, d) for d, t in G.edges]

    fig, ax = plt.subplots(figsize=(16, 16))
    nx.draw_networkx_edges(
        G, pos, edgelist=edges, ax=ax, alpha=0.75,
        edge_color=[TEAMS[t][0] for _, t in edges],
        width=[1 + 0.6 * len(G.edges[e]["seasons"]) for e in edges],
    )
    nx.draw_networkx_edge_labels(
        G, pos, ax=ax, font_size=7, font_color="#444",
        edge_labels={e: year_label(G.edges[e]["seasons"]) for e in edges},
        bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85),
    )
    nx.draw_networkx_nodes(G, pos, nodelist=teams, ax=ax, node_size=7500,
                           node_color=[TEAMS[t][0] for t in teams])
    nx.draw_networkx_nodes(G, pos, nodelist=drivers, ax=ax, node_size=650,
                           node_color=["#FFE08A" if G.degree(d) > 1 else "white" for d in drivers],
                           edgecolors="#333", linewidths=1)
    nx.draw_networkx_labels(G, pos, labels={d: d for d in drivers}, ax=ax, font_size=8, font_weight="bold")
    for t in teams:
        x, y = pos[t]
        color, former = TEAMS[t]
        r, g, b = to_rgb(color)
        text_color = "#111" if 0.299 * r + 0.587 * g + 0.114 * b > 0.6 else "white"
        ax.text(x, y + (0.015 if former else 0), t, ha="center", va="bottom" if former else "center",
                fontsize=10, fontweight="bold", color=text_color)
        if former:
            ax.text(x, y - 0.005, former, ha="center", va="top", fontsize=6.5, color=text_color,
                    linespacing=1.1)

    ax.set_title("Who drove for whom: F1 qualifying 2018–2026", fontsize=18, fontweight="bold")
    ax.text(
        0.5, 0, "Big circle = team (earlier names inside).  Small circle = driver.  Line = drove for that team, "
        "label = seasons (19–20 = 2019–2020).\nYellow drivers raced for 2+ teams: they link the teams "
        "together, which is what lets the model compare drivers across different cars.",
        transform=ax.transAxes, ha="center", va="top", fontsize=11, color="#333",
    )
    ax.axis("off")
    ax.margins(0.03)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main() -> None:
    G = build_graph(pd.read_parquet(CLEAN))
    drivers = [n for n, k in G.nodes(data="kind") if k == "driver"]
    movers = [d for d in drivers if G.degree(d) > 1]
    print(f"{len(drivers)} drivers, {len(G) - len(drivers)} teams, "
          f"{len(movers)} drove for 2+ teams, connected: {nx.is_connected(G)}")
    draw(G, FIGURE)
    print(f"saved {FIGURE}")


if __name__ == "__main__":
    main()
