"""
Find MLB batter combinations (pairs, trios, quads) who all homered on the
same day the most times in the 2026 season. Uses the free MLB Stats API.
"""

import requests
import time
from itertools import combinations
from collections import defaultdict

BASE = "https://statsapi.mlb.com/api/v1"
TOP_N = 20


def get_schedule():
    """Return {date_str: [gamePk, ...]} for all final regular-season games."""
    url = f"{BASE}/schedule"
    params = {
        "sportId": 1,
        "gameType": "R",
        "startDate": "2026-03-26",
        "endDate": "2026-06-05",
        "fields": "dates,date,games,gamePk,status,codedGameState",
    }
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()

    games_by_date = {}
    for d in data.get("dates", []):
        pks = [
            g["gamePk"]
            for g in d.get("games", [])
            if g["status"]["codedGameState"] == "F"
        ]
        if pks:
            games_by_date[d["date"]] = pks

    return games_by_date


def get_hr_hitters(game_pk):
    """Return list of player names who hit >=1 HR in this game."""
    url = f"https://statsapi.mlb.com/api/v1/game/{game_pk}/boxscore"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    data = r.json()

    hitters = []
    for side in ("home", "away"):
        players = data.get("teams", {}).get(side, {}).get("players", {})
        for player_data in players.values():
            batting = player_data.get("stats", {}).get("batting", {})
            if batting.get("homeRuns", 0) >= 1:
                hitters.append(player_data["person"]["fullName"])
    return hitters


def build_combo_counts(hr_by_date, size):
    """Count every `size`-player combination that all homered on the same day."""
    counts = defaultdict(int)
    dates  = defaultdict(list)
    for date_str, players in sorted(hr_by_date.items()):
        for combo in combinations(sorted(players), size):
            counts[combo] += 1
            dates[combo].append(date_str)
    return counts, dates


def print_table(title, ranked, dates_map, top=TOP_N):
    col_combo  = max(len(" / ".join(c)) for c, _ in ranked[:top]) + 2
    col_combo  = max(col_combo, len("Players"))
    col_count  = 6
    col_dates  = 60

    sep = f"+{'-'*(col_combo+2)}+{'-'*(col_count+2)}+{'-'*(col_dates+2)}+"
    hdr = f"| {'Players':<{col_combo}} | {'Days':>{col_count}} | {'Dates':<{col_dates}} |"

    print(f"\n{title}")
    print(sep)
    print(hdr)
    print(sep)
    for rank, (combo, count) in enumerate(ranked[:top], 1):
        names      = " / ".join(combo)
        dates_str  = ", ".join(dates_map[combo])
        # Wrap dates if too long
        if len(dates_str) > col_dates:
            dates_str = dates_str[:col_dates - 1] + "…"
        print(f"| {names:<{col_combo}} | {count:>{col_count}} | {dates_str:<{col_dates}} |")
    print(sep)


def main():
    print("Fetching 2026 schedule…")
    games_by_date = get_schedule()
    total_games = sum(len(v) for v in games_by_date.values())
    print(f"  {len(games_by_date)} game-days, {total_games} completed games\n")

    hr_by_date = defaultdict(set)
    processed = 0
    for date_str, pks in sorted(games_by_date.items()):
        for pk in pks:
            try:
                hitters = get_hr_hitters(pk)
                hr_by_date[date_str].update(hitters)
            except Exception as e:
                print(f"  WARNING: game {pk} on {date_str} failed: {e}")
            processed += 1
            if processed % 50 == 0:
                print(f"  …{processed}/{total_games} games fetched")
            time.sleep(0.05)

    print("\nDone fetching. Building combination counts…")

    for size, label in [(2, "PAIRS"), (3, "TRIOS"), (4, "QUADS")]:
        counts, dates_map = build_combo_counts(hr_by_date, size)
        ranked = sorted(counts.items(), key=lambda x: -x[1])
        title = f"TOP {TOP_N} {label} — all homered on the same day (2026 season)"
        print_table(title, ranked, dates_map)


if __name__ == "__main__":
    main()
