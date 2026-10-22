"""Read/write the speakers list and the talk schedule (CSV files in ./data)."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
SPEAKERS_CSV = DATA_DIR / "speakers.csv"
SCHEDULE_CSV = DATA_DIR / "schedule.csv"

SPEAKER_COLS = ["name", "email", "active"]
SCHEDULE_COLS = ["date", "speaker", "email", "status", "swapped_with", "event_id", "synced"]

# Statuses
SCHEDULED, CONFIRMED, SWAPPED, DONE = "Scheduled", "Confirmed", "Swapped", "Done"
STATUSES = [SCHEDULED, CONFIRMED, SWAPPED, DONE]
LOCKED = {CONFIRMED, SWAPPED, DONE}  # kept when a schedule is regenerated


def _to_bool(v) -> bool:
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() not in {"false", "0", "no", "n"}


def normalize_speakers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    if "name" not in df.columns:
        raise ValueError("The CSV needs a 'name' column.")
    if "email" not in df.columns:
        df["email"] = ""
    if "active" not in df.columns:
        df["active"] = True
    df["name"] = df["name"].fillna("").astype(str).str.strip()
    df["email"] = df["email"].fillna("").astype(str).str.strip()
    df["active"] = df["active"].fillna(True).apply(_to_bool)
    df = df[df["name"] != ""].drop_duplicates("name")
    return df[SPEAKER_COLS].reset_index(drop=True)


def load_speakers() -> pd.DataFrame:
    if not SPEAKERS_CSV.exists():
        return pd.DataFrame(columns=SPEAKER_COLS)
    return normalize_speakers(pd.read_csv(SPEAKERS_CSV, dtype=str))


def save_speakers(df: pd.DataFrame) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    normalize_speakers(df).to_csv(SPEAKERS_CSV, index=False)


def empty_schedule() -> pd.DataFrame:
    return pd.DataFrame(columns=SCHEDULE_COLS)


def load_schedule() -> pd.DataFrame:
    if not SCHEDULE_CSV.exists():
        return empty_schedule()
    df = pd.read_csv(SCHEDULE_CSV, dtype=str).fillna("")
    for c in SCHEDULE_COLS:
        if c not in df.columns:
            df[c] = ""
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df["synced"] = df["synced"].apply(lambda v: str(v).lower() == "true")
    return df[SCHEDULE_COLS].sort_values("date").reset_index(drop=True)


def save_schedule(df: pd.DataFrame) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    df = df[SCHEDULE_COLS].sort_values("date").reset_index(drop=True)
    df.to_csv(SCHEDULE_CSV, index=False)
