from __future__ import annotations

import re
from datetime import datetime

import requests

from .config import FOTMOB_BASE_URL, OSLO_TIMEZONE
from .models import LeagueRoundData, MatchRow, StandingRow


class FotMobClient:
    TEAM_NAME_OVERRIDES = {
        "Odds Ballklubb": "Odd",
    }

    def __init__(self, timeout_seconds: int = 20) -> None:
        self._session = requests.Session()
        self._timeout_seconds = timeout_seconds
        self._venue_cache: dict[int, str] = {}

    def get_round_data(
        self,
        league_id: int,
        league_name: str,
        season: str | None = None,
        round_override: int | None = None,
    ) -> LeagueRoundData:
        payload = self._get_league_payload(league_id=league_id, season=season)
        standings = self._parse_standings(payload=payload)
        matches, round_name = self._parse_next_round_matches(payload=payload, round_override=round_override)
        season_name = payload.get("details", {}).get("selectedSeason") or payload.get("details", {}).get("latestSeason") or ""

        return LeagueRoundData(
            league_name=league_name,
            season=season_name,
            round_name=round_name,
            standings=standings,
            matches=matches,
        )

    def _get_league_payload(self, league_id: int, season: str | None = None) -> dict:
        params = {"id": str(league_id)}
        if season:
            params["season"] = season

        response = self._session.get(
            f"{FOTMOB_BASE_URL}/api/leagues",
            params=params,
            timeout=self._timeout_seconds,
        )
        response.raise_for_status()
        return response.json()

    def _parse_standings(self, payload: dict) -> list[StandingRow]:
        table_container = payload.get("table", [])
        if not table_container:
            return []

        rows = table_container[0].get("data", {}).get("table", {}).get("all", [])
        if not rows:
            return []

        standings: list[StandingRow] = []
        for row in rows:
            goals_for, goals_against = self._parse_scores_string(row.get("scoresStr", "0-0"))
            standings.append(
                StandingRow(
                    position=int(row.get("idx", 0)),
                    team=self._normalize_team_name(str(row.get("name", ""))),
                    played=int(row.get("played", 0)),
                    wins=int(row.get("wins", 0)),
                    draws=int(row.get("draws", 0)),
                    losses=int(row.get("losses", 0)),
                    goals_for=goals_for,
                    goals_against=goals_against,
                    goal_diff=int(row.get("goalConDiff", 0)),
                    points=int(row.get("pts", 0)),
                )
            )
        return standings

    def _parse_next_round_matches(
        self,
        payload: dict,
        round_override: int | None = None,
    ) -> tuple[list[MatchRow], int | str]:
        fixtures = payload.get("fixtures", {})
        all_matches = fixtures.get("allMatches", [])
        if not all_matches:
            raise ValueError("Fant ingen kamper i ligaresponsen.")

        target_round: int | str | None = round_override

        if target_round is None:
            first_unplayed = fixtures.get("firstUnplayedMatch")
            anchor_match = None

            if first_unplayed and first_unplayed.get("firstUnplayedMatchId"):
                first_id = str(first_unplayed["firstUnplayedMatchId"])
                anchor_match = next((m for m in all_matches if str(m.get("id")) == first_id), None)

            if anchor_match is None:
                anchor_match = next((m for m in all_matches if not bool(m.get("status", {}).get("finished", False))), None)

            if anchor_match is not None:
                target_round = anchor_match.get("roundName", anchor_match.get("round", ""))
            else:
                active_round = (
                    fixtures.get("fixtureInfo", {})
                    .get("activeRound", {})
                    .get("roundId")
                )
                if active_round is None:
                    raise ValueError("Fant ingen kommende kamp eller aktiv runde i denne sesongen.")
                target_round = active_round

        round_matches = [
            m
            for m in all_matches
            if str(m.get("roundName", m.get("round", ""))) == str(target_round)
        ]

        round_matches.sort(key=lambda m: m.get("status", {}).get("utcTime", ""))

        parsed_matches: list[MatchRow] = []
        for raw_match in round_matches:
            status = raw_match.get("status", {})
            utc_time = status.get("utcTime")
            if not utc_time:
                continue

            kickoff_utc = self._parse_utc_datetime(utc_time)
            marker = self._match_marker(status=status, kickoff_utc=kickoff_utc)
            is_finished = bool(status.get("finished", False))
            home = raw_match.get("home", {})
            away = raw_match.get("away", {})
            home_id = int(home.get("id", 0))
            match_id = str(raw_match.get("id", ""))
            venue = self._get_home_venue_name(team_id=home_id)

            page_url = raw_match.get("pageUrl", "")
            match_url = f"{FOTMOB_BASE_URL}{page_url}" if page_url.startswith("/") else page_url
            if not match_url:
                match_url = f"{FOTMOB_BASE_URL}/match/{match_id}"

            parsed_matches.append(
                MatchRow(
                    match_id=match_id,
                    round_name=target_round,
                    kickoff_utc=kickoff_utc,
                    home_team=self._normalize_team_name(str(home.get("name", ""))),
                    home_team_id=home_id,
                    away_team=self._normalize_team_name(str(away.get("name", ""))),
                    marker=marker,
                    is_finished=is_finished,
                    venue=venue,
                    match_url=match_url,
                )
            )

        if not parsed_matches:
            raise ValueError("Fant ikke gyldige kamper i neste runde.")

        return parsed_matches, target_round

    def _get_home_venue_name(self, team_id: int) -> str:
        if team_id in self._venue_cache:
            return self._venue_cache[team_id]

        if team_id == 0:
            return "-"

        response = self._session.get(
            f"{FOTMOB_BASE_URL}/api/teams",
            params={"id": str(team_id)},
            timeout=self._timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        venue_name = (
            payload.get("overview", {})
            .get("venue", {})
            .get("widget", {})
            .get("name")
        )
        parsed_name = str(venue_name).strip() if venue_name else "-"
        self._venue_cache[team_id] = parsed_name
        return parsed_name

    @staticmethod
    def _parse_scores_string(scores: str) -> tuple[int, int]:
        match = re.split(r"\s*-\s*", scores.strip(), maxsplit=1)
        if len(match) != 2:
            return 0, 0
        try:
            return int(match[0]), int(match[1])
        except ValueError:
            return 0, 0

    @staticmethod
    def _parse_utc_datetime(value: str) -> datetime:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    @staticmethod
    def _normalize_team_name(name: str) -> str:
        normalized_name = FotMobClient.TEAM_NAME_OVERRIDES.get(name, name)
        if normalized_name.endswith(" (W)"):
            return normalized_name[:-4]
        return normalized_name

    @staticmethod
    def _match_marker(status: dict, kickoff_utc: datetime) -> str:
        if bool(status.get("finished", False)):
            raw_score = str(status.get("scoreStr", "")).strip()
            if raw_score:
                return raw_score.replace(" ", "")
        return kickoff_utc.astimezone(OSLO_TIMEZONE).strftime("%H:%M")
