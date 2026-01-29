import logging
import requests
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO

from opportunity_core.utils.comment_generator import CommentGenerator

logger = logging.getLogger(__name__)

# ... (existing imports)


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
    deal_tag: str = "FIRSAT"  # "FIRSAT" or "FİYAT DÜŞTÜ"


class TelegramNotifier:
    """Handles posting deal notifications to Telegram channel."""

    def __init__(self, bot_token: str, channel_id: str, environment: str = "production"):
        """
        Initialize Telegram Bot.

        Args:
            bot_token: Telegram Bot token from @BotFather
            channel_id: Telegram channel ID (e.g., @channelname or -100123456789)
            environment: Environment mode ('production' or 'development')
        """
        self.bot_token = bot_token
        self.channel_id = channel_id
        self.environment = environment
        self.api_url = f"https://api.telegram.org/bot{bot_token}"

        # Verify bot connection
        try:
            response = requests.get(f"{self.api_url}/getMe", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    username = data["result"]["username"]
                    env_label = "🧪 TEST" if environment == "development" else "🚀 PRODUCTION"
                    logger.info(f"Connected to Telegram bot: @{username}")
                    logger.info(f"Environment: {env_label}")
                    logger.info(f"Target channel: {channel_id}")
                    logger.info("Telegram bot initialized successfully")
                else:
                    raise Exception(f"Bot verification failed: {data}")
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"Telegram bot initialization failed: {e}")
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
        Format deal information into a Telegram message.
        Compliant with Telegram Ads guidelines (no excessive caps/emojis).

        Args:
            deal: Deal information

        Returns:
            Formatted message
        """
        # Shorten the affiliate link
        short_url = self.shorten_url(deal.detail_page_url)

        # 1. Header (Clean, no caps lock)
        # "Fırsat %45 İndirim" or "Fiyat Düştü %10 Kazanç"
        if deal.deal_tag == "FİYAT DÜŞTÜ":
            header = f"Fiyat Düştü %{deal.discount_percentage} Kazanç"
        else:
            header = f"Fırsat %{deal.discount_percentage} İndirim"

        message = f"<b>{header}</b>\n\n"

        # 2. Product Title (Clean)
        message += f"{deal.title}\n\n"

        # 3. Editor's Note (Human-like comment)
        try:
            comment = CommentGenerator.generate_comment(deal)

            # Source is now clean, no need for extra processing
            if comment:
                message += f"<b>Editörün Notu:</b> {comment}\n\n"
        except Exception as e:
            logger.warning(f"Failed to generate comment: {e}")

        # 4. Price Analysis (Bulleted list, professional)
        message += f"<b>Fiyat Analizi:</b>\n"
        # Add strikethrough to old price
        message += f"• Eski Fiyat: <s>{deal.original_price:,.2f} {deal.currency}</s>\n".replace(",", ".")
        message += f"• Yeni Fiyat: {deal.current_price:,.2f} {deal.currency}\n".replace(",", ".")

        savings = deal.original_price - deal.current_price
        message += f"• Kazanç: {savings:,.2f} {deal.currency}\n".replace(",", ".")

        # Historical Context (Clean text, no "WARNING" emojis)
        days_tracked = 0
        if deal.first_discovered_at:
            now = datetime.now(timezone.utc)
            discovered = deal.first_discovered_at
            if discovered.tzinfo is None:
                discovered = discovered.replace(tzinfo=timezone.utc)
            days_tracked = (now - discovered).days

        if deal.lowest_price_180d and deal.current_price <= deal.lowest_price_180d and days_tracked >= 180:
            message += f"• Not: Son 6 ayın en düşük fiyatı.\n"
        elif deal.lowest_price_90d and deal.current_price <= deal.lowest_price_90d and days_tracked >= 90:
            message += f"• Not: Son 3 ayın en düşük fiyatı.\n"
        elif deal.lowest_price_30d and deal.current_price <= deal.lowest_price_30d and days_tracked >= 30:
            message += f"• Not: Son 1 ayın en düşük fiyatı.\n"

        message += "\n"

        # 5. Footer / CTA (Simple link)
        message += f"🔗 <a href='{short_url}'>Fırsata Git</a>\n\n"

        # 6. Tags
        message += "#Amazon #işbirliği"

        return message

    def post_deal(self, deal: DealInfo) -> dict | None:
        """
        Post a deal to Telegram channel.

        Args:
            deal: Deal information to post

        Returns:
            Dict with message_id if successful, None otherwise
        """
        message = self.format_deal_message(deal)
        max_retries = 3

        for attempt in range(max_retries):
            try:
                if deal.image_url:
                    # Download image
                    logger.info(f"Downloading image from: {deal.image_url}")
                    img_response = requests.get(deal.image_url, timeout=20)  # Increased timeout for image download

                    if img_response.status_code == 200:
                        # Send photo with caption using multipart/form-data
                        files = {"photo": ("product.jpg", BytesIO(img_response.content), "image/jpeg")}
                        data = {"chat_id": self.channel_id, "caption": message, "parse_mode": "HTML"}

                        # Increased timeout to 60s for upload
                        response = requests.post(f"{self.api_url}/sendPhoto", files=files, data=data, timeout=60)

                        if response.status_code == 200 and response.json().get("ok"):
                            logger.info("Deal posted to Telegram with image")
                            result = response.json()["result"]
                            return {"message_id": str(result["message_id"])}
                        else:
                            error_msg = response.json().get("description", response.text)
                            logger.error(f"Failed to post deal to Telegram: {error_msg}")
                            # Don't retry client errors (4xx) unless it's 429
                            if 400 <= response.status_code < 500 and response.status_code != 429:
                                return None
                    else:
                        logger.warning(f"Failed to download image: HTTP {img_response.status_code}")
                        # Fallback to text message immediately if image fails
                        # but continue in the same logic flow

                # Send text message if no image or image download failed
                data = {
                    "chat_id": self.channel_id,
                    "text": message,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": False,
                }

                response = requests.post(f"{self.api_url}/sendMessage", json=data, timeout=60)

                if response.status_code == 200 and response.json().get("ok"):
                    logger.info("Deal posted to Telegram without image")
                    result = response.json()["result"]
                    return {"message_id": str(result["message_id"])}
                else:
                    error_msg = response.json().get("description", response.text)
                    logger.error(f"Failed to post deal to Telegram: {error_msg}")
                    if 400 <= response.status_code < 500 and response.status_code != 429:
                        return None

            except requests.exceptions.RequestException as e:
                wait_time = (attempt + 1) * 2
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            except Exception as e:
                logger.error(f"Unexpected error posting to Telegram: {e}")
                return None

        logger.error(f"❌ All {max_retries} attempts to post to Telegram failed.")
        return None
