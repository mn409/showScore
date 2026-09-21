import json
import logging
from datetime import date, datetime, timedelta, timezone

import redis as sync_redis
from sqlalchemy import distinct, func, select

from app.core.config import settings
from app.db.sync_session import SyncSessionLocal
from app.models.score import ScoreHistory
from app.models.user import User
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

# Keep daily keys for 45 days, weekly keys for 26 weeks (~6 months)
DAILY_RETENTION_DAYS = 45
WEEKLY_RETENTION_WEEKS = 26


def _redis() -> sync_redis.Redis:
    return sync_redis.from_url(settings.REDIS_URL, decode_responses=True)


@celery_app.task(name="app.workers.tasks.cleanup_expired_leaderboard_keys")
def cleanup_expired_leaderboard_keys() -> dict:
    """Delete daily/weekly Redis sorted sets older than the retention window."""
    r = _redis()
    deleted = []

    cutoff_day = date.today() - timedelta(days=DAILY_RETENTION_DAYS)
    for key in r.scan_iter(match="leaderboard:daily:*"):
        try:
            key_date = date.fromisoformat(key.split(":")[-1])
        except ValueError:
            continue
        if key_date < cutoff_day:
            r.delete(key)
            deleted.append(key)

    cutoff_week_date = date.today() - timedelta(weeks=WEEKLY_RETENTION_WEEKS)
    cutoff_iso_year, cutoff_iso_week, _ = cutoff_week_date.isocalendar()
    for key in r.scan_iter(match="leaderboard:weekly:*"):
        try:
            part = key.split(":")[-1]  # e.g. 2026-W38
            year_str, week_str = part.split("-W")
            year, week = int(year_str), int(week_str)
        except (ValueError, IndexError):
            continue
        if (year, week) < (cutoff_iso_year, cutoff_iso_week):
            r.delete(key)
            deleted.append(key)

    logger.info("Cleanup removed %d expired leaderboard keys", len(deleted))
    return {"deleted_keys": deleted, "count": len(deleted)}


@celery_app.task(name="app.workers.tasks.aggregate_weekly_leaderboard")
def aggregate_weekly_leaderboard() -> dict:
    """
    Recompute the current ISO week's leaderboard from PostgreSQL as a
    source-of-truth reconciliation pass (in case Redis was ever flushed
    or drifted from Postgres).
    """
    today = date.today()
    iso_year, iso_week, _ = today.isocalendar()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    r = _redis()
    key = f"leaderboard:weekly:{iso_year}-W{iso_week:02d}"

    with SyncSessionLocal() as db:
        rows = db.execute(
            select(ScoreHistory.user_id, func.max(ScoreHistory.score))
            .where(ScoreHistory.score_date >= week_start, ScoreHistory.score_date <= week_end)
            .group_by(ScoreHistory.user_id)
        ).all()

        if rows:
            pipe = r.pipeline()
            pipe.delete(key)
            mapping = {str(user_id): score for user_id, score in rows}
            pipe.zadd(key, mapping)
            pipe.execute()

    logger.info("Reconciled weekly leaderboard %s with %d users", key, len(rows) if rows else 0)
    return {"key": key, "users": len(rows) if rows else 0}


@celery_app.task(name="app.workers.tasks.aggregate_daily_leaderboard")
def aggregate_daily_leaderboard(target_day: str | None = None) -> dict:
    """Reconcile a given day's leaderboard (defaults to today) from Postgres."""
    day = date.fromisoformat(target_day) if target_day else date.today()
    r = _redis()
    key = f"leaderboard:daily:{day.isoformat()}"

    with SyncSessionLocal() as db:
        rows = db.execute(
            select(ScoreHistory.user_id, func.max(ScoreHistory.score))
            .where(ScoreHistory.score_date == day)
            .group_by(ScoreHistory.user_id)
        ).all()

        if rows:
            pipe = r.pipeline()
            pipe.delete(key)
            mapping = {str(user_id): score for user_id, score in rows}
            pipe.zadd(key, mapping)
            pipe.execute()

    logger.info("Reconciled daily leaderboard %s with %d users", key, len(rows) if rows else 0)
    return {"key": key, "users": len(rows) if rows else 0}


@celery_app.task(name="app.workers.tasks.generate_analytics_report")
def generate_analytics_report() -> dict:
    """Generate a daily analytics snapshot and cache it in Redis for the admin dashboard."""
    with SyncSessionLocal() as db:
        total_users = db.execute(select(func.count(User.id))).scalar_one()
        total_scores = db.execute(select(func.count(ScoreHistory.id))).scalar_one()
        total_games = db.execute(select(func.count(distinct(ScoreHistory.game_id)))).scalar_one()

        today = date.today()
        scores_today = db.execute(
            select(func.count(ScoreHistory.id)).where(ScoreHistory.score_date == today)
        ).scalar_one()

        active_users_today = db.execute(
            select(func.count(distinct(ScoreHistory.user_id))).where(
                ScoreHistory.score_date == today
            )
        ).scalar_one()

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_users": total_users,
        "total_scores_submitted": total_scores,
        "total_games": total_games,
        "scores_submitted_today": scores_today,
        "active_users_today": active_users_today,
    }

    r = _redis()
    r.set("analytics:latest_report", json.dumps(report), ex=60 * 60 * 26)  # keep ~1 day + buffer

    logger.info("Generated analytics report: %s", report)
    return report
