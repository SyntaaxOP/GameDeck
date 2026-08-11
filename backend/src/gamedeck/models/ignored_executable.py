from datetime import datetime
from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from gamedeck.db import Base

class IgnoredExecutable(Base):
    __tablename__ = "ignored_executables"
    __table_args__ = (UniqueConstraint("executable_path", name="uq_ignored_executables_path"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    executable_name: Mapped[str] = mapped_column(String(255), nullable=False)
    executable_path: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
