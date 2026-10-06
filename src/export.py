import json

import arviz as az
import pandas as pd

from src.model import CLEAN, OUTPUTS, SAMPLE_DIMS

THIN = 20
ERAS = {"2018-2021": [2018, 2019, 2020, 2021], "2022-2025": [2022, 2023, 2024, 2025], "2026": [2026]}


def draws(da, key: str) -> pd.DataFrame:
    x = -da.stack(sample=SAMPLE_DIMS)
    names = pd.Series(x[da.dims[-1]].values).str.rsplit(" ", n=1, expand=True)
    index = pd.MultiIndex.from_arrays([names[0], names[1].astype(int)], names=[key, "season"])
    return pd.DataFrame(x.values, index=index)


def car_share(drivers: pd.DataFrame, cars: pd.DataFrame) -> pd.DataFrame:
    car = cars.groupby(level="season").var(ddof=0)
    driver = drivers.groupby(level="season").var(ddof=0)
    return car / (car + driver)


def by_era(share: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({era: share.loc[seasons].mean() for era, seasons in ERAS.items()}).T


def summary(x: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "car_share": x.mean(axis=1), "q05": x.quantile(0.05, axis=1), "q95": x.quantile(0.95, axis=1),
    }).round(3)


def pole_laps(df: pd.DataFrame) -> pd.Series:
    return df.groupby(["season", "round", "session"])["lap_time"].min().groupby("season").median().round(3)


def records(x: pd.DataFrame) -> list[dict]:
    return [
        {x.index.names[0]: name, "season": int(season), "draws": row.round(3).tolist()}
        for (name, season), row in x.iterrows()
    ]


def main() -> None:
    posterior = az.from_netcdf(OUTPUTS / "posterior.nc").posterior
    drivers, cars = draws(posterior["beta"], "driver"), draws(posterior["gamma"], "team")
    share = car_share(drivers, cars)

    seasons = summary(share).assign(pole_lap=pole_laps(pd.read_parquet(CLEAN)))
    result = {
        "seasons": seasons.rename_axis("season").reset_index().to_dict("records"),
        "eras": summary(by_era(share)).rename_axis("era").reset_index().to_dict("records"),
    }
    (OUTPUTS / "seasons.json").write_text(json.dumps(result, indent=2))

    thinned = {"drivers": records(drivers.iloc[:, ::THIN]), "cars": records(cars.iloc[:, ::THIN])}
    (OUTPUTS / "draws.json").write_text(json.dumps(thinned, separators=(",", ":")))
    print(seasons.to_string())
    print(summary(by_era(share)).to_string())


if __name__ == "__main__":
    main()
