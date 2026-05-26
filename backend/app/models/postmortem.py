"""
PostMortem ORM model.
Stores AI-generated and manual post-mortem reports for resolved incidents.
"""
from datetime import datetime

from sqlalchemy import Text, DateTime, ForeignKey, Integer, Boolean, func, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PostMortem(Base):
    __tablename__ = "postmortems"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    incident_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    root_cause: Mapped[str] = mapped_column(Text, nullable=False)
    impact: Mapped[str] = mapped_column(Text, nullable=False)
    timeline: Mapped[str] = mapped_column(Text, nullable=False)
    action_items: Mapped[str] = mapped_column(Text, nullable=False)
    lessons_learned: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_by_ai: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ai_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    incident = relationship("Incident", back_populates="postmortems")

    def __repr__(self) -> str:
        return f"<PostMortem(id={self.id}, incident_id={self.incident_id}, ai={self.generated_by_ai})>"
