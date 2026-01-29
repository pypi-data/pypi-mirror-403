"""
OneRoster Resources

Resource classes for interacting with the OneRoster API.
"""

from .assessment import (
    AssessmentLineItemsResource,
    AssessmentResultsResource,
    ScopedAssessmentLineItemResource,
)
from .base import CRUDResource, ReadOnlyResource
from .gradebook import (
    CategoriesResource,
    LineItemsResource,
    ResultsResource,
    ScopedLineItemResource,
    ScopedResultResource,
    ScoreScalesResource,
)
from .resources import ResourcesResource, ScopedResourceResource
from .rostering import (
    AcademicSessionsResource,
    ClassesResource,
    CoursesResource,
    DemographicsResource,
    EnrollmentsResource,
    GradingPeriodsResource,
    OrgsResource,
    SchoolsResource,
    ScopedAcademicSessionResource,
    ScopedClassResource,
    ScopedCourseResource,
    ScopedDemographicsResource,
    ScopedEnrollmentResource,
    ScopedGradingPeriodResource,
    ScopedOrgResource,
    ScopedSchoolResource,
    ScopedStudentResource,
    ScopedTeacherResource,
    ScopedTermResource,
    ScopedUserResource,
    StudentsResource,
    TeachersResource,
    TermsResource,
    UsersResource,
)

__all__ = [
    "AcademicSessionsResource",
    "AssessmentLineItemsResource",
    "AssessmentResultsResource",
    "CRUDResource",
    "CategoriesResource",
    "ClassesResource",
    "CoursesResource",
    "DemographicsResource",
    "EnrollmentsResource",
    "GradingPeriodsResource",
    "LineItemsResource",
    "OrgsResource",
    "ReadOnlyResource",
    "ResourcesResource",
    "ResultsResource",
    "SchoolsResource",
    "ScopedAcademicSessionResource",
    "ScopedAssessmentLineItemResource",
    "ScopedClassResource",
    "ScopedCourseResource",
    "ScopedDemographicsResource",
    "ScopedEnrollmentResource",
    "ScopedGradingPeriodResource",
    "ScopedLineItemResource",
    "ScopedOrgResource",
    "ScopedResourceResource",
    "ScopedResultResource",
    "ScopedSchoolResource",
    "ScopedStudentResource",
    "ScopedTeacherResource",
    "ScopedTermResource",
    "ScopedUserResource",
    "ScoreScalesResource",
    "StudentsResource",
    "TeachersResource",
    "TermsResource",
    "UsersResource",
]
