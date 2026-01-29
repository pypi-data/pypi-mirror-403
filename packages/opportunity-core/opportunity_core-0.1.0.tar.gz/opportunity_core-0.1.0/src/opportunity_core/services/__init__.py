"""Core services for Opportunity Radar."""

from opportunity_core.services.database_manager import (
    DatabaseManager,
    get_db,
    get_db_manager,
    init_database,
)
from opportunity_core.services.deal_detection import DealDetectionEngine, DealType, DetectedDeal
from opportunity_core.services.price_monitoring import PriceMonitoringService
from opportunity_core.services.product_discovery import ProductDiscoveryService

__all__ = [
    "DatabaseManager",
    "init_database",
    "get_db_manager",
    "get_db",
    "ProductDiscoveryService",
    "PriceMonitoringService",
    "DealDetectionEngine",
    "DealType",
    "DetectedDeal",
]
