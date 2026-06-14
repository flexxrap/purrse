import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class Budget(Base):
    __tablename__ = "budgets"
    __table_args__ = (
        CheckConstraint("limit_cents > 0", name="budgets_limit_positive"),
        CheckConstraint("month ~ '^[0-9]{4}-[0-9]{2}$'", name="budgets_month_format"),
        UniqueConstraint("user_id", "category_id", "month", name="uq_budgets_user_category_month"),
        Index("idx_budgets_user_month", "user_id", "month"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    category_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    month: Mapped[str] = mapped_column(String(7), nullable=False)
    limit_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    alert_80_sent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        default=datetime.utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        default=datetime.utcnow,
        onupdate=func.now(),
    )
