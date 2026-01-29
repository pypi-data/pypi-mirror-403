"""
InsAIts SDK - Configuration
===========================
Centralized configuration for the SDK.
"""

import os

# ============================================
# Development/Testing Mode
# ============================================

# Enable development mode for testing with mock API keys
DEV_MODE = os.getenv("INSAITS_DEV_MODE", "").lower() == "true"

# Test API keys for development (use in tests)
DEV_API_KEYS = {
    "test-pro-unlimited": {"tier": "pro", "valid": True},
    "test-starter-10k": {"tier": "starter", "valid": True},
    "test-free-100": {"tier": "free", "valid": True},
}

# ============================================
# API Configuration
# ============================================

# Production API URL (Railway deployment)
API_BASE_URL = "https://insaitsapi-production.up.railway.app"
API_URL_DEV = "http://localhost:8000"

# Use dev URL if environment variable is set
if os.getenv("INSAITS_DEV_MODE"):
    API_BASE_URL = API_URL_DEV
# Allow custom API URL override
if os.getenv("INSAITS_API_URL"):
    API_BASE_URL = os.getenv("INSAITS_API_URL")

API_ENDPOINTS = {
    "validate": f"{API_BASE_URL}/api/keys/validate",
    "usage_check": f"{API_BASE_URL}/api/usage/check",
    "usage_track": f"{API_BASE_URL}/api/usage/track",
    "embeddings": f"{API_BASE_URL}/api/embeddings/generate",
    "register": f"{API_BASE_URL}/api/keys/generate",
}


# ============================================
# Tier Limits
# ============================================

# Anonymous (no API key) - VERY limited, forces registration
ANONYMOUS_LIMITS = {
    "session_messages": 5,  # Only 5 messages without key!
    "daily_messages": 5,
    "history_size": 5,
    "cloud_embeddings": False,
    "export": False,
    "show_warning": True,  # Show "register for more" warning
}

# Free tier (registered, free API key)
FREE_TIER_LIMITS = {
    "daily_messages": 100,
    "session_messages": 100,
    "history_size": 100,
    "cloud_embeddings": False,
    "export": False,
    "show_warning": False,
}

# Starter tier ($29/mo or €99 lifetime)
STARTER_TIER_LIMITS = {
    "daily_messages": 10000,
    "session_messages": 10000,
    "history_size": 1000,
    "cloud_embeddings": True,
    "export": True,
    "show_warning": False,
}

# Pro tier ($79/mo or $299 lifetime)
PRO_TIER_LIMITS = {
    "daily_messages": -1,  # Unlimited
    "session_messages": -1,
    "history_size": 10000,
    "cloud_embeddings": True,
    "export": True,
    "show_warning": False,
}

TIER_LIMITS = {
    "anonymous": ANONYMOUS_LIMITS,
    "free": FREE_TIER_LIMITS,
    "starter": STARTER_TIER_LIMITS,
    "pro": PRO_TIER_LIMITS,
    "lifetime": PRO_TIER_LIMITS,  # Legacy, same as Pro
    "lifetime_starter": STARTER_TIER_LIMITS,  # €99 one-time
    "lifetime_pro": PRO_TIER_LIMITS,  # $299 one-time
    "enterprise": PRO_TIER_LIMITS,
}


# ============================================
# Cache Settings
# ============================================

LICENSE_CACHE_TTL = 3600  # 1 hour - how long to cache license validation
EMBEDDING_CACHE_SIZE = 2000
OFFLINE_GRACE_PERIOD = 86400  # 24 hours - allow cached validation if offline


# ============================================
# Feature Flags
# ============================================

FEATURES = {
    "anonymous": {
        "anomaly_detection": True,
        "local_embeddings": True,
        "synthetic_embeddings": True,
        "cloud_embeddings": False,
        "conversation_reading": True,
        "export": False,
        "graph": False,
        "cloud_sync": False,
        "dashboard": False,
        "integrations": False,
    },
    "free": {
        "anomaly_detection": True,
        "local_embeddings": True,
        "synthetic_embeddings": True,
        "cloud_embeddings": False,
        "conversation_reading": True,
        "export": False,
        "graph": True,
        "cloud_sync": False,
        "dashboard": True,
        "integrations": True,
    },
    "starter": {
        "anomaly_detection": True,
        "local_embeddings": True,
        "synthetic_embeddings": True,
        "cloud_embeddings": True,
        "conversation_reading": True,
        "export": True,
        "graph": True,
        "cloud_sync": True,
        "dashboard": True,
        "integrations": True,
    },
    "pro": {
        "anomaly_detection": True,
        "local_embeddings": True,
        "synthetic_embeddings": True,
        "cloud_embeddings": True,
        "conversation_reading": True,
        "export": True,
        "graph": True,
        "cloud_sync": True,
        "dashboard": True,
        "integrations": True,
    },
    "lifetime": {
        "anomaly_detection": True,
        "local_embeddings": True,
        "synthetic_embeddings": True,
        "cloud_embeddings": True,
        "conversation_reading": True,
        "export": True,
        "graph": True,
        "cloud_sync": True,
        "dashboard": True,
        "integrations": True,
    },
    "lifetime_starter": {
        "anomaly_detection": True,
        "local_embeddings": True,
        "synthetic_embeddings": True,
        "cloud_embeddings": True,
        "conversation_reading": True,
        "export": True,
        "graph": True,
        "cloud_sync": True,
        "dashboard": True,
        "integrations": True,
    },
    "lifetime_pro": {
        "anomaly_detection": True,
        "local_embeddings": True,
        "synthetic_embeddings": True,
        "cloud_embeddings": True,
        "conversation_reading": True,
        "export": True,
        "graph": True,
        "cloud_sync": True,
        "dashboard": True,
        "integrations": True,
    },
}


def get_feature(tier: str, feature: str) -> bool:
    """Check if a feature is available for a tier."""
    tier_features = FEATURES.get(tier, FEATURES["anonymous"])
    return tier_features.get(feature, False)


def get_tier_limits(tier: str) -> dict:
    """Get limits for a specific tier."""
    return TIER_LIMITS.get(tier, ANONYMOUS_LIMITS)


# ============================================
# Registration URL
# ============================================

REGISTER_URL = "https://github.com/Nomadu27/InsAIts.API"
PRICING_URL = "https://buy.stripe.com/00w6oH87R77T32A96Eb3q00"
