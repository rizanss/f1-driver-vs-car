import json

import arviz as az
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pymc as pm

from src.baseline import CLEAN, EVENT, evaluate as baseline_scores, split_events, split_future, teammate_gaps
from src.model import DRIVER, OUTPUTS, PRIORS, SAMPLE_DIMS, SEED, build_model, diagnostics, ratings, sample

SPLIT_SEEDS = range(5)
PPC_THIN = 10
QUANTILES = [0.25, 0.5, 0.75, 0.9, 0.99]
PRIOR_VARIANTS = {f"{k} x{f}": PRIORS | {k: PRIORS[k] * f} for k in ("tau_driver", "tau_drift", "tau_car") for f in (0.5, 2)}
MIN_TOP5_OVERLAP = 4
SWITCHES = [
    ("ALO", 2022, 2023, "car"),
    ("SAI", 2024, 2025, "car"),
    ("PER", 2020, 2021, "car"),
    ("BOT", 2021, 2022, "car"),
    ("ALB", 2020, 2022, "car"),
    ("RIC", 2020, 2021, "driver"),
]
FIGURE = OUTPUTS / "figures" / "ppc_teammate_gaps.png"


def drop_events(df: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    return df[~df.set_index(EVENT).index.isin(events.set_index(EVENT).index)]


def driver_effects(idata) -> pd.Series:
    beta = idata.posterior["beta"].mean(SAMPLE_DIMS).to_series()
    beta.index = pd.MultiIndex.from_tuples([(d, int(s)) for d, s in beta.index.str.split()], names=DRIVER)
    return beta


def predict(effects: pd.Series, gaps: pd.DataFrame) -> pd.Series:
    own = effects.loc[list(zip(gaps["driver"], gaps["season"]))].to_numpy()
    mate = effects.loc[list(zip(gaps["teammate"], gaps["season"]))].to_numpy()
    return pd.Series(own - mate, index=gaps.index)


def holdout(df: pd.DataFrame, train_gaps: pd.DataFrame, test_gaps: pd.DataFrame) -> dict:
    train = drop_events(df, test_gaps[EVENT].drop_duplicates())
    idata = sample(build_model(train, forecast=test_gaps[DRIVER]))
    error = test_gaps["gap"] - predict(driver_effects(idata), test_gaps)
    return baseline_scores(train_gaps, test_gaps) | {"model_mae": error.abs().mean()} | diagnostics(idata)


def simulated_gaps(df: pd.DataFrame, idata) -> list[pd.Series]:
    thinned = idata.posterior.isel(draw=slice(None, None, PPC_THIN))
    with build_model(df):
        y = pm.sample_posterior_predictive(thinned, random_seed=SEED, progressbar=False).posterior_predictive["y"]
    sims = y.stack(sample=SAMPLE_DIMS).transpose("sample", ...).values
    return [teammate_gaps(df.assign(lap_time=np.exp(sim / 100)))["gap"] for sim in sims]


def ppc(df: pd.DataFrame, gaps: pd.DataFrame, idata) -> dict:
    sims = simulated_gaps(df, idata)
    real = gaps["gap"].abs().quantile(QUANTILES)
    fake = pd.DataFrame([s.abs().quantile(QUANTILES) for s in sims])
    table = pd.DataFrame({"real": real, "sim_q05": fake.quantile(0.05), "sim_median": fake.median(), "sim_q95": fake.quantile(0.95)})
    table["inside"] = table["real"].between(table["sim_q05"], table["sim_q95"])
    plot_ppc(gaps["gap"], pd.concat(sims))
    return {"abs_gap_quantiles": table.rename_axis("quantile").reset_index().to_dict("records"), "passed": bool(table["inside"].all())}


def plot_ppc(real: pd.Series, fake: pd.Series) -> None:
    bins = np.linspace(-3, 3, 121)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(real.clip(-3, 3), bins=bins, density=True, color="#9aa5b1", label="Real")
    ax.hist(fake.clip(-3, 3), bins=bins, density=True, histtype="step", lw=1.8, color="#d6336c", label="Simulated by model")
    ax.set(yscale="log", xlabel="Gap to teammate in the same session part (%, clipped at Â±3)", ylabel="Density (log)",
           title="Posterior predictive check: teammate gaps")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIGURE, dpi=150)
    plt.close(fig)


