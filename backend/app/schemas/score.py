import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class ScoreSubmit(BaseModel):
    game_id: str = Field(min_length=1, max_length=100)
    score: int = Field(ge=0, le=1_000_000_000, description="Score must be a non-negative integer")


class ScoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    game_id: str
    score: int
    score_date: date
    created_at: datetime


class ScoreSubmitResponse(BaseModel):
    accepted: bool
    reason: str
    score: ScoreOut | None = None
    global_rank: int | None = None
    game_rank: int | None = None
    daily_rank: int | None = None
    weekly_rank: int | None = None


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: str
    username: str
    score: float


class LeaderboardResponse(BaseModel):
    scope: str
    entries: list[LeaderboardEntry]
    total_entries: int


class UserRankResponse(BaseModel):
    scope: str
    user_id: str
    username: str
    score: float | None
    rank: int | None
