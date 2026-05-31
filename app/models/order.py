from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))
    sales_channel_id: Mapped[int] = mapped_column(ForeignKey("sales_channels.id"))
    campaign_id: Mapped[int | None] = mapped_column(ForeignKey("campaigns.id"), nullable=True)
    order_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(30))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    customer = relationship("Customer", back_populates="orders")
    sales_channel = relationship("SalesChannel", back_populates="orders")
    campaign = relationship("Campaign", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")
