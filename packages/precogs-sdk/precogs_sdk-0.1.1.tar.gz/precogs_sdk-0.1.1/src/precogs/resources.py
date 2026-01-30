"""API resource classes for Precogs SDK."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from precogs.http import HTTPClient


class BaseResource:
    """Base class for API resources."""

    def __init__(self, client: HTTPClient):
        self._client = client


class APIKeysResource(BaseResource):
    """Manage API keys."""

    def list(self) -> list[dict[str, Any]]:
        """List all API keys for the authenticated user.
        
        Returns:
            List of API key objects (without raw keys).
        """
        response = self._client.get("/keys")
        return response.get("keys", [])

    def create(self, name: str) -> dict[str, Any]:
        """Create a new API key.
        
        Args:
            name: Display name for the key.
            
        Returns:
            Dict with 'rawKey' (show only once!) and key metadata.
        """
        return self._client.post("/keys", json={"name": name})

    def revoke(self, key_id: str) -> dict[str, Any]:
        """Revoke (delete) an API key.
        
        Args:
            key_id: The ID of the key to revoke.
        """
        return self._client.delete(f"/keys/{key_id}")

    def update(self, key_id: str, name: str) -> dict[str, Any]:
        """Rename an API key.
        
        Args:
            key_id: The ID of the key to update.
            name: New display name.
        """
        return self._client.patch(f"/keys/{key_id}", json={"name": name})


class ProjectsResource(BaseResource):
    """Manage projects."""

    def list(self) -> list[dict[str, Any]]:
        """List all projects for the authenticated user."""
        response = self._client.get("/projects")
        return response.get("projects", [])

    def get(self, project_id: str) -> dict[str, Any]:
        """Get a specific project by ID."""
        return self._client.get(f"/projects/{project_id}")

    def create(
        self,
        name: str,
        repo_url: str,
        provider: str = "github",
        branch: str = "main",
    ) -> dict[str, Any]:
        """Create a new project.
        
        Args:
            name: Project display name.
            repo_url: Repository URL.
            provider: VCS provider (github, gitlab, bitbucket).
            branch: Default branch to scan.
        """
        return self._client.post("/projects", json={
            "name": name,
            "repoUrl": repo_url,
            "provider": provider,
            "branch": branch,
        })

    def update(self, project_id: str, **kwargs) -> dict[str, Any]:
        """Update project settings."""
        return self._client.patch(f"/projects/{project_id}", json=kwargs)

    def delete(self, project_id: str) -> dict[str, Any]:
        """Deactivate a project."""
        return self._client.delete(f"/projects/{project_id}")


class ScansResource(BaseResource):
    """Trigger and manage security scans."""

    def trigger_code_scan(
        self,
        project_id: str,
        branch: str | None = None,
    ) -> dict[str, Any]:
        """Trigger a code security scan (SAST).
        
        Args:
            project_id: Project to scan.
            branch: Branch to scan (optional, uses default).
            
        Returns:
            Scan job info with status.
        """
        payload = {"projectId": project_id}
        if branch:
            payload["branch"] = branch
        return self._client.post("/scan/trigger", json=payload)

    def trigger_dependency_scan(self, project_id: str) -> dict[str, Any]:
        """Trigger a dependency/SCA scan."""
        return self._client.post("/scan/dependency", json={"projectId": project_id})

    def trigger_iac_scan(self, project_id: str) -> dict[str, Any]:
        """Trigger an Infrastructure as Code scan."""
        return self._client.post("/scan/iac", json={"projectId": project_id})

    def trigger_container_scan(
        self,
        project_id: str,
        image: str,
    ) -> dict[str, Any]:
        """Trigger a container image scan.
        
        Args:
            project_id: Associated project.
            image: Container image reference (e.g., 'nginx:latest').
        """
        return self._client.post("/scan/container", json={
            "projectId": project_id,
            "image": image,
        })

    def get_status(self, scan_id: str) -> dict[str, Any]:
        """Get scan status and progress."""
        return self._client.get(f"/scan/{scan_id}/status")

    def get_results(self, scan_id: str) -> dict[str, Any]:
        """Get scan results with vulnerabilities."""
        return self._client.get(f"/scan/{scan_id}/results")


class VulnerabilitiesResource(BaseResource):
    """Query and manage vulnerabilities."""

    def list(
        self,
        project_id: str | None = None,
        severity: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List vulnerabilities with optional filters.
        
        Args:
            project_id: Filter by project.
            severity: Filter by severity (critical, high, medium, low).
            status: Filter by status (open, fixed, ignored).
            limit: Max results to return.
        """
        params = {"limit": limit}
        if project_id:
            params["projectId"] = project_id
        if severity:
            params["severity"] = severity
        if status:
            params["status"] = status

        response = self._client.get("/vulnerabilities", params=params)
        return response.get("vulnerabilities", [])

    def get(self, vuln_id: str) -> dict[str, Any]:
        """Get vulnerability details including fix suggestions."""
        return self._client.get(f"/vulnerabilities/{vuln_id}")

    def update_status(self, vuln_id: str, status: str, reason: str = "") -> dict[str, Any]:
        """Update vulnerability status (e.g., mark as fixed or ignored).
        
        Args:
            vuln_id: Vulnerability ID.
            status: New status (open, fixed, ignored).
            reason: Reason for status change.
        """
        return self._client.patch(f"/vulnerabilities/{vuln_id}", json={
            "status": status,
            "reason": reason,
        })

    def get_ai_fix(self, vuln_id: str) -> dict[str, Any]:
        """Get AI-generated fix suggestion for a vulnerability."""
        return self._client.get(f"/vulnerabilities/{vuln_id}/fix")


class DashboardResource(BaseResource):
    """Dashboard analytics and summaries."""

    def get_overview(self, project_id: str | None = None) -> dict[str, Any]:
        """Get security overview dashboard data."""
        params = {"projectId": project_id} if project_id else {}
        return self._client.get("/dashboard/overview", params=params)

    def get_severity_distribution(self, project_id: str | None = None) -> dict[str, Any]:
        """Get vulnerability severity distribution."""
        params = {"projectId": project_id} if project_id else {}
        return self._client.get("/dashboard/severity-distribution", params=params)

    def get_trend(
        self,
        project_id: str | None = None,
        days: int = 30,
    ) -> dict[str, Any]:
        """Get vulnerability trend over time."""
        params = {"days": days}
        if project_id:
            params["projectId"] = project_id
        return self._client.get("/dashboard/trend", params=params)

    def get_top_vulnerabilities(
        self,
        limit: int = 10,
        project_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get top vulnerabilities by severity/impact."""
        params = {"limit": limit}
        if project_id:
            params["projectId"] = project_id
        response = self._client.get("/dashboard/top-vulnerabilities", params=params)
        return response.get("vulnerabilities", [])
