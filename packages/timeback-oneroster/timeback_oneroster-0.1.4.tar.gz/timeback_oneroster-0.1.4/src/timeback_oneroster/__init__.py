"""
Timeback OneRoster Client

A Python client for the OneRoster API with async support and lazy pagination.

Example:
    ```python
    from timeback_oneroster import OneRosterClient

    client = OneRosterClient(
        base_url="https://api.example.com",
        client_id="your-client-id",
        client_secret="your-client-secret",
    )

    # List users with pagination
    users = await client.users.list()

    # Stream all users with lazy pagination
    async for user in client.users.stream():
        print(user)

    # Scoped resources
    classes = await client.users("user-id").classes()
    students = await client.schools("school-id").students()
    results = await client.classes("class-id").student("student-id").results()
    ```
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("timeback-oneroster")
except PackageNotFoundError:
    __version__ = "0.0.0"

from .client import OneRosterClient
from .exceptions import (
    APIError,
    AuthenticationError,
    ForbiddenError,
    InputValidationError,
    NotFoundError,
    OneRosterError,
    RateLimitError,
    ServerError,
    TimebackError,
    ValidationError,
    ValidationIssue,
    create_input_validation_error,
)
from .lib import (
    FieldCondition,
    FieldOperators,
    FilterValue,
    WhereClause,
    where_to_filter,
)
from .types import (
    AcademicSession,
    AgentInput,
    AssessmentLineItem,
    AssessmentResult,
    Base,
    Category,
    Class,
    ComponentResource,
    Course,
    CourseComponent,
    CredentialCreateResponse,
    DecryptedCredential,
    Demographics,
    Enrollment,
    EnrollmentRole,
    LineItem,
    ListParams,
    Organization,
    OrgType,
    PageResult,
    Ref,
    RefWithHref,
    Resource,
    Result,
    ResultStatus,
    ScoreScale,
    ScoreScaleValue,
    ScoreStatus,
    SessionType,
    User,
    UserId,
    UserRole,
    UserRoleAssignment,
)
from .utils import (
    normalize_boolean,
    normalize_date_only,
    parse_grades,
)

__all__ = [
    "APIError",
    "AcademicSession",
    "AgentInput",
    "AssessmentLineItem",
    "AssessmentResult",
    "AuthenticationError",
    "Base",
    "Category",
    "Class",
    "ComponentResource",
    "Course",
    "CourseComponent",
    "CredentialCreateResponse",
    "DecryptedCredential",
    "Demographics",
    "Enrollment",
    "EnrollmentRole",
    "FieldCondition",
    "FieldOperators",
    "FilterValue",
    "ForbiddenError",
    "InputValidationError",
    "LineItem",
    "ListParams",
    "NotFoundError",
    "OneRosterClient",
    "OneRosterError",
    "OrgType",
    "Organization",
    "PageResult",
    "RateLimitError",
    "Ref",
    "RefWithHref",
    "Resource",
    "Result",
    "ResultStatus",
    "ScoreScale",
    "ScoreScaleValue",
    "ScoreStatus",
    "ServerError",
    "SessionType",
    "TimebackError",
    "User",
    "UserId",
    "UserRole",
    "UserRoleAssignment",
    "ValidationError",
    "ValidationIssue",
    "WhereClause",
    "__version__",
    "create_input_validation_error",
    "normalize_boolean",
    "normalize_date_only",
    "parse_grades",
    "where_to_filter",
]
