"""
Pull lap-by-lap data for the 2023 F1 season using FastF1.

Output columns per lap:
  season, round, event_name, driver, lap_number,
  compound, tyre_age, position, gap_to_car_ahead_s, safety_car_status
"""

import warnings
import fastf1
import pandas as pd
from pathlib import Path

warnings.filterwarnings("ignore")

SEASON = 2023
CACHE_DIR = Path("data/cache")
OUTPUT_PATH = Path("data/processed") / f"laps_{SEASON}.parquet"

fastf1.Cache.enable_cache(str(CACHE_DIR))


# FastF1 TrackStatus is a string of single-digit codes present during the lap.
# "1"=clear  "2"=yellow  "4"=SC  "5"=red  "6"=VSC  "7"=VSC ending
def _track_status_label(status):
    s = str(status) if pd.notna(status) else ""
    if "4" in s:
        return "sc"
    if "6" in s or "7" in s:
        return "vsc"
    if "2" in s:
        return "yellow"
    return "clear"


def _gap_to_car_ahead(laps: pd.DataFrame) -> pd.Series:
    """
    For each driver/lap, return seconds behind the car directly ahead.
    Uses the session-elapsed Time at lap completion; leader gets 0.0.
    Lapped cars are handled naturally since their Time is simply larger.
    """
    gaps = pd.Series(index=laps.index, dtype=float)

    for lap_num, group in laps.groupby("LapNumber"):
        valid = group.dropna(subset=["Position", "Time"]).sort_values("Position")
        if valid.empty:
            continue

        times = valid["Time"].values  # numpy timedelta64 array
        positions = list(valid.index)

        for i, idx in enumerate(positions):
            if i == 0:
                gaps.at[idx] = 0.0
            else:
                delta = times[i] - times[i - 1]
                # Convert numpy timedelta64 -> seconds
                gaps.at[idx] = float(delta) / 1e9  # ns -> s

    return gaps


def process_race(year: int, round_number: int, event_name: str) -> pd.DataFrame:
    session = fastf1.get_session(year, round_number, "R")
    session.load(telemetry=False, weather=False, messages=False)

    laps = session.laps.copy()

    laps["gap_to_car_ahead_s"] = _gap_to_car_ahead(laps)
    laps["safety_car_status"] = laps["TrackStatus"].apply(_track_status_label)

    out = laps[[
        "Driver", "LapNumber", "Compound", "TyreLife",
        "Position", "gap_to_car_ahead_s", "safety_car_status", "LapTime",
    ]].copy()

    out["lap_time_s"] = out["LapTime"].dt.total_seconds()
    out.drop(columns=["LapTime"], inplace=True)

    out.rename(columns={
        "Driver": "driver",
        "LapNumber": "lap_number",
        "Compound": "compound",
        "TyreLife": "tyre_age",
        "Position": "position",
    }, inplace=True)

    out.insert(0, "season", year)
    out.insert(1, "round", round_number)
    out.insert(2, "event_name", event_name)

    return out.reset_index(drop=True)


def main():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    schedule = fastf1.get_event_schedule(SEASON, include_testing=False)
    total_rounds = len(schedule)

    all_laps = []
    failed = []

    for _, event in schedule.iterrows():
        round_num = int(event["RoundNumber"])
        event_name = event["EventName"]
        print(f"[{round_num:2d}/{total_rounds}] {event_name} ... ", end="", flush=True)
        try:
            df = process_race(SEASON, round_num, event_name)
            all_laps.append(df)
            print(f"{len(df)} laps")
        except Exception as exc:
            print(f"FAILED — {exc}")
            failed.append((round_num, event_name, str(exc)))

    if not all_laps:
        print("No data collected.")
        return

    combined = pd.concat(all_laps, ignore_index=True)
    combined.to_parquet(OUTPUT_PATH, index=False)
    print(f"\nSaved {len(combined):,} laps across {len(all_laps)} races -> {OUTPUT_PATH}")

    if failed:
        print(f"\nFailed rounds ({len(failed)}):")
        for r, name, err in failed:
            print(f"  Round {r} {name}: {err}")


if __name__ == "__main__":
    main()
