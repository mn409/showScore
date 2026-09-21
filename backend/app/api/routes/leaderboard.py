from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import get_current_user
from app.db.redis_client import get_redis
from app.models.user import User
from app.schemas.score import LeaderboardEntry, LeaderboardResponse, UserRankResponse
from app.services.leaderboard_service import LeaderboardService

router = APIRouter(prefix="/api/leaderboard", tags=["leaderboard"])


async def _service() -> LeaderboardService:
    redis = await get_redis()
    return LeaderboardService(redis)


@router.get("/global", response_model=LeaderboardResponse)
async def global_leaderboard(top: int = Query(10, ge=1, le=100), offset: int = Query(0, ge=0)):
    service = await _service()
    key = service.resolve_key("global")
    entries = await service.get_top_n(key, n=top, offset=offset)
    total = await service.get_total_entries(key)
    return LeaderboardResponse(
        scope="global", entries=[LeaderboardEntry(**e) for e in entries], total_entries=total
    )


@router.get("/game/{game_id}", response_model=LeaderboardResponse)
async def game_leaderboard(
    game_id: str, top: int = Query(10, ge=1, le=100), offset: int = Query(0, ge=0)
):
    service = await _service()
    key = service.resolve_key("game", game_id=game_id)
    entries = await service.get_top_n(key, n=top, offset=offset)
    total = await service.get_total_entries(key)
    return LeaderboardResponse(
        scope=f"game:{game_id}", entries=[LeaderboardEntry(**e) for e in entries], total_entries=total
    )


@router.get("/daily", response_model=LeaderboardResponse)
async def daily_leaderboard(
    on: date | None = None, top: int = Query(10, ge=1, le=100), offset: int = Query(0, ge=0)
):
    service = await _service()
    key = service.resolve_key("daily", on=on)
    entries = await service.get_top_n(key, n=top, offset=offset)
    total = await service.get_total_entries(key)
    return LeaderboardResponse(
        scope=f"daily:{(on or date.today()).isoformat()}",
        entries=[LeaderboardEntry(**e) for e in entries],
        total_entries=total,
    )


@router.get("/weekly", response_model=LeaderboardResponse)
async def weekly_leaderboard(
    on: date | None = None, top: int = Query(10, ge=1, le=100), offset: int = Query(0, ge=0)
):
    service = await _service()
    key = service.resolve_key("weekly", on=on)
    entries = await service.get_top_n(key, n=top, offset=offset)
    total = await service.get_total_entries(key)
    return LeaderboardResponse(
        scope="weekly", entries=[LeaderboardEntry(**e) for e in entries], total_entries=total
    )


@router.get("/rank/me", response_model=UserRankResponse)
async def my_rank(
    scope: str = Query("global", pattern="^(global|game|daily|weekly)$"),
    game_id: str | None = None,
    on: date | None = None,
    user: User = Depends(get_current_user),
):
    service = await _service()
    try:
        key = service.resolve_key(scope, game_id=game_id, on=on)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    rank, score = await service.get_user_rank(key, str(user.id))
    return UserRankResponse(
        scope=scope, user_id=str(user.id), username=user.username, score=score, rank=rank
    )


@router.get("/rank/{user_id}", response_model=UserRankResponse)
async def user_rank(
    user_id: str,
    scope: str = Query("global", pattern="^(global|game|daily|weekly)$"),
    game_id: str | None = None,
    on: date | None = None,
):
    service = await _service()
    try:
        key = service.resolve_key(scope, game_id=game_id, on=on)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    rank, score = await service.get_user_rank(key, user_id)
    username = await service.get_username(user_id)
    return UserRankResponse(scope=scope, user_id=user_id, username=username, score=score, rank=rank)
