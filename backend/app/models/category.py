import uuid
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (
        CheckConstraint("char_length(name) <= 64", name="categories_name_length"),
        CheckConstraint("color ~ '^#[0-9A-Fa-f]{6}$'", name="categories_color_format"),
        CheckConstraint("type IN ('income', 'expense')", name="categories_type_values"),
        Index("idx_categories_user_id", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    color: Mapped[str] = mapped_column(String(7), nullable=False)
    type: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), default=lambda: datetime.now(timezone.utc)
    )
