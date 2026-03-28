from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT_DIR = Path(__file__).resolve().parent.parent
CACHE_PATH = ROOT_DIR / "data" / "cache.json"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from norskfotballbot.config import DEFAULT_LEAGUES, FOTMOB_BASE_URL


def fetch_json(session: requests.Session, path: str, params: dict[str, str]) -> dict:
    response = session.get(
        f"{FOTMOB_BASE_URL}{path}",
        params=params,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def collect_team_ids(league_payload: dict) -> set[int]:
    fixtures = league_payload.get("fixtures", {})
    all_matches = fixtures.get("allMatches", [])
    fixture_teams = fixtures.get("fixtureInfo", {}).get("teams", [])

    team_ids: set[int] = set()

    for team in fixture_teams:
        team_id = int(team.get("id", 0))
        if team_id:
            team_ids.add(team_id)

    for match in all_matches:
        home_id = int(match.get("home", {}).get("id", 0))
        away_id = int(match.get("away", {}).get("id", 0))
        if home_id:
            team_ids.add(home_id)
        if away_id:
            team_ids.add(away_id)

    return team_ids


def extract_venue_name(team_payload: dict) -> str:
    venue_name = (
        team_payload.get("overview", {})
        .get("venue", {})
        .get("widget", {})
        .get("name")
    )
    return str(venue_name).strip() if venue_name else "-"


def build_cache() -> dict:
    session = requests.Session()

    league_payloads: dict[str, dict] = {}
    team_ids: set[int] = set()

    for league in DEFAULT_LEAGUES:
        payload = fetch_json(session, "/api/leagues", {"id": str(league.league_id)})
        league_payloads[str(league.league_id)] = payload
        team_ids.update(collect_team_ids(payload))

    venues: dict[str, str] = {}
    for team_id in sorted(team_ids):
        team_payload = fetch_json(session, "/api/teams", {"id": str(team_id)})
        venues[str(team_id)] = extract_venue_name(team_payload)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "fotmob",
        "leagues": league_payloads,
        "venues": venues,
    }


def main() -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    cache = build_cache()
    CACHE_PATH.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Skrev cache til {CACHE_PATH}")


if __name__ == "__main__":
    main()
