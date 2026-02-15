from __future__ import annotations

from datetime import datetime

from .config import OSLO_TIMEZONE
from .models import LeagueRoundData, StandingRow


def build_post_title(rounds: list[LeagueRoundData]) -> str:
    if not rounds:
        return "Rundetrad"

    round_bits = [f"{r.league_name} runde {r.round_name}" for r in rounds]
    start, end = _date_range(rounds)
    if start.date() == end.date():
        date_part = start.strftime("%d.%m.%Y")
    else:
        date_part = f"{start.strftime('%d.%m')} - {end.strftime('%d.%m.%Y')}"
    return f"Rundetrad: {' og '.join(round_bits)} ({date_part})"


def build_post_body(rounds: list[LeagueRoundData]) -> str:
    lines: list[str] = []
    for index, league_round in enumerate(rounds):
        if league_round.standings:
            lines.append(f"#Tabell før runden ({league_round.league_name})")
            lines.extend(_render_standings_table(league_round.standings))
            lines.append("")
        lines.append(f"#Rundens kamper ({league_round.league_name}, runde {league_round.round_name})")
        lines.append("Dato|Hjemmelag||Bortelag|Stadion")
        lines.append("---|----|:----:|----|----")

        for match in league_round.matches:
            local_dt = match.kickoff_utc.astimezone(OSLO_TIMEZONE)
            date_part = local_dt.strftime("%d.%m.%Y")
            marker = f"[{match.marker}]({match.match_url})" if match.match_url else match.marker
            lines.append(f"{date_part}|{match.home_team}|{marker}|{match.away_team}|{match.venue}")

        if index < len(rounds) - 1:
            lines.append("")
            lines.append("---")
            lines.append("")

    return "\n".join(lines).strip()


def _render_standings_table(rows: list[StandingRow]) -> list[str]:
    output = [
        "Nr | Lag | K | S | U | T | + | - | +/- | P |",
        "---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        diff = f"{row.goal_diff:+d}"
        output.append(
            f"{row.position}.|{row.team}|{row.played}|{row.wins}|{row.draws}|{row.losses}|"
            f"{row.goals_for}|{row.goals_against}|{diff}|{row.points}|"
        )
    return output


def _date_range(rounds: list[LeagueRoundData]) -> tuple[datetime, datetime]:
    kickoff_times = [
        match.kickoff_utc.astimezone(OSLO_TIMEZONE)
        for league_round in rounds
        for match in league_round.matches
    ]
    if not kickoff_times:
        now = datetime.now(tz=OSLO_TIMEZONE)
        return now, now
    return min(kickoff_times), max(kickoff_times)
