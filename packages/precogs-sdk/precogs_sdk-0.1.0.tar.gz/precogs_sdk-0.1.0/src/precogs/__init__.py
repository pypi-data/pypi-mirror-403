"""
Precogs SDK - Official Python client for Precogs AI security platform.

Usage:
    from precogs import PrecogsClient
    
    client = PrecogsClient(api_key="pk_live_xxx")
    
    # Trigger a code scan
    result = client.scans.trigger_code_scan(project_id="proj_123")
    
    # List projects
    projects = client.projects.list()
"""

from precogs.client import PrecogsClient
from precogs.exceptions import (
    PrecogsError,
    AuthenticationError,
    RateLimitError,
    NotFoundError,
    ValidationError,
    InsufficientTokensError,
)

__version__ = "0.1.0"
__all__ = [
    "PrecogsClient",
    "PrecogsError",
    "AuthenticationError",
    "RateLimitError",
    "NotFoundError",
    "ValidationError",
    "InsufficientTokensError",
]
