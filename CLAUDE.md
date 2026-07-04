# F1 Markov Pit Stop Decision Model

## Project Overview

A Python-based model of Formula 1 pit stop decisions using Markov chains. The model treats pit stop decisions as a sequence of states, where the team (agent) decides at each lap whether to pit or stay out based on current race conditions.

## Goals

- Model pit stop decision-making as a Markov chain over race laps
- Capture the key state variables that influence whether a team should pit (tyre degradation, track position, gap to cars ahead/behind, safety car status, etc.)
- Evaluate decision quality and compare against historical race outcomes

## Tech Stack

- **Language**: Python 3.x
- **Key libraries**: pandas, matplotlib, FastF1
- **Data**: FastF1 API — 2023 full season (22 races)

## Project Structure

```
f1-markov-pit-model/
├── data/
│   ├── cache/          # FastF1 HTTP cache (git-ignored)
│   └── processed/      # Parquet outputs
│       ├── laps_2023.parquet    # Raw lap data (one row per driver per lap)
│       └── states_2023.parquet  # Encoded state space used for Markov model
├── notebooks/
│   └── explore_data.ipynb  # EDA: state distributions, pit rates, tyre degradation
├── scripts/
│   └── pull_2023_laps.py   # Data pipeline — pulls lap data from FastF1
└── CLAUDE.md
```

### Running the data pipeline

```bash
# Pull all 22 races of the 2023 season (downloads to data/cache, writes data/processed/laps_2023.parquet)
python3 scripts/pull_2023_laps.py
```

Output schema (`laps_2023.parquet`) — 24,431 rows:

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
| `lap_time_s` | float | lap time in seconds (NaN for laps where FastF1 has no time) |

## Markov Chain Design

### State Space

Each row in `states_2023.parquet` encodes one lap as a discrete state tuple: `lap_number | compound | tire_age_bin | position_bin | race_state | gap_bin`

| variable | values | bins |
|---|---|---|
| `lap_number` | 1–70 | (continuous — not binned) |
| `compound` | SOFT / MEDIUM / HARD | — |
| `tire_age_bin` | 0–5 | 0–5, 6–10, 11–15, 16–20, 21–25, 26+ laps |
| `position_bin` | 0–4 | P1–3, P4–6, P7–10, P11–15, P16–20 |
| `race_state` | green / sc / vsc | mapped from FastF1 TrackStatus |
| `gap_bin` | 0–3 | <1 s, 1–3 s, 3–5 s, >5 s behind car ahead |

Theoretical state count: 70 × 3 × 6 × 5 × 3 × 4 = **75,600** states. The 2023 dataset covers 23,259 rows across 22 races and 22 drivers.

### Transition Probabilities

TBD — how probabilities are estimated (historical data, simulation, hand-tuned) to be defined.

### Decision / Action Space

At each lap, the agent chooses:
- **Stay out (0)** — continue on current tyres (~94.7% of laps)
- **Pit (1)** — take a tyre stop (incurring pit lane time loss, resetting tyre age) (~5.3% of laps)

## Data

- **Source**: FastF1 (wraps the official F1 timing API + Ergast)
- **Cache**: FastF1 HTTP cache lives in `data/cache/` — first run downloads ~100MB, subsequent runs are fast
- **Raw laps**: `data/processed/laps_2023.parquet` — 24,431 rows, one per driver per lap, includes `lap_time_s`
- **Encoded states**: `data/processed/states_2023.parquet` — 23,259 rows after dropping laps with unusable data (INTERMEDIATE/WET compounds, missing positions, etc.)

## Exploratory Analysis (`notebooks/explore_data.ipynb`)

Sections in the notebook:

1. **First 10 rows** — sanity check of encoded state columns
2. **State variable distributions** — histograms and bar charts for each binned variable
3. **Pit vs stay-out split** — overall action balance (~94.7% stay out)
4. **Pit rate by compound and race state** — bar charts + heatmap; SC/VSC laps show ~3–4× higher pit rate than green flag
5. **Tyre degradation curves** — average lap time delta (normalised by per-race median) vs tyre age for SOFT, MEDIUM, HARD on green-flag laps (70–120 s filter); uses `laps_2023.parquet`

## Development Notes

- No comments unless the WHY is non-obvious
- No premature abstractions — keep it simple until the model is validated
- Tests live alongside source code (structure TBD)
