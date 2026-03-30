from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Text, String, DateTime, func
from datetime import datetime

from src.db.database import Base



import uuid
class User(Base):
     __tablename__ = 'users'

     uid: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
     username: Mapped[str] = mapped_column(String(30), nullable=False)
     email: Mapped[str] = mapped_column(String(255), nullable=False)
     password_hash: Mapped[str] = mapped_column(Text, nullable=False)
     created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
     updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now, onupdate=func.now())