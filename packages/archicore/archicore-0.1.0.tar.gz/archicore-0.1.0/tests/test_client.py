"""
Tests for ArchiCore Python SDK
"""

import pytest
from unittest.mock import Mock, patch
import json

from archicore import (
    ArchiCore,
    ArchiCoreError,
    AuthenticationError,
    RateLimitError,
    NotFoundError,
    ValidationError,
)


class TestArchiCoreClient:
    """Tests for the main ArchiCore client."""

    def test_init_requires_api_key(self):
        """Client should require an API key."""
        with pytest.raises(ValueError, match="api_key is required"):
            ArchiCore(api_key=None)

        with pytest.raises(ValueError, match="api_key is required"):
            ArchiCore(api_key="")

    def test_init_sets_defaults(self):
        """Client should set default values."""
        client = ArchiCore(api_key="test-key")
        assert client.api_key == "test-key"
        assert client.base_url == "https://api.archicore.io/api/v1"
        assert client.timeout == 30

    def test_init_custom_base_url(self):
        """Client should accept custom base URL."""
        client = ArchiCore(
            api_key="test-key",
            base_url="https://custom.example.com/api/v1/"
        )
        assert client.base_url == "https://custom.example.com/api/v1"

    def test_context_manager(self):
        """Client should work as context manager."""
        with ArchiCore(api_key="test-key") as client:
            assert client.api_key == "test-key"


class TestProjectsResource:
    """Tests for the projects resource."""

    @pytest.fixture
    def client(self):
        return ArchiCore(api_key="test-key")

    @patch("requests.Session.request")
    def test_list_projects(self, mock_request, client):
        """Should list all projects."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "projects": [
                {"id": "1", "name": "Project 1"},
                {"id": "2", "name": "Project 2"},
            ]
        }
        mock_request.return_value = mock_response

        projects = client.projects.list()

        assert len(projects) == 2
        assert projects[0]["name"] == "Project 1"

    @patch("requests.Session.request")
    def test_get_project(self, mock_request, client):
        """Should get a specific project."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "project": {"id": "123", "name": "Test Project"}
        }
        mock_request.return_value = mock_response

        project = client.projects.get("123")

        assert project["id"] == "123"
        assert project["name"] == "Test Project"

    @patch("requests.Session.request")
    def test_create_project(self, mock_request, client):
        """Should create a new project."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "success": True,
            "project": {"id": "new-id", "name": "New Project"}
        }
        mock_request.return_value = mock_response

        project = client.projects.create(name="New Project")

        assert project["name"] == "New Project"

    @patch("requests.Session.request")
    def test_search_project(self, mock_request, client):
        """Should search code in project."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "results": [
                {"file": "auth.ts", "line": 10, "code": "function login()"},
            ]
        }
        mock_request.return_value = mock_response

        results = client.projects.search("123", query="authentication")

        assert len(results) == 1
        assert results[0]["file"] == "auth.ts"


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.fixture
    def client(self):
        return ArchiCore(api_key="test-key")

    @patch("requests.Session.request")
    def test_authentication_error(self, mock_request, client):
        """Should raise AuthenticationError on 401."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "Invalid API key"}
        mock_request.return_value = mock_response

        with pytest.raises(AuthenticationError):
            client.projects.list()

    @patch("requests.Session.request")
    def test_not_found_error(self, mock_request, client):
        """Should raise NotFoundError on 404."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"error": "Project not found"}
        mock_request.return_value = mock_response

        with pytest.raises(NotFoundError):
            client.projects.get("non-existent")

    @patch("requests.Session.request")
    def test_rate_limit_error(self, mock_request, client):
        """Should raise RateLimitError on 429."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {
            "X-RateLimit-Limit": "100",
            "X-RateLimit-Remaining": "0",
            "Retry-After": "60",
        }
        mock_response.json.return_value = {"error": "Rate limit exceeded"}
        mock_request.return_value = mock_response

        with pytest.raises(RateLimitError) as exc_info:
            client.projects.list()

        assert exc_info.value.retry_after == 60

    @patch("requests.Session.request")
    def test_validation_error(self, mock_request, client):
        """Should raise ValidationError on 400."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "Invalid parameters"}
        mock_request.return_value = mock_response

        with pytest.raises(ValidationError):
            client.projects.create(name="")


class TestWebhooksResource:
    """Tests for webhooks resource."""

    @pytest.fixture
    def client(self):
        return ArchiCore(api_key="test-key")

    @patch("requests.Session.request")
    def test_list_webhooks(self, mock_request, client):
        """Should list webhooks."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "webhooks": [
                {"id": "1", "url": "https://example.com/webhook"},
            ]
        }
        mock_request.return_value = mock_response

        webhooks = client.webhooks.list()

        assert len(webhooks) == 1
        assert webhooks[0]["url"] == "https://example.com/webhook"

    @patch("requests.Session.request")
    def test_create_webhook(self, mock_request, client):
        """Should create a webhook."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "webhook": {
                "id": "new-id",
                "url": "https://example.com/webhook",
                "events": ["project.indexed"],
            }
        }
        mock_request.return_value = mock_response

        webhook = client.webhooks.create(
            url="https://example.com/webhook",
            events=["project.indexed"]
        )

        assert webhook["url"] == "https://example.com/webhook"

    @patch("requests.Session.request")
    def test_delete_webhook(self, mock_request, client):
        """Should delete a webhook."""
        mock_response = Mock()
        mock_response.status_code = 204
        mock_response.content = b""
        mock_request.return_value = mock_response

        result = client.webhooks.delete("webhook-id")

        assert result is True
