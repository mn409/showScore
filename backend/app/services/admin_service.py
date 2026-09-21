from datetime import date, timedelta

from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.score import ScoreHistory
from app.models.user import User


async def get_system_stats(db: AsyncSession) -> dict:
    total_users = (await db.execute(select(func.count(User.id)))).scalar_one()
    total_scores = (await db.execute(select(func.count(ScoreHistory.id)))).scalar_one()
    total_games = (await db.execute(select(func.count(distinct(ScoreHistory.game_id))))).scalar_one()
    today = date.today()
    scores_today = (
        await db.execute(
            select(func.count(ScoreHistory.id)).where(ScoreHistory.score_date == today)
        )
    ).scalar_one()

    return {
        "total_users": total_users,
        "total_scores_submitted": total_scores,
        "total_games": total_games,
        "scores_submitted_today": scores_today,
    }


async def get_activity_trend(db: AsyncSession, days: int = 14) -> list[dict]:
    start = date.today() - timedelta(days=days - 1)
    result = await db.execute(
        select(
            ScoreHistory.score_date,
            func.count(ScoreHistory.id),
            func.count(distinct(ScoreHistory.user_id)),
        )
        .where(ScoreHistory.score_date >= start)
        .group_by(ScoreHistory.score_date)
        .order_by(ScoreHistory.score_date)
    )
    rows = result.all()
    by_day = {r[0]: {"submissions": r[1], "unique_users": r[2]} for r in rows}

    trend = []
    for i in range(days):
        d = start + timedelta(days=i)
        entry = by_day.get(d, {"submissions": 0, "unique_users": 0})
        trend.append({"day": d, **entry})
    return trend
