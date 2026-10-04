# CLAUDE.md

Separate F1 driver one-lap pace from car pace using qualifying data 2018–2026 and a Bayesian model. Full spec in `PRD.md`.

## Rules

- Read `PRD.md` before starting a new stage.
- Work only on the requested stage, then stop and summarize the results.
- Never re-download data that is already in the cache (`data/raw/`).
- Every data-cleaning function must have a test.
- Run the model on 2 seasons first before running all seasons.
- Code style: clean, minimal comments, no overengineering.

## Setup

```bash
py -3.12 -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
```

## Commands

```bash
.venv/Scripts/python -m pytest
.venv/Scripts/python -m src.ingest
.venv/Scripts/python -m src.clean
```

## Layout

- `src/` — pipeline modules (`ingest`, `clean`, `network`, `baseline`, `model`, `evaluate`)
- `data/raw/` — FastF1 cache (gitignored)
- `data/clean/` — cleaned parquet + drop log
- `outputs/` — model ratings (JSON), posterior samples, figures
- `notebooks/` — exploration
- `tests/` — pytest
- `web/` — Next.js dashboard (Stage 5)

## Modeling conventions

- Target: `y = 100 * ln(lap_seconds)`; effects are in percent.
- Center β (driver) and γ (car) to zero within each season.
- Sample with `pm.sample(nuts_sampler="nutpie")`.
- PyTensor uses MSYS2 g++ (`C:\msys64\ucrt64\bin`) with `PYTENSOR_FLAGS=base_compiledir=C:/pytensor_cache` (forward slashes; backslashes resolve to a folder inside the project) (the user path has a space).
- Displayed ratings flip the sign: higher = faster.
