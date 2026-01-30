"""Main Precogs client class."""

from __future__ import annotations

import os

from precogs.http import HTTPClient
from precogs.resources import (
    APIKeysResource,
    ProjectsResource,
    ScansResource,
    VulnerabilitiesResource,
    DashboardResource,
)


class PrecogsClient:
    """
    Official Python client for Precogs AI security platform.
    
    Usage:
        from precogs import PrecogsClient
        
        # Initialize with API key
        client = PrecogsClient(api_key="pk_live_xxx")
        
        # Or use environment variable PRECOGS_API_KEY
        client = PrecogsClient()
        
        # Trigger a scan
        result = client.scans.trigger_code_scan(project_id="proj_123")
        
        # List projects
        projects = client.projects.list()
        
        # Get vulnerabilities
        vulns = client.vulnerabilities.list(severity="critical")
    
    Args:
        api_key: Precogs API key (pk_live_xxx format). 
                 Falls back to PRECOGS_API_KEY environment variable.
        base_url: Override API base URL (for self-hosted or staging).
        timeout: Request timeout in seconds (default: 30).
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
    ):
        # Resolve API key from param or environment
        resolved_key = api_key or os.environ.get("PRECOGS_API_KEY")
        if not resolved_key:
            raise ValueError(
                "API key is required. Pass api_key parameter or set PRECOGS_API_KEY environment variable."
            )

        # Resolve base URL from param or environment
        resolved_base_url = base_url or os.environ.get("PRECOGS_BASE_URL")

        # Validate key format
        if not resolved_key.startswith("pk_"):
            raise ValueError(
                "Invalid API key format. Keys should start with 'pk_live_' or 'pk_test_'."
            )

        # Initialize HTTP client
        self._http = HTTPClient(
            api_key=resolved_key,
            base_url=resolved_base_url,
            timeout=timeout,
        )

        # Initialize API resources
        self.api_keys = APIKeysResource(self._http)
        self.projects = ProjectsResource(self._http)
        self.scans = ScansResource(self._http)
        self.vulnerabilities = VulnerabilitiesResource(self._http)
        self.dashboard = DashboardResource(self._http)

    def close(self) -> None:
        """Close the client and release resources."""
        self._http.close()

    def __enter__(self) -> "PrecogsClient":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"<PrecogsClient base_url={self._http.base_url!r}>"
