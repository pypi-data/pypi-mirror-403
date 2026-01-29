"""Database models for Amazon Deal Tracker."""

from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Seller(Base):
    """Stores seller information to normalize seller data."""

    __tablename__ = "sellers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    seller_name = Column(String(255), unique=True, nullable=False, index=True)
    is_amazon = Column(Boolean, default=False, nullable=False, index=True)
    first_seen_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    last_seen_at = Column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False
    )
    total_products = Column(Integer, default=0, nullable=False)

    # Relationships
    products = relationship("Product", back_populates="seller")
    price_records = relationship("PriceHistory", back_populates="seller")

    def __repr__(self):
        return f"<Seller(id={self.id}, name='{self.seller_name}', is_amazon={self.is_amazon})>"


class Product(Base):
    """Stores discovered ASINs - the product pool we track."""

    __tablename__ = "products"

    asin = Column(String(10), primary_key=True, index=True)
    title = Column(Text, nullable=True)
    url = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)
    category = Column(String(100), nullable=True, index=True)

    # Discovery metadata
    first_discovered_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    last_seen_at = Column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False
    )
    discovery_keywords = Column(Text, nullable=True)  # Keywords that found this product

    # Tracking flags
    is_active = Column(Boolean, default=True, nullable=False, index=True)  # Should we track this?
    check_priority = Column(Integer, default=1, nullable=False)  # 1=high, 2=medium, 3=low
    next_check_at = Column(
        DateTime, default=lambda: datetime.now(UTC), nullable=False, index=True
    )  # Adaptive scheduling

    # Product metadata (cached from PA API)
    rating = Column(Float, nullable=True)
    review_count = Column(Integer, nullable=True)
    is_prime_eligible = Column(Boolean, default=False)
    seller_id = Column(Integer, ForeignKey("sellers.id", ondelete="SET NULL"), nullable=True, index=True)

    # Relationships
    price_history = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan")
    alerts = relationship("AlertSent", back_populates="product", cascade="all, delete-orphan")
    seller = relationship("Seller", back_populates="products")

    # Indexes for common queries
    __table_args__ = (
        Index("ix_products_active_priority", "is_active", "check_priority"),
        Index("ix_products_last_seen", "last_seen_at"),
        Index("ix_products_seller", "seller_id"),
        Index("ix_products_category_active", "category", "is_active"),
    )

    def __repr__(self):
        return f"<Product(asin='{self.asin}', title='{self.title[:50] if self.title else None}')>"


class PriceHistory(Base):
    """Time series price data - tracks price changes over time."""

    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    asin = Column(String(10), ForeignKey("products.asin", ondelete="CASCADE"), nullable=False, index=True)

    # Price data
    price_amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="TRY", nullable=False)

    # Original/list price (if available from Amazon)
    list_price = Column(Numeric(10, 2), nullable=True)
    savings_amount = Column(Numeric(10, 2), nullable=True)
    savings_percentage = Column(Integer, nullable=True)

    # Seller information (keep for historical data)
    seller_name = Column(String(255), nullable=True)
    seller_id = Column(Integer, ForeignKey("sellers.id", ondelete="SET NULL"), nullable=True, index=True)
    is_amazon_seller = Column(Boolean, default=False)
    is_prime_eligible = Column(Boolean, default=False)
    is_free_shipping = Column(Boolean, default=False)
    availability_message = Column(String(255), nullable=True)

    # Timestamp
    captured_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    # Relationships
    product = relationship("Product", back_populates="price_history")
    seller = relationship("Seller", back_populates="price_records")

    # Indexes for time-series queries
    __table_args__ = (
        Index("ix_price_history_asin_captured", "asin", "captured_at"),
        Index("ix_price_history_captured_at", "captured_at"),
        Index("ix_price_history_seller", "seller_id"),
    )

    def __repr__(self):
        return f"<PriceHistory(asin='{self.asin}', price={self.price_amount}, captured_at='{self.captured_at}')>"


class AlertSent(Base):
    """Tracks sent alerts to prevent duplicates and spam."""

    __tablename__ = "alerts_sent"

    id = Column(Integer, primary_key=True, autoincrement=True)
    asin = Column(String(10), ForeignKey("products.asin", ondelete="CASCADE"), nullable=False, index=True)

    # Alert metadata
    alert_type = Column(String(50), nullable=False, index=True)  # e.g., DROP_24H, NEW_LOW_30D, FIRST_TIME_DEAL
    price_amount = Column(Numeric(10, 2), nullable=False)
    previous_price = Column(Numeric(10, 2), nullable=True)
    discount_percentage = Column(Integer, nullable=True)

    # Publishing details
    sent_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False, index=True)
    platform = Column(String(20), nullable=False)  # telegram, twitter
    message_id = Column(String(100), nullable=True)  # Platform-specific message ID

    # Cooldown management
    cooldown_until = Column(DateTime, nullable=True, index=True)

    # Relationship
    product = relationship("Product", back_populates="alerts")

    # Prevent duplicate alerts
    __table_args__ = (
        Index("ix_alerts_asin_sent_at", "asin", "sent_at"),
        Index("ix_alerts_asin_cooldown", "asin", "cooldown_until"),
        UniqueConstraint("asin", "alert_type", "sent_at", name="uq_alert_asin_type_time"),
    )

    def __repr__(self):
        return f"<AlertSent(asin='{self.asin}', type='{self.alert_type}', price={self.price_amount})>"


class PriceStatistics(Base):
    """Materialized view / cache of price statistics for fast queries."""

    __tablename__ = "price_statistics"

    asin = Column(String(10), ForeignKey("products.asin", ondelete="CASCADE"), primary_key=True)

    # Current price
    current_price = Column(Numeric(10, 2), nullable=True)
    current_price_updated_at = Column(DateTime, nullable=True)

    # Historical minimums
    min_price_24h = Column(Numeric(10, 2), nullable=True)
    min_price_7d = Column(Numeric(10, 2), nullable=True)
    min_price_30d = Column(Numeric(10, 2), nullable=True)
    min_price_all_time = Column(Numeric(10, 2), nullable=True)

    # Historical maximums
    max_price_24h = Column(Numeric(10, 2), nullable=True)
    max_price_7d = Column(Numeric(10, 2), nullable=True)
    max_price_30d = Column(Numeric(10, 2), nullable=True)

    # Averages
    avg_price_7d = Column(Numeric(10, 2), nullable=True)
    avg_price_30d = Column(Numeric(10, 2), nullable=True)

    # Price change indicators
    price_change_24h = Column(Numeric(10, 2), nullable=True)  # Absolute change
    price_change_24h_pct = Column(Float, nullable=True)  # Percentage change

    # Volatility
    price_volatility_30d = Column(Float, nullable=True)  # Standard deviation

    # Last update
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    def __repr__(self):
        return f"<PriceStatistics(asin='{self.asin}', current={self.current_price})>"
