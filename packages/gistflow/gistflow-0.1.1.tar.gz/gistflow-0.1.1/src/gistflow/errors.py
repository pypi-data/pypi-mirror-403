class GistFlowError(Exception):
    """Base exception for gistflow."""


class AuthError(GistFlowError):
    """Authentication/authorization failed."""


class NotFoundError(GistFlowError):
    """Resource not found (gist, file, etc.)."""


class RateLimitError(GistFlowError):
    """GitHub rate limit hit."""


class ApiError(GistFlowError):
    """Generic API error."""
