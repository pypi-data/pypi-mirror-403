"""Custom Exception Class Definitions"""


class LLMClientError(Exception):
    """LLM client base exception class"""
    pass


class ConfigurationError(LLMClientError):
    """Configuration error exception"""
    pass


class APIError(LLMClientError):
    """API call error exception"""
    pass


class NetworkError(LLMClientError):
    """Network error exception"""
    pass


class ValidationError(LLMClientError):
    """Validation error exception"""
    pass


class RateLimitError(LLMClientError):
    """Rate limit error exception (429 Too Many Requests)"""
    pass


class ServerError(LLMClientError):
    """Server error exception (5xx status codes) - retryable"""
    pass