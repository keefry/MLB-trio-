"""
Find the trio of MLB batters who all homered on the same day the most times
in the 2026 season. Uses the free MLB Stats API.
"""

import requests
import time
from itertools import combinations
from collections import defaultdict

BASE = "https://statsapi.mlb.com/api/v1"

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


def main():
    print("Fetching 2026 schedule…")
    games_by_date = get_schedule()
    total_dates = len(games_by_date)
    total_games = sum(len(v) for v in games_by_date.values())
    print(f"  {total_dates} game-days, {total_games} completed games\n")

    # date -> set of players who homered that day
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
            time.sleep(0.05)   # ~20 req/s — polite but fast

    print(f"\nDone fetching. Building trio counts…\n")

    # Count every 3-player combination across all days
    trio_counts = defaultdict(int)
    trio_dates  = defaultdict(list)

    for date_str, players in sorted(hr_by_date.items()):
        player_list = sorted(players)
        for trio in combinations(player_list, 3):
            trio_counts[trio] += 1
            trio_dates[trio].append(date_str)

    # Sort by count descending
    ranked = sorted(trio_counts.items(), key=lambda x: -x[1])

    print("=" * 60)
    print("TOP 20 TRIOS — players who all homered on the same day")
    print("=" * 60)
    for rank, (trio, count) in enumerate(ranked[:20], 1):
        names = " / ".join(trio)
        dates = ", ".join(trio_dates[trio])
        print(f"\n#{rank}  {names}")
        print(f"     {count} shared HR day(s): {dates}")

    if ranked:
        best_trio, best_count = ranked[0]
        print("\n" + "=" * 60)
        print(f"ANSWER: {' / '.join(best_trio)}")
        print(f"All three homered on the same day {best_count} time(s).")
        print("=" * 60)
    else:
        print("No trio found — check date range or API response.")


if __name__ == "__main__":
    main()
