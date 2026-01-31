"""
OneRoster Resources Types

Types for digital learning resources and content.
"""

from typing import Literal

from pydantic import ConfigDict, Field

from .base import Base, Ref

# ═══════════════════════════════════════════════════════════════════════════════
# RESOURCE
# ═══════════════════════════════════════════════════════════════════════════════


class Resource(Base):
    """
    A digital learning resource (content, activity, or material).

    Resources represent external content that can be assigned to
    students through courses and classes.
    """

    title: str
    vendor_resource_id: str = Field(alias="vendorResourceId")
    vendor_id: str | None = Field(default=None, alias="vendorId")
    application_id: str | None = Field(default=None, alias="applicationId")
    roles: list[Literal["primary", "secondary"]] | None = None
    importance: Literal["primary", "secondary"] | None = None

    model_config = ConfigDict(populate_by_name=True)


# ═══════════════════════════════════════════════════════════════════════════════
# COURSE COMPONENT
# ═══════════════════════════════════════════════════════════════════════════════


class CourseComponent(Base):
    """
    A component or module within a course.

    Course components represent units, lessons, or sections within a course.
    """

    title: str
    course: Ref
    course_component: Ref | None = Field(default=None, alias="courseComponent")
    parent: Ref | None = None
    sort_order: int | None = Field(default=None, alias="sortOrder")
    prerequisites: list[str] | None = None
    prerequisite_criteria: Literal["ALL", "ANY"] | None = Field(
        default=None, alias="prerequisiteCriteria"
    )
    unlock_date: str | None = Field(default=None, alias="unlockDate")

    model_config = ConfigDict(populate_by_name=True)


# ═══════════════════════════════════════════════════════════════════════════════
# COMPONENT RESOURCE
# ═══════════════════════════════════════════════════════════════════════════════


class ComponentResource(Base):
    """
    A resource linked to a course component.

    Component resources map digital content to specific parts
    of a course structure.
    """

    title: str
    course_component: Ref = Field(alias="courseComponent")
    resource: Ref
    sort_order: int | None = Field(default=None, alias="sortOrder")
    lesson_type: str | None = Field(default=None, alias="lessonType")

    model_config = ConfigDict(populate_by_name=True)


# ═══════════════════════════════════════════════════════════════════════════════
# INPUT TYPES
# ═══════════════════════════════════════════════════════════════════════════════


class AgentInput(Base):
    """Input for adding an agent (parent/guardian) relationship."""

    agent: Ref


class CredentialCreateResponse(Base):
    """Response from creating user credentials."""

    user_profile_id: str = Field(alias="userProfileId")
    credential_id: str = Field(alias="credentialId")
    message: str

    model_config = ConfigDict(populate_by_name=True)


class DecryptedCredential(Base):
    """Response from decrypting user credentials."""

    password: str
