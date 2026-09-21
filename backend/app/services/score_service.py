from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.score import ScoreHistory
from app.models.user import User
from app.schemas.score import ScoreSubmit
from app.services.leaderboard_service import LeaderboardService

# Basic anti-tampering: reject implausible jumps. Configurable ceiling.
MAX_SINGLE_SCORE = 1_000_000_000
MAX_SCORE_DELTA_MULTIPLIER = 50  # a new score can't be > 50x the user's previous best for a game


class ScoreValidationError(Exception):
    pass


async def get_previous_best(db: AsyncSession, user_id, game_id: str) -> int | None:
    result = await db.execute(
        select(ScoreHistory.score)
        .where(ScoreHistory.user_id == user_id, ScoreHistory.game_id == game_id)
        .order_by(ScoreHistory.score.desc())
        .limit(1)
    )
    row = result.scalar_one_or_none()
    return row


def validate_score_bounds(score: int, previous_best: int | None) -> None:
    if score < 0 or score > MAX_SINGLE_SCORE:
        raise ScoreValidationError("Score is out of allowed bounds")
    if previous_best and previous_best > 0:
        if score > previous_best * MAX_SCORE_DELTA_MULTIPLIER:
            raise ScoreValidationError(
                "Score increase is implausibly large; flagged for anti-tampering review"
            )


async def submit_score(
    db: AsyncSession,
    redis_service: LeaderboardService,
    user: User,
    payload: ScoreSubmit,
) -> dict:
    previous_best = await get_previous_best(db, user.id, payload.game_id)
    validate_score_bounds(payload.score, previous_best)

    rule = settings.SCORE_UPDATE_RULE

    # Decide whether to persist a new history row based on the rule.
    should_persist = True
    if rule == "higher_only" and previous_best is not None and payload.score <= previous_best:
        should_persist = False

    score_row = None
    if should_persist:
        score_row = ScoreHistory(
            user_id=user.id,
            game_id=payload.game_id,
            score=payload.score,
        )
        db.add(score_row)
        await db.commit()
        await db.refresh(score_row)

    # Always sync Redis meta so leaderboard shows a username even before first score
    await redis_service.cache_user_meta(str(user.id), user.username)

    if should_persist or rule != "higher_only":
        rank_info = await redis_service.apply_score(
            user_id=str(user.id),
            game_id=payload.game_id,
            score=payload.score,
            rule=rule,
            when=datetime.now(timezone.utc),
        )
    else:
        # No DB write, but still report current standing without mutating Redis
        rank_info = {}
        from app.services.leaderboard_service import GLOBAL_KEY, game_key

        g_rank, _ = await redis_service.get_user_rank(GLOBAL_KEY, str(user.id))
        gm_rank, _ = await redis_service.get_user_rank(game_key(payload.game_id), str(user.id))
        rank_info = {
            "global_rank": g_rank,
            "game_rank": gm_rank,
            "daily_rank": None,
            "weekly_rank": None,
        }

    return {
        "accepted": should_persist,
        "reason": "stored" if should_persist else f"rejected by rule '{rule}': score not higher than previous best ({previous_best})",
        "score": score_row,
        **rank_info,
    }
