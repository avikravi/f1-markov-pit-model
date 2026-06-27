"""
Encode lap-by-lap F1 data into discrete Markov chain states.

State tuple: (lap_number, compound, tire_age_bin, position_bin, race_state, gap_bin)
Action:       1 = driver pitted on the next lap, 0 = stayed out
"""

import pandas as pd
from pathlib import Path

INPUT  = Path("data/processed/laps_2023.parquet")
OUTPUT = Path("data/processed/states_2023.parquet")

DRY_COMPOUNDS = {"SOFT", "MEDIUM", "HARD"}

RACE_STATE_MAP = {
    "clear":  "green",
    "yellow": "green",
    "sc":     "sc",
    "vsc":    "vsc",
}


def _bin_tyre_age(s: pd.Series) -> pd.Series:
    # 0-5→0, 6-10→1, 11-15→2, 16-20→3, 21-25→4, 26+→5
    return pd.cut(
        s,
        bins=[0, 5, 10, 15, 20, 25, float("inf")],
        labels=[0, 1, 2, 3, 4, 5],
        right=True,
        include_lowest=True,
    ).astype(int)


def _bin_position(s: pd.Series) -> pd.Series:
    # P1-3→0, P4-6→1, P7-10→2, P11-15→3, P16-20→4
    return pd.cut(
        s,
        bins=[0, 3, 6, 10, 15, 20],
        labels=[0, 1, 2, 3, 4],
        right=True,
        include_lowest=True,
    ).astype(int)


def _bin_gap(s: pd.Series) -> pd.Series:
    # cap at 10s, then <1→0, 1-3→1, 3-5→2, >5→3
    capped = s.clip(upper=10.0)
    return pd.cut(
        capped,
        bins=[0, 1, 3, 5, 10],
        labels=[0, 1, 2, 3],
        right=True,
        include_lowest=True,
    ).astype(int)


def _label_actions(df: pd.DataFrame) -> pd.DataFrame:
    """
    For each (round, driver) group sorted by lap_number:
      action = 1 if next lap's tyre_age < current lap's tyre_age (pit occurred).
    Last lap of each driver's race is dropped — no next-lap reference.
    Computed on the FULL dataset before compound filtering so lap continuity
    is preserved across compound changes (e.g. SOFT → INTERMEDIATE → HARD).
    """
    parts = []
    for _, group in df.groupby(["round", "driver"], sort=False):
        group = group.sort_values("lap_number").copy()
        next_age = group["tyre_age"].shift(-1)
        group["action"] = (next_age < group["tyre_age"]).astype(int)
        parts.append(group.iloc[:-1])
    return pd.concat(parts, ignore_index=True)


def main():
    df = pd.read_parquet(INPUT)

    # Label pit actions before filtering (preserves lap sequence across compounds)
    df = _label_actions(df)

    # Keep dry-compound laps only
    df = df[df["compound"].isin(DRY_COMPOUNDS)].copy()

    # Drop the 41 rows where position / gap are null (DNFs with missing timing)
    df = df.dropna(subset=["position", "gap_to_car_ahead_s"]).copy()

    # Encode discrete state dimensions
    df["tire_age_bin"] = _bin_tyre_age(df["tyre_age"])
    df["position_bin"] = _bin_position(df["position"])
    df["gap_bin"]      = _bin_gap(df["gap_to_car_ahead_s"])
    df["lap_number"]   = df["lap_number"].astype(int)
    df["race_state"]   = df["safety_car_status"].map(RACE_STATE_MAP)

    # State tuple as a pipe-delimited string for portable parquet storage;
    # parse back with: s.split("|") -> [lap_number, compound, tire_age_bin, ...]
    df["state_tuple"] = (
        df["lap_number"].astype(str)      + "|" +
        df["compound"]                    + "|" +
        df["tire_age_bin"].astype(str)    + "|" +
        df["position_bin"].astype(str)    + "|" +
        df["race_state"]                  + "|" +
        df["gap_bin"].astype(str)
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUTPUT, index=False)

    # --- Output ---
    STATE_COLS = [
        "lap_number", "compound", "tire_age_bin",
        "position_bin", "race_state", "gap_bin",
        "action", "state_tuple",
    ]

    print("=== Shape ===")
    print(df.shape)

    print("\n=== First 10 rows (state columns) ===")
    print(df[STATE_COLS].head(10).to_string(index=False))

    print("\n=== Action split ===")
    counts = df["action"].value_counts().sort_index()
    total  = len(df)
    for val, cnt in counts.items():
        label = "pitted" if val else "stayed out"
        print(f"  {val}  ({label}): {cnt:>6,}  ({cnt / total:.1%})")


if __name__ == "__main__":
    main()
