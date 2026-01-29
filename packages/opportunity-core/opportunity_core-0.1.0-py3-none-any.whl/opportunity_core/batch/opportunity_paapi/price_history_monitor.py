"""
New architecture keyword monitor - discovers products, monitors prices, detects deals.

This replaces the old deal_monitor_unified.py with a price history-based approach.
"""

import argparse
import logging
import time
from datetime import datetime, timezone

from sqlalchemy import func

from opportunity_core.models.database import Product
from opportunity_core.services.database_manager import init_database, get_db_manager
from opportunity_core.services.deal_detection import DealDetectionEngine, DetectedDeal
from opportunity_core.utils.load_config import MonitoringConfig
from opportunity_core.services.price_monitoring import PriceMonitoringService
from opportunity_core.services.product_discovery import ProductDiscoveryService
from opportunity_core.utils.authentication import Authentication, AuthenticationConfig
from opportunity_core.utils.load_config import (
    DatabaseConfig,
    DealConfig,
    PaapiConfig,
    PlatformConfig,
    TelegramConfig,
    TwitterConfig,
)
from opportunity_core.utils.telegram_notifier import DealInfo as TelegramDealInfo
from opportunity_core.utils.telegram_notifier import TelegramNotifier
from opportunity_core.utils.twitter_notifier import DealInfo as TwitterDealInfo
from opportunity_core.utils.twitter_notifier import TwitterNotifier


def setup_logging(environment: str = "production") -> logging.Logger:
    """Setup console logging only (database stores all data)."""
    console_handler = logging.StreamHandler()
    # Simplified format: [HH:MM:SS] MESSAGE
    formatter = logging.Formatter("[%(asctime)s] %(message)s", datefmt="%H:%M:%S")
    console_handler.setFormatter(formatter)

    logging.basicConfig(level=logging.INFO, handlers=[console_handler], force=True)
    return logging.getLogger(__name__)

#TODO Remove this line...
logger = logging.getLogger(__name__)


