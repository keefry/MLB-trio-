"""
Check which top HR-combo players have games scheduled tomorrow (2026-06-06).
"""

import requests
from collections import defaultdict

BASE = "https://statsapi.mlb.com/api/v1"
TOMORROW = "2026-06-06"

# Top combos from find_trio.py output (name exactly as returned by API)
TOP_PAIRS = [
    ("Munetaka Murakami", "Yordan Alvarez"),
    ("Colson Montgomery", "Munetaka Murakami"),
    ("Dillon Dingler", "Kyle Schwarber"),
    ("James Wood", "Munetaka Murakami"),
    ("Jake Bauers", "Willy Adames"),
    ("Kyle Schwarber", "Yordan Alvarez"),
    ("Ben Rice", "Yandy Díaz"),
    ("Bryce Harper", "Matt Olson"),
    ("Casey Schmitt", "Willson Contreras"),
    ("Byron Buxton", "Pete Alonso"),
]
TOP_TRIOS = [
    ("James Wood", "Munetaka Murakami", "Yordan Alvarez"),
    ("Casey Schmitt", "Christian Walker", "Willson Contreras"),
    ("Colson Montgomery", "Drake Baldwin", "Munetaka Murakami"),
    ("Hunter Goodman", "Jake Bauers", "Willy Adames"),
    ("Hunter Goodman", "Oneil Cruz", "Pete Alonso"),
    ("Aaron Judge", "Bryce Harper", "Matt Olson"),
]
TOP_QUADS = [
    ("Dillon Dingler", "Kyle Schwarber", "Luke Raley", "Will Smith"),
    ("Jacob Young", "Kyle Schwarber", "Luke Raley", "Munetaka Murakami"),
    ("Corey Seager", "Elly De La Cruz", "Sal Stewart", "Shea Langeliers"),
    ("Hunter Goodman", "Jake Bauers", "Willy Adames", "Yordan Alvarez"),
    ("Hunter Goodman", "Oneil Cruz", "Pete Alonso", "Yordan Alvarez"),
    ("Aaron Judge", "Bryce Harper", "Kyle Tucker", "Matt Olson"),
]

ALL_PLAYERS = sorted({p for combo in TOP_PAIRS + TOP_TRIOS + TOP_QUADS for p in combo})


def get_tomorrow_teams():
    """Return set of teamIds playing tomorrow and a map teamId->teamName."""
    url = f"{BASE}/schedule"
    params = {"sportId": 1, "gameType": "R", "date": TOMORROW,
              "fields": "dates,games,teams,home,away,team,id,name"}
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()

    team_ids = set()
    id_to_name = {}
    matchups = []
    for d in data.get("dates", []):
        for g in d.get("games", []):
            home = g["teams"]["home"]["team"]
            away = g["teams"]["away"]["team"]
            team_ids.update([home["id"], away["id"]])
            id_to_name[home["id"]] = home["name"]
            id_to_name[away["id"]] = away["name"]
            matchups.append((away["name"], home["name"]))
    return team_ids, id_to_name, matchups


def get_team_names():
    """Return {teamId: teamName} for all MLB teams."""
    r = requests.get(f"{BASE}/teams", params={"sportId": 1}, timeout=20)
    r.raise_for_status()
    return {t["id"]: t["name"] for t in r.json().get("teams", [])}


def get_player_teams(team_names):
    """Return {fullName: (teamId, teamName)} for all active 2026 players."""
    url = f"{BASE}/sports/1/players"
    r = requests.get(url, params={"season": 2026}, timeout=30)
    r.raise_for_status()

    result = {}
    for p in r.json().get("people", []):
        name = p.get("fullName", "")
        tid = p.get("currentTeam", {}).get("id")
        if tid:
            result[name] = (tid, team_names.get(tid, f"Team {tid}"))
    return result


def check_combo(combo, player_team_map, playing_team_ids):
    """Return list of (name, team, playing?) for each player in combo."""
    rows = []
    for name in combo:
        info = player_team_map.get(name)
        if info:
            tid, tname = info
            playing = tid in playing_team_ids
        else:
            tname, playing = "Unknown", False
        rows.append((name, tname, playing))
    return rows


def print_combo_check(label, combos, player_team_map, playing_team_ids):
    print(f"\n{'='*70}")
    print(f"  {label}")
    print(f"{'='*70}")
    for combo in combos:
        rows = check_combo(combo, player_team_map, playing_team_ids)
        all_playing = all(r[2] for r in rows)
        status = "ALL PLAYING ✓" if all_playing else "NOT all playing"
        print(f"\n  [{status}]  {' / '.join(combo)}")
        for name, team, playing in rows:
            flag = "plays" if playing else "OFF  "
            print(f"    {flag}  {name:<25} ({team})")


def main():
    print(f"Checking schedule for {TOMORROW}…")
    playing_ids, id_to_name, matchups = get_tomorrow_teams()
    print(f"  {len(matchups)} games scheduled:")
    for away, home in matchups:
        print(f"    {away} @ {home}")

    print(f"\nLooking up {len(ALL_PLAYERS)} players' current teams…")
    team_names = get_team_names()
    player_team_map = get_player_teams(team_names)

    print_combo_check("TOP PAIRS",  TOP_PAIRS,  player_team_map, playing_ids)
    print_combo_check("TOP TRIOS",  TOP_TRIOS,  player_team_map, playing_ids)
    print_combo_check("TOP QUADS",  TOP_QUADS,  player_team_map, playing_ids)


if __name__ == "__main__":
    main()
