import uuid
from datetime import datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.session import Base


class ScoreHistory(Base):
    __tablename__ = "score_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    game_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    score_date: Mapped[datetime] = mapped_column(
        Date, server_default=func.current_date(), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    user = relationship("User", back_populates="scores")
