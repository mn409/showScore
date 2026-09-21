from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user
from app.core.limiter import limiter
from app.db.redis_client import get_redis
from app.db.session import get_db
from app.models.score import ScoreHistory
from app.models.user import User
from app.schemas.score import ScoreOut, ScoreSubmit, ScoreSubmitResponse
from app.services.leaderboard_service import LeaderboardService
from app.services.score_service import ScoreValidationError, submit_score

router = APIRouter(prefix="/api/scores", tags=["scores"])


@router.post("/submit", response_model=ScoreSubmitResponse)
@limiter.limit(settings.SCORE_SUBMIT_RATE_LIMIT)
async def submit(
    request: Request,
    payload: ScoreSubmit,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    redis = await get_redis()
    service = LeaderboardService(redis)
    try:
        result = await submit_score(db, service, user, payload)
    except ScoreValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    return result


@router.get("/history", response_model=list[ScoreOut])
async def my_history(
    game_id: str | None = None,
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    limit = max(1, min(limit, 200))
    query = select(ScoreHistory).where(ScoreHistory.user_id == user.id)
    if game_id:
        query = query.where(ScoreHistory.game_id == game_id)
    query = query.order_by(ScoreHistory.created_at.desc()).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
