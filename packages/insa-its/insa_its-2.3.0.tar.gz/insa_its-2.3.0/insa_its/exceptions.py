class insAItsError(Exception):
    """Base exception for insAIts SDK"""
    pass


class RateLimitError(insAItsError):
    """Rate limit exceeded"""
    pass


class APIError(insAItsError):
    """API communication error"""
    pass


class AuthenticationError(insAItsError):
    """Authentication failed"""
    pass


class EmbeddingError(insAItsError):
    """Embedding generation failed"""
    pass


class HallucinationError(insAItsError):
    """Hallucination detection error"""
    pass