class PriceHistoryDealMonitor:
    """New architecture deal monitor using price history."""

    def __init__(self, service_name: str | None = None):
        """Initialize the deal monitor."""
        # Load configurations
        self.paapi_config = PaapiConfig()
        self.deal_config = DealConfig()
        self.platform_config = PlatformConfig()
        self.database_config = DatabaseConfig()
        self.service_name = service_name

        # Setup logging
        global logger
        logger = setup_logging(self.platform_config.environment)

        env_emoji = "🧪" if self.platform_config.is_development() else "🚀"
        env_name = "DEVELOPMENT" if self.platform_config.is_development() else "PRODUCTION"
        logger.info(f"{env_emoji} Environment: {env_name}")

        # Initialize database
        logger.info("🔌 Connecting to database...")
        init_database(self.database_config.get_database_url(), echo=False)
        self.db_manager = get_db_manager()
        logger.info("✅ Database connected")

        # Setup PA API authentication
        auth_config = AuthenticationConfig(
            access_key=self.paapi_config.access_key,
            secret_key=self.paapi_config.secret_key,
            partner_tag=self.paapi_config.partner_tag,
            host=self.paapi_config.host,
            region=self.paapi_config.region,
        )
        auth = Authentication(config=auth_config)
        api_client = auth.authenticate()

        # Initialize notifiers
        self.notifiers = []

        if self.platform_config.enable_telegram:
            telegram_config = TelegramConfig()
            self.telegram_notifier = TelegramNotifier(
                bot_token=telegram_config.bot_token,
                channel_id=telegram_config.get_active_channel_id(self.platform_config.environment),
            )
            self.notifiers.append(("Telegram", self.telegram_notifier))
            logger.info("✅ Telegram notifier enabled")

        if self.platform_config.enable_twitter:
            try:
                twitter_config = TwitterConfig()
                self.twitter_notifier = TwitterNotifier(
                    api_key=twitter_config.api_key,
                    api_secret=twitter_config.api_secret,
                    access_token=twitter_config.access_token,
                    access_token_secret=twitter_config.access_token_secret,
                    bearer_token=twitter_config.bearer_token,
                )
                self.notifiers.append(("Twitter", self.twitter_notifier))
                logger.info("✅ Twitter notifier enabled")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Twitter notifier: {e}")
                logger.warning("⚠️  Continuing without Twitter support.")

        if not self.notifiers:
            logger.warning("⚠️  No notifiers enabled! Set ENABLE_TELEGRAM=true or ENABLE_TWITTER=true")

        # Initialize services (with database session)
        with self.db_manager.get_session() as session:
            self.discovery_service = ProductDiscoveryService(
                api_client=api_client,
                partner_tag=self.paapi_config.partner_tag,
                partner_type=self.paapi_config.partner_type,
                marketplace=self.paapi_config.marketplace,
                db_session=session,
            )

            self.price_monitor = PriceMonitoringService(
                api_client=api_client,
                partner_tag=self.paapi_config.partner_tag,
                partner_type=self.paapi_config.partner_type,
                marketplace=self.paapi_config.marketplace,
                db_session=session,
            )

            self.deal_detector = DealDetectionEngine(
                db_session=session,
                cooldown_hours=24,
            )

        # Load monitoring configuration from environment
        self.monitoring_config = MonitoringConfig()

        # Get keywords from config (externalized, no more hard-coded!)
        self.keywords_list = self.monitoring_config.get_keywords_list()
        logger.info(f"📋 Loaded {len(self.keywords_list)} keywords from config")

        logger.info("=" * 80)
        logger.info("✅ INITIALIZATION COMPLETE")
        logger.info("=" * 80)

    def run_discovery_phase(self):
        """Phase 1: Discover new products and build ASIN pool."""
        logger.info("\n" + "=" * 80)
        logger.info("🔍 PHASE 1: PRODUCT DISCOVERY")
        logger.info("=" * 80)

        with self.db_manager.get_session() as session:
            discovery = ProductDiscoveryService(
                api_client=self.discovery_service.api_client,
                partner_tag=self.paapi_config.partner_tag,
                partner_type=self.paapi_config.partner_type,
                marketplace=self.paapi_config.marketplace,
                db_session=session,
            )

            stats = discovery.discover_from_keyword_list(
                keywords_list=self.keywords_list,
                search_index="All",
                max_pages_per_keyword=3,  # Keep at 3 pages (relevance drops after that)
                category="general",
                use_variations=True,  # ENABLED
                variation_letters="abcdefghij",  # Increased to 10 variations (a-j)
            )

            logger.info(f"✅ Discovery phase complete: {stats['total_new']} new products")

    def run_price_monitoring_phase(self, segment_index: int | None = None, total_segments: int = 3):
        """Phase 2: Check prices for all active products."""
        logger.info("\n" + "=" * 80)
        logger.info("💰 PHASE 2: PRICE MONITORING")
        logger.info("=" * 80)

        with self.db_manager.get_session() as session:
            monitor = PriceMonitoringService(
                api_client=self.price_monitor.api_client,
                partner_tag=self.paapi_config.partner_tag,
                partner_type=self.paapi_config.partner_type,
                marketplace=self.paapi_config.marketplace,
                db_session=session,
            )

            # Initialize detector with current session for real-time alerts
            detector = DealDetectionEngine(db_session=session, cooldown_hours=24)

            def on_batch_complete(updated_asins: list[str]):
                if not updated_asins:
                    return

                # logger.info(f"⚡ Real-time detection for {len(updated_asins)} products...")
                deals = detector.detect_deals(target_asins=updated_asins)

                for deal in deals:
                    self._process_and_publish_deal(deal, detector)

            # Calculate segment based on current hour if not provided
            if segment_index is None:
                current_hour = datetime.now(timezone.utc).hour
                segment_index = current_hour % total_segments
                logger.info(f"📊 Auto-calculated segment: {segment_index + 1}/{total_segments} (Hour: {current_hour})")
            else:
                logger.info(f"📊 Manual segment: {segment_index + 1}/{total_segments}")

            stats = monitor.check_prices_for_active_products(
                batch_size=10,
                max_batches=None,
                on_batch_processed=on_batch_complete,
                segment_index=segment_index,
                total_segments=total_segments,
            )

            logger.info(
                f"✅ Price monitoring complete: {stats['products_checked']} checked, {stats['prices_updated']} updated"
            )

    def run_deal_detection_phase(self):
        """Phase 3: Detect deals using price history and publish."""
        logger.info("\n" + "=" * 80)
        logger.info("🎯 PHASE 3: DEAL DETECTION & PUBLISHING")
        logger.info("=" * 80)

        published_count = 0

        with self.db_manager.get_session() as session:
            detector = DealDetectionEngine(db_session=session, cooldown_hours=24)

            deals_generator = detector.detect_deals(limit=None)  # Check all products

            logger.info("Starting deal detection stream...")

            for deal in deals_generator:
                logger.info(f"\n📢 Publishing deal: [{deal.asin}] {deal.product.title[:50]}...")
                logger.info(f"   Type: {deal.deal_type.value}")
                logger.info(f"   Price: {deal.current_price} {deal.currency}")
                logger.info(f"   Reason: {deal.reason}")

                # Publish to all enabled platforms
                if self._process_and_publish_deal(deal, detector):
                    published_count += 1

                time.sleep(5)  # Delay between publications

        logger.info(f"\n✅ Deal detection complete: {published_count} deals published")

    def _publish_to_telegram(self, deal: DetectedDeal) -> str | None:
        """Publish deal to Telegram."""
        try:
            # Determine deal tag (FIRSAT vs FİYAT DÜŞTÜ)
            # If it's an official Amazon deal (indicated in reason or by deal type), use FIRSAT
            # Otherwise, if it's purely a historical drop, use FİYAT DÜŞTÜ
            deal_tag = "FIRSAT"
            if "Amazon Deal" in deal.reason:
                deal_tag = "FIRSAT"
            elif deal.deal_type.value == "ALL_TIME_LOW" or deal.deal_type.value == "DROP_24H":
                # If it's a historical drop without explicit Amazon Deal mention, check savings
                # If savings_percentage matches discount_percentage, it might be official
                # But safer to default to FİYAT DÜŞTÜ for historical comparisons unless we know otherwise
                deal_tag = "FİYAT DÜŞTÜ"

            deal_info = TelegramDealInfo(
                asin=deal.asin,
                title=deal.product.title or "Amazon Deal",
                current_price=deal.current_price,
                original_price=deal.previous_price or deal.current_price * 1.2,
                discount_percentage=int(deal.discount_percentage) if deal.discount_percentage else 0,
                currency=deal.currency,
                image_url=deal.product.image_url,
                detail_page_url=deal.product.url or f"https://{self.paapi_config.marketplace}/dp/{deal.asin}",
                rating=deal.product.rating,
                review_count=deal.product.review_count,
                is_prime_eligible=deal.product.is_prime_eligible,
                lowest_price_30d=deal.lowest_price_30d,
                lowest_price_90d=deal.lowest_price_90d,
                lowest_price_180d=deal.lowest_price_180d,
                first_discovered_at=deal.product.first_discovered_at,
                deal_tag=deal_tag,
            )
            result = self.telegram_notifier.post_deal(deal_info)
            return result.get("message_id") if result else None
        except Exception as e:
            logger.error(f"Telegram publish error: {e}")
            return None

    def _publish_to_twitter(self, deal: DetectedDeal) -> str | None:
        """Publish deal to Twitter."""
        try:
            deal_info = TwitterDealInfo(
                asin=deal.asin,
                title=deal.product.title or "Amazon Deal",
                current_price=deal.current_price,
                original_price=deal.previous_price or deal.current_price * 1.2,
                discount_percentage=int(deal.discount_percentage) if deal.discount_percentage else 15,
                currency=deal.currency,
                detail_page_url=deal.product.url or f"https://{self.paapi_config.marketplace}/dp/{deal.asin}",
                image_url=deal.product.image_url,
                lowest_price_30d=deal.lowest_price_30d,
                lowest_price_90d=deal.lowest_price_90d,
                lowest_price_180d=deal.lowest_price_180d,
                first_discovered_at=deal.product.first_discovered_at,
            )
            result = self.twitter_notifier.post_deal(deal_info)
            return result.get("tweet_id") if result else None
        except Exception as e:
            logger.error(f"Twitter publish error: {e}")
            return None

    def _process_and_publish_deal(self, deal: DetectedDeal, detector: DealDetectionEngine) -> bool:
        """Process a detected deal and publish to enabled platforms."""
        is_published = False

        logger.info(f"\n📢 Publishing deal: [{deal.asin}] {deal.product.title[:50]}...")
        logger.info(f"   Type: {deal.deal_type.value}")
        logger.info(f"   Price: {deal.current_price} {deal.currency}")
        logger.info(f"   Reason: {deal.reason}")

        for platform_name, notifier in self.notifiers:
            try:
                platform_key = platform_name.lower()

                if platform_name == "Telegram":
                    message_id = self._publish_to_telegram(deal)
                    if message_id:
                        logger.info(f"   ✅ Published to {platform_name}")
                        detector.record_alert(deal, platform=platform_key, message_id=message_id)
                        is_published = True

                elif platform_name == "Twitter":
                    # Check rate limit (15 tweets per 24h)
                    if detector.check_platform_rate_limit("twitter", limit=15, window_hours=24):
                        logger.warning(f"   ⚠️ Twitter rate limit reached (15/24h). Skipping {deal.asin}.")
                        continue

                    message_id = self._publish_to_twitter(deal)
                    if message_id:
                        logger.info(f"   ✅ Published to {platform_name}")
                        detector.record_alert(deal, platform=platform_key, message_id=message_id)
                        is_published = True

            except Exception as e:
                logger.error(f"   ❌ Error publishing to {platform_name}: {e}")

        return is_published

    def run_once(self):
        """Run a single complete monitoring cycle."""
        logger.info("\n" + "━" * 80)
        logger.info("🚀 CYCLE BAŞLADI")
        logger.info("━" * 80)

        start_time = time.time()

        # Store stats from each phase
        discovery_stats = {}
        monitoring_stats = {}
        detection_stats = {}

        # Phase 1: Discovery
        with self.db_manager.get_session() as session:
            discovery = ProductDiscoveryService(
                api_client=self.discovery_service.api_client,
                partner_tag=self.paapi_config.partner_tag,
                partner_type=self.paapi_config.partner_type,
                marketplace=self.paapi_config.marketplace,
                db_session=session,
            )
            discovery_stats = discovery.discover_from_keyword_list(
                keywords_list=self.keywords_list,
                search_index="All",
                max_pages_per_keyword=3,
            )

            # Run cleanup for inactive products (once per discovery cycle)
            deleted_count = discovery.cleanup_inactive_products(days_threshold=30)
            logger.info(f"🧹 Cleanup: {deleted_count} inactive products deactivated")

        time.sleep(10)

        # Phase 2: Price Monitoring
        with self.db_manager.get_session() as session:
            monitor = PriceMonitoringService(
                api_client=self.price_monitor.api_client,
                partner_tag=self.paapi_config.partner_tag,
                partner_type=self.paapi_config.partner_type,
                marketplace=self.paapi_config.marketplace,
                db_session=session,
            )
            monitoring_stats = monitor.check_prices_for_active_products(
                batch_size=10,
                max_batches=None,
            )
        time.sleep(10)

        # Phase 3: Deal Detection & Publishing
        published_count = 0
        with self.db_manager.get_session() as session:
            detector = DealDetectionEngine(db_session=session, cooldown_hours=24)
            deals_generator = detector.detect_deals(limit=None)

            for deal in deals_generator:
                for platform_name, notifier in self.notifiers:
                    try:
                        platform_key = platform_name.lower()

                        if platform_name == "Twitter":
                            # Rate Limit Check: Max 13 tweets per 24 hours
                            if detector.check_platform_rate_limit(platform="twitter", limit=13, window_hours=24):
                                logger.warning("🐦 Twitter rate limit reached (13/24h). Skipping tweet.")
                                continue

                        if platform_name == "Telegram":
                            from opportunity_core.utils.telegram_notifier import DealInfo as TelegramDealInfo

                            deal_info = TelegramDealInfo(
                                asin=deal.asin,
                                title=deal.product.title or "Amazon Deal",
                                current_price=deal.current_price,
                                original_price=deal.previous_price or deal.current_price * 1.2,
                                discount_percentage=int(deal.discount_percentage) if deal.discount_percentage else 0,
                                currency=deal.currency,
                                image_url=deal.product.image_url,
                                detail_page_url=deal.product.url
                                or f"https://{self.paapi_config.marketplace}/dp/{deal.asin}",
                                rating=deal.product.rating,
                                review_count=deal.product.review_count,
                                is_prime_eligible=deal.product.is_prime_eligible,
                                lowest_price_30d=deal.lowest_price_30d,
                                lowest_price_90d=deal.lowest_price_90d,
                                lowest_price_180d=deal.lowest_price_180d,
                                first_discovered_at=deal.product.first_discovered_at,
                            )
                            result = notifier.post_deal(deal_info)
                            if result and result.get("message_id"):
                                detector.record_alert(deal, platform=platform_key, message_id=result.get("message_id"))
                                published_count += 1

                    except Exception as e:
                        logger.error(f"   ❌ {platform_name} error: {e}")

                time.sleep(5)

        elapsed = time.time() - start_time

        # Calculate total database stats
        with self.db_manager.get_session() as session:
            from opportunity_core.models.database import Product

            total_products = session.query(Product).count()
            active_products = session.query(Product).filter(Product.is_active == True).count()

        # Print comprehensive summary
        logger.info("\n" + "━" * 80)
        logger.info("📊 CYCLE ÖZET")
        logger.info("━" * 80)
        logger.info(f"⏱️  Süre: {elapsed / 60:.1f} dakika ({elapsed:.0f} saniye)")
        logger.info("")
        logger.info(f"📦 FAZ 1 - ÜRÜN KEŞFİ:")
        logger.info(f"   • {discovery_stats.get('keywords_searched', 0)} keyword tarandı")
        logger.info(f"   • {discovery_stats.get('total_new', 0)} YENİ ürün keşfedildi")
        logger.info("")
        logger.info(f"💰 FAZ 2 - FİYAT TAKİBİ:")
        logger.info(f"   • {monitoring_stats.get('products_checked', 0)} ürün kontrol edildi")
        logger.info(f"   • {monitoring_stats.get('prices_updated', 0)} fiyat güncellendi")
        logger.info(f"   • {monitoring_stats.get('errors', 0)} hata")
        logger.info("")
        logger.info(f"🎯 FAZ 3 - FIRSAT TESPİTİ:")
        logger.info(f"   • {published_count} FIRSAT yayınlandı")
        logger.info("")
        logger.info(f"📈 VERİTABANI DURUMU:")
        logger.info(f"   • Toplam ürün: {total_products}")
        logger.info(f"   • Aktif ürün: {active_products}")
        logger.info("━" * 80)

    def _should_run_initial_discovery(self, lookback_hours: int) -> bool:
        """
        Check if we should run discovery on startup.
        If the system was active recently (last_seen_at < lookback_hours), skip initial discovery.
        """
        try:
            with self.db_manager.get_session() as session:
                # Get the most recent last_seen_at from Product table
                last_seen = session.query(func.max(Product.last_seen_at)).scalar()

                if not last_seen:
                    logger.info("🆕 No products found in database. Running initial discovery.")
                    return True

                # Ensure last_seen is timezone-aware (UTC)
                if last_seen.tzinfo is None:
                    last_seen = last_seen.replace(tzinfo=timezone.utc)

                now = datetime.now(timezone.utc)
                diff = now - last_seen
                hours_diff = diff.total_seconds() / 3600

                if hours_diff < lookback_hours:
                    logger.info(f"⏭️  System active recently ({hours_diff:.1f}h ago). Skipping initial discovery.")
                    return False

                logger.info(f"🔍 System inactive for {hours_diff:.1f}h. Running initial discovery.")
                return True

        except Exception as e:
            logger.error(f"⚠️ Error checking initial discovery status: {e}")
            return True  # Fail safe: run discovery

    def _should_run_initial_monitoring(self, lookback_minutes: int) -> tuple[bool, float]:
        """
        Check if we should run price monitoring on startup.

        Returns:
            tuple[bool, float]: (should_run, minutes_since_last_update)
        """
        # SKIP SMART WAIT IN DEVELOPMENT
        if self.platform_config.is_development():
            logger.info("🧪 Development mode: Skipping smart wait. Running monitoring immediately.")
            return True, 0.0

        try:
            with self.db_manager.get_session() as session:
                from opportunity_core.models.database import PriceStatistics

                # Get the most recent updated_at from PriceStatistics table
                last_update = session.query(func.max(PriceStatistics.updated_at)).scalar()

                if not last_update:
                    logger.info("🆕 No price history found. Running initial monitoring.")
                    return True, 0.0

                # Ensure last_update is timezone-aware (UTC)
                if last_update.tzinfo is None:
                    last_update = last_update.replace(tzinfo=timezone.utc)

                now = datetime.now(timezone.utc)
                diff = now - last_update
                minutes_diff = diff.total_seconds() / 60

                if minutes_diff < lookback_minutes:
                    logger.info(f"⏭️  Prices checked recently ({minutes_diff:.1f}m ago). Skipping initial monitoring.")
                    return False, minutes_diff

                logger.info(f"💰 Prices not checked for {minutes_diff:.1f}m. Running initial monitoring.")
                return True, minutes_diff

        except Exception as e:
            logger.error(f"⚠️ Error checking initial monitoring status: {e}")
            return True, 0.0  # Fail safe: run monitoring

    def run_continuous(self, interval_seconds: int = 3600, discovery_interval_cycles: int = 4):
        """
        Run continuous monitoring with intervals.

        Args:
            interval_seconds: Sleep time between cycles (default 3600s)
            discovery_interval_cycles: Run discovery every N cycles (default 4 = 12h if interval is 3h)
        """
        logger.info(f"🔄 Starting continuous monitoring (Interval: {interval_seconds}s)")
        logger.info(f"📅 Product Discovery will run every {discovery_interval_cycles} cycles")

        cycle_count = 0

        while True:
            try:
                # Schedule Logic (TRT is UTC+3)
                # 01:00 TRT = 22:00 UTC -> Discovery
                # 02:00 - 09:00 TRT = 23:00 - 06:00 UTC -> Sleep
                # 09:00 - 01:00 TRT = 06:00 - 22:00 UTC -> Monitoring

                now_utc = datetime.now(timezone.utc)
                hour_utc = now_utc.hour

                # 1. Nighttime Pause (02:00 - 09:00 TRT)
                if hour_utc >= 23 or hour_utc < 6:
                    logger.info(f"🌙 Nighttime pause (02:00-09:00 TRT). Sleeping for 1 hour...")
                    time.sleep(3600)
                    continue

                cycle_count += 1
                logger.info(f"\n🚀 STARTING CYCLE {cycle_count}")

                # 2. Discovery Phase (01:00 TRT / 22:00 UTC)
                # We run discovery only if it's the 22:00 UTC hour
                run_discovery = hour_utc == 22

                # Smart Startup Override:
                # If it's the very first cycle after restart, and we are NOT in the discovery hour,
                # check if we missed a discovery recently or if the DB is empty.
                if cycle_count == 1 and not run_discovery:
                    # Only run initial discovery if DB is empty or very stale (e.g. > 24h)
                    # We don't want to force discovery on every restart during the day
                    if self._should_run_initial_discovery(lookback_hours=24):
                        logger.info("🆕 Initial discovery triggered by smart startup.")
                        run_discovery = True

                if run_discovery:
                    logger.info("🔍 Phase 1: Product Discovery (Scheduled 01:00 TRT)")
                    self.run_discovery_phase()

                    # CRITICAL: Do NOT run monitoring after discovery at night.
                    # User requested: "Keşiften sonra herhangi bir process çalışmayacak"
                    # So we sleep until the next cycle (which will likely hit the night pause)
                    logger.info("😴 Discovery finished. Skipping monitoring to respect night schedule.")
                    logger.info(f"\n⏰ Waiting {interval_seconds}s until next cycle...\n")
                    time.sleep(interval_seconds)
                    continue

                # 3. Monitoring Phase (Segmented)
                # We split the workload into 3 segments to run every hour
                total_segments = 3
                current_segment = (cycle_count - 1) % total_segments

                # Smart Startup for Price Monitoring:
                if cycle_count == 1:
                    should_run_monitoring, minutes_since_last = self._should_run_initial_monitoring(lookback_minutes=60)
                else:
                    should_run_monitoring = True
                    minutes_since_last = 0.0

                if should_run_monitoring:
                    logger.info(f"💰 Phase 2: Price Monitoring (Segment {current_segment + 1}/{total_segments})")

                    updated_asins_in_segment = []

                    def on_batch_complete_segment(batch_asins: list[str]):
                        updated_asins_in_segment.extend(batch_asins)
                        with self.db_manager.get_session() as session:
                            detector = DealDetectionEngine(db_session=session, cooldown_hours=24)
                            deals = detector.detect_deals(target_asins=batch_asins)
                            for deal in deals:
                                self._process_and_publish_deal(deal, detector)

                    with self.db_manager.get_session() as session:
                        monitor = PriceMonitoringService(
                            api_client=self.price_monitor.api_client,
                            partner_tag=self.paapi_config.partner_tag,
                            partner_type=self.paapi_config.partner_type,
                            marketplace=self.paapi_config.marketplace,
                            db_session=session,
                        )

                        monitor.check_prices_for_active_products(
                            batch_size=10,
                            max_batches=None,
                            on_batch_processed=on_batch_complete_segment,
                            segment_index=current_segment,
                            total_segments=total_segments,
                        )

                    logger.info(f"🎯 Phase 3: Deal Detection (Targeted for {len(updated_asins_in_segment)} products)")
                    logger.info("✅ Deal detection handled in real-time during monitoring.")

                else:
                    remaining_seconds = max(0, interval_seconds - int(minutes_since_last * 60))
                    logger.info(f"⏭️  Skipping Price Monitoring (Run {minutes_since_last:.1f}m ago).")
                    logger.info(f"⏳ Smart Wait: Sleeping for {remaining_seconds}s to sync with schedule...")
                    time.sleep(remaining_seconds)
                    continue

                logger.info(f"\n⏰ Waiting {interval_seconds}s until next cycle...\n")
                time.sleep(interval_seconds)

            except KeyboardInterrupt:
                logger.info("\n⏹️  Shutting down gracefully...")
                break
            except Exception as e:
                logger.error(f"❌ Error in monitoring cycle: {e}", exc_info=True)
                logger.info(f"⏰ Retrying in {interval_seconds}s...")
                time.sleep(interval_seconds)

    def run_test_notification(self):
        """Run a single test notification with dummy data."""
        logger.info("\n" + "=" * 80)
        logger.info("🧪 RUNNING TEST NOTIFICATION")
        logger.info("=" * 80)

        from opportunity_core.services.deal_detection import DealType
        from opportunity_core.models.database import PriceStatistics

        # Create dummy product
        dummy_product = Product(
            asin="TEST123456",
            title="Philips Airfryer XXL Smart Sensing Fritöz (Test Ürünü)",
            url="https://www.amazon.com.tr/dp/TEST123456",
            image_url="https://m.media-amazon.com/images/I/61q6x-g5iJL._AC_SL1500_.jpg",
            rating=4.8,
            review_count=1500,
            is_prime_eligible=True,
            first_discovered_at=datetime.now(timezone.utc),
        )

        # Create dummy statistics
        dummy_stats = PriceStatistics(
            asin="TEST123456",
            current_price=3000.00,
            min_price_30d=4500.00,
            avg_price_30d=5000.00,
            min_price_all_time=3000.00,
        )

        # Create dummy deal
        dummy_deal = DetectedDeal(
            asin="TEST123456",
            deal_type=DealType.ALL_TIME_LOW,
            current_price=3000.00,
            previous_price=5000.00,
            discount_amount=2000.00,
            discount_percentage=40.0,
            currency="TRY",
            product=dummy_product,
            statistics=dummy_stats,
            confidence_score=1.0,
            reason="Test Notification (All Time Low)",
            lowest_price_30d=4500.00,
            lowest_price_90d=4800.00,
            lowest_price_180d=5000.00,
        )

        logger.info("Generated dummy deal data.")

        # Publish to Telegram
        if self.platform_config.enable_telegram:
            logger.info("Sending to Telegram...")
            msg_id = self._publish_to_telegram(dummy_deal)
            if msg_id:
                logger.info(f"✅ Telegram test successful! Message ID: {msg_id}")
            else:
                logger.error("❌ Telegram test failed.")

        # Publish to Twitter
        if self.platform_config.enable_twitter:
            logger.info("Sending to Twitter...")
            tweet_id = self._publish_to_twitter(dummy_deal)
            if tweet_id:
                logger.info(f"✅ Twitter test successful! Tweet ID: {tweet_id}")
            else:
                logger.error("❌ Twitter test failed.")

        logger.info("\nTest complete. Exiting.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Amazon Deal Monitor - Price History Architecture")
    parser.add_argument(
        "--mode",
        choices=["once", "continuous", "discovery", "monitoring", "detection", "test_notification"],
        default="once",
        help="Run mode",
    )
    parser.add_argument(
        "--segment",
        type=int,
        help="Specific segment index to run (0-based)",
    )
    parser.add_argument(
        "--total-segments",
        type=int,
        default=3,
        help="Total number of segments (default: 3)",
    )

    args = parser.parse_args()

    monitor = PriceHistoryDealMonitor(service_name="keyword-monitor")

    if args.mode == "once":
        monitor.run_once()
    elif args.mode == "continuous":
        monitor.run_continuous(interval_seconds=args.interval)
    elif args.mode == "discovery":
        monitor.run_discovery_phase()
    elif args.mode == "monitoring":
        monitor.run_price_monitoring_phase(segment_index=args.segment, total_segments=args.total_segments)
    elif args.mode == "detection":
        monitor.run_deal_detection_phase()
    elif args.mode == "test_notification":
        monitor.run_test_notification()


if __name__ == "__main__":
    main()
