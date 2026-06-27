# F1 Markov Pit Stop Decision Model

## Project Overview

A Python-based model of Formula 1 pit stop decisions using Markov chains. The model treats pit stop decisions as a sequence of states, where the team (agent) decides at each lap whether to pit or stay out based on current race conditions.

## Goals

- Model pit stop decision-making as a Markov chain over race laps
- Capture the key state variables that influence whether a team should pit (tyre degradation, track position, gap to cars ahead/behind, safety car status, etc.)
- Evaluate decision quality and compare against historical race outcomes

## Tech Stack

- **Language**: Python 3.x
- **Key libraries**: TBD (likely numpy, pandas, matplotlib; possibly scipy for Markov chain utilities)
- **Data**: TBD — details to be provided

## Project Structure

```
f1-markov-pit-model/
├── data/
│   ├── cache/          # FastF1 HTTP cache (git-ignored)
│   └── processed/      # Parquet outputs
├── scripts/
│   └── pull_2023_laps.py   # Data pipeline — pulls lap data from FastF1
└── CLAUDE.md
```

### Running the data pipeline

```bash
# Pull all 22 races of the 2023 season (downloads to data/cache, writes data/processed/laps_2023.parquet)
python3 scripts/pull_2023_laps.py
```

Output schema (`laps_2023.parquet`):

| column | type | notes |
|---|---|---|
| `season` | int | always 2023 |
| `round` | int | 1–22 |
| `event_name` | str | e.g. "Bahrain Grand Prix" |
| `driver` | str | 3-letter code (VER, HAM, …) |
| `lap_number` | float | |
| `compound` | str | SOFT / MEDIUM / HARD / INTERMEDIATE / WET |
| `tyre_age` | float | laps on current set |
| `position` | float | track position at lap end |
| `gap_to_car_ahead_s` | float | seconds behind car directly ahead; 0.0 for leader |
| `safety_car_status` | str | clear / yellow / sc / vsc |

## Markov Chain Design

### State Space

TBD — initial conditions and state variable definitions to be provided by user.

### Transition Probabilities

TBD — how probabilities are estimated (historical data, simulation, hand-tuned) to be defined.

### Decision / Action Space

At each lap, the agent chooses:
- **Stay out** — continue on current tyres
- **Pit** — take a tyre stop (incurring pit lane time loss, resetting tyre age)

## Data

- **Source**: FastF1 (wraps the official F1 timing API + Ergast)
- **Cache**: FastF1 HTTP cache lives in `data/cache/` — first run downloads ~100MB, subsequent runs are fast
- **Primary dataset**: `data/processed/laps_2023.parquet` — one row per driver per lap

## Development Notes

- No comments unless the WHY is non-obvious
- No premature abstractions — keep it simple until the model is validated
- Tests live alongside source code (structure TBD)
