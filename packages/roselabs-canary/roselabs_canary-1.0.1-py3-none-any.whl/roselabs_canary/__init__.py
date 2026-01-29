"""
Canary SDK for Python

Scan your dependencies for known vulnerabilities.

Example:
    >>> from roselabs_canary import Canary
    >>>
    >>> canary = Canary(
    ...     api_key="your-api-key",
    ...     service_name="my-app",  # Auto-creates if doesn't exist
    ... )
    >>>
    >>> result = canary.submit_scan(
    ...     lockfiles=[
    ...         {"filename": "requirements.txt", "content": "..."}
    ...     ]
    ... )
    >>> print(f"Found {result.vulnerabilities.total} vulnerabilities")
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import httpx

__version__ = "1.1.0"
__all__ = ["Canary", "CanaryError", "ScanResult", "VulnerabilityCounts", "Lockfile"]


class CanaryError(Exception):
    """Exception raised for Canary API errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response: Any = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response = response


@dataclass
class VulnerabilityCounts:
    """Vulnerability counts by severity."""

    critical: int
    high: int
    medium: int
    low: int
    total: int


@dataclass
class Vulnerability:
    """Details of a single vulnerability."""

    id: str
    package_name: str
    installed_version: str
    patched_version: str | None
    severity: str
    title: str
    description: str
    cve_id: str | None
    references: list[str]


@dataclass
class ScanResult:
    """Result of a vulnerability scan."""

    scan_id: str
    service_id: str
    service_name: str
    status: str
    vulnerabilities: VulnerabilityCounts
    scan_url: str
    details: list[Vulnerability] | None = None


@dataclass
class Lockfile:
    """Lockfile to scan."""

    filename: str
    content: str
    path: str | None = None


class Canary:
    """
    Canary API client for vulnerability scanning.

    Services are automatically created if they don't exist.
    Subsequent scans with the same service name will update the existing service.

    Args:
        api_key: Canary API key from team settings.
        service_name: Name of the service (auto-created if doesn't exist).
        api_url: API base URL (defaults to https://canary.api.roselabs.io).
        timeout: Request timeout in seconds (default: 30).

    Example:
        >>> canary = Canary(
        ...     api_key="your-api-key",
        ...     service_name="my-backend-api",
        ... )
        >>> result = canary.submit_scan(
        ...     lockfiles=[
        ...         Lockfile(filename="requirements.txt", content="django==4.0.0")
        ...     ]
        ... )
    """

    DEFAULT_API_URL = "https://canary.api.roselabs.io"
    DEFAULT_TIMEOUT = 30

    def __init__(
        self,
        api_key: str,
        service_name: str,
        api_url: str | None = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        if not api_key:
            raise CanaryError("api_key is required")
        if not service_name:
            raise CanaryError("service_name is required")

        self.api_key = api_key
        self.service_name = service_name
        self.api_url = api_url or self.DEFAULT_API_URL
        self.timeout = timeout

        self._client = httpx.Client(
            base_url=self.api_url,
            headers={
                "X-API-Key": self.api_key,
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )

    def __enter__(self) -> "Canary":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def submit_scan(
        self,
        lockfiles: list[Lockfile | dict[str, Any]],
        commit_sha: str | None = None,
        branch: str | None = None,
    ) -> ScanResult:
        """
        Submit lockfiles for vulnerability scanning.

        Services are automatically created if they don't exist.
        Subsequent scans with the same service name will update the existing service.

        Args:
            lockfiles: List of lockfiles to scan. Can be Lockfile objects or dicts
                       with 'filename' and 'content' keys.
            commit_sha: Git commit SHA (optional).
            branch: Git branch name (optional).

        Returns:
            ScanResult with vulnerability counts and details.

        Raises:
            CanaryError: If the API request fails.

        Example:
            >>> result = canary.submit_scan(
            ...     lockfiles=[
            ...         {"filename": "poetry.lock", "content": "..."},
            ...     ],
            ...     commit_sha="abc123",
            ...     branch="main",
            ... )
        """
        if not lockfiles:
            raise CanaryError("At least one lockfile is required")

        # Normalize lockfiles to dicts
        normalized = []
        for lf in lockfiles:
            if isinstance(lf, Lockfile):
                normalized.append({
                    "filename": lf.filename,
                    "content": lf.content,
                    "path": lf.path,
                })
            else:
                normalized.append(lf)

        payload = {
            "lockfiles": normalized,
            "source": "sdk-python",
        }
        if commit_sha:
            payload["commit_sha"] = commit_sha
        if branch:
            payload["branch"] = branch

        # URL encode the service name for the path
        encoded_service_name = quote(self.service_name, safe="")

        try:
            response = self._client.post(
                f"/v1/services/{encoded_service_name}/scans",
                json=payload,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise CanaryError(
                f"API request failed: {e.response.text}",
                status_code=e.response.status_code,
                response=e.response.text,
            ) from e
        except httpx.RequestError as e:
            raise CanaryError(f"Request failed: {e}") from e

        data = response.json()
        return self._parse_scan_result(data)

    def get_scan(self, scan_id: str) -> ScanResult:
        """
        Retrieve details of a previous scan.

        Args:
            scan_id: The scan ID to retrieve.

        Returns:
            ScanResult with vulnerability counts and details.

        Raises:
            CanaryError: If the API request fails.
        """
        try:
            response = self._client.get(f"/scans/{scan_id}")
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise CanaryError(
                f"API request failed: {e.response.text}",
                status_code=e.response.status_code,
                response=e.response.text,
            ) from e
        except httpx.RequestError as e:
            raise CanaryError(f"Request failed: {e}") from e

        data = response.json()
        return self._parse_scan_result(data)

    def _parse_scan_result(self, data: dict[str, Any]) -> ScanResult:
        """Parse API response into ScanResult."""
        vuln_data = data.get("vulnerabilities", {})
        vulnerabilities = VulnerabilityCounts(
            critical=vuln_data.get("critical", 0),
            high=vuln_data.get("high", 0),
            medium=vuln_data.get("medium", 0),
            low=vuln_data.get("low", 0),
            total=vuln_data.get("total", 0),
        )

        details = None
        if "details" in data and data["details"]:
            details = [
                Vulnerability(
                    id=v["id"],
                    package_name=v["package_name"],
                    installed_version=v["installed_version"],
                    patched_version=v.get("patched_version"),
                    severity=v["severity"],
                    title=v["title"],
                    description=v["description"],
                    cve_id=v.get("cve_id"),
                    references=v.get("references", []),
                )
                for v in data["details"]
            ]

        return ScanResult(
            scan_id=data.get("scan_id", data.get("id", "")),
            service_id=data.get("service_id", ""),
            service_name=data.get("service_name", self.service_name),
            status=data["status"],
            vulnerabilities=vulnerabilities,
            scan_url=data.get("scan_url", ""),
            details=details,
        )
