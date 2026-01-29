"""
ArchiCore API Client
"""

import requests
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin

from .exceptions import (
    ArchiCoreError,
    AuthenticationError,
    RateLimitError,
    NotFoundError,
    ValidationError,
    ServerError,
)


class BaseResource:
    """Base class for API resources."""

    def __init__(self, client: "ArchiCore"):
        self._client = client

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Dict[str, Any] = None,
        params: Dict[str, Any] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        return self._client._request(method, endpoint, data, params, **kwargs)


class ProjectsResource(BaseResource):
    """Projects API resource."""

    def list(self) -> List[Dict[str, Any]]:
        """
        List all projects.

        Returns:
            List of project objects.

        Example:
            projects = client.projects.list()
            for project in projects:
                print(project['name'])
        """
        response = self._request("GET", "/projects")
        return response.get("data", response.get("projects", []))

    def get(self, project_id: str) -> Dict[str, Any]:
        """
        Get a specific project by ID.

        Args:
            project_id: The project ID.

        Returns:
            Project object with details.
        """
        response = self._request("GET", f"/projects/{project_id}")
        return response.get("data", response.get("project", response))

    def create(
        self,
        name: str,
        source: str = None,
        github_url: str = None,
        gitlab_url: str = None,
    ) -> Dict[str, Any]:
        """
        Create a new project.

        Args:
            name: Project name.
            source: Local path to project source (optional).
            github_url: GitHub repository URL (optional).
            gitlab_url: GitLab repository URL (optional).

        Returns:
            Created project object.
        """
        data = {"name": name}
        if source:
            data["source"] = source
        if github_url:
            data["githubUrl"] = github_url
        if gitlab_url:
            data["gitlabUrl"] = gitlab_url

        response = self._request("POST", "/projects", data=data)
        return response.get("data", response.get("project", response))

    def delete(self, project_id: str) -> bool:
        """
        Delete a project.

        Args:
            project_id: The project ID.

        Returns:
            True if successful.
        """
        self._request("DELETE", f"/projects/{project_id}")
        return True

    def index(self, project_id: str, force: bool = False) -> Dict[str, Any]:
        """
        Trigger project indexing.

        Args:
            project_id: The project ID.
            force: Force re-indexing even if already indexed.

        Returns:
            Indexing status.
        """
        data = {"force": force} if force else None
        response = self._request("POST", f"/projects/{project_id}/index", data=data)
        return response

    def search(
        self,
        project_id: str,
        query: str,
        limit: int = 10,
        threshold: float = 0.7,
    ) -> List[Dict[str, Any]]:
        """
        Semantic search in project code.

        Args:
            project_id: The project ID.
            query: Natural language search query.
            limit: Maximum number of results (default 10).
            threshold: Similarity threshold 0-1 (default 0.7).

        Returns:
            List of search results with code snippets.

        Example:
            results = client.projects.search(
                "project-id",
                query="authentication middleware"
            )
        """
        data = {
            "query": query,
            "limit": limit,
            "threshold": threshold,
        }
        response = self._request("POST", f"/projects/{project_id}/search", data=data)
        return response.get("data", response.get("results", []))

    def ask(
        self,
        project_id: str,
        question: str,
        context: str = None,
    ) -> Dict[str, Any]:
        """
        Ask AI assistant about the project.

        Args:
            project_id: The project ID.
            question: Natural language question.
            context: Additional context (optional).

        Returns:
            AI response with answer and relevant code.

        Example:
            answer = client.projects.ask(
                "project-id",
                question="How does the authentication system work?"
            )
            print(answer['response'])
        """
        data = {"question": question}
        if context:
            data["context"] = context

        response = self._request("POST", f"/projects/{project_id}/ask", data=data)
        return response.get("data", response)

    def metrics(self, project_id: str) -> Dict[str, Any]:
        """
        Get code metrics for a project.

        Args:
            project_id: The project ID.

        Returns:
            Metrics object with code quality data.
        """
        response = self._request("GET", f"/projects/{project_id}/metrics")
        return response.get("data", response.get("metrics", response))

    def security(self, project_id: str) -> Dict[str, Any]:
        """
        Get security scan results.

        Args:
            project_id: The project ID.

        Returns:
            Security report with vulnerabilities.
        """
        response = self._request("GET", f"/projects/{project_id}/security")
        return response.get("data", response.get("security", response))

    def analyze(
        self,
        project_id: str,
        changes: List[Dict[str, Any]] = None,
        files: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Perform impact analysis.

        Args:
            project_id: The project ID.
            changes: List of code changes to analyze.
            files: List of file paths that changed.

        Returns:
            Impact analysis results.

        Example:
            impact = client.projects.analyze(
                "project-id",
                files=["src/auth/login.ts"]
            )
            print(f"Affected: {len(impact['affected_files'])} files")
        """
        data = {}
        if changes:
            data["changes"] = changes
        if files:
            data["files"] = files

        response = self._request("POST", f"/projects/{project_id}/analyze", data=data)
        return response.get("data", response)

    # ==================== ENTERPRISE METHODS ====================

    def enterprise_estimate(self, project_id: str) -> Dict[str, Any]:
        """
        Get enterprise-scale project estimation.

        Analyzes project size and recommends analysis tier for large projects.

        Args:
            project_id: The project ID.

        Returns:
            Estimation with recommended tier, total files, and time estimate.

        Example:
            estimate = client.projects.enterprise_estimate("project-id")
            print(f"Recommended tier: {estimate['recommendation']}")
            print(f"Total files: {estimate['totalFiles']}")
        """
        response = self._request("GET", f"/projects/{project_id}/enterprise/estimate")
        return response.get("data", response)

    def enterprise_index(
        self,
        project_id: str,
        tier: str = "standard",
        sampling_strategy: str = "smart",
        sampling_max_files: int = None,
        focus_directories: List[str] = None,
        exclude_patterns: List[str] = None,
        incremental_since: str = None,
    ) -> Dict[str, Any]:
        """
        Start enterprise indexing with custom options.

        For large projects (50K+ files), use sampling and tiered analysis.

        Args:
            project_id: The project ID.
            tier: Analysis tier - "quick", "standard", or "deep" (Enterprise only).
            sampling_strategy: "smart", "hot-files", "random", or "directory-balanced".
            sampling_max_files: Maximum number of files to analyze.
            focus_directories: List of directories to prioritize.
            exclude_patterns: Patterns to exclude from analysis.
            incremental_since: ISO date or commit hash for incremental indexing.

        Returns:
            Task ID and status for async tracking.

        Example:
            # Quick analysis for exploration
            task = client.projects.enterprise_index(
                "project-id",
                tier="quick",
                sampling_strategy="smart"
            )

            # Deep analysis with focus directories
            task = client.projects.enterprise_index(
                "project-id",
                tier="deep",
                focus_directories=["src/core", "src/api"]
            )
        """
        data = {
            "tier": tier,
            "sampling": {
                "enabled": True,
                "strategy": sampling_strategy,
            }
        }

        if sampling_max_files:
            data["sampling"]["maxFiles"] = sampling_max_files

        if focus_directories:
            data["focusDirectories"] = focus_directories

        if exclude_patterns:
            data["excludePatterns"] = exclude_patterns

        if incremental_since:
            data["incremental"] = {
                "enabled": True,
                "since": incremental_since,
            }

        response = self._request("POST", f"/projects/{project_id}/enterprise/index", data=data)
        return response.get("data", response)

    def enterprise_files_preview(
        self,
        project_id: str,
        tier: str = "standard",
        strategy: str = "smart",
    ) -> Dict[str, Any]:
        """
        Preview files that would be analyzed with given options.

        Args:
            project_id: The project ID.
            tier: Analysis tier - "quick", "standard", or "deep".
            strategy: Sampling strategy.

        Returns:
            List of files that would be analyzed.

        Example:
            preview = client.projects.enterprise_files_preview(
                "project-id",
                tier="standard",
                strategy="smart"
            )
            print(f"Would analyze {preview['totalSelected']} files")
        """
        params = {"tier": tier, "strategy": strategy}
        response = self._request("GET", f"/projects/{project_id}/enterprise/files", params=params)
        return response.get("data", response)

    def enterprise_incremental(
        self,
        project_id: str,
        since: str,
    ) -> Dict[str, Any]:
        """
        Check for incremental changes since a date or commit.

        Useful for re-indexing only changed files.

        Args:
            project_id: The project ID.
            since: ISO date (e.g., "2024-01-01") or git commit hash.

        Returns:
            List of changed files.

        Example:
            # Check changes since last week
            changes = client.projects.enterprise_incremental(
                "project-id",
                since="2024-01-01"
            )

            # Check changes since a commit
            changes = client.projects.enterprise_incremental(
                "project-id",
                since="abc123f"
            )
        """
        data = {"since": since}
        response = self._request("POST", f"/projects/{project_id}/enterprise/incremental", data=data)
        return response.get("data", response)


class WebhooksResource(BaseResource):
    """Webhooks API resource."""

    def list(self) -> List[Dict[str, Any]]:
        """
        List all webhooks.

        Returns:
            List of webhook objects.
        """
        response = self._request("GET", "/webhooks")
        return response.get("data", response.get("webhooks", []))

    def create(
        self,
        url: str,
        events: List[str],
        project_id: str = None,
        secret: str = None,
    ) -> Dict[str, Any]:
        """
        Create a new webhook.

        Args:
            url: Webhook endpoint URL.
            events: List of events to subscribe to.
            project_id: Limit to specific project (optional).
            secret: Webhook secret for signature verification.

        Returns:
            Created webhook object.

        Example:
            webhook = client.webhooks.create(
                url="https://example.com/webhook",
                events=["project.indexed", "analysis.complete"]
            )
        """
        data = {
            "url": url,
            "events": events,
        }
        if project_id:
            data["projectId"] = project_id
        if secret:
            data["secret"] = secret

        response = self._request("POST", "/webhooks", data=data)
        return response.get("data", response.get("webhook", response))

    def delete(self, webhook_id: str) -> bool:
        """
        Delete a webhook.

        Args:
            webhook_id: The webhook ID.

        Returns:
            True if successful.
        """
        self._request("DELETE", f"/webhooks/{webhook_id}")
        return True


class ArchiCore:
    """
    ArchiCore API client.

    Args:
        api_key: Your ArchiCore API key.
        base_url: API base URL (default: https://api.archicore.io/api/v1).
        timeout: Request timeout in seconds (default: 30).

    Example:
        from archicore import ArchiCore

        client = ArchiCore(api_key="your-api-key")

        # List projects
        projects = client.projects.list()

        # Search code
        results = client.projects.search("project-id", query="auth logic")

        # Ask AI
        answer = client.projects.ask("project-id", question="How does auth work?")
    """

    DEFAULT_BASE_URL = "https://api.archicore.io/api/v1"

    def __init__(
        self,
        api_key: str,
        base_url: str = None,
        timeout: int = 30,
    ):
        if not api_key:
            raise ValueError("api_key is required")

        self.api_key = api_key
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "archicore-python/0.1.0",
            }
        )

        # Initialize resources
        self.projects = ProjectsResource(self)
        self.webhooks = WebhooksResource(self)

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Dict[str, Any] = None,
        params: Dict[str, Any] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Make an API request."""
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))

        try:
            response = self._session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=self.timeout,
                **kwargs,
            )
        except requests.exceptions.Timeout:
            raise ArchiCoreError("Request timed out", code="TIMEOUT")
        except requests.exceptions.ConnectionError:
            raise ArchiCoreError("Connection failed", code="CONNECTION_ERROR")

        return self._handle_response(response)

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle API response and raise appropriate exceptions."""
        # Parse rate limit headers
        rate_limit_info = {
            "limit": response.headers.get("X-RateLimit-Limit"),
            "remaining": response.headers.get("X-RateLimit-Remaining"),
            "reset": response.headers.get("X-RateLimit-Reset"),
        }

        # Success
        if response.status_code in (200, 201, 204):
            if response.status_code == 204 or not response.content:
                return {"success": True}
            try:
                return response.json()
            except ValueError:
                return {"success": True, "data": response.text}

        # Parse error response
        try:
            error_data = response.json()
            error_message = error_data.get("error", error_data.get("message", "Unknown error"))
            error_code = error_data.get("code")
        except ValueError:
            error_message = response.text or "Unknown error"
            error_code = None

        # Raise appropriate exception
        if response.status_code == 401:
            raise AuthenticationError(error_message)
        elif response.status_code == 403:
            raise ArchiCoreError(error_message, code="FORBIDDEN", status_code=403)
        elif response.status_code == 404:
            raise NotFoundError(error_message)
        elif response.status_code == 429:
            raise RateLimitError(
                error_message,
                retry_after=int(response.headers.get("Retry-After", 60)),
                limit=int(rate_limit_info["limit"]) if rate_limit_info["limit"] else None,
                remaining=int(rate_limit_info["remaining"]) if rate_limit_info["remaining"] else None,
            )
        elif response.status_code == 400:
            raise ValidationError(error_message)
        elif response.status_code >= 500:
            raise ServerError(error_message)
        else:
            raise ArchiCoreError(
                error_message,
                code=error_code,
                status_code=response.status_code,
            )

    def close(self):
        """Close the client session."""
        self._session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
