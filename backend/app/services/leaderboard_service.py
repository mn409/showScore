"""
Redis sorted-set backed ranking engine.

Key design:
  leaderboard:global                -> all-time global scores
  leaderboard:game:{game_id}        -> all-time per-game scores
  leaderboard:daily:{YYYY-MM-DD}    -> per-day scores (all games)
  leaderboard:weekly:{YYYY-Www}     -> per ISO-week scores (all games)

Each sorted set member is the user's UUID (string). We keep a side hash
  user:meta:{user_id} -> {"username": ...}
so we can render leaderboards without hitting Postgres for every row.
"""

from datetime import date, datetime, timezone

import redis.asyncio as aioredis

GLOBAL_KEY = "leaderboard:global"


def game_key(game_id: str) -> str:
    return f"leaderboard:game:{game_id}"


def daily_key(d: date) -> str:
    return f"leaderboard:daily:{d.isoformat()}"


def weekly_key(d: date) -> str:
    iso_year, iso_week, _ = d.isocalendar()
    return f"leaderboard:weekly:{iso_year}-W{iso_week:02d}"


def user_meta_key(user_id: str) -> str:
    return f"user:meta:{user_id}"


class LeaderboardService:
    def __init__(self, redis: aioredis.Redis):
        self.redis = redis

    async def cache_user_meta(self, user_id: str, username: str) -> None:
        await self.redis.hset(user_meta_key(user_id), mapping={"username": username})

    async def get_username(self, user_id: str) -> str:
        val = await self.redis.hget(user_meta_key(user_id), "username")
        return val or "unknown"

    async def apply_score(
        self,
        user_id: str,
        game_id: str,
        score: int,
        rule: str = "higher_only",
        when: datetime | None = None,
    ) -> dict:
        """
        Update all relevant sorted sets according to the configured rule.
        rule: higher_only | always_overwrite | sum
        Returns dict with the new ranks (0-indexed converted to 1-indexed).
        """
        when = when or datetime.now(timezone.utc)
        d = when.date()

        keys = [GLOBAL_KEY, game_key(game_id), daily_key(d), weekly_key(d)]

        pipe = self.redis.pipeline()
        for key in keys:
            if rule == "always_overwrite":
                pipe.zadd(key, {user_id: score})
            elif rule == "sum":
                pipe.zincrby(key, score, user_id)
            else:  # higher_only (default) - use ZADD GT so it only updates if score is higher
                pipe.zadd(key, {user_id: score}, gt=True)
            # ensure a floor entry exists even if GT rejected the update
            pipe.zscore(key, user_id)
        results = await pipe.execute()

        # results alternate [zadd_result, zscore_result, ...]
        scores = results[1::2]

        ranks = {}
        rank_pipe = self.redis.pipeline()
        for key in keys:
            rank_pipe.zrevrank(key, user_id)
        rank_results = await rank_pipe.execute()

        for key, r in zip(keys, rank_results):
            ranks[key] = (r + 1) if r is not None else None

        return {
            "global_rank": ranks[GLOBAL_KEY],
            "game_rank": ranks[game_key(game_id)],
            "daily_rank": ranks[daily_key(d)],
            "weekly_rank": ranks[weekly_key(d)],
            "global_score": scores[0],
            "game_score": scores[1],
        }

    async def get_top_n(self, key: str, n: int = 10, offset: int = 0) -> list[dict]:
        raw = await self.redis.zrevrange(key, offset, offset + n - 1, withscores=True)
        entries = []
        for idx, (user_id, score) in enumerate(raw, start=offset + 1):
            username = await self.get_username(user_id)
            entries.append(
                {"rank": idx, "user_id": user_id, "username": username, "score": score}
            )
        return entries

    async def get_total_entries(self, key: str) -> int:
        return await self.redis.zcard(key)

    async def get_user_rank(self, key: str, user_id: str) -> tuple[int | None, float | None]:
        pipe = self.redis.pipeline()
        pipe.zrevrank(key, user_id)
        pipe.zscore(key, user_id)
        rank, score = await pipe.execute()
        return (rank + 1 if rank is not None else None), score

    def resolve_key(self, scope: str, game_id: str | None = None, on: date | None = None) -> str:
        on = on or datetime.now(timezone.utc).date()
        if scope == "global":
            return GLOBAL_KEY
        if scope == "game":
            if not game_id:
                raise ValueError("game_id is required for 'game' scope")
            return game_key(game_id)
        if scope == "daily":
            return daily_key(on)
        if scope == "weekly":
            return weekly_key(on)
        raise ValueError(f"Unknown scope: {scope}")
