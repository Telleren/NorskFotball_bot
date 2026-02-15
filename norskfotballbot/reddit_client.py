from __future__ import annotations

import os

import praw


class RedditPoster:
    def __init__(self) -> None:
        self._reddit = praw.Reddit(
            client_id=_require_env("REDDIT_CLIENT_ID"),
            client_secret=_require_env("REDDIT_CLIENT_SECRET"),
            username=_require_env("REDDIT_USERNAME"),
            password=_require_env("REDDIT_PASSWORD"),
            user_agent=_require_env("REDDIT_USER_AGENT"),
        )

    def submit_post(self, subreddit_name: str, title: str, body: str) -> str:
        submission = self._reddit.subreddit(subreddit_name).submit(title=title, selftext=body)
        return submission.url


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Mangler miljoverdi: {name}")
    return value

