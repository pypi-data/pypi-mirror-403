"""Tests for OneRoster types."""

from timeback_oneroster import (
    AcademicSession,
    Class,
    Course,
    Enrollment,
    Organization,
    User,
)


class TestUser:
    """Tests for User model."""

    def test_minimal_user(self):
        """Minimal user should work."""
        user = User(
            sourcedId="user-123",
            givenName="John",
            familyName="Doe",
        )
        assert user.sourced_id == "user-123"
        assert user.given_name == "John"
        assert user.family_name == "Doe"
        assert user.status == "active"

    def test_full_user(self):
        """Full user with all fields should work."""
        user = User(
            sourcedId="user-123",
            status="active",
            givenName="John",
            familyName="Doe",
            middleName="Michael",
            email="john.doe@example.com",
            username="jdoe",
            enabledUser="true",
            grades=["09", "10"],
        )
        assert user.email == "john.doe@example.com"
        assert user.username == "jdoe"
        assert user.enabled_user is True
        assert user.grades == [9, 10]


class TestOrganization:
    """Tests for Organization model."""

    def test_school(self):
        """School organization should work."""
        school = Organization(
            sourcedId="school-123",
            name="Lincoln High School",
            type="school",
            identifier="LHS-001",
        )
        assert school.sourced_id == "school-123"
        assert school.name == "Lincoln High School"
        assert school.type == "school"
        assert school.identifier == "LHS-001"

    def test_district(self):
        """District organization should work."""
        district = Organization(
            sourcedId="district-123",
            name="Springfield School District",
            type="district",
        )
        assert district.type == "district"


class TestClass:
    """Tests for Class model."""

    def test_class(self):
        """Class should work."""
        cls = Class(
            sourcedId="class-123",
            title="Algebra I - Period 1",
            classCode="ALG1-P1",
            classType="scheduled",
            grades=["09"],
            subjects=["Math"],
        )
        assert cls.sourced_id == "class-123"
        assert cls.title == "Algebra I - Period 1"
        assert cls.class_code == "ALG1-P1"
        assert cls.class_type == "scheduled"
        assert cls.grades == [9]


class TestCourse:
    """Tests for Course model."""

    def test_course(self):
        """Course should work."""
        course = Course(
            sourcedId="course-123",
            title="Algebra I",
            courseCode="ALG1",
            grades=["09", "10"],
            subjects=["Math"],
        )
        assert course.sourced_id == "course-123"
        assert course.title == "Algebra I"
        assert course.course_code == "ALG1"
        assert course.grades == [9, 10]


class TestEnrollment:
    """Tests for Enrollment model."""

    def test_enrollment(self):
        """Enrollment should work."""
        enrollment = Enrollment(
            sourcedId="enroll-123",
            user={"sourcedId": "user-123"},
            **{"class": {"sourcedId": "class-123"}},
            role="student",
            primary=True,
        )
        assert enrollment.sourced_id == "enroll-123"
        assert enrollment.user.sourced_id == "user-123"
        assert enrollment.class_.sourced_id == "class-123"
        assert enrollment.role == "student"
        assert enrollment.primary is True


class TestAcademicSession:
    """Tests for AcademicSession model."""

    def test_academic_session_normalization(self):
        session = AcademicSession(
            sourcedId="term-1",
            title="Fall 2024",
            type="term",
            startDate="2024-08-15T00:00:00.000Z",
            endDate="2024-12-20T00:00:00.000Z",
            schoolYear="2024",
        )
        assert session.start_date == "2024-08-15"
        assert session.end_date == "2024-12-20"
        assert session.school_year == 2024
