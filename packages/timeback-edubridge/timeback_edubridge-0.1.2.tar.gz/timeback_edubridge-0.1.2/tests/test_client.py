"""
Tests for the EduBridge client.
"""

import pytest

from timeback_edubridge import EdubridgeClient
from timeback_edubridge.lib.transport import Paths


class TestEdubridgeClient:
    """Tests for EdubridgeClient initialization."""

    def test_client_requires_base_url(self) -> None:
        """Client should raise error without sufficient config."""
        with pytest.raises(ValueError, match="Missing required environment variable"):
            EdubridgeClient()

    def test_client_initializes_with_base_url(self) -> None:
        """Client should initialize with explicit config."""
        client = EdubridgeClient(
            base_url="https://api.example.com",
            auth_url="https://auth.example.com/oauth2/token",
            client_id="test-id",
            client_secret="test-secret",
        )

        assert client._transport.base_url == "https://api.example.com"
        assert client.enrollments is not None
        assert client.users is not None
        assert client.analytics is not None
        assert client.applications is not None
        assert client.subject_tracks is not None
        assert client.learning_reports is not None

    def test_client_initializes_with_full_config(self) -> None:
        """Client should initialize with full configuration."""
        client = EdubridgeClient(
            base_url="https://api.example.com",
            auth_url="https://auth.example.com/oauth2/token",
            client_id="test-id",
            client_secret="test-secret",
            timeout=60.0,
        )

        assert client._transport.base_url == "https://api.example.com"
        assert client._provider is not None
        assert client._provider.timeout == 60.0


class TestPaths:
    """Tests for API paths configuration."""

    def test_default_paths(self) -> None:
        """Default paths should be configured correctly."""
        paths = Paths()
        assert paths.base == "/edubridge"

    def test_custom_paths(self) -> None:
        """Custom paths should be configurable."""
        paths = Paths(base="/custom/v2")
        assert paths.base == "/custom/v2"


class TestResourcesAttached:
    """Tests that all resources are properly attached to client."""

    def test_enrollments_resource(self) -> None:
        """Enrollments resource should be attached."""
        client = EdubridgeClient(
            base_url="https://api.example.com",
            auth_url="https://auth.example.com/oauth2/token",
            client_id="test-id",
            client_secret="test-secret",
        )
        assert hasattr(client, "enrollments")
        assert client.enrollments is not None

    def test_users_resource(self) -> None:
        """Users resource should be attached."""
        client = EdubridgeClient(
            base_url="https://api.example.com",
            auth_url="https://auth.example.com/oauth2/token",
            client_id="test-id",
            client_secret="test-secret",
        )
        assert hasattr(client, "users")
        assert client.users is not None

    def test_analytics_resource(self) -> None:
        """Analytics resource should be attached."""
        client = EdubridgeClient(
            base_url="https://api.example.com",
            auth_url="https://auth.example.com/oauth2/token",
            client_id="test-id",
            client_secret="test-secret",
        )
        assert hasattr(client, "analytics")
        assert client.analytics is not None

    def test_applications_resource(self) -> None:
        """Applications resource should be attached."""
        client = EdubridgeClient(
            base_url="https://api.example.com",
            auth_url="https://auth.example.com/oauth2/token",
            client_id="test-id",
            client_secret="test-secret",
        )
        assert hasattr(client, "applications")
        assert client.applications is not None

    def test_subject_tracks_resource(self) -> None:
        """Subject tracks resource should be attached."""
        client = EdubridgeClient(
            base_url="https://api.example.com",
            auth_url="https://auth.example.com/oauth2/token",
            client_id="test-id",
            client_secret="test-secret",
        )
        assert hasattr(client, "subject_tracks")
        assert client.subject_tracks is not None

    def test_learning_reports_resource(self) -> None:
        """Learning reports resource should be attached."""
        client = EdubridgeClient(
            base_url="https://api.example.com",
            auth_url="https://auth.example.com/oauth2/token",
            client_id="test-id",
            client_secret="test-secret",
        )
        assert hasattr(client, "learning_reports")
        assert client.learning_reports is not None
