from __future__ import annotations

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv

from .config import DEFAULT_LEAGUES
from .fotmob_client import FotMobClient
from .reddit_client import RedditPoster
from .round_thread import build_post_body, build_post_title


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lag rundetrad for Eliteserien, OBOS-ligaen og Norgesmesterskapet, og post til Reddit pa kommando."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    preview_cmd = subparsers.add_parser("preview", help="Vis generert rundetrad i terminal.")
    preview_cmd.add_argument("--season", help="Overstyr sesong, f.eks. 2026 eller 2025/2026.")
    preview_cmd.add_argument("--round", type=int, help="Overstyr runde, f.eks. 5.")
    preview_cmd.add_argument("--title", help="Overstyr post-tittel.")
    preview_cmd.add_argument("--save", help="Lagre output til fil.")

    post_cmd = subparsers.add_parser("post", help="Post generert rundetrad til Reddit.")
    post_cmd.add_argument("--season", help="Overstyr sesong, f.eks. 2026 eller 2025/2026.")
    post_cmd.add_argument("--round", type=int, help="Overstyr runde, f.eks. 5.")
    post_cmd.add_argument("--title", help="Overstyr post-tittel.")
    post_cmd.add_argument(
        "--subreddit",
        default=os.getenv("REDDIT_SUBREDDIT"),
        help="Subreddit-navn. Leser REDDIT_SUBREDDIT hvis ikke oppgitt.",
    )

    return parser.parse_args()


def main() -> None:
    load_dotenv()
    args = parse_args()

    if args.round is not None:
        invalid_leagues = [league for league in DEFAULT_LEAGUES if args.round > league.max_round]
        if invalid_leagues:
            details = ", ".join(f"{league.display_name} (1-{league.max_round})" for league in invalid_leagues)
            raise ValueError(f"Ugyldig runde {args.round} for: {details}.")

    client = FotMobClient()
    rounds = [
        client.get_round_data(
            league_id=league.league_id,
            league_name=league.display_name,
            season=args.season,
            round_override=args.round,
        )
        for league in DEFAULT_LEAGUES
    ]

    title = args.title or build_post_title(rounds)
    body = build_post_body(rounds)

    if args.command == "preview":
        print(title)
        print("")
        print(body)
        if args.save:
            output_path = Path(args.save)
            output_path.write_text(f"{title}\n\n{body}\n", encoding="utf-8")
            print("")
            print(f"Lagret i {output_path}")
        return

    if args.command == "post":
        if not args.subreddit:
            raise ValueError("Mangler subreddit. Oppgi --subreddit eller sett REDDIT_SUBREDDIT i .env.")
        poster = RedditPoster()
        post_url = poster.submit_post(subreddit_name=args.subreddit, title=title, body=body)
        print(f"Publisert: {post_url}")
        return

    raise ValueError("Ukjent kommando.")


if __name__ == "__main__":
    main()
