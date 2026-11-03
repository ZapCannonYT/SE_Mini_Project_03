"""SQLAlchemy models (data layer). Importing this package registers every table on Base.metadata."""
from app.models.audit import AuditLog
from app.models.forecast import Forecast, ForecastPoint, HorizonUnit
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.recommendation import Recommendation, RiskLevel
from app.models.sales import SalesRecord
from app.models.setting import Setting
from app.models.user import Role, User

__all__ = [
    "AuditLog",
    "Forecast",
    "ForecastPoint",
    "HorizonUnit",
    "Inventory",
    "Product",
    "Recommendation",
    "RiskLevel",
    "Role",
    "SalesRecord",
    "Setting",
    "User",
]
