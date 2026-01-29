"""Twitter notification service for Amazon deals."""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO

import requests
import tweepy

from opportunity_core.utils.comment_generator import CommentGenerator

logger = logging.getLogger(__name__)


@dataclass
class DealInfo:
    """Data class for deal information."""

    title: str
    current_price: float
    original_price: float
    discount_percentage: int
    currency: str
    asin: str
    detail_page_url: str
    image_url: str | None = None
    category: str | None = None  # Product category
    rating: float | None = None  # Product rating
    review_count: int | None = None  # Number of reviews
    seller_name: str | None = None  # Merchant/seller name
    seller_feedback_count: int | None = None  # Seller feedback count
    seller_feedback_rating: float | None = None  # Seller feedback rating
    is_amazon_fulfilled: bool = False  # Amazon satıcı mı?
    availability_message: str | None = None  # Availability message
    stock_quantity: int | None = None  # Available stock
    is_prime_eligible: bool = False  # Prime üyelerine özel
    is_free_shipping: bool = False  # Ücretsiz kargo
    lowest_price_30d: float | None = None
    lowest_price_90d: float | None = None
    lowest_price_180d: float | None = None
    first_discovered_at: datetime | None = None


class TwitterNotifier:
    """Handles posting deal notifications to Twitter."""

    def __init__(
        self, api_key: str, api_secret: str, access_token: str, access_token_secret: str, bearer_token: str = ""
    ):
        """
        Initialize Twitter API client.

        Args:
            api_key: Twitter API key (Consumer Key)
            api_secret: Twitter API secret (Consumer Secret)
            access_token: Twitter access token
            access_token_secret: Twitter access token secret
            bearer_token: Optional bearer token for v2 API
        """
        try:
            # Use Twitter API v2 Client (supports Free tier)
            self.client = tweepy.Client(
                consumer_key=api_key,
                consumer_secret=api_secret,
                access_token=access_token,
                access_token_secret=access_token_secret,
            )

            # Also keep v1.1 API for media upload
            auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_token_secret)
            self.api = tweepy.API(auth)

            # Verify credentials
            me = self.client.get_me()
            logger.info(f"Twitter authentication successful. User: @{me.data.username}")
        except Exception as e:
            logger.error(f"Twitter authentication failed: {e}")
            raise

    def shorten_url(self, url: str) -> str:
        """
        Shorten URL using TinyURL service.

        Args:
            url: Long URL to shorten

        Returns:
            Shortened URL or original if service fails
        """
        try:
            response = requests.get(f"http://tinyurl.com/api-create.php?url={url}", timeout=5)
            if response.status_code == 200:
                shortened = response.text
                logger.info(f"URL shortened: {url[:50]}... -> {shortened}")
                return shortened
        except Exception as e:
            logger.warning(f"URL shortening failed: {e}. Using original URL.")
        return url

    def format_deal_message(self, deal: DealInfo) -> str:
        """
        Format deal information into a tweet message with shortened link.

        Args:
            deal: Deal information

        Returns:
            Formatted tweet message
        """
        # Shorten the affiliate link
        short_url = self.shorten_url(deal.detail_page_url)

        # Build compact info for Twitter (280 char limit)
        if deal.is_amazon_fulfilled:
            seller_tag = "Amazon Turkiye"  # Display as "Amazon Turkiye" for Twitter (no Turkish chars)
        elif deal.seller_name:
            # If seller name contains "amazon.com.tr", show as "Amazon Turkiye"
            if "amazon.com.tr" in deal.seller_name.lower():
                seller_tag = "Amazon Turkiye"
            else:
                seller_tag = deal.seller_name[:15]
                # Add seller feedback rating if available (compact format)
                if deal.seller_feedback_rating:
                    seller_tag += f" ⭐{deal.seller_feedback_rating:.1f}"
        else:
            seller_tag = ""
        rating_tag = f"⭐{deal.rating:.1f}" if deal.rating else ""
        review_tag = f"({deal.review_count})" if deal.review_count and deal.review_count < 10000 else ""

        # Add Prime/Shipping badges (compact)
        badges = []
        if deal.is_prime_eligible:
            badges.append("Prime")
        if deal.is_free_shipping:
            badges.append("Ucretsiz Kargo")

        # Build message components (compact for 280 char limit)
        message = f"Fırsat! %{deal.discount_percentage} indirim\n\n"
        message += f"{deal.title[:60]}...\n"

        # Add Human-like Comment (Shortened)
        try:
            comment = CommentGenerator.generate_comment(deal)
            # Source is now clean
            if comment:
                message += f"Editorun Notu: {comment}\n\n"
        except Exception:
            message += "\n"

        # Satıcı bilgileri (compact)
        if deal.is_amazon_fulfilled or (deal.seller_name and "amazon" in deal.seller_name.lower()):
            message += f"Satici: Amazon Turkiye\n"
        elif deal.seller_name:
            message += f"Satici: {deal.seller_name[:20]}\n"
            if deal.seller_feedback_rating:
                message += f"Satici Puani: {deal.seller_feedback_rating:.1f}"
                if deal.seller_feedback_count:
                    message += f" ({deal.seller_feedback_count})\n"
                else:
                    message += "\n"

        # Ürün değerlendirmesi (compact)
        if deal.rating:
            message += f"Urun Puani: {deal.rating:.1f}/5"
            if deal.review_count:
                message += f" ({deal.review_count} yorum)\n"
            else:
                message += "\n"

        # Kargo bilgileri (compact)
        shipping_parts = []
        if deal.is_prime_eligible:
            shipping_parts.append("Prime")
        if deal.is_free_shipping:
            shipping_parts.append("Bedava Kargo")
        if shipping_parts:
            message += " | ".join(shipping_parts) + "\n"

        # Stok durumu (sadece kritik)
        if deal.availability_message and (
            "kaldı" in deal.availability_message.lower() or "son" in deal.availability_message.lower()
        ):
            import re

            numbers = re.findall(r"\d+", deal.availability_message)
            if numbers:
                message += f"SON {numbers[0]} ADET!\n"
            else:
                message += f"Stok azaliyor!\n"

        # Fiyat bilgileri
        message += (
            f"\nFIYAT\n"
            f"Eski: {deal.original_price:.0f} TRY\n"
            f"Yeni: {deal.current_price:.0f} TRY\n"
            f"Tasarruf: {(deal.original_price - deal.current_price):.0f} TRY\n\n"
            f"{short_url}\n\n"
            f"#Amazon #işbirliği"
        )

        return message[:280]  # Twitter character limit

    def post_deal(self, deal: DealInfo) -> dict | None:
        """
        Post a deal to Twitter with product image using API v2.

        Args:
            deal: Deal information to post

        Returns:
            Dict with tweet_id if successful, None otherwise
        """
        try:
            message = self.format_deal_message(deal)

            # Try to download and upload image if URL is available
            media_id = None
            if deal.image_url:
                try:
                    logger.info(f"Downloading image from: {deal.image_url}")
                    response = requests.get(deal.image_url, timeout=10)
                    if response.status_code == 200:
                        image_data = BytesIO(response.content)
                        image_data.name = "image.jpg"
                        # Upload media using v1.1 API (still supported for media)
                        media = self.api.media_upload(filename="image.jpg", file=image_data)
                        media_id = media.media_id
                        logger.info(f"Image uploaded successfully. Media ID: {media_id}")
                    else:
                        logger.warning(f"Failed to download image: HTTP {response.status_code}")
                except Exception as img_error:
                    logger.warning(f"Could not process image: {img_error}. Posting without image.")

            # Post tweet using API v2 (Free tier supported)
            if media_id:
                tweet = self.client.create_tweet(text=message, media_ids=[str(media_id)])
                logger.info(f"Deal posted to Twitter with image. Tweet ID: {tweet.data['id']}")
            else:
                tweet = self.client.create_tweet(text=message)
                logger.info(f"Deal posted to Twitter without image. Tweet ID: {tweet.data['id']}")

            return {"tweet_id": str(tweet.data["id"])}

        except tweepy.TweepyException as e:
            logger.error(f"Failed to post deal to Twitter: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error posting to Twitter: {e}")
            return None

    def post_deal_with_image(self, deal: DealInfo, image_path: str | None = None) -> bool:
        """
        Post a deal to Twitter with an image using API v2.

        Args:
            deal: Deal information to post
            image_path: Optional path to image file

        Returns:
            True if successful, False otherwise
        """
        try:
            message = self.format_deal_message(deal)

            if image_path:
                # Upload media using v1.1 API
                media = self.api.media_upload(image_path)
                # Post tweet with media using v2 API
                tweet = self.client.create_tweet(text=message, media_ids=[str(media.media_id)])
            else:
                # Post without media using v2 API
                tweet = self.client.create_tweet(text=message)

            logger.info(f"Deal posted to Twitter successfully. Tweet ID: {tweet.data['id']}")
            return True

        except tweepy.TweepyException as e:
            logger.error(f"Failed to post deal with image to Twitter: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error posting to Twitter: {e}")
            return False
