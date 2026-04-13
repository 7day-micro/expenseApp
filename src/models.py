import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base


class User(Base):
    __tablename__ = "users"

    __table_args__ = (
        CheckConstraint("role IN ('user', 'admin')", name="ck_users_role_valid"),
        Index("idx_users_email", "email", unique=True),
    )

    uid: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(30), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # role
    role: Mapped[str] = mapped_column(
        String(20), default="user", server_default="user", nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # updated for ASYNC

    # Removed lazy="selectin" that was causing extreme overhead when get a user with
    # lot of expense
    # Using passive delete to avoid sqlachemty set expenses.user_id to NULL before delete
    categories: Mapped[list[Category]] = relationship(
        back_populates="user", passive_deletes=True
    )
    expenses: Mapped[list[Expense]] = relationship(
        back_populates="user", passive_deletes=True
    )
    budgets: Mapped[list[Budget]] = relationship(
        back_populates="user", passive_deletes=True
    )


class Category(Base):
    __tablename__ = "categories"

    __table_args__ = (
        Index("idx_categories_user_id", "user_id"),
        UniqueConstraint("user_id", "name", name="uq_categories_name_user"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        ForeignKey("users.uid", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    color_icon: Mapped[str] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # updated for ASYNC
    user: Mapped[User] = relationship(
        back_populates="categories",
    )
    expenses: Mapped[list[Expense]] = relationship(
        back_populates="category",
    )
    budgets: Mapped[list[Budget]] = relationship(
        back_populates="category",
    )


class Expense(Base):
    __tablename__ = "expenses"

    __table_args__ = (
        Index("idx_expenses_category_id", "category_id"),
        Index("idx_expenses_user_category", "user_id", "category_id"),
        Index("idx_expenses_user_date", "user_id", "transaction_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("users.uid", ondelete="CASCADE"), nullable=False
    )
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    transaction_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    note: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # updated for ASYNC
    user: Mapped[User] = relationship(
        back_populates="expenses",
    )
    category: Mapped[Category] = relationship(
        back_populates="expenses",
    )


class Budget(Base):
    __tablename__ = "budgets"

    __table_args__ = (
        Index("idx_budgets_user_category", "user_id", "category_id"),
        Index("idx_budgets_user_month_year", "user_id", "month_year"),
        UniqueConstraint(
            "user_id", "month_year", "category_id", name="uq_user_category_month"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("users.uid", ondelete="CASCADE"), nullable=False
    )
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    amount_limit: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    month_year: Mapped[date] = mapped_column(Date(), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # updated for ASYNC
    user: Mapped[User] = relationship(back_populates="budgets", lazy="selectin")
    category: Mapped[Category] = relationship(back_populates="budgets", lazy="selectin")
