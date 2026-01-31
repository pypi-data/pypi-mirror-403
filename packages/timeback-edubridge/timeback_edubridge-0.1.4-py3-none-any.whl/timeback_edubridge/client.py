"""
EduBridge Client

The main entry point for interacting with the EduBridge API.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Protocol, cast

from .lib.transport import Transport
from .resources import (
    AnalyticsResource,
    ApplicationsResource,
    EnrollmentsResource,
    LearningReportsResource,
    SubjectTrackResource,
    UsersResource,
)

if TYPE_CHECKING:
    from timeback_common import AuthCheckResult, Environment, TimebackProvider


Platform = Literal["BEYOND_AI", "LEARNWITH_AI"]


class EdubridgeTransportLike(Protocol):
    """Duck-typed transport interface for custom transports."""

    base_url: str

    async def close(self) -> None:
        """Close the transport and release resources."""
        ...


class EdubridgeClient:
    """
    Client for interacting with the EduBridge API.

    The client provides access to all EduBridge resources for learning
    platform integration.

    Example:
        ```python
        from timeback_edubridge import EdubridgeClient

        client = EdubridgeClient(
            base_url="https://api.example.com",
            auth_url="https://auth.example.com/oauth2/token",
            client_id="your-client-id",
            client_secret="your-client-secret",
        )

        # Or use environment variables
        client = EdubridgeClient(env="PRODUCTION")

        # Enrollments
        enrollments = await client.enrollments.list(user_id="user-123")
        await client.enrollments.enroll("user-123", "course-456")

        # Users
        students = await client.users.list_students()
        teachers = await client.users.list_teachers()

        # Analytics
        activity = await client.analytics.get_activity(
            student_id="student-123",
            start_date="2025-01-01",
            end_date="2025-01-31",
        )

        # Applications
        apps = await client.applications.list()

        # Subject Tracks
        tracks = await client.subject_tracks.list()

        # Learning Reports
        profile = await client.learning_reports.get_map_profile("user-123")

        # Close when done
        await client.close()
        ```
    """

    def __init__(
        self,
        *,
        platform: Platform | None = None,
        env: str | None = None,
        transport: EdubridgeTransportLike | None = None,
        base_url: str | None = None,
        auth_url: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        timeout: float = 30.0,
        provider: TimebackProvider | None = None,
    ) -> None:
        """
        Initialize the EduBridge client.

        You can configure the client in three ways:

        1. **Provider mode** (recommended for TimebackClient):
           Pass a `provider` to share auth state with other clients.

        2. **Environment-based configuration**: Pass an `env` string (e.g., "PRODUCTION")
           and the client will look for environment variables with that prefix:
           - `{ENV}_EDUBRIDGE_BASE_URL`
           - `{ENV}_EDUBRIDGE_TOKEN_URL`
           - `{ENV}_EDUBRIDGE_CLIENT_ID`
           - `{ENV}_EDUBRIDGE_CLIENT_SECRET`

        3. **Explicit configuration**: Pass the URLs and credentials directly.

        Args:
            env: Environment name for loading from environment variables
            base_url: Base URL for the EduBridge API
            auth_url: OAuth2 token endpoint URL
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            timeout: Request timeout in seconds (default: 30)
            provider: Optional TimebackProvider for shared auth
        """
        # Support transport injection mode
        self._transport: Transport | EdubridgeTransportLike
        if transport is not None:
            self._transport = transport
            self._provider = None
        else:
            from timeback_common import EnvVarNames, build_provider_env, build_provider_explicit

            env_vars = EnvVarNames(
                base_url="EDUBRIDGE_BASE_URL",
                auth_url="EDUBRIDGE_TOKEN_URL",
                client_id="EDUBRIDGE_CLIENT_ID",
                client_secret="EDUBRIDGE_CLIENT_SECRET",
            )

            if provider is None:
                if env is not None:
                    provider = build_provider_env(
                        platform=platform,
                        env=cast("Environment", env),
                        client_id=client_id,
                        client_secret=client_secret,
                        timeout=timeout,
                        env_vars=env_vars,
                    )
                else:
                    provider = build_provider_explicit(
                        base_url=base_url,
                        auth_url=auth_url,
                        client_id=client_id,
                        client_secret=client_secret,
                        timeout=timeout,
                        env_vars=env_vars,
                    )

            # Platform gating (LearnWith.AI edubridge is unsupported)
            if not provider.has_service("edubridge"):
                raise ValueError('Service "edubridge" is not supported on this platform')

            self._provider = provider

            endpoint = provider.get_endpoint("edubridge")
            paths = provider.get_paths("edubridge")
            token_manager = provider.get_token_manager("edubridge")

            self._transport = Transport(
                base_url=endpoint.base_url,
                token_manager=token_manager,
                paths=paths,
                timeout=provider.timeout,
                no_auth=token_manager is None,
            )

        # ── Resources ─────────────────────────────────────────────────────────
        # Cast needed because Resources expect full Transport
        # but we allow duck-typed transports for testing flexibility
        _transport = cast("Transport", self._transport)
        self.enrollments = EnrollmentsResource(_transport)
        self.users = UsersResource(_transport)
        self.analytics = AnalyticsResource(_transport)
        self.applications = ApplicationsResource(_transport)
        self.subject_tracks = SubjectTrackResource(_transport)
        self.learning_reports = LearningReportsResource(_transport)

    def get_transport(self) -> Transport | EdubridgeTransportLike:
        """
        Get the underlying transport for advanced use cases.

        Returns:
            The transport instance used by this client
        """
        return self._transport

    async def check_auth(self) -> AuthCheckResult:
        """
        Verify that OAuth authentication is working.

        Returns:
            Auth check result with ok, latency_ms, and checks

        Raises:
            RuntimeError: If client was initialized without a provider
        """
        if self._provider is None:
            raise RuntimeError("Cannot check auth: client initialized without provider")
        return await self._provider.check_auth()

    async def close(self) -> None:
        """Close the HTTP client and release resources."""
        await self._transport.close()

    async def __aenter__(self) -> EdubridgeClient:
        """Async context manager entry."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        """Async context manager exit."""
        await self.close()
