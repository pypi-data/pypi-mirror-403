import pytest
from datetime import datetime, timedelta, timezone
from opportunity_core.services.deal_detection import DealDetectionEngine, DealType
from opportunity_core.models.database import PriceHistory, Product


def test_all_time_low_rule(db_session, product_factory, price_history_factory, stats_factory):
    """Test that AllTimeLowRule correctly identifies all-time low prices."""
    # Setup
    product = product_factory(asin="B00TEST_ATL")

    # Create history: Old low was 1000, now it's 900 (10% drop, 100 TL savings > 50 TL)
    price_history_factory(product, price=1000.0, captured_at=datetime.now(timezone.utc) - timedelta(days=10))
    current_price = price_history_factory(product, price=900.0)

    # Stats say min was 1000 (before this update), but we simulate the update
    # In reality, stats are updated before detection. So let's set stats to reflect the NEW low.
    stats = stats_factory(
        product,
        min_price_all_time=900.0,  # Current price IS the new low
        avg_price_30d=1000.0,
    )

    engine = DealDetectionEngine(db_session)

    # Debug prints
    print(f"\nProduct: {product.asin}")
    print(f"Stats: min_all_time={stats.min_price_all_time}, avg_30d={stats.avg_price_30d}")

    deals = list(engine.detect_deals(target_asins=[product.asin]))

    assert len(deals) == 1
    assert deals[0].deal_type == DealType.ALL_TIME_LOW
    assert deals[0].current_price == 900.0
    assert deals[0].discount_percentage == 10.0  # (1000-900)/1000


def test_drop_24h_rule(db_session, product_factory, price_history_factory, stats_factory):
    """Test that Drop24HRule detects significant price drops."""
    product = product_factory(asin="B00TEST_DROP")

    # Current price 800, was 1000 yesterday (200 TL drop > 50 TL threshold)
    price_history_factory(product, price=800.0)

    stats_factory(
        product,
        price_change_24h=-200.0,
        price_change_24h_pct=-20.0,
        min_price_all_time=700.0,  # Not an all time low
    )

    engine = DealDetectionEngine(db_session)
    # Configure rule to accept 15% drop
    engine.rules[1].min_drop_percentage = 15.0

    deals = list(engine.detect_deals(target_asins=[product.asin]))

    assert len(deals) == 1
    assert deals[0].deal_type == DealType.DROP_24H
    assert deals[0].discount_percentage == 20.0


def test_cooldown_logic(db_session, product_factory, price_history_factory, stats_factory):
    """Test that cooldown prevents spamming unless price drops further."""
    product = product_factory(asin="B00TEST_COOL")
    # Initial deal: 200 -> 100 (50% discount, 100 TL savings > 50 TL)
    price_history_factory(product, price=100.0)
    stats = stats_factory(product, min_price_all_time=100.0, avg_price_30d=200.0)

    engine = DealDetectionEngine(db_session, cooldown_hours=24)

    # 1. First detection - should be found
    deals1 = list(engine.detect_deals(target_asins=[product.asin]))
    assert len(deals1) == 1

    # Record the alert
    engine.record_alert(deals1[0], platform="telegram")

    # 2. Immediate second check - should be ignored (cooldown)
    deals2 = list(engine.detect_deals(target_asins=[product.asin]))
    assert len(deals2) == 0

    # 3. Price drops further (85.0) - should be found again
    # Drop must be >10% to trigger AllTimeLowRule now (100 -> 85 is 15%)
    price_history_factory(product, price=85.0)
    # Update stats for new price to trigger AllTimeLowRule
    stats.min_price_all_time = 85.0
    db_session.commit()

    deals3 = list(engine.detect_deals(target_asins=[product.asin]))
    assert len(deals3) == 1
    assert deals3[0].current_price == 85.0
