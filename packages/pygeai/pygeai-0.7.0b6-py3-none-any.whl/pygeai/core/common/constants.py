from enum import Enum


class AuthType(Enum):
    """Authentication method types for PyGEAI SDK."""
    API_KEY = "api_key"
    OAUTH_TOKEN = "oauth_token"
    NONE = "none"
