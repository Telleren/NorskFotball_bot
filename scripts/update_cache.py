from __future__ import annotations

import html
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT_DIR = Path(__file__).resolve().parent.parent
CACHE_PATH = ROOT_DIR / "data" / "cache.json"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from norskfotballbot.config import DEFAULT_LEAGUES, FOTMOB_BASE_URL


REQUEST_HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "accept-language": "en-US,en;q=0.9,nb;q=0.8",
    "referer": f"{FOTMOB_BASE_URL}/",
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/134.0.0.0 Safari/537.36"
    ),
}
NEXT_DATA_PATTERN = re.compile(
    r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>'
)


def fetch_html(session: requests.Session, target_url: str) -> str:
    response = session.get(
        target_url,
        headers=REQUEST_HEADERS,
        timeout=30,
    )
    response.raise_for_status()
    return response.text


def parse_next_data(page_html: str) -> dict:
    match = NEXT_DATA_PATTERN.search(page_html)
    if not match:
        raise ValueError("Fant ikke __NEXT_DATA__ i HTML-responsen.")
    return json.loads(html.unescape(match.group(1)))


def fetch_league_payload(session: requests.Session, league_id: int) -> dict:
    page_html = fetch_html(session, f"{FOTMOB_BASE_URL}/leagues/{league_id}/overview")
    next_data = parse_next_data(page_html)
    page_props = next_data.get("props", {}).get("pageProps", {})
    if not page_props.get("fixtures"):
        raise ValueError(f"Fant ikke ligadata for league_id={league_id}.")
    return page_props


def fetch_team_payload(session: requests.Session, team_id: int) -> dict:
    page_html = fetch_html(session, f"{FOTMOB_BASE_URL}/teams/{team_id}/overview")
    next_data = parse_next_data(page_html)
    page_props = next_data.get("props", {}).get("pageProps", {})

    if page_props.get("details") and page_props.get("overview"):
        return page_props

    fallback = page_props.get("fallback", {})
    fallback_key = f"team-{team_id}"
    if fallback_key not in fallback:
        raise ValueError(f"Fant ikke lagdata for team_id={team_id}.")
    return fallback[fallback_key]


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
    venue = team_payload.get("overview", {}).get("venue") or {}
    venue_name = venue.get("widget", {}).get("name")
    return str(venue_name).strip() if venue_name else "-"


def build_cache() -> dict:
    session = requests.Session()
    session.trust_env = False

    league_payloads: dict[str, dict] = {}
    team_ids: set[int] = set()

    for league in DEFAULT_LEAGUES:
        payload = fetch_league_payload(session, league.league_id)
        league_payloads[str(league.league_id)] = payload
        team_ids.update(collect_team_ids(payload))

    venues: dict[str, str] = {}
    for team_id in sorted(team_ids):
        team_payload = fetch_team_payload(session, team_id)
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
