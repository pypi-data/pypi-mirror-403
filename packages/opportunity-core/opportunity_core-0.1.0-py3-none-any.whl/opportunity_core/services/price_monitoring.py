"""Price monitoring service - tracks price changes over time."""

import logging
import time
from datetime import UTC, datetime, timedelta
from typing import Any, Callable, Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from opportunity_core.models.database import PriceHistory, PriceStatistics, Product
from opportunity_core.utils.api_helper import call_with_backoff
from paapi5_python_sdk.api.default_api import DefaultApi
from paapi5_python_sdk.models import GetItemsRequest, GetItemsResource
from paapi5_python_sdk.rest import ApiException

logger = logging.getLogger(__name__)


class PriceMonitoringService:
    """Monitors and records price changes for tracked products."""

    def __init__(
        self,
        api_client: DefaultApi,
        partner_tag: str,
        partner_type: str,
        marketplace: str,
        db_session: Session,
    ):
        """
        Initialize price monitoring service.

        Args:
            api_client: Authenticated PA API client
            partner_tag: Amazon partner tag
            partner_type: Partner type
            marketplace: Amazon marketplace domain
            db_session: Database session
        """
        self.api_client = api_client
        self.partner_tag = partner_tag
        self.partner_type = partner_type
        self.marketplace = marketplace
        self.db_session = db_session

    def check_prices_for_active_products(
        self,
        batch_size: int = 10,
        max_batches: Optional[int] = None,
        on_batch_processed: Optional[Callable[[list[str]], None]] = None,
        segment_index: int = 0,
        total_segments: int = 1,
    ) -> dict[str, int]:
        """
        Check prices for all active products in batches.

        Args:
            batch_size: Number of ASINs to check per API call (max 10)
            max_batches: Maximum number of batches to process (None = all)
            on_batch_processed: Callback function called with list of updated ASINs after each batch
            segment_index: Index of the current segment (0 to total_segments-1)
            total_segments: Total number of segments to split the workload into

        Returns:
            Statistics: {products_checked, prices_updated, errors}
        """
        batch_size = min(batch_size, 10)  # PA API limit
        products_checked = 0
        prices_updated = 0
        errors = 0

        # SMART MONITORING: Select products due for check
        now_utc = datetime.now(UTC)

        # 1. Base Query: Active products only
        query = (
            self.db_session.query(Product)
            .filter(Product.is_active == True)
            .filter(Product.next_check_at <= datetime.now(UTC))
            .order_by(Product.check_priority, Product.next_check_at)
        )

        # 4. Global Limit for Safety
        # Optimization: Decreased from 3500 to 2500 to reduce hourly load
        # Calculation: 2500 products/hr / 10 batch = 250 req/hr
        GLOBAL_LIMIT = 2500

        logger.info(f"📊 Selecting max {GLOBAL_LIMIT} products due for check (Priority-based)...")
        active_products = query.limit(GLOBAL_LIMIT).all()

        if not active_products:
            logger.info("✅ No products due for check. Smart monitoring allows skipping this cycle.")
            return {
                "products_checked": 0,
                "prices_updated": 0,
                "errors": 0,
            }

        total_products = len(active_products)

        # Process in batches
        for i in range(0, total_products, batch_size):
            if max_batches and i // batch_size >= max_batches:
                logger.info(f"⏸️  Reached max batches limit ({max_batches})")
                break

            batch = active_products[i : i + batch_size]
            asins = [p.asin for p in batch]

            logger.info(f"  Batch {i // batch_size + 1}: Checking {len(asins)} products...")

            try:
                results = self._check_prices_batch(asins)
                products_checked += len(asins)
                prices_updated += len([r for r in results if r])

                # Trigger callback for real-time detection
                if on_batch_processed:
                    try:
                        on_batch_processed(asins)
                    except Exception as cb_err:
                        logger.error(f"Error in batch callback: {cb_err}")

            except Exception as e:
                logger.error(f"Error checking batch: {e}")
                errors += len(asins)

            # Rate limiting between batches (Optimized: 2.0s is safe for GetItems with 10 items)
            time.sleep(2.0)

        logger.info(f"✅ Price check complete: {products_checked} checked, {prices_updated} updated, {errors} errors")

        return {
            "products_checked": products_checked,
            "prices_updated": prices_updated,
            "errors": errors,
        }

    def _check_prices_batch(self, asins: list[str]) -> list[Optional[PriceHistory]]:
        """
        Check prices for a batch of ASINs using GetItems API.

        Args:
            asins: List of ASINs to check (max 10)

        Returns:
            List of PriceHistory records created (None for failures)
        """
        results = []

        try:
            # Request comprehensive price and seller info
            request = GetItemsRequest(
                partner_tag=self.partner_tag,
                partner_type=self.partner_type,
                marketplace=self.marketplace,
                item_ids=asins,
                resources=[
                    GetItemsResource.OFFERS_LISTINGS_PRICE,
                    GetItemsResource.OFFERS_LISTINGS_SAVINGBASIS,
                    GetItemsResource.OFFERS_LISTINGS_MERCHANTINFO,
                    GetItemsResource.OFFERS_LISTINGS_AVAILABILITY_MESSAGE,
                    GetItemsResource.OFFERS_LISTINGS_DELIVERYINFO_ISPRIMEELIGIBLE,
                    GetItemsResource.OFFERS_LISTINGS_DELIVERYINFO_ISFREESHIPPINGELIGIBLE,
                    GetItemsResource.ITEMINFO_TITLE,
                ],
            )

            # Use backoff for API call
            response = call_with_backoff(
                self.api_client.get_items,
                request,
                max_retries=10,  # Increased from 3 to 10
                initial_delay=5.0,
                max_delay=120.0,  # Allow waiting up to 2 minutes
                backoff_factor=2.0,
            )

            if response and hasattr(response, "items_result") and response.items_result:
                if hasattr(response.items_result, "items") and response.items_result.items:
                    for item in response.items_result.items:
                        price_record = self._extract_and_store_price(item)
                        results.append(price_record)

            # Handle errors for specific ASINs
            if response and hasattr(response, "errors") and response.errors:
                for error in response.errors:
                    logger.warning(f"  Error for ASIN: {error}")

                    # Check for InvalidParameterValue error (invalid ASIN)
                    if hasattr(error, "code") and error.code == "InvalidParameterValue":
                        # Try to extract ASIN from message
                        # Message format: "The ItemIds B0998F82WC provided in the request is invalid."
                        import re

                        msg = error.message if hasattr(error, "message") else str(error)
                        match = re.search(r"ItemIds\s+([A-Z0-9]{10})", msg)

                        if match:
                            invalid_asin = match.group(1)
                            logger.warning(f"🚫 Invalid ASIN detected: {invalid_asin}. Deleting product.")

                            # Delete product from database
                            try:
                                product = self.db_session.query(Product).filter(Product.asin == invalid_asin).first()
                                if product:
                                    self.db_session.delete(product)
                                    self.db_session.commit()
                                    logger.info(f"✅ Product {invalid_asin} deleted successfully.")
                            except Exception as db_err:
                                logger.error(f"Failed to delete invalid product {invalid_asin}: {db_err}")
                                self.db_session.rollback()

                    results.append(None)

        except ApiException as e:
            logger.error(f"PA API error in batch price check: {e}")
            results = [None] * len(asins)
        except Exception as e:
            logger.error(f"Unexpected error in batch price check: {e}")
            results = [None] * len(asins)

        return results

    def cleanup_inactive_products(self, days_threshold: int = 30) -> int:
        """
        Deactivate products that have been out of stock or have no price updates for N days.

        Args:
            days_threshold: Number of days to look back (default 30)

        Returns:
            Number of products deactivated
        """
        logger.info(f"🧹 Starting cleanup of inactive products (Threshold: {days_threshold} days)...")

        cutoff_date = datetime.now(UTC) - timedelta(days=days_threshold)
        deactivated_count = 0

        try:
            # 1. Get all currently active products
            active_products = self.db_session.query(Product).filter(Product.is_active == True).all()

            for product in active_products:
                # Check if we have ANY price history in the last N days
                recent_history = (
                    self.db_session.query(PriceHistory)
                    .filter(and_(PriceHistory.asin == product.asin, PriceHistory.captured_at >= cutoff_date))
                    .count()
                )

                # If no history at all in 30 days, deactivate
                if recent_history == 0:
                    logger.info(f"  [{product.asin}] No price history in {days_threshold} days. Deactivating.")
                    product.is_active = False
                    deactivated_count += 1
                    continue

                # If there is history, check if it's ALL "out of stock" (price=0 or None)
                # But our PriceHistory only stores valid prices usually.
                # If we store 0 for out of stock, we check that.
                # Currently _extract_and_store_price returns None if no record is created.
                # So 'recent_history == 0' effectively covers "Out of Stock" if we don't record OOS.

                # However, if we updated last_seen_at but didn't add price history, that means OOS.
                # Let's check last_seen_at vs cutoff
                if product.last_seen_at and product.last_seen_at < cutoff_date:
                    logger.info(f"  [{product.asin}] Last seen > {days_threshold} days ago. Deactivating.")
                    product.is_active = False
                    deactivated_count += 1

            self.db_session.commit()
            logger.info(f"✅ Cleanup complete. Deactivated {deactivated_count} products.")
            return deactivated_count

        except Exception as e:
            logger.error(f"Error during product cleanup: {e}")
            self.db_session.rollback()
            return 0

    def _extract_and_store_price(self, item: Any) -> Optional[PriceHistory]:
        """
        Extract price data from API response and store in database.

        Args:
            item: PA API GetItems response item

        Returns:
            PriceHistory record if successful, None otherwise
        """
        try:
            # Extract ASIN
            asin = item.asin if hasattr(item, "asin") else None
            if not asin:
                return None

            # Extract price from offers
            current_price = None
            currency = "TRY"
            list_price = None
            savings_amount = None
            savings_percentage = None
            seller_name = None
            is_amazon_seller = False
            is_prime_eligible = False
            is_free_shipping = False
            availability_message = None

            # Check Offers (v1) - most reliable
            if hasattr(item, "offers") and item.offers:
                if hasattr(item.offers, "listings") and item.offers.listings:
                    listing = item.offers.listings[0]  # First listing

                    # Current price
                    if hasattr(listing, "price") and listing.price:
                        if hasattr(listing.price, "amount"):
                            current_price = float(listing.price.amount)
                        if hasattr(listing.price, "currency"):
                            currency = listing.price.currency

                    # List price / savings basis
                    if hasattr(listing, "saving_basis") and listing.saving_basis:
                        if hasattr(listing.saving_basis, "amount"):
                            list_price = float(listing.saving_basis.amount)

                    # Calculate savings
                    if current_price and list_price and list_price > current_price:
                        savings_amount = list_price - current_price
                        savings_percentage = int((savings_amount / list_price) * 100)

                    # Seller info
                    if hasattr(listing, "merchant_info") and listing.merchant_info:
                        if hasattr(listing.merchant_info, "name"):
                            seller_name = listing.merchant_info.name
                            if seller_name and "amazon" in seller_name.lower():
                                is_amazon_seller = True

                    # Availability
                    if hasattr(listing, "availability") and listing.availability:
                        if hasattr(listing.availability, "message"):
                            availability_message = listing.availability.message

                    # Delivery info
                    if hasattr(listing, "delivery_info") and listing.delivery_info:
                        if hasattr(listing.delivery_info, "is_prime_eligible"):
                            is_prime_eligible = listing.delivery_info.is_prime_eligible
                        if hasattr(listing.delivery_info, "is_free_shipping_eligible"):
                            is_free_shipping = listing.delivery_info.is_free_shipping_eligible

            # Must have valid price to record
            if current_price is None or current_price <= 0:
                logger.debug(f"  [{asin}] No valid price found, skipping")
                return None

            # Store price history record
            price_record = PriceHistory(
                asin=asin,
                price_amount=current_price,
                currency=currency,
                list_price=list_price,
                savings_amount=savings_amount,
                savings_percentage=savings_percentage,
                seller_name=seller_name,
                is_amazon_seller=is_amazon_seller,
                is_prime_eligible=is_prime_eligible,
                is_free_shipping=is_free_shipping,
                availability_message=availability_message,
                captured_at=datetime.now(UTC),
            )

            self.db_session.add(price_record)
            self.db_session.commit()

            logger.debug(f"  [{asin}] Price recorded: {current_price} {currency}")

            # Update price statistics
            self._update_price_statistics(asin)

            return price_record

        except Exception as e:
            logger.error(f"Error storing price for ASIN: {e}")
            self.db_session.rollback()
            return None

    def _update_price_statistics(self, asin: str):
        """
        Update materialized price statistics for an ASIN.

        Calculates min/max/avg prices over different time windows.

        Args:
            asin: Product ASIN
        """
        try:
            now = datetime.now(UTC)

            # Get current price
            latest = (
                self.db_session.query(PriceHistory)
                .filter(PriceHistory.asin == asin)
                .order_by(PriceHistory.captured_at.desc())
                .first()
            )

            if not latest:
                return

            # Calculate statistics over different time windows
            stats = {
                "asin": asin,
                "current_price": latest.price_amount,
                "current_price_updated_at": latest.captured_at,
            }

            # 24 hours
            stats_24h = self._calculate_window_stats(asin, now - timedelta(hours=24))
            stats.update(
                {
                    "min_price_24h": stats_24h["min_price"],
                    "max_price_24h": stats_24h["max_price"],
                }
            )

            # 7 days
            stats_7d = self._calculate_window_stats(asin, now - timedelta(days=7))
            stats.update(
                {
                    "min_price_7d": stats_7d["min_price"],
                    "max_price_7d": stats_7d["max_price"],
                    "avg_price_7d": stats_7d["avg_price"],
                }
            )

            # 30 days
            stats_30d = self._calculate_window_stats(asin, now - timedelta(days=30))
            stats.update(
                {
                    "min_price_30d": stats_30d["min_price"],
                    "max_price_30d": stats_30d["max_price"],
                    "avg_price_30d": stats_30d["avg_price"],
                    "price_volatility_30d": stats_30d["volatility"],
                }
            )

            # All time
            all_time = (
                self.db_session.query(func.min(PriceHistory.price_amount)).filter(PriceHistory.asin == asin).scalar()
            )
            stats["min_price_all_time"] = all_time

            # Price change 24h
            if stats_24h["first_price"]:
                stats["price_change_24h"] = float(latest.price_amount) - stats_24h["first_price"]
                stats["price_change_24h_pct"] = float((stats["price_change_24h"] / stats_24h["first_price"]) * 100)

            # Upsert statistics
            existing = self.db_session.query(PriceStatistics).filter_by(asin=asin).first()
            if existing:
                for key, value in stats.items():
                    if key != "asin":
                        setattr(existing, key, value)
                existing.updated_at = now
            else:
                stat_record = PriceStatistics(**stats)
                self.db_session.add(stat_record)

            self.db_session.commit()

            # SMART MONITORING: Update next_check_at based on activity
            self._update_adaptive_schedule(asin, stats)

        except Exception as e:
            logger.error(f"Error updating statistics for {asin}: {e}")
            self.db_session.rollback()

    def _update_adaptive_schedule(self, asin: str, stats: dict):
        """
        Dynamically schedule the next check time based on product activity.

        Strategies:
        1. High Priority (1h): Significant price change recently or deal detected.
        2. Medium Priority (4-6h): Stable price for 24h.
        3. Low Priority (12-24h): Stable for > 3 days or out of stock.
        """
        try:
            product = self.db_session.query(Product).filter(Product.asin == asin).first()
            if not product:
                return

            now = datetime.now(UTC)
            next_check_hours = 4  # Default medium
            priority = 2

            # Signal: High Demand / Popularity
            # If product has lots of reviews, it's popular -> Prices fluctuate more often -> Check more often
            # This is a 'Professional' touch: Volume = Volatility
            review_count = product.review_count or 0
            if review_count > 1000:
                next_check_hours = 3  # Boost standard check frequency
                logger.debug(f"  [{asin}] High popularity ({review_count} reviews). Reduced interval to 3h.")

            # Signal: Recent Price Change (Last 24h)
            pct_change = abs(stats.get("price_change_24h_pct") or 0)

            if pct_change > 1.0:
                # Active! Check sooner.
                next_check_hours = 1
                priority = 1
                logger.debug(f"  [{asin}] Active price change ({pct_change:.1f}%). High priority.")

            # Signal: Stable for long time
            elif (stats.get("price_volatility_30d") or 0) < 0.1:
                # Very stable. Check less often.
                next_check_hours = 12
                # But if it's super popular, don't ignore it for THAT long
                if review_count > 1000:
                    next_check_hours = 6

                priority = 3
                logger.debug(f"  [{asin}] Price stable. Low priority.")

            # Signal: High Savings (Potential Deal)
            # If current price is much lower than 30d max, keep watching closely
            max_30d = float(stats.get("max_price_30d") or 0)
            current = float(stats.get("current_price") or 0)
            if max_30d > 0 and current > 0:
                discount_from_high = ((max_30d - current) / max_30d) * 100
                if discount_from_high > 20:
                    # It's deeply discounted, watch for further drops or expiration
                    next_check_hours = 2
                    priority = 1

            # Update Product
            product.check_priority = priority
            product.next_check_at = now + timedelta(hours=next_check_hours)

            self.db_session.commit()

        except Exception as e:
            logger.error(f"Error updating schedule for {asin}: {e}")

    def _calculate_window_stats(self, asin: str, since: datetime) -> dict:
        """Calculate price statistics for a time window."""
        records = (
            self.db_session.query(PriceHistory.price_amount)
            .filter(and_(PriceHistory.asin == asin, PriceHistory.captured_at >= since))
            .order_by(PriceHistory.captured_at)
            .all()
        )

        if not records:
            return {
                "min_price": None,
                "max_price": None,
                "avg_price": None,
                "first_price": None,
                "volatility": None,
            }

        prices = [float(r[0]) for r in records]

        # Calculate volatility (standard deviation)
        volatility = None
        if len(prices) > 1:
            avg = sum(prices) / len(prices)
            variance = sum((p - avg) ** 2 for p in prices) / len(prices)
            volatility = variance**0.5

        return {
            "min_price": min(prices),
            "max_price": max(prices),
            "avg_price": sum(prices) / len(prices),
            "first_price": prices[0],
            "volatility": volatility,
        }
