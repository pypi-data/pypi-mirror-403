"""
Rostering Resources
"""

from .academic_sessions import (
    AcademicSessionsResource,
    GradingPeriodsResource,
    ScopedAcademicSessionResource,
    ScopedGradingPeriodResource,
    ScopedTermResource,
    TermsResource,
)
from .classes import (
    ClassesResource,
    ScopedClassAcademicSessionResource,
    ScopedClassLineItemResource,
    ScopedClassResource,
    ScopedClassStudentResource,
)
from .courses import CoursesResource, ScopedCourseResource
from .demographics import DemographicsResource, ScopedDemographicsResource
from .enrollments import EnrollmentsResource, ScopedEnrollmentResource
from .orgs import OrgsResource, ScopedOrgResource
from .schools import SchoolsResource, ScopedSchoolClassResource, ScopedSchoolResource
from .users import (
    ScopedStudentResource,
    ScopedTeacherResource,
    ScopedUserResource,
    StudentsResource,
    TeachersResource,
    UsersResource,
)

__all__ = [
    "AcademicSessionsResource",
    "ClassesResource",
    "CoursesResource",
    "DemographicsResource",
    "EnrollmentsResource",
    "GradingPeriodsResource",
    "OrgsResource",
    "SchoolsResource",
    "ScopedAcademicSessionResource",
    "ScopedClassAcademicSessionResource",
    "ScopedClassLineItemResource",
    "ScopedClassResource",
    "ScopedClassStudentResource",
    "ScopedCourseResource",
    "ScopedDemographicsResource",
    "ScopedEnrollmentResource",
    "ScopedGradingPeriodResource",
    "ScopedOrgResource",
    "ScopedSchoolClassResource",
    "ScopedSchoolResource",
    "ScopedStudentResource",
    "ScopedTeacherResource",
    "ScopedTermResource",
    "ScopedUserResource",
    "StudentsResource",
    "TeachersResource",
    "TermsResource",
    "UsersResource",
]