def top5(drivers: pd.DataFrame) -> pd.Series:
    return drivers.sort_values("rating", ascending=False).groupby("season")["driver"].apply(lambda d: set(d.head(5)))


def top5_overlap(reference: pd.DataFrame, variant: pd.DataFrame) -> pd.Series:
    ref, var = top5(reference), top5(variant)
    return pd.Series({int(s): len(ref[s] & var[s]) for s in ref.index})


def robustness(df: pd.DataFrame, reference: dict) -> dict:
    variants = {}
    for name, priors in PRIOR_VARIANTS.items():
        idata = sample(build_model(df, priors))
        overlap = top5_overlap(pd.DataFrame(reference["drivers"]), pd.DataFrame(ratings(idata, df)["drivers"]))
        variants[name] = {"min_top5_overlap": int(overlap.min()), "top5_overlap": overlap.to_dict()} | diagnostics(idata)
    passed = all(v["min_top5_overlap"] >= MIN_TOP5_OVERLAP for v in variants.values())
    return {"variants": variants, "passed": passed}


def decompose(reference: dict, driver: str, before: int, after: int) -> dict:
    drivers = pd.DataFrame(reference["drivers"]).set_index(["driver", "season"])
    cars = pd.DataFrame(reference["cars"]).set_index(["team", "season"])
    team = {s: drivers.loc[(driver, s), "teams"][0] for s in (before, after)}
    return {
        "teams": [team[before], team[after]],
        "driver_change": drivers.loc[(driver, after), "rating"] - drivers.loc[(driver, before), "rating"],
        "car_change": cars.loc[(team[after], after), "rating"] - cars.loc[(team[before], before), "rating"],
    }


def sanity(reference: dict) -> dict:
    cases = []
    for driver, before, after, expected in SWITCHES:
        case = decompose(reference, driver, before, after)
        dominant = "car" if abs(case["car_change"]) > abs(case["driver_change"]) else "driver"
        cases.append({"driver": driver, "seasons": [before, after], **case, "expected": expected, "dominant": dominant})
    return {"cases": cases, "passed": all(c["dominant"] == c["expected"] for c in cases)}


def healthy(diag: dict) -> bool:
    return diag["divergences"] == 0 and diag["max_rhat"] < 1.01


def main() -> None:
    df = pd.read_parquet(CLEAN)
    gaps = teammate_gaps(df)
    idata = az.from_netcdf(OUTPUTS / "posterior.nc")
    reference = json.loads((OUTPUTS / "ratings.json").read_text())

    random_events = [holdout(df, *split_events(gaps, seed=s)) | {"seed": s} for s in SPLIT_SEEDS]
    future = holdout(df, *split_future(gaps))
    robust = robustness(df, reference)
    refits = random_events + [future] + list(robust["variants"].values())
    results = {
        "random_events": {"splits": random_events, "passed": all(r["model_mae"] < r["baseline_mae"] for r in random_events)},
        "future_2026": future | {"passed": bool(future["model_mae"] < future["baseline_mae"])},
        "ppc": ppc(df, gaps, idata),
        "health": {"full": reference["diagnostics"], "refits_healthy": sum(map(healthy, refits)), "refits": len(refits),
                   "passed": healthy(reference["diagnostics"]) and all(map(healthy, refits))},
        "robustness": robust,
        "sanity": sanity(reference),
    }
    (OUTPUTS / "validation.json").write_text(json.dumps(results, indent=2, default=float))

    print(pd.DataFrame(random_events).round(3).to_string(index=False))
    print(pd.Series(future).round(3).to_string())
    print(pd.DataFrame(results["ppc"]["abs_gap_quantiles"]).round(3).to_string(index=False))
    print(pd.DataFrame({k: v["min_top5_overlap"] for k, v in robust["variants"].items()}, index=["min_top5_overlap"]).T)
    print(pd.DataFrame(results["sanity"]["cases"]).round(3).to_string(index=False))
    print({k: v["passed"] for k, v in results.items()})


if __name__ == "__main__":
    main()
