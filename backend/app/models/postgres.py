"""SQLAlchemy models — PostgreSQL is the source of truth for orders."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

ORDER_STATUSES = ("PENDING", "PROCESSING", "SHIPPED")


class Base(DeclarativeBase):
    """Declarative base for every PostgreSQL table."""


class User(Base):
    """A customer account with authentication."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="CUSTOMER")
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Deliberately not auto-loaded: the API never walks user -> orders.
    orders: Mapped[list["Order"]] = relationship(
        back_populates="user", lazy="raise", passive_deletes=True
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"<User {self.id} {self.name} {self.role}>"

    __table_args__ = (
        CheckConstraint("role IN ('CUSTOMER', 'ADMIN')", name="ck_users_role"),
    )


class Order(Base):
    """Transactional order header — the canonical order record."""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_number: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    order_date: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    #: Set by the Celery worker after a successful Elasticsearch index write.
    search_indexed_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped[User] = relationship(back_populates="orders", lazy="selectin")
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="OrderItem.id",
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING','PROCESSING','SHIPPED')",
            name="ck_orders_status",
        ),
        CheckConstraint("total_amount >= 0", name="ck_orders_total_non_negative"),
        Index("ix_orders_status", "status"),
        Index("ix_orders_user_order_date", "user_id", "order_date"),
    )

    @property
    def customer(self) -> User:
        """Alias used by response schemas (`OrderResponse.customer`)."""
        return self.user

    def recalculate_total(self) -> Decimal:
        """Recompute the header total from its line items (debug/verification)."""
        return sum((item.line_total for item in self.items), Decimal("0.00"))


class OrderItem(Base):
    """Order line — stores a *snapshot* of the product at purchase time."""

    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    #: Snapshot of MongoDB `products.title` at the moment of purchase.
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    #: Snapshot of MongoDB `products.price` at the moment of purchase.
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    order: Mapped[Order] = relationship(back_populates="items")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_order_items_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="ck_order_items_price_non_negative"),
    )

    @property
    def line_total(self) -> Decimal:
        return (self.unit_price * self.quantity).quantize(Decimal("0.01"))

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"<OrderItem {self.id} order={self.order_id} {self.title!r}>"
