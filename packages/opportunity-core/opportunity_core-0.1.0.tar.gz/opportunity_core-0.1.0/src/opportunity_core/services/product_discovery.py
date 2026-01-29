"""Product discovery service - crawls Amazon to build ASIN pool."""

import logging
import time
from datetime import UTC, datetime
from typing import Any, Callable, Optional

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from opportunity_core.models.database import Product
from opportunity_core.utils.api_helper import call_with_backoff
from opportunity_core.utils.authentication import Authentication, AuthenticationConfig
from paapi5_python_sdk.api.default_api import DefaultApi
from paapi5_python_sdk.models import SearchItemsRequest, SearchItemsResource
from paapi5_python_sdk.rest import ApiException

logger = logging.getLogger(__name__)


class ProductDiscoveryService:
    """Discovers and stores ASINs from Amazon PA API."""

    def __init__(
        self,
        api_client: DefaultApi,
        partner_tag: str,
        partner_type: str,
        marketplace: str,
        db_session: Session,
    ):
        """
        Initialize product discovery service.

        Args:
            api_client: Authenticated PA API client
            partner_tag: Amazon partner tag
            partner_type: Partner type (e.g., 'Associates')
            marketplace: Amazon marketplace domain
            db_session: Database session
        """
        self.api_client = api_client
        self.partner_tag = partner_tag
        self.partner_type = partner_type
        self.marketplace = marketplace
        self.db_session = db_session

    def discover_products(
        self,
        keywords: str,
        search_index: str = "All",
        max_pages: int = 10,
        category: Optional[str] = None,
        on_product_found: Optional[Callable[[Product], None]] = None,
    ) -> int:
        """
        Discover products using keyword search and store in database.

        Args:
            keywords: Search keywords
            search_index: Amazon search index (category)
            max_pages: Maximum number of pages to crawl (max 10)
            category: Optional category tag for discovered products
            on_product_found: Optional callback when product is discovered

        Returns:
            Number of new products discovered
        """
        new_products = 0
        updated_products = 0
        items_per_page = 10  # PA API maximum

        logger.info(f"🔍 Starting product discovery: '{keywords}' (max {max_pages} pages)")

        try:
            for page in range(1, min(max_pages, 10) + 1):
                logger.info(f"  Page {page}/{max_pages}...")

                # Minimal resources for discovery - we only need identifiers
                request = SearchItemsRequest(
                    partner_tag=self.partner_tag,
                    partner_type=self.partner_type,
                    marketplace=self.marketplace,
                    keywords=keywords,
                    search_index=search_index,
                    resources=[
                        SearchItemsResource.ITEMINFO_TITLE,
                        SearchItemsResource.IMAGES_PRIMARY_LARGE,
                    ],
                    item_count=items_per_page,
                    item_page=page,
                )

                # Use backoff for API call
                response = call_with_backoff(
                    self.api_client.search_items,
                    request,
                    max_retries=10,  # Increased from 3 to 10
                    initial_delay=5.0,
                    max_delay=120.0,  # Allow waiting up to 2 minutes
                    backoff_factor=2.0,
                )

                # Process results
                if response and hasattr(response, "search_result") and response.search_result:
                    if hasattr(response.search_result, "items") and response.search_result.items:
                        for item in response.search_result.items:
                            product = self._extract_and_store_product(item, keywords, category)
                            if product:
                                if product.first_discovered_at == product.last_seen_at:
                                    new_products += 1
                                else:
                                    updated_products += 1

                                if on_product_found:
                                    on_product_found(product)
                    else:
                        logger.warning(f"  Page {page}: No items in response")
                        break
                else:
                    logger.warning(f"  Page {page}: Empty response")
                    break

                # Rate limiting (User recommendation: ~1.2s for SearchItems)
                if page < max_pages:
                    time.sleep(12.0)  # Increased to 12.0s to be safe

            logger.info(
                f"✅ Discovery complete: {new_products} new, {updated_products} updated (keywords: '{keywords}')"
            )

        except ApiException as e:
            logger.error(f"PA API error during discovery: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during discovery: {e}")

        return new_products

    @staticmethod
    def generate_keyword_variations(
        base_keywords: list[str], add_letters: bool = True, letters: str = "abcdefghijklmnopqrstuvwxyz"
    ) -> list[str]:
        """
        Generate keyword variations to improve discovery coverage.

        Amazon's SearchItems API returns different results for queries like:
        - "temizlik" vs "temizlik a" vs "temizlik b"

        This helps overcome pagination limits and discover more diverse products.

        Args:
            base_keywords: List of base keywords (e.g., ["temizlik", "kozmetik"])
            add_letters: Whether to add letter suffixes (a-z)
            letters: Letters to append (default: a-z)

        Returns:
            Expanded list with variations

        Example:
            >>> generate_keyword_variations(["temizlik"], add_letters=True)
            ["temizlik", "temizlik a", "temizlik b", ..., "temizlik z"]
        """
        variations = []

        for keyword in base_keywords:
            # Always include the base keyword
            variations.append(keyword)

            # Add letter variations if enabled
            if add_letters:
                for letter in letters:
                    variations.append(f"{keyword} {letter}")

        return variations

    def _extract_and_store_product(
        self, item: Any, discovery_keywords: str, category: Optional[str] = None
    ) -> Optional[Product]:
        """
        Extract product data from API response and store/update in database.

        Args:
            item: PA API item response
            discovery_keywords: Keywords used to discover this product
            category: Optional category tag

        Returns:
            Product instance if successful, None otherwise
        """
        try:
            # Extract ASIN
            asin = item.asin if hasattr(item, "asin") else None
            if not asin:
                return None

            # Extract optional metadata
            title = None
            if hasattr(item, "item_info") and item.item_info:
                if hasattr(item.item_info, "title") and item.item_info.title:
                    title = item.item_info.title.display_value

            image_url = None
            if hasattr(item, "images") and item.images:
                if hasattr(item.images, "primary") and item.images.primary:
                    if hasattr(item.images.primary, "large") and item.images.primary.large:
                        image_url = item.images.primary.large.url

            url = None
            if hasattr(item, "detail_page_url"):
                url = item.detail_page_url

            # Upsert product (insert or update if exists)
            now = datetime.now(UTC)

            # PostgreSQL upsert syntax
            stmt = insert(Product).values(
                asin=asin,
                title=title,
                url=url or f"https://{self.marketplace}/dp/{asin}",
                image_url=image_url,
                category=category,
                discovery_keywords=discovery_keywords,
                first_discovered_at=now,
                last_seen_at=now,
                is_active=True,
                check_priority=1,
            )

            # On conflict, update last_seen_at and metadata
            stmt = stmt.on_conflict_do_update(
                index_elements=["asin"],
                set_={
                    "last_seen_at": now,
                    "title": title if title else Product.title,
                    "url": url if url else Product.url,
                    "image_url": image_url if image_url else Product.image_url,
                    "category": category if category else Product.category,
                    "is_active": True,
                },
            )

            self.db_session.execute(stmt)
            self.db_session.commit()

            # Fetch the product to return
            product = self.db_session.query(Product).filter_by(asin=asin).first()
            return product

        except Exception as e:
            logger.error(f"Error storing product: {e}")
            self.db_session.rollback()
            return None

    def discover_from_keyword_list(
        self,
        keywords_list: list[str],
        search_index: str = "All",
        max_pages_per_keyword: int = 10,
        category: Optional[str] = None,
        use_variations: bool = False,
        variation_letters: str = "abcdefghijklmnopqrstuvwxyz",
    ) -> dict[str, int]:
        """
        Discover products from multiple keyword searches.

        Args:
            keywords_list: List of keyword strings
            search_index: Amazon search index
            max_pages_per_keyword: Pages to crawl per keyword
            category: Category tag for discovered products
            use_variations: Whether to generate keyword variations with letters
            variation_letters: Letters to use for variations (default: a-z)

        Returns:
            Dictionary with statistics: {total_new, total_updated, keywords_searched}

        Example:
            # Simple usage (11 keywords)
            discover_from_keyword_list(["temizlik", "kozmetik"])

            # With variations (11 keywords → 11 + 11*26 = 297 keyword variations)
            discover_from_keyword_list(
                ["temizlik", "kozmetik"],
                use_variations=True
            )

            # With limited variations (first 5 letters only)
            discover_from_keyword_list(
                ["temizlik", "kozmetik"],
                use_variations=True,
                variation_letters="abcde"
            )
        """
        # Generate variations if requested
        if use_variations:
            original_count = len(keywords_list)
            keywords_list = self.generate_keyword_variations(keywords_list, add_letters=True, letters=variation_letters)
            logger.info(f"📝 Generated {len(keywords_list)} keyword variations from {original_count} base keywords")

        total_new = 0
        total_updated = 0

        logger.info("=" * 80)
        logger.info(f"🚀 MULTI-KEYWORD DISCOVERY STARTED")
        logger.info(f"   Keywords: {len(keywords_list)}")
        logger.info(f"   Pages per keyword: {max_pages_per_keyword}")
        logger.info(f"   Category: {category or 'None'}")
        logger.info(f"   Variations: {'Enabled' if use_variations else 'Disabled'}")
        logger.info("=" * 80)

        for i, keywords in enumerate(keywords_list, 1):
            logger.info(f"\n>>> Keyword {i}/{len(keywords_list)}: '{keywords}'")

            new = self.discover_products(
                keywords=keywords,
                search_index=search_index,
                max_pages=max_pages_per_keyword,
                category=category,
            )

            total_new += new

            # Rate limiting between keywords
            if i < len(keywords_list):
                time.sleep(20.0)  # Increased to 20.0s between keywords

        logger.info("\n" + "=" * 80)
        logger.info(f"✅ DISCOVERY COMPLETED")
        logger.info(f"   Total new products: {total_new}")
        logger.info(f"   Keywords searched: {len(keywords_list)}")
        logger.info("=" * 80)

        return {
            "total_new": total_new,
            "keywords_searched": len(keywords_list),
        }
