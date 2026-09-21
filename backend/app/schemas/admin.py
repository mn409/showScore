from datetime import date

from pydantic import BaseModel


class SystemStats(BaseModel):
    total_users: int
    total_scores_submitted: int
    total_games: int
    scores_submitted_today: int


class DailyActivity(BaseModel):
    day: date
    submissions: int
    unique_users: int


class ActivityTrendResponse(BaseModel):
    days: int
    trend: list[DailyActivity]


class TopPlayer(BaseModel):
    rank: int
    user_id: str
    username: str
    score: float


class TopPlayersResponse(BaseModel):
    scope: str
    players: list[TopPlayer]


class HealthMetrics(BaseModel):
    database: str
    redis: str
    environment: str
