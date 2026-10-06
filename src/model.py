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
DRIVER = ["driver", "season"]
HYPER = ["tau_driver", "tau_drift", "learn", "tau_car", "tau_team_part", "sigma", "nu"]
NUISANCE = ["z_team_part"]
SAMPLE_DIMS = ("chain", "draw")
SEED = 2023
PRIORS = {"tau_driver": 0.5, "tau_drift": 0.1, "learn": 0.2, "tau_car": 1.0, "tau_team_part": 0.3, "sigma": 0.5}
DEBUT_BEFORE_2018 = {
    "ALO", "BOT", "ERI", "GAS", "GIO", "GRO", "HAM", "HAR", "HUL", "KUB", "KVY",
    "MAG", "OCO", "PER", "RAI", "RIC", "SAI", "STR", "VAN", "VER", "VET",
}


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


def second_season(drivers: pd.DataFrame) -> np.ndarray:
    nth = drivers.groupby("driver").cumcount()
    return ((nth == 1) & ~drivers["driver"].isin(DEBUT_BEFORE_2018)).to_numpy(float)


def build_model(df: pd.DataFrame, priors: dict = PRIORS, forecast: pd.DataFrame | None = None) -> pm.Model:
    y = 100 * np.log(df["lap_time"].to_numpy())
    parts, part = encode(df, PART)
    drivers, driver = encode(pd.concat([df[DRIVER], forecast[DRIVER]]) if forecast is not None else df, DRIVER)
    driver = driver[: len(df)]
    teams, team = encode(df, ["team", "season"])
    team_parts, team_part = encode(df, PART + ["team"])
    gap = seasons_since(drivers)
    part_mean = pd.Series(y).groupby(part).mean().to_numpy()

    coords = {
        "part": labels(parts), "driver_season": labels(drivers),
        "team_season": labels(teams), "team_part": labels(team_parts),
    }
    with pm.Model(coords=coords) as model:
        alpha = pm.Normal("alpha", mu=part_mean, sigma=2, dims="part")

        tau_driver = pm.HalfNormal("tau_driver", priors["tau_driver"])
        tau_drift = pm.HalfNormal("tau_drift", priors["tau_drift"])
        step = pm.math.where(gap.isna().to_numpy(), tau_driver, tau_drift * np.sqrt(gap.fillna(1).to_numpy()))
        learn = pm.Normal("learn", 0, priors["learn"])
        z_driver = pm.Normal("z_driver", dims="driver_season")
        beta_raw = walk_matrix(drivers) @ (learn * second_season(drivers) + step * z_driver)
        beta = pm.Deterministic("beta", center_matrix(drivers["season"].to_numpy()) @ beta_raw, dims="driver_season")

        tau_car = pm.HalfNormal("tau_car", priors["tau_car"])
        basis = zero_sum_basis(teams["season"].to_numpy())
        car = pm.Normal("car", 0, tau_car, shape=basis.shape[1])
        gamma = pm.Deterministic("gamma", basis @ car, dims="team_season")

        tau_team_part = pm.HalfNormal("tau_team_part", priors["tau_team_part"])
        z_team_part = pm.Normal("z_team_part", dims="team_part")
        delta = tau_team_part * z_team_part

        sigma = pm.HalfNormal("sigma", priors["sigma"])
        nu = pm.Gamma("nu", alpha=2, beta=0.1)
        mu = alpha[part] + beta[driver] + gamma[team] + delta[team_part]
        pm.StudentT("y", nu=nu, mu=mu, sigma=sigma, observed=y)
    return model


def sample(model: pm.Model, seed: int = SEED):
    with model:
        return pm.sample(
            nuts_sampler="nutpie", draws=2000, chains=4, target_accept=0.85, random_seed=seed, progressbar=False
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
    drivers, _ = encode(df, DRIVER)
    teams = df.groupby(DRIVER)["team"].unique().map(list).to_numpy()
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
    diag = diagnostics(idata)
    print(diag)
    if not seasons:
        OUTPUTS.mkdir(exist_ok=True)
        result = ratings(idata, df) | {"diagnostics": diag}
        (OUTPUTS / "ratings.json").write_text(json.dumps(result, indent=2))
        idata["posterior"] = idata.posterior.to_dataset().drop_vars(NUISANCE)
        idata.to_netcdf(OUTPUTS / "posterior.nc")


if __name__ == "__main__":
    main()
