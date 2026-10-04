import json
import sys
from pathlib import Path

import arviz as az
import numpy as np
import pandas as pd
import pymc as pm

CLEAN = Path("data/clean/qualifying.parquet")
OUTPUTS = Path("outputs")
PART = ["season", "round", "session", "part"]
HYPER = ["tau_driver", "tau_drift", "tau_car", "sigma", "nu"]
SAMPLE_DIMS = ("chain", "draw")
SEED = 2023


def encode(df: pd.DataFrame, keys: list[str]) -> tuple[pd.DataFrame, np.ndarray]:
    groups = df.groupby(keys, sort=True)
    return groups.size().reset_index()[keys], groups.ngroup().to_numpy()


def labels(table: pd.DataFrame) -> list[str]:
    return table.astype(str).agg(" ".join, axis=1).tolist()


def center_matrix(groups: np.ndarray) -> np.ndarray:
    same = groups[:, None] == groups[None, :]
    return np.eye(len(groups)) - same / same.sum(axis=1, keepdims=True)


def zero_sum_basis(groups: np.ndarray) -> np.ndarray:
    values, vectors = np.linalg.eigh(center_matrix(groups))
    return vectors[:, values > 0.5]


def walk_matrix(drivers: pd.DataFrame) -> np.ndarray:
    d, s = drivers["driver"].to_numpy(), drivers["season"].to_numpy()
    return ((d[:, None] == d[None, :]) & (s[None, :] <= s[:, None])).astype(float)


def seasons_since(drivers: pd.DataFrame) -> pd.Series:
    return drivers.groupby("driver")["season"].diff()


def build_model(df: pd.DataFrame) -> pm.Model:
    y = 100 * np.log(df["lap_time"].to_numpy())
    parts, part = encode(df, PART)
    drivers, driver = encode(df, ["driver", "season"])
    teams, team = encode(df, ["team", "season"])
    gap = seasons_since(drivers)
    part_mean = pd.Series(y).groupby(part).mean().to_numpy()

    coords = {"part": labels(parts), "driver_season": labels(drivers), "team_season": labels(teams)}
    with pm.Model(coords=coords) as model:
        alpha = pm.Normal("alpha", mu=part_mean, sigma=2, dims="part")

        tau_driver = pm.HalfNormal("tau_driver", 0.5)
        tau_drift = pm.HalfNormal("tau_drift", 0.1)
        step = pm.math.where(gap.isna().to_numpy(), tau_driver, tau_drift * np.sqrt(gap.fillna(1).to_numpy()))
        z_driver = pm.Normal("z_driver", dims="driver_season")
        beta_raw = walk_matrix(drivers) @ (step * z_driver)
        beta = pm.Deterministic("beta", center_matrix(drivers["season"].to_numpy()) @ beta_raw, dims="driver_season")

        tau_car = pm.HalfNormal("tau_car", 1.0)
        basis = zero_sum_basis(teams["season"].to_numpy())
        car = pm.Normal("car", 0, tau_car, shape=basis.shape[1])
        gamma = pm.Deterministic("gamma", basis @ car, dims="team_season")

        sigma = pm.HalfNormal("sigma", 0.5)
        nu = pm.Gamma("nu", alpha=2, beta=0.1)
        pm.StudentT("y", nu=nu, mu=alpha[part] + beta[driver] + gamma[team], sigma=sigma, observed=y)
    return model


def sample(model: pm.Model, seed: int = SEED):
    with model:
        return pm.sample(
            nuts_sampler="nutpie", draws=4000, chains=4, target_accept=0.85, random_seed=seed, progressbar=False
        )


def diagnostics(idata) -> dict:
    summary = az.summary(idata, kind="diagnostics")
    return {
        "divergences": int(idata.sample_stats["diverging"].sum()),
        "max_rhat": float(summary["r_hat"].max()),
        "min_ess_bulk": float(summary["ess_bulk"].min()),
    }


def summarize(table: pd.DataFrame, draws) -> pd.DataFrame:
    return table.assign(
        rating=draws.mean(SAMPLE_DIMS).values,
        q05=draws.quantile(0.05, dim=SAMPLE_DIMS).values,
        q95=draws.quantile(0.95, dim=SAMPLE_DIMS).values,
    ).round(3)


def ratings(idata, df: pd.DataFrame) -> dict:
    drivers, _ = encode(df, ["driver", "season"])
    teams = df.groupby(["driver", "season"])["team"].unique().map(list).to_numpy()
    cars, _ = encode(df, ["team", "season"])
    return {
        "drivers": summarize(drivers.assign(teams=teams), -idata.posterior["beta"]).to_dict("records"),
        "cars": summarize(cars, -idata.posterior["gamma"]).to_dict("records"),
    }


def main() -> None:
    df = pd.read_parquet(CLEAN)
    seasons = [int(s) for s in sys.argv[1:]]
    if seasons:
        df = df[df["season"].isin(seasons)]
    idata = sample(build_model(df))
    print(az.summary(idata, var_names=HYPER).to_string())
    print(diagnostics(idata))
    if not seasons:
        OUTPUTS.mkdir(exist_ok=True)
        (OUTPUTS / "ratings.json").write_text(json.dumps(ratings(idata, df), indent=2))
        idata.to_netcdf(OUTPUTS / "posterior.nc")


if __name__ == "__main__":
    main()
