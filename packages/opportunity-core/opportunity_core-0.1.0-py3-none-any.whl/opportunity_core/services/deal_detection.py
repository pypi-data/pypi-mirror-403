"""Deal detection engine - rules-based deal identification using price history."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from opportunity_core.models.database import AlertSent, PriceHistory, PriceStatistics, Product

logger = logging.getLogger(__name__)


class DealType(Enum):
    """Types of deals the system can detect."""

    DROP_24H = "DROP_24H"  # Price dropped in last 24 hours
    NEW_LOW_7D = "NEW_LOW_7D"  # New 7-day low
    NEW_LOW_30D = "NEW_LOW_30D"  # New 30-day low
    ALL_TIME_LOW = "ALL_TIME_LOW"  # All-time lowest price
    FIRST_TIME_DEAL = "FIRST_TIME_DEAL"  # Product first discovered with good price
    SIGNIFICANT_DROP = "SIGNIFICANT_DROP"  # Large absolute price drop
    VOLATILE_DROP = "VOLATILE_DROP"  # Drop during high volatility period


@dataclass
class DetectedDeal:
    """Represents a detected deal with all context."""

    asin: str
    deal_type: DealType
    current_price: float
    previous_price: Optional[float]
    discount_amount: Optional[float]
    discount_percentage: Optional[float]
    currency: str
    product: Product
    statistics: PriceStatistics
    confidence_score: float  # 0.0-1.0, how confident we are this is a real deal
    reason: str  # Human-readable explanation
    lowest_price_30d: Optional[float] = None
    lowest_price_90d: Optional[float] = None
    lowest_price_180d: Optional[float] = None


class DealRule(ABC):
    """Abstract base class for deal detection rules."""

    @abstractmethod
    def evaluate(
        self, product: Product, current_price: PriceHistory, stats: PriceStatistics, db_session: Session
    ) -> Optional[DetectedDeal]:
        """
        Evaluate if this rule detects a deal.

        Args:
            product: Product being evaluated
            current_price: Most recent price record
            stats: Price statistics
            db_session: Database session

        Returns:
            DetectedDeal if rule triggers, None otherwise
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Return rule name for logging."""
        pass


class Drop24HRule(DealRule):
    """Detects price drops within last 24 hours."""

    def __init__(self, min_drop_percentage: float = 10.0, min_drop_amount: float = 10.0):
        """
        Initialize rule.

        Args:
            min_drop_percentage: Minimum percentage drop required (e.g., 10 = 10%)
            min_drop_amount: Minimum absolute price drop in currency units
        """
        self.min_drop_percentage = min_drop_percentage
        self.min_drop_amount = min_drop_amount

    def get_name(self) -> str:
        return f"24h Drop (≥{self.min_drop_percentage}% or ≥{self.min_drop_amount})"

    def evaluate(
        self, product: Product, current_price: PriceHistory, stats: PriceStatistics, db_session: Session
    ) -> Optional[DetectedDeal]:
        """Check for significant 24-hour price drop."""
        if not stats.price_change_24h or not stats.price_change_24h_pct:
            return None

        # Price must have dropped (negative change)
        if stats.price_change_24h >= 0:
            return None

        drop_amount = abs(float(stats.price_change_24h))
        drop_percentage = abs(stats.price_change_24h_pct)

        # Check thresholds
        if drop_percentage >= self.min_drop_percentage or drop_amount >= self.min_drop_amount:
            # Get previous price
            prev_price = float(current_price.price_amount) + drop_amount

            return DetectedDeal(
                asin=product.asin,
                deal_type=DealType.DROP_24H,
                current_price=float(current_price.price_amount),
                previous_price=prev_price,
                discount_amount=drop_amount,
                discount_percentage=drop_percentage,
                currency=current_price.currency,
                product=product,
                statistics=stats,
                confidence_score=min(drop_percentage / 50.0, 1.0),  # Higher % = higher confidence
                reason=f"Price dropped {drop_percentage:.1f}% ({drop_amount:.2f} {current_price.currency}) in last 24h",
            )

        return None


class NewLow30DRule(DealRule):
    """Detects new 30-day low prices."""

    def __init__(self, threshold_percentage: float = 5.0):
        """
        Initialize rule.

        Args:
            threshold_percentage: How close to minimum (e.g., 5 = within 5% of 30-day min)
        """
        self.threshold_percentage = threshold_percentage

    def get_name(self) -> str:
        return f"30-day Low (within {self.threshold_percentage}%)"

    def evaluate(
        self, product: Product, current_price: PriceHistory, stats: PriceStatistics, db_session: Session
    ) -> Optional[DetectedDeal]:
        """Check if current price is near or at 30-day minimum."""
        if not stats.min_price_30d:
            return None

        current = float(current_price.price_amount)
        min_30d = float(stats.min_price_30d)

        # Calculate how close we are to the minimum
        if current <= min_30d * (1 + self.threshold_percentage / 100):
            discount_from_avg = None
            discount_pct = None

            if stats.avg_price_30d:
                avg_30d = float(stats.avg_price_30d)
                discount_from_avg = avg_30d - current
                discount_pct = (discount_from_avg / avg_30d) * 100

            # Only report if there is a meaningful discount vs 30-day average
            if discount_pct and discount_pct >= 1.0:
                return DetectedDeal(
                    asin=product.asin,
                    deal_type=DealType.NEW_LOW_30D,
                    current_price=current,
                    previous_price=float(stats.avg_price_30d) if stats.avg_price_30d else None,
                    discount_amount=discount_from_avg,
                    discount_percentage=discount_pct,
                    currency=current_price.currency,
                    product=product,
                    statistics=stats,
                    confidence_score=0.8 if current == min_30d else 0.6,
                    reason=f"At 30-day low: {current:.2f} {current_price.currency} (-{discount_pct:.1f}% vs 30d avg)",
                )

        return None


class AllTimeLowRule(DealRule):
    """Detects all-time lowest prices."""

    def get_name(self) -> str:
        return "All-Time Low"

    def evaluate(
        self, product: Product, current_price: PriceHistory, stats: PriceStatistics, db_session: Session
    ) -> Optional[DetectedDeal]:
        """Check if current price is all-time lowest."""
        if not stats.min_price_all_time:
            return None

        current = float(current_price.price_amount)
        all_time_min = float(stats.min_price_all_time)

        # Must be exactly at all-time low
        if abs(current - all_time_min) < 0.01:  # Within 0.01 for floating point comparison
            discount_from_avg = None
            discount_pct = None

            if stats.avg_price_30d:
                avg = float(stats.avg_price_30d)
                discount_from_avg = avg - current
                discount_pct = (discount_from_avg / avg) * 100

            # 1. If we have a significant historical discount, it's a deal
            # Refined Rule: Must be at least 10% discount AND 50 TL savings vs 30-day average
            if discount_pct is not None and discount_pct >= 10.0 and discount_from_avg >= 50.0:
                return DetectedDeal(
                    asin=product.asin,
                    deal_type=DealType.ALL_TIME_LOW,
                    current_price=current,
                    previous_price=float(stats.avg_price_30d) if stats.avg_price_30d else None,
                    discount_amount=discount_from_avg,
                    discount_percentage=discount_pct,
                    currency=current_price.currency,
                    product=product,
                    statistics=stats,
                    confidence_score=1.0,  # Highest confidence
                    reason=f"🔥 ALL-TIME LOW: {current:.2f} {current_price.currency} (-{discount_pct:.0f}% vs 30d avg)",
                )

            # 2. If no historical discount (e.g., new product), check Amazon's official savings
            # This prevents 0% discount notifications for new products
            # Increased threshold to 15% to ensure only significant deals are flagged for new items
            # Also enforce 50 TL minimum savings to avoid low-value spam
            if (
                current_price.savings_percentage
                and current_price.savings_percentage >= 15
                and current_price.savings_amount
                and float(current_price.savings_amount) >= 50.0
            ):
                return DetectedDeal(
                    asin=product.asin,
                    deal_type=DealType.ALL_TIME_LOW,
                    current_price=current,
                    previous_price=float(current_price.list_price) if current_price.list_price else None,
                    discount_amount=float(current_price.savings_amount) if current_price.savings_amount else None,
                    discount_percentage=current_price.savings_percentage,
                    currency=current_price.currency,
                    product=product,
                    statistics=stats,
                    confidence_score=0.9,
                    reason=f"🔥 ALL-TIME LOW & Amazon Deal: -{current_price.savings_percentage}% (List: {current_price.list_price})",
                )

        return None


class SignificantDropRule(DealRule):
    """Detects large absolute price drops regardless of timeframe."""

    def __init__(self, min_drop_amount: float = 50.0, lookback_days: int = 7):
        """
        Initialize rule.

        Args:
            min_drop_amount: Minimum absolute price drop
            lookback_days: Days to look back for comparison
        """
        self.min_drop_amount = min_drop_amount
        self.lookback_days = lookback_days

    def get_name(self) -> str:
        return f"Significant Drop (≥{self.min_drop_amount} in {self.lookback_days}d)"

    def evaluate(
        self, product: Product, current_price: PriceHistory, stats: PriceStatistics, db_session: Session
    ) -> Optional[DetectedDeal]:
        """Check for large absolute price drops."""
        # Get price from N days ago
        lookback_date = datetime.now(UTC) - timedelta(days=self.lookback_days)

        old_price_record = (
            db_session.query(PriceHistory)
            .filter(
                and_(
                    PriceHistory.asin == product.asin,
                    PriceHistory.captured_at <= lookback_date,
                )
            )
            .order_by(PriceHistory.captured_at.desc())
            .first()
        )

        if not old_price_record:
            return None

        current = float(current_price.price_amount)
        old_price = float(old_price_record.price_amount)
        drop = old_price - current

        if drop >= self.min_drop_amount:
            drop_pct = (drop / old_price) * 100

            return DetectedDeal(
                asin=product.asin,
                deal_type=DealType.SIGNIFICANT_DROP,
                current_price=current,
                previous_price=old_price,
                discount_amount=drop,
                discount_percentage=drop_pct,
                currency=current_price.currency,
                product=product,
                statistics=stats,
                confidence_score=min(drop / 100.0, 1.0),
                reason=f"Significant drop: {drop:.2f} {current_price.currency} ({drop_pct:.1f}%) in {self.lookback_days} days",
            )

        return None


class DealDetectionEngine:
    """Main deal detection engine that applies rules and manages cooldowns."""

    def __init__(self, db_session: Session, cooldown_hours: int = 24):
        """
        Initialize deal detection engine.

        Args:
            db_session: Database session
            cooldown_hours: Hours to wait before re-alerting same ASIN
        """
        self.db_session = db_session
        self.cooldown_hours = cooldown_hours

        # Configure detection rules (customize as needed)
        self.rules = [
            AllTimeLowRule(),  # Highest priority
            Drop24HRule(min_drop_percentage=20.0, min_drop_amount=100.0),  # Aggressive: 20% or 100TL drop
            NewLow30DRule(threshold_percentage=3.0),  # Near 30-day minimum
            SignificantDropRule(min_drop_amount=100.0, lookback_days=7),  # Large drops: 100TL
        ]

        logger.info(f"Deal detection engine initialized with {len(self.rules)} rules")

    def detect_deals(self, limit: Optional[int] = None, target_asins: Optional[list[str]] = None):
        """
        Scan all active products and detect deals.
        Yields detected deals one by one.

        Args:
            limit: Maximum number of products to check (None = all)
            target_asins: Optional list of ASINs to check (None = all active)

        Yields:
            DetectedDeal objects
        """
        # Get products with recent price updates
        query = self.db_session.query(Product).filter(Product.is_active == True)

        # Filter by specific ASINs if provided
        if target_asins:
            query = query.filter(Product.asin.in_(target_asins))

        query = query.order_by(Product.check_priority, Product.last_seen_at.desc())

        if limit:
            query = query.limit(limit)

        products = query.all()

        logger.info(f"🔍 Scanning {len(products)} products for deals...")

        count = 0
        for product in products:
            deal = self._evaluate_product(product)
            if deal:
                count += 1
                yield deal

        logger.info(f"✅ Found {count} deals")

    def _evaluate_product(self, product: Product) -> Optional[DetectedDeal]:
        """
        Evaluate a single product against all rules.

        Args:
            product: Product to evaluate

        Returns:
            Highest confidence deal if detected, None otherwise
        """
        # Get latest price
        latest_price = (
            self.db_session.query(PriceHistory)
            .filter(PriceHistory.asin == product.asin)
            .order_by(PriceHistory.captured_at.desc())
            .first()
        )

        if not latest_price:
            return None

        # Get statistics
        stats = self.db_session.query(PriceStatistics).filter_by(asin=product.asin).first()

        if not stats:
            return None

        # Check cooldown (pass current price to check for stale deals)
        current_price_val = float(latest_price.price_amount)
        if self._is_in_cooldown(product.asin, current_price_val):
            logger.debug(f"  [{product.asin}] In cooldown or stale deal, skipping")
            return None

        # Apply all rules and pick best deal
        detected_deals = []
        for rule in self.rules:
            deal = rule.evaluate(product, latest_price, stats, self.db_session)
            if deal:
                logger.debug(f"  [{product.asin}] {rule.get_name()} triggered: {deal.reason}")
                detected_deals.append(deal)

        # Return highest confidence deal
        if detected_deals:
            best_deal = max(detected_deals, key=lambda d: d.confidence_score)

            # Enforce minimum thresholds (20% discount AND 100 TL savings)
            # Unless it's an ALL_TIME_LOW or FIRST_TIME_DEAL which might be special
            is_special_deal = best_deal.deal_type in [DealType.ALL_TIME_LOW, DealType.FIRST_TIME_DEAL]

            # Global Filter: Even for special deals, require minimum 100 TL savings or exceptionally high discount
            # Exception: If item is cheap (<500 TL) but has huge discount (>40%), allow it (e.g. 200 TL savings on 500 TL item)

            savings = best_deal.discount_amount or 0
            pct = best_deal.discount_percentage or 0

            # Strict Filter:
            # 1. Savings < 100 TL -> REJECT (unless >40% discount)
            # 2. Discount < 20% -> REJECT (unless All Time Low)

            if savings < 100.0:
                if pct < 40.0:
                    logger.debug(f"  [{product.asin}] Savings too low ({savings} < 100 TL), skipping")
                    return None

            if pct < 20.0 and not is_special_deal:
                logger.debug(f"  [{product.asin}] Discount too low ({pct}% < 20%), skipping")
                return None

            # Calculate historical context
            self._add_historical_context(best_deal)

            logger.info(
                f"  ✅ [{product.asin}] Deal detected: {best_deal.deal_type.value} (confidence: {best_deal.confidence_score:.2f})"
            )
            return best_deal

        return None

    def _add_historical_context(self, deal: DetectedDeal):
        """Calculate and add historical low prices to the deal object."""
        try:
            now = datetime.now(UTC)

            # Helper to get min price for a window
            def get_min_price(days: int) -> Optional[float]:
                cutoff = now - timedelta(days=days)
                min_price = (
                    self.db_session.query(func.min(PriceHistory.price_amount))
                    .filter(and_(PriceHistory.asin == deal.asin, PriceHistory.captured_at >= cutoff))
                    .scalar()
                )
                return float(min_price) if min_price else None

            deal.lowest_price_30d = get_min_price(30)
            deal.lowest_price_90d = get_min_price(90)
            deal.lowest_price_180d = get_min_price(180)

        except Exception as e:
            logger.error(f"Error calculating historical context for {deal.asin}: {e}")

    def _is_in_cooldown(self, asin: str, current_price: float) -> bool:
        """
        Check if ASIN should be silenced (cooldown or stale deal).

        Args:
            asin: Product ASIN
            current_price: Current price of the product

        Returns:
            True if should be silenced, False otherwise
        """
        # Get the very last alert sent for this ASIN
        last_alert = (
            self.db_session.query(AlertSent).filter(AlertSent.asin == asin).order_by(AlertSent.sent_at.desc()).first()
        )

        if not last_alert:
            return False  # Never alerted before

        now = datetime.now(UTC)
        time_since_alert = now - last_alert.sent_at.replace(tzinfo=UTC)

        # Check if price dropped significantly since last alert
        last_price = float(last_alert.price_amount)
        is_further_drop = current_price < last_price * 0.99

        # 1. Cooldown Check: Within 24 hours
        if time_since_alert < timedelta(hours=self.cooldown_hours):
            # If price dropped further, allow it!
            if is_further_drop:
                return False
            # Otherwise, silence it
            return True

        # 2. Stale Deal Check: If >24h passed
        # If price is same or higher than last alert, don't spam
        if is_further_drop:
            return False  # Price dropped further! Alert again.

        # Otherwise, it's the same old deal. Silence it.
        return True

    def check_platform_rate_limit(self, platform: str, limit: int, window_hours: int = 24) -> bool:
        """
        Check if the platform has reached its rate limit.

        Args:
            platform: Platform name (e.g., 'twitter')
            limit: Maximum number of alerts allowed in the window
            window_hours: Time window in hours

        Returns:
            True if limit reached (should block), False otherwise
        """
        cutoff = datetime.now(UTC) - timedelta(hours=window_hours)

        count = (
            self.db_session.query(AlertSent)
            .filter(
                and_(
                    AlertSent.platform == platform,
                    AlertSent.sent_at >= cutoff,
                )
            )
            .count()
        )

        return count >= limit

    def record_alert(self, deal: DetectedDeal, platform: str, message_id: Optional[str] = None) -> AlertSent:
        """
        Record that an alert was sent for a deal.

        Args:
            deal: The detected deal
            platform: Platform where alert was sent (telegram, twitter)
            message_id: Platform-specific message ID

        Returns:
            AlertSent record
        """
        cooldown_until = datetime.now(UTC) + timedelta(hours=self.cooldown_hours)

        alert = AlertSent(
            asin=deal.asin,
            alert_type=deal.deal_type.value,
            price_amount=deal.current_price,
            previous_price=deal.previous_price,
            discount_percentage=int(deal.discount_percentage) if deal.discount_percentage else None,
            sent_at=datetime.now(UTC),
            platform=platform,
            message_id=message_id,
            cooldown_until=cooldown_until,
        )

        self.db_session.add(alert)
        self.db_session.commit()

        logger.info(f"  📝 Alert recorded for [{deal.asin}] on {platform} (cooldown until {cooldown_until})")

        return alert
