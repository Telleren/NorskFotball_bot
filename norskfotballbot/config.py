from dataclasses import dataclass
from zoneinfo import ZoneInfo


OSLO_TIMEZONE = ZoneInfo("Europe/Oslo")
FOTMOB_BASE_URL = "https://www.fotmob.com"


@dataclass(frozen=True)
class LeagueConfig:
    league_id: int
    display_name: str
    max_round: int = 30


DEFAULT_LEAGUES = [
    LeagueConfig(league_id=59, display_name="Eliteserien"),
    LeagueConfig(league_id=203, display_name="OBOS-ligaen"),
    LeagueConfig(league_id=331, display_name="Toppserien", max_round=22),
    LeagueConfig(league_id=206, display_name="Norgesmesterskapet", max_round=7),
]
