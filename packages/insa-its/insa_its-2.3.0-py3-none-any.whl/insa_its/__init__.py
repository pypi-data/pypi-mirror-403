"""
insAIts SDK - pip install insa-its
Multi-LLM Agent Communication Monitoring & Hallucination Detection

Features:
- Real-time anomaly detection (shorthand, jargon, context loss)
- LLM fingerprint validation
- Decipher mode (translate AI-to-AI communication)
- Anchor-aware detection (V2: context-preserving false positive suppression)
- Forensic chain tracing (V2: trace anomalies back to root cause)
- Hallucination detection (V2.3: fact tracking, source grounding,
  phantom citation detection, confidence decay tracking)
- Cross-agent contradiction detection (unique to InsAIts)
- Adaptive jargon dictionary with domain-specific dictionaries
- Terminal dashboard for live monitoring
- LangChain & CrewAI integrations
"""

from .monitor import insAItsMonitor
from .detector import AnomalyDetector, Anomaly
from .license import LicenseManager, get_license_manager
from .config import FREE_TIER_LIMITS, FEATURES, get_feature
from .exceptions import (
    insAItsError,
    RateLimitError,
    APIError,
    AuthenticationError,
    EmbeddingError,
    HallucinationError,
)
from .hallucination import (
    FactTracker,
    SourceGrounder,
    SelfConsistencyChecker,
    PhantomCitationDetector,
    ConfidenceDecayTracker,
    FactClaim,
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

__version__ = "2.3.0"
__all__ = [
    # Core
    "insAItsMonitor",
    "AnomalyDetector",
    "Anomaly",
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
    "HallucinationError",
    # Hallucination Detection (Phase 3)
    "FactTracker",
    "SourceGrounder",
    "SelfConsistencyChecker",
    "PhantomCitationDetector",
    "ConfidenceDecayTracker",
    "FactClaim",
    # Dashboard
    "LiveDashboard",
    "SimpleDashboard",
    "create_dashboard",
    "DASHBOARD_AVAILABLE",
]