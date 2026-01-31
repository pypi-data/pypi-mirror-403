"""
OneRoster Client

The main entry point for interacting with the OneRoster API.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Protocol, cast

from .lib.transport import Transport
from .resources.assessment import (
    AssessmentLineItemsResource,
    AssessmentResultsResource,
)
from .resources.gradebook import (
    CategoriesResource,
    LineItemsResource,
    ResultsResource,
    ScoreScalesResource,
)
from .resources.resources import ResourcesResource
from .resources.rostering import (
    AcademicSessionsResource,
    ClassesResource,
    CoursesResource,
    DemographicsResource,
    EnrollmentsResource,
    GradingPeriodsResource,
    OrgsResource,
    SchoolsResource,
    StudentsResource,
    TeachersResource,
    TermsResource,
    UsersResource,
)

if TYPE_CHECKING:
    from timeback_common import AuthCheckResult, Environment, TimebackProvider


Platform = Literal["BEYOND_AI", "LEARNWITH_AI"]


class OneRosterTransportLike(Protocol):
    """Duck-typed transport interface for custom transports."""

    base_url: str

    async def close(self) -> None:
        """Close the transport and release resources."""
        ...


class OneRosterClient:
    """
    Client for interacting with the OneRoster API.

    The client provides access to all OneRoster resources through typed
    resource classes with built-in pagination support.

    Example:
        ```python
        from timeback_oneroster import OneRosterClient

        client = OneRosterClient(
            base_url="https://api.example.com",
            client_id="your-client-id",
            client_secret="your-client-secret",
        )

        # Or use environment variables
        client = OneRosterClient(env="PRODUCTION")

        # Rostering
        users = await client.users.list()
        students = await client.students.list()
        teachers = await client.teachers.list()
        schools = await client.schools.list()
        classes = await client.classes.list()
        courses = await client.courses.list()
        enrollments = await client.enrollments.list()
        orgs = await client.orgs.list()
        academic_sessions = await client.academic_sessions.list()
        terms = await client.terms.list()
        grading_periods = await client.grading_periods.list()
        demographics = await client.demographics.list()

        # Gradebook
        line_items = await client.line_items.list()
        results = await client.results.list()
        categories = await client.categories.list()
        score_scales = await client.score_scales.list()

        # Assessment
        assessment_line_items = await client.assessment_line_items.list()
        assessment_results = await client.assessment_results.list()

        # Resources
        resources = await client.resources.list()

        # Scoped operations
        user_classes = await client.users("user-id").classes()
        school_students = await client.schools("school-id").students()
        class_line_items = await client.classes("class-id").line_items()
        term_classes = await client.terms("term-id").classes()
        course_components = await client.courses("course-id").components()

        # Nested scopes
        student_results = await client.classes("class-id").student("student-id").results()
        line_item_results = await client.classes("class-id").line_item("line-item-id").results()
        school_class_students = await client.schools("school-id").class_("class-id").students()

        # Streaming with lazy pagination
        async for user in client.users.stream():
            print(user)

        # Close when done
        await client.close()
        ```
    """

    def __init__(
        self,
        *,
        platform: Platform | None = None,
        env: str | None = None,
        transport: OneRosterTransportLike | None = None,
        base_url: str | None = None,
        auth_url: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        timeout: float = 30.0,
        provider: TimebackProvider | None = None,
    ) -> None:
        """
        Initialize the OneRoster client.

        You can configure the client in three ways:

        1. **Provider mode** (recommended for TimebackClient):
           Pass a `provider` to share auth state with other clients.

        2. **Environment-based configuration**: Pass an `env` string (e.g., "PRODUCTION")
           and the client will look for environment variables with that prefix:
           - `{ENV}_ONEROSTER_BASE_URL`
           - `{ENV}_ONEROSTER_AUTH_URL`
           - `{ENV}_ONEROSTER_CLIENT_ID`
           - `{ENV}_ONEROSTER_CLIENT_SECRET`

        3. **Explicit configuration**: Pass the URLs and credentials directly.

        Args:
            env: Environment name for loading from environment variables
            base_url: Base URL for the OneRoster API
            auth_url: OAuth2 token endpoint URL
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            timeout: Request timeout in seconds (default: 30)
            provider: Optional TimebackProvider for shared auth
        """
        # Support transport injection mode
        self._transport: Transport | OneRosterTransportLike
        if transport is not None:
            self._transport = transport
            self._provider = None
        else:
            from timeback_common import EnvVarNames, build_provider_env, build_provider_explicit

            env_vars = EnvVarNames(
                base_url="ONEROSTER_BASE_URL",
                auth_url="ONEROSTER_TOKEN_URL",
                client_id="ONEROSTER_CLIENT_ID",
                client_secret="ONEROSTER_CLIENT_SECRET",
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

            self._provider = provider

            endpoint = provider.get_endpoint("oneroster")
            paths = provider.get_paths("oneroster")
            token_manager = provider.get_token_manager("oneroster")

            self._transport = Transport(
                base_url=endpoint.base_url,
                token_manager=token_manager,
                paths=paths,
                timeout=provider.timeout,
                no_auth=token_manager is None,
            )

        # ── Resources (cast needed: duck-typed transports allowed for testing) ──
        _transport = cast("Transport", self._transport)

        # ── Rostering Resources ───────────────────────────────────────────────
        self.users = UsersResource(_transport)
        self.students = StudentsResource(_transport)
        self.teachers = TeachersResource(_transport)
        self.schools = SchoolsResource(_transport)
        self.classes = ClassesResource(_transport)
        self.courses = CoursesResource(_transport)
        self.enrollments = EnrollmentsResource(_transport)
        self.orgs = OrgsResource(_transport)
        self.academic_sessions = AcademicSessionsResource(_transport)
        self.terms = TermsResource(_transport)
        self.grading_periods = GradingPeriodsResource(_transport)
        self.demographics = DemographicsResource(_transport)

        # ── Gradebook Resources ───────────────────────────────────────────────
        self.line_items = LineItemsResource(_transport)
        self.results = ResultsResource(_transport)
        self.categories = CategoriesResource(_transport)
        self.score_scales = ScoreScalesResource(_transport)

        # ── Assessment Resources ──────────────────────────────────────────────
        self.assessment_line_items = AssessmentLineItemsResource(_transport)
        self.assessment_results = AssessmentResultsResource(_transport)

        # ── Resources Resource ────────────────────────────────────────────────
        self.resources = ResourcesResource(_transport)

    def get_transport(self) -> Transport | OneRosterTransportLike:
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

    async def __aenter__(self) -> OneRosterClient:
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
