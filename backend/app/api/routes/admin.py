from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin
from app.db.redis_client import get_redis
from app.db.session import get_db
from app.schemas.admin import (
    ActivityTrendResponse,
    HealthMetrics,
    SystemStats,
    TopPlayer,
    TopPlayersResponse,
)
from app.services.admin_service import get_activity_trend, get_system_stats
from app.services.leaderboard_service import LeaderboardService
from app.core.config import settings

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/stats", response_model=SystemStats, dependencies=[Depends(get_current_admin)])
async def system_stats(db: AsyncSession = Depends(get_db)):
    return await get_system_stats(db)


@router.get(
    "/analytics/trend", response_model=ActivityTrendResponse, dependencies=[Depends(get_current_admin)]
)
async def activity_trend(days: int = Query(14, ge=1, le=90), db: AsyncSession = Depends(get_db)):
    trend = await get_activity_trend(db, days=days)
    return ActivityTrendResponse(days=days, trend=trend)


@router.get(
    "/analytics/top-players",
    response_model=TopPlayersResponse,
    dependencies=[Depends(get_current_admin)],
)
async def top_players(
    scope: str = Query("daily", pattern="^(daily|weekly|global)$"),
    on: date | None = None,
    top: int = Query(10, ge=1, le=100),
):
    redis = await get_redis()
    service = LeaderboardService(redis)
    key = service.resolve_key(scope, on=on)
    entries = await service.get_top_n(key, n=top)
    return TopPlayersResponse(scope=scope, players=[TopPlayer(**e) for e in entries])


@router.get("/health", response_model=HealthMetrics, dependencies=[Depends(get_current_admin)])
async def health_metrics(db: AsyncSession = Depends(get_db)):
    db_status = "ok"
    redis_status = "ok"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    try:
        redis = await get_redis()
        await redis.ping()
    except Exception:
        redis_status = "error"

    return HealthMetrics(database=db_status, redis=redis_status, environment=settings.ENVIRONMENT)
