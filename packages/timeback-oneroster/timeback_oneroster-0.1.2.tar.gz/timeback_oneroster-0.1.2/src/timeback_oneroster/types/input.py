"""
OneRoster Input Schemas

Pydantic models for validating OneRoster write operation inputs.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# ═══════════════════════════════════════════════════════════════════════════════
# COMMON TYPES
# ═══════════════════════════════════════════════════════════════════════════════

NonEmptyString = Annotated[str, Field(min_length=1)]

Status = Literal["active", "tobedeleted"]

UserRole = Literal[
    "administrator",
    "aide",
    "guardian",
    "parent",
    "proctor",
    "relative",
    "student",
    "teacher",
]

OrganizationType = Literal[
    "department",
    "school",
    "district",
    "local",
    "state",
    "national",
]

ClassType = Literal["homeroom", "scheduled"]

SessionType = Literal["gradingPeriod", "semester", "schoolYear", "term"]

ScoreStatus = Literal[
    "exempt",
    "fully graded",
    "not submitted",
    "partially graded",
    "submitted",
]

EnrollRole = Literal["student", "teacher"]

RoleType = Literal["primary", "secondary"]


class Ref(BaseModel):
    """Reference to another OneRoster entity."""

    sourced_id: NonEmptyString = Field(alias="sourcedId")
    type: str | None = None
    href: str | None = None

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


# ═══════════════════════════════════════════════════════════════════════════════
# USER INPUT
# ═══════════════════════════════════════════════════════════════════════════════


class UserIdInput(BaseModel):
    """External user identifier."""

    type: NonEmptyString
    identifier: NonEmptyString

    model_config = ConfigDict(extra="forbid")


class UserRoleInput(BaseModel):
    """Role assignment for a user."""

    role_type: RoleType = Field(alias="roleType")
    role: UserRole
    org: Ref
    user_profile: str | None = Field(default=None, alias="userProfile")
    metadata: dict[str, Any] | None = None
    begin_date: str | None = Field(default=None, alias="beginDate")
    end_date: str | None = Field(default=None, alias="endDate")

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class UserCreateInput(BaseModel):
    """
    Input for creating a OneRoster user.
    """

    sourced_id: NonEmptyString = Field(alias="sourcedId")
    status: Status | None = None
    enabled_user: bool = Field(alias="enabledUser")
    given_name: NonEmptyString = Field(alias="givenName")
    family_name: NonEmptyString = Field(alias="familyName")
    middle_name: str | None = Field(default=None, alias="middleName")
    username: str | None = None
    email: EmailStr | None = None
    roles: Annotated[list[UserRoleInput], Field(min_length=1)]
    user_ids: list[UserIdInput] | None = Field(default=None, alias="userIds")
    agents: list[Ref] | None = None
    grades: list[str] | None = None
    identifier: str | None = None
    sms: str | None = None
    phone: str | None = None
    pronouns: str | None = None
    password: str | None = None
    metadata: dict[str, Any] | None = None

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


# ═══════════════════════════════════════════════════════════════════════════════
# ORGANIZATION INPUT
# ═══════════════════════════════════════════════════════════════════════════════


class OrgCreateInput(BaseModel):
    """
    Input for creating a OneRoster organization.
    """

    sourced_id: str | None = Field(default=None, alias="sourcedId")
    status: Status | None = None
    name: NonEmptyString
    type: OrganizationType
    identifier: str | None = None
    parent: Ref | None = None
    metadata: dict[str, Any] | None = None

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class SchoolCreateInput(BaseModel):
    """
    Input for creating a OneRoster school.
    """

    sourced_id: str | None = Field(default=None, alias="sourcedId")
    status: Status | None = None
    name: NonEmptyString
    type: Literal["school"] | None = None
    identifier: str | None = None
    parent: Ref | None = None
    metadata: dict[str, Any] | None = None

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


# ═══════════════════════════════════════════════════════════════════════════════
# COURSE INPUT
# ═══════════════════════════════════════════════════════════════════════════════


class CourseCreateInput(BaseModel):
    """
    Input for creating a OneRoster course.
    """

    sourced_id: str | None = Field(default=None, alias="sourcedId")
    status: Status | None = None
    title: NonEmptyString
    org: Ref
    course_code: str | None = Field(default=None, alias="courseCode")
    subjects: list[str] | None = None
    grades: list[str] | None = None
    level: str | None = None
    metadata: dict[str, Any] | None = None

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


# ═══════════════════════════════════════════════════════════════════════════════
# CLASS INPUT
# ═══════════════════════════════════════════════════════════════════════════════


class ClassCreateInput(BaseModel):
    """
    Input for creating a OneRoster class.
    """

    sourced_id: str | None = Field(default=None, alias="sourcedId")
    status: Status | None = None
    title: NonEmptyString
    terms: Annotated[list[Ref], Field(min_length=1)]
    course: Ref
    org: Ref
    class_code: str | None = Field(default=None, alias="classCode")
    class_type: ClassType | None = Field(default=None, alias="classType")
    location: str | None = None
    grades: list[str] | None = None
    subjects: list[str] | None = None
    subject_codes: list[str] | None = Field(default=None, alias="subjectCodes")
    periods: list[str] | None = None
    metadata: dict[str, Any] | None = None

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


# ═══════════════════════════════════════════════════════════════════════════════
# CLASS UPDATE INPUT
# ═══════════════════════════════════════════════════════════════════════════════


class ClassUpdateInput(BaseModel):
    """
    Input for updating a OneRoster class (partial update).
    """

    sourced_id: str | None = Field(default=None, alias="sourcedId")
    status: Status | None = None
    title: NonEmptyString | None = None
    terms: list[Ref] | None = None
    course: Ref | None = None
    org: Ref | None = None
    class_code: str | None = Field(default=None, alias="classCode")
    class_type: ClassType | None = Field(default=None, alias="classType")
    location: str | None = None
    grades: list[str] | None = None
    subjects: list[str] | None = None
    subject_codes: list[str] | None = Field(default=None, alias="subjectCodes")
    periods: list[str] | None = None
    metadata: dict[str, Any] | None = None

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


# ═══════════════════════════════════════════════════════════════════════════════
# ACADEMIC SESSION INPUT
# ═══════════════════════════════════════════════════════════════════════════════


class AcademicSessionCreateInput(BaseModel):
    """
    Input for creating a OneRoster academic session.
    """

    sourced_id: NonEmptyString = Field(alias="sourcedId")
    status: Status
    title: NonEmptyString
    start_date: str = Field(alias="startDate")
    end_date: str = Field(alias="endDate")
    type: SessionType
    school_year: NonEmptyString = Field(alias="schoolYear")
    org: Ref
    parent: Ref | None = None
    children: list[Ref] | None = None
    metadata: dict[str, Any] | None = None

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


# ═══════════════════════════════════════════════════════════════════════════════
# ENROLLMENT INPUT
# ═══════════════════════════════════════════════════════════════════════════════


class EnrollmentCreateInput(BaseModel):
    """
    Input for creating a OneRoster enrollment.
    """

    sourced_id: str | None = Field(default=None, alias="sourcedId")
    status: Status | None = None
    user: Ref
    class_: Ref = Field(alias="class")
    school: Ref | None = None
    role: UserRole
    primary: Literal["true", "false"] | None = None
    begin_date: str | None = Field(default=None, alias="beginDate")
    end_date: str | None = Field(default=None, alias="endDate")
    metadata: dict[str, Any] | None = None

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class EnrollInput(BaseModel):
    """
    Input for the convenience enroll method.
    """

    sourced_id: NonEmptyString = Field(alias="sourcedId")
    role: EnrollRole
    primary: Literal["true", "false"] | None = None
    begin_date: str | None = Field(default=None, alias="beginDate")
    end_date: str | None = Field(default=None, alias="endDate")
    metadata: dict[str, Any] | None = None

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


# ═══════════════════════════════════════════════════════════════════════════════
# GRADEBOOK: CATEGORY INPUT
# ═══════════════════════════════════════════════════════════════════════════════


class CategoryCreateInput(BaseModel):
    """
    Input for creating a OneRoster category.
    """

    sourced_id: str | None = Field(default=None, alias="sourcedId")
    title: NonEmptyString
    status: Status
    weight: float | None = None
    metadata: dict[str, Any] | None = None

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


# ═══════════════════════════════════════════════════════════════════════════════
# GRADEBOOK: LINE ITEM INPUT
# ═══════════════════════════════════════════════════════════════════════════════


class LineItemCreateInput(BaseModel):
    """
    Input for creating a OneRoster line item.
    """

    sourced_id: str | None = Field(default=None, alias="sourcedId")
    title: NonEmptyString
    class_: Ref = Field(alias="class")
    school: Ref
    category: Ref
    assign_date: str = Field(alias="assignDate")
    due_date: str = Field(alias="dueDate")
    status: Status
    description: str | None = None
    result_value_min: float | None = Field(default=None, alias="resultValueMin")
    result_value_max: float | None = Field(default=None, alias="resultValueMax")
    score_scale: Ref | None = Field(default=None, alias="scoreScale")
    metadata: dict[str, Any] | None = None

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


# ═══════════════════════════════════════════════════════════════════════════════
# GRADEBOOK: RESULT INPUT
# ═══════════════════════════════════════════════════════════════════════════════


class ResultCreateInput(BaseModel):
    """
    Input for creating a OneRoster result (grade).
    """

    sourced_id: str | None = Field(default=None, alias="sourcedId")
    line_item: Ref = Field(alias="lineItem")
    student: Ref
    class_: Ref | None = Field(default=None, alias="class")
    score_date: str = Field(alias="scoreDate")
    score_status: ScoreStatus = Field(alias="scoreStatus")
    score: float | None = None
    text_score: str | None = Field(default=None, alias="textScore")
    status: Status
    comment: str | None = None
    metadata: dict[str, Any] | None = None

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


# ═══════════════════════════════════════════════════════════════════════════════
# GRADEBOOK: SCORE SCALE INPUT
# ═══════════════════════════════════════════════════════════════════════════════


class ScoreScaleValueInput(BaseModel):
    """Score scale value entry."""

    item_value_lhs: NonEmptyString = Field(alias="itemValueLHS")
    item_value_rhs: NonEmptyString = Field(alias="itemValueRHS")
    value: str | None = None
    description: str | None = None

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class ScoreScaleCreateInput(BaseModel):
    """
    Input for creating a OneRoster score scale.
    """

    sourced_id: str | None = Field(default=None, alias="sourcedId")
    title: NonEmptyString
    status: Status
    type: NonEmptyString
    class_: Ref | None = Field(default=None, alias="class")
    course: Ref | None = None
    score_scale_value: Annotated[list[ScoreScaleValueInput], Field(min_length=1)] = Field(
        alias="scoreScaleValue"
    )
    min_score: float | None = Field(default=None, alias="minScore")
    max_score: float | None = Field(default=None, alias="maxScore")
    metadata: dict[str, Any] | None = None

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


# ═══════════════════════════════════════════════════════════════════════════════
# RESOURCE INPUT
# ═══════════════════════════════════════════════════════════════════════════════


class ResourceCreateInput(BaseModel):
    """
    Input for creating a OneRoster resource.
    """

    sourced_id: str | None = Field(default=None, alias="sourcedId")
    title: NonEmptyString
    vendor_resource_id: NonEmptyString = Field(alias="vendorResourceId")
    roles: list[RoleType] | None = None
    importance: RoleType | None = None
    vendor_id: str | None = Field(default=None, alias="vendorId")
    application_id: str | None = Field(default=None, alias="applicationId")
    status: Status | None = None
    metadata: dict[str, Any] | None = None

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT INPUT
# ═══════════════════════════════════════════════════════════════════════════════


class AgentInput(BaseModel):
    """
    Input for adding an agent (parent/guardian) relationship.
    """

    agent_sourced_id: NonEmptyString = Field(alias="agentSourcedId")

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


# ═══════════════════════════════════════════════════════════════════════════════
# DEMOGRAPHICS INPUT
# ═══════════════════════════════════════════════════════════════════════════════


class DemographicsCreateInput(BaseModel):
    """
    Input for creating/updating demographics.
    """

    sourced_id: NonEmptyString = Field(alias="sourcedId")

    # Allow extra fields for demographics (uses .loose() in TS)
    model_config = ConfigDict(extra="allow", populate_by_name=True)


# ═══════════════════════════════════════════════════════════════════════════════
# ASSESSMENT INPUT
# ═══════════════════════════════════════════════════════════════════════════════


class AssessmentLineItemCreateInput(BaseModel):
    """
    Input for creating/updating an assessment line item.
    """

    sourced_id: str | None = Field(default=None, alias="sourcedId")
    status: Status
    title: NonEmptyString
    description: str | None = None
    class_: Ref | None = Field(default=None, alias="class")
    parent_assessment_line_item: Ref | None = Field(default=None, alias="parentAssessmentLineItem")
    score_scale: Ref | None = Field(default=None, alias="scoreScale")
    result_value_min: float | None = Field(default=None, alias="resultValueMin")
    result_value_max: float | None = Field(default=None, alias="resultValueMax")
    component: Ref | None = None
    component_resource: Ref | None = Field(default=None, alias="componentResource")
    course: Ref | None = None
    metadata: dict[str, Any] | None = None

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class AssessmentResultCreateInput(BaseModel):
    """
    Input for creating/updating an assessment result.
    """

    sourced_id: str | None = Field(default=None, alias="sourcedId")
    status: Status
    assessment_line_item: Ref = Field(alias="assessmentLineItem")
    student: Ref
    score: float | None = None
    text_score: str | None = Field(default=None, alias="textScore")
    score_date: NonEmptyString = Field(alias="scoreDate")
    score_scale: Ref | None = Field(default=None, alias="scoreScale")
    score_percentile: float | None = Field(default=None, alias="scorePercentile")
    score_status: ScoreStatus = Field(alias="scoreStatus")
    comment: str | None = None
    in_progress: str | None = Field(default=None, alias="inProgress")
    incomplete: str | None = None
    late: str | None = None
    missing: str | None = None
    metadata: dict[str, Any] | None = None

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


__all__ = [
    "AcademicSessionCreateInput",
    "AgentInput",
    "AssessmentLineItemCreateInput",
    "AssessmentResultCreateInput",
    "CategoryCreateInput",
    "ClassCreateInput",
    "ClassUpdateInput",
    "CourseCreateInput",
    "DemographicsCreateInput",
    "EnrollInput",
    "EnrollmentCreateInput",
    "LineItemCreateInput",
    "OrgCreateInput",
    "Ref",
    "ResourceCreateInput",
    "ResultCreateInput",
    "SchoolCreateInput",
    "ScoreScaleCreateInput",
    "ScoreScaleValueInput",
    "UserCreateInput",
    "UserIdInput",
    "UserRoleInput",
]
