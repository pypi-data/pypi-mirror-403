"""Database connection and session management."""

import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from opportunity_core.models.database import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and sessions."""

    def __init__(self, database_url: str, echo: bool = False, pool_size: int = 10, max_overflow: int = 20):
        """
        Initialize database manager.

        Args:
            database_url: SQLAlchemy database URL (e.g., postgresql://user:pass@host:port/db)
            echo: Whether to echo SQL queries (for debugging)
            pool_size: Number of connections to keep in pool
            max_overflow: Maximum overflow connections beyond pool_size
        """
        self.database_url = database_url
        self.engine = create_engine(
            database_url,
            echo=echo,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=3600,  # Recycle connections after 1 hour
        )

        # Configure SQLite for better concurrency if using SQLite
        if "sqlite" in database_url.lower():

            @event.listens_for(Engine, "connect")
            def set_sqlite_pragma(dbapi_conn, connection_record):
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        logger.info(f"Database manager initialized: {self._safe_url()}")

    def _safe_url(self) -> str:
        """Return database URL with password masked."""
        if "@" in self.database_url:
            parts = self.database_url.split("@")
            if ":" in parts[0]:
                user_pass = parts[0].split("://")[-1]
                user = user_pass.split(":")[0] if ":" in user_pass else user_pass
                return f"{self.database_url.split('://')[0]}://{user}:***@{parts[1]}"
        return self.database_url

    def create_tables(self):
        """Create all tables in the database."""
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created successfully")

    def drop_tables(self):
        """Drop all tables in the database (USE WITH CAUTION)."""
        logger.warning("Dropping all database tables...")
        Base.metadata.drop_all(bind=self.engine)
        logger.warning("All database tables dropped")

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Get a database session with automatic commit/rollback.

        Usage:
            with db_manager.get_session() as session:
                product = session.query(Product).filter_by(asin="B08TEST").first()
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    def get_raw_session(self) -> Session:
        """
        Get a raw database session (caller must manage commit/rollback/close).

        Use get_session() context manager instead when possible.
        """
        return self.SessionLocal()

    def health_check(self) -> bool:
        """
        Check if database connection is healthy.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            with self.get_session() as session:
                session.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    def close(self):
        """Close database engine and dispose of connection pool."""
        logger.info("Closing database connections...")
        self.engine.dispose()
        logger.info("Database connections closed")


# Singleton instance for application use
_db_manager: DatabaseManager | None = None


def init_database(database_url: str, echo: bool = False) -> DatabaseManager:
    """
    Initialize the global database manager.

    Args:
        database_url: SQLAlchemy database URL
        echo: Whether to echo SQL queries

    Returns:
        DatabaseManager instance
    """
    global _db_manager
    _db_manager = DatabaseManager(database_url, echo=echo)
    return _db_manager


def get_db_manager() -> DatabaseManager:
    """
    Get the global database manager instance.

    Raises:
        RuntimeError: If database not initialized
    """
    if _db_manager is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _db_manager


# Dependency injection helper for FastAPI / web frameworks
def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for getting database session.

    Usage:
        @app.get("/products")
        def get_products(db: Session = Depends(get_db)):
            return db.query(Product).all()
    """
    db_manager = get_db_manager()
    with db_manager.get_session() as session:
        yield session
