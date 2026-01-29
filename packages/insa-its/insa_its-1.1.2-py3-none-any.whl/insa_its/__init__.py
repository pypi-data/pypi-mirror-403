"""
insAIts SDK - pip install insa-its
Multi-LLM Agent Deciphering + Shorthand Detection

Features:
- Real-time anomaly detection (shorthand, jargon, context loss)
- LLM fingerprint validation
- Decipher mode (translate AI-to-AI communication)
- Terminal dashboard for live monitoring
- LangChain & CrewAI integrations
"""

from .monitor import insAItsMonitor
from .detector import AnomalyDetector
from .license import LicenseManager, get_license_manager
from .config import FREE_TIER_LIMITS, FEATURES, get_feature
from .exceptions import (
    insAItsError,
    RateLimitError,
    APIError,
    AuthenticationError,
    EmbeddingError,
)

# Dashboard (requires: pip install rich)
try:
    from .dashboard import LiveDashboard, SimpleDashboard, create_dashboard
    DASHBOARD_AVAILABLE = True
except ImportError:
    DASHBOARD_AVAILABLE = False
    LiveDashboard = None
    SimpleDashboard = None
    create_dashboard = None

__version__ = "1.1.0"
__all__ = [
    # Core
    "insAItsMonitor",
    "AnomalyDetector",
    "LicenseManager",
    "get_license_manager",
    # Config
    "FREE_TIER_LIMITS",
    "FEATURES",
    "get_feature",
    # Exceptions
    "insAItsError",
    "RateLimitError",
    "APIError",
    "AuthenticationError",
    "EmbeddingError",
    # Dashboard
    "LiveDashboard",
    "SimpleDashboard",
    "create_dashboard",
    "DASHBOARD_AVAILABLE",
]