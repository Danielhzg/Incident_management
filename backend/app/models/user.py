"""
User / Engineer ORM model.
Represents engineers and managers who interact with incidents.
"""
import enum
from datetime import datetime

from sqlalchemy import String, Enum, DateTime, func, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(str, enum.Enum):
    ENGINEER = "engineer"
    LEAD = "lead"
    MANAGER = "manager"


class UserTier(int, enum.Enum):
    TIER_1 = 1
    TIER_2 = 2
    TIER_3 = 3


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", create_constraint=True),
        default=UserRole.ENGINEER,
        nullable=False,
    )
    tier: Mapped[UserTier] = mapped_column(
        Enum(UserTier, name="user_tier", create_constraint=True),
        default=UserTier.TIER_1,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    acknowledged_incidents = relationship(
        "Incident", back_populates="acknowledger", foreign_keys="Incident.acknowledged_by"
    )
    resolved_incidents = relationship(
        "Incident", back_populates="resolver", foreign_keys="Incident.resolved_by"
    )
    assigned_incidents = relationship(
        "Incident", back_populates="assignee", foreign_keys="Incident.assigned_to"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
