from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class QueryFeedback(Base):
    __tablename__ = "query_feedback"

    id: Mapped[int] = mapped_column(primary_key=True)
    query_log_id: Mapped[int] = mapped_column(ForeignKey("query_logs.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    rating: Mapped[int] = mapped_column(Integer)
    is_helpful: Mapped[bool] = mapped_column(Boolean)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    query_log = relationship("QueryLog", back_populates="feedback_entries")
    user = relationship("User", back_populates="feedback_entries")
