"""
OneRoster Rostering Types

Types for rostering entities: users, orgs, courses, classes, enrollments, terms.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..utils import normalize_boolean, parse_grades
from .base import Base, RefWithHref

# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS / LITERALS
# ═══════════════════════════════════════════════════════════════════════════════

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

OrgType = Literal[
    "department",
    "school",
    "district",
    "local",
    "state",
    "national",
]

ClassType = Literal["homeroom", "scheduled"]

EnrollmentRole = Literal["administrator", "proctor", "student", "teacher"]


# ═══════════════════════════════════════════════════════════════════════════════
# ORGANIZATION
# ═══════════════════════════════════════════════════════════════════════════════


class Organization(Base):
    """
    An organization such as a school, district, or department.

    Organizations form a hierarchy with parent/child relationships.
    """

    name: str
    type: OrgType
    identifier: str | None = None
    parent: RefWithHref | None = None
    children: list[RefWithHref] | None = None


# ═══════════════════════════════════════════════════════════════════════════════
# USER
# ═══════════════════════════════════════════════════════════════════════════════


class UserRoleAssignment(BaseModel):
    """A role assignment for a user at a specific organization."""

    role_type: Literal["primary", "secondary"] = Field(alias="roleType")
    role: UserRole
    org: RefWithHref | None = None
    begin_date: str | None = Field(default=None, alias="beginDate")
    end_date: str | None = Field(default=None, alias="endDate")

    model_config = ConfigDict(populate_by_name=True)


class UserId(BaseModel):
    """An external user identifier from another system."""

    type: str
    identifier: str


class User(Base):
    """
    A user in the OneRoster system.

    Users can be students, teachers, parents, administrators, or other roles.
    """

    username: str | None = None
    user_ids: list[UserId] | None = Field(default=None, alias="userIds")
    enabled_user: bool = Field(default=True, alias="enabledUser")
    given_name: str = Field(alias="givenName")
    family_name: str = Field(alias="familyName")
    middle_name: str | None = Field(default=None, alias="middleName")
    email: str | None = None
    sms: str | None = None
    phone: str | None = None
    roles: list[UserRoleAssignment] | None = None
    agents: list[RefWithHref] | None = None
    orgs: list[RefWithHref] | None = None
    grades: list[int] | None = None
    password: str | None = None

    @field_validator("enabled_user", mode="before")
    @classmethod
    def _coerce_enabled_user(cls, v: object) -> object:
        if v is None:
            return v
        return normalize_boolean(v)  # type: ignore[arg-type]

    @field_validator("grades", mode="before")
    @classmethod
    def _coerce_grades(cls, v: object) -> object:
        if v is None:
            return None
        return parse_grades(v)  # type: ignore[arg-type]

    model_config = ConfigDict(populate_by_name=True)


# ═══════════════════════════════════════════════════════════════════════════════
# ACADEMIC SESSION
# ═══════════════════════════════════════════════════════════════════════════════

SessionType = Literal[
    "gradingPeriod",
    "semester",
    "schoolYear",
    "term",
]


class AcademicSession(Base):
    """An academic session (term, semester, school year, grading period)."""

    title: str
    type: SessionType
    start_date: str = Field(alias="startDate")
    end_date: str = Field(alias="endDate")
    parent: RefWithHref | None = None
    children: list[RefWithHref] | None = None
    school_year: int | None = Field(default=None, alias="schoolYear")

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def _coerce_date_str(cls, v: object) -> object:
        # Beyond AI OneRoster responses return `startDate`/`endDate` as ISO datetime strings
        # (e.g. "2024-01-01T00:00:00.000Z"). Our SDK surface uses date strings, so normalize.
        if v is None:
            return v
        s = str(v)
        return s.split("T", 1)[0]

    @field_validator("school_year", mode="before")
    @classmethod
    def _coerce_school_year(cls, v: object) -> object:
        # Beyond AI OneRoster responses return `schoolYear` as a number (e.g. 2024).
        # Our model uses an int, so normalize accordingly.
        if v is None:
            return None
        if isinstance(v, int):
            return v
        if isinstance(v, float):
            return int(v)
        if isinstance(v, str):
            return int(v)
        raise ValueError("schoolYear must be a number or numeric string")

    model_config = ConfigDict(populate_by_name=True)


# ═══════════════════════════════════════════════════════════════════════════════
# COURSE
# ═══════════════════════════════════════════════════════════════════════════════


class Course(Base):
    """A course offered by a school."""

    title: str
    school_year: RefWithHref | None = Field(default=None, alias="schoolYear")
    course_code: str | None = Field(default=None, alias="courseCode")
    grades: list[int] | None = None
    subjects: list[str] | None = None
    org: RefWithHref | None = None
    subject_codes: list[str] | None = Field(default=None, alias="subjectCodes")
    resources: list[RefWithHref] | None = None

    @field_validator("grades", mode="before")
    @classmethod
    def _coerce_grades(cls, v: object) -> object:
        if v is None:
            return None
        return parse_grades(v)  # type: ignore[arg-type]

    model_config = ConfigDict(populate_by_name=True)


# ═══════════════════════════════════════════════════════════════════════════════
# CLASS
# ═══════════════════════════════════════════════════════════════════════════════


class Class(Base):
    """A class (section) of a course."""

    title: str
    class_code: str | None = Field(default=None, alias="classCode")
    class_type: ClassType | None = Field(default=None, alias="classType")
    location: str | None = None
    grades: list[int] | None = None
    subjects: list[str] | None = None
    course: RefWithHref | None = None
    school: RefWithHref | None = None
    terms: list[RefWithHref] | None = None
    subject_codes: list[str] | None = Field(default=None, alias="subjectCodes")
    periods: list[str] | None = None
    resources: list[RefWithHref] | None = None

    @field_validator("grades", mode="before")
    @classmethod
    def _coerce_grades(cls, v: object) -> object:
        if v is None:
            return None
        return parse_grades(v)  # type: ignore[arg-type]

    model_config = ConfigDict(populate_by_name=True)


# ═══════════════════════════════════════════════════════════════════════════════
# ENROLLMENT
# ═══════════════════════════════════════════════════════════════════════════════


class Enrollment(Base):
    """An enrollment of a user in a class."""

    user: RefWithHref
    class_: RefWithHref = Field(alias="class")
    school: RefWithHref | None = None
    role: EnrollmentRole
    primary: bool | None = None
    begin_date: str | None = Field(default=None, alias="beginDate")
    end_date: str | None = Field(default=None, alias="endDate")

    model_config = ConfigDict(populate_by_name=True)


# ═══════════════════════════════════════════════════════════════════════════════
# DEMOGRAPHICS
# ═══════════════════════════════════════════════════════════════════════════════

Sex = Literal["male", "female"]


class Demographics(Base):
    """Demographic information for a user."""

    birth_date: str | None = Field(default=None, alias="birthDate")
    sex: Sex | None = None
    american_indian_or_alaska_native: bool | None = Field(
        default=None, alias="americanIndianOrAlaskaNative"
    )
    asian: bool | None = None
    black_or_african_american: bool | None = Field(default=None, alias="blackOrAfricanAmerican")
    native_hawaiian_or_other_pacific_islander: bool | None = Field(
        default=None, alias="nativeHawaiianOrOtherPacificIslander"
    )
    white: bool | None = None
    demographic_race_two_or_more_races: bool | None = Field(
        default=None, alias="demographicRaceTwoOrMoreRaces"
    )
    hispanic_or_latino_ethnicity: bool | None = Field(
        default=None, alias="hispanicOrLatinoEthnicity"
    )
    country_of_birth_code: str | None = Field(default=None, alias="countryOfBirthCode")
    state_of_birth_abbreviation: str | None = Field(default=None, alias="stateOfBirthAbbreviation")
    city_of_birth: str | None = Field(default=None, alias="cityOfBirth")
    public_school_residence_status: str | None = Field(
        default=None, alias="publicSchoolResidenceStatus"
    )

    model_config = ConfigDict(populate_by_name=True)
