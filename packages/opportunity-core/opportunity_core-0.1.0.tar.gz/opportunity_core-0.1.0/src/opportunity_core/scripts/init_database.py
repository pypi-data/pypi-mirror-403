"""Initialize database schema and run migrations."""

import argparse
import logging
import sys

from opportunity_core.models.database import Base
from opportunity_core.services.database_manager import DatabaseManager
from opportunity_core.utils.load_config import DatabaseConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def init_database(database_url: str, drop_existing: bool = False):
    """
    Initialize database schema.

    Args:
        database_url: SQLAlchemy database URL
        drop_existing: If True, drop all existing tables first (DESTRUCTIVE!)
    """
    logger.info("=" * 80)
    logger.info("DATABASE INITIALIZATION")
    logger.info("=" * 80)

    # Initialize database manager
    db_manager = DatabaseManager(database_url, echo=True)

    # Health check
    if not db_manager.health_check():
        logger.error("❌ Database connection failed! Check your DATABASE_URL.")
        sys.exit(1)

    logger.info("✅ Database connection successful")

    # Drop tables if requested
    if drop_existing:
        logger.warning("⚠️  DROPPING ALL EXISTING TABLES...")
        response = input("Are you sure? This will DELETE ALL DATA! Type 'yes' to confirm: ")
        if response.lower() != "yes":
            logger.info("Aborted.")
            return

        db_manager.drop_tables()
        logger.info("✅ All tables dropped")

    # Create tables
    logger.info("Creating database schema...")
    db_manager.create_tables()
    logger.info("✅ Database schema created successfully")

    # Print table information
    logger.info("\n" + "=" * 80)
    logger.info("CREATED TABLES:")
    logger.info("=" * 80)

    tables = [
        ("products", "Stores discovered ASINs for tracking"),
        ("price_history", "Time series price data"),
        ("price_statistics", "Materialized price stats (min/max/avg)"),
        ("alerts_sent", "Tracks sent alerts to prevent duplicates"),
    ]

    for table_name, description in tables:
        logger.info(f"  ✓ {table_name:20} - {description}")

    logger.info("\n" + "=" * 80)
    logger.info("✅ DATABASE READY!")
    logger.info("=" * 80)

    db_manager.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Initialize Amazon Deals Tracker database")
    parser.add_argument(
        "--database-url",
        help="Database URL (default: from .env DATABASE_URL)",
        default=None,
    )
    parser.add_argument(
        "--drop",
        action="store_true",
        help="Drop all existing tables before creating (DESTRUCTIVE!)",
    )

    args = parser.parse_args()

    # Get database URL
    if args.database_url:
        database_url = args.database_url
    else:
        config = DatabaseConfig()
        database_url = config.get_database_url()

    logger.info(f"Database URL: {database_url.split('@')[0]}@***")  # Mask password

    try:
        init_database(database_url, drop_existing=args.drop)
    except Exception as e:
        logger.error(f"❌ Initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
