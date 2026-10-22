"""Talk dates and the fair random speaker draw."""
from __future__ import annotations

import random
from collections import Counter
from datetime import date, timedelta

EXCLUDED_MONTHS = {12, 1}  # no talks in December or January


def sa_public_holidays(year: int) -> dict:
    """South African public holidays (empty if the `holidays` package is missing)."""
    try:
        import holidays

        return dict(holidays.country_holidays("ZA", years=year))
    except Exception:
        return {}


def talk_mondays(year: int, start: date | None = None, skip_holidays: bool = True) -> list[date]:
    """Every Monday in `year` (Feb–Nov), optionally from `start` and skipping public holidays."""
    d = date(year, 1, 1)
    d += timedelta(days=(0 - d.weekday()) % 7)  # first Monday
    hols = sa_public_holidays(year) if skip_holidays else {}
    out = []
    while d.year == year:
        if d.month not in EXCLUDED_MONTHS and (start is None or d >= start) and d not in hols:
            out.append(d)
        d += timedelta(days=7)
    return out


def draw_speakers(
    names: list[str],
    n: int,
    past_counts: dict[str, int] | None = None,
    last_speaker: str | None = None,
    seed: int | str | None = None,
) -> list[str]:
    """Pick `n` speakers fairly at random.

    Nobody speaks twice until everyone has spoken once. The first round favours
    people with the fewest past talks, and nobody speaks two weeks in a row.
    """
    if not names:
        raise ValueError("No active speakers to choose from.")
    rng = random.Random(seed)
    past = Counter(past_counts or {})
    pool = sorted(names, key=lambda x: (past[x], rng.random()))
    result: list[str] = []
    prev = last_speaker
    while len(result) < n:
        if not pool:
            pool = list(names)
            rng.shuffle(pool)
        if len(pool) > 1 and pool[0] == prev:
            pool[0], pool[1] = pool[1], pool[0]
        prev = pool.pop(0)
        result.append(prev)
    return result
