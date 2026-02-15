from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class StandingRow:
    position: int
    team: str
    played: int
    wins: int
    draws: int
    losses: int
    goals_for: int
    goals_against: int
    goal_diff: int
    points: int


@dataclass(frozen=True)
class MatchRow:
    match_id: str
    round_name: int | str
    kickoff_utc: datetime
    home_team: str
    home_team_id: int
    away_team: str
    marker: str
    is_finished: bool
    venue: str
    match_url: str


@dataclass(frozen=True)
class LeagueRoundData:
    league_name: str
    season: str
    round_name: int | str
    standings: list[StandingRow]
    matches: list[MatchRow]

