from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "showscore",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

celery_app.conf.beat_schedule = {
    "cleanup-expired-leaderboard-keys": {
        "task": "app.workers.tasks.cleanup_expired_leaderboard_keys",
        "schedule": crontab(hour=0, minute=15),  # daily just after midnight UTC
    },
    "generate-daily-analytics-report": {
        "task": "app.workers.tasks.generate_analytics_report",
        "schedule": crontab(hour=0, minute=30),
    },
    "aggregate-weekly-leaderboard": {
        "task": "app.workers.tasks.aggregate_weekly_leaderboard",
        "schedule": crontab(hour=0, minute=45, day_of_week=1),  # Monday after week rollover
    },
}